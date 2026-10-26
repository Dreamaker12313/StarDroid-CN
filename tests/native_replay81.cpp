// End-to-end replay regression using external, user-supplied original data.
// Records real command bytes against normal economies; does not patch world state.
#include "../native/runtime.cpp"
#include <iostream>
#include <functional>
#include <fstream>
using namespace bwgame;
static int checks=0,scenarios=0;static std::string capturePath;
static void check(bool okay,const char* why){++checks;if(!okay)throw std::runtime_error(why);}
static void rejected(const std::function<void()>& fn,const char* why){bool failed=false;try{fn();}catch(const std::exception&){failed=true;}check(failed,why);}
static void put32(std::vector<uint8_t>& b,size_t at,uint32_t value){for(int i=0;i<4;i++)b.at(at+i)=uint8_t(value>>(i*8));}
static void put64(std::vector<uint8_t>& b,size_t at,uint64_t value){for(int i=0;i<8;i++)b.at(at+i)=uint8_t(value>>(i*8));}
static void rehash(std::vector<uint8_t>& b){put64(b,b.size()-8,native_save::hash_bytes(b.data(),b.size()-8));}
// Serialize simulation and every saved AI field, excluding camera, sounds,
// spectator flags and the replay reader's action-stream cursor.
static uint64_t world_hash(){
 std::vector<uint8_t> bytes;native_save::Codec c(false,bytes,g_ui->st);c.world();
 c.fields(g_ui->current_action_state.selection,g_ui->current_action_state.control_groups);
 if(g_campaign){auto& a=*g_campaign;
  c.fields(a.units_paused,a.objectives,a.countdown_ms,a.timer_paused,a.deaths,a.scores,a.counted_deaths,a.switches,
    a.kills,a.events,a.towns,a.threads,a.spawned,a.ai_actions,a.ai_error,a.ai_trace,a.ai_clock,a.ai_random,a.defence_alerts);
 }
 return native_save::hash(bytes);
}
static uint64_t sync_hash(){bool was=net_active;net_active=true;auto h=net_hash();net_active=was;return h;}
static std::vector<std::pair<std::string,uint64_t>> fields(){
 std::vector<std::pair<std::string,uint64_t>> v;auto add=[&](std::string n,uint64_t value){v.emplace_back(n,value);};auto& st=g_ui->st;
 add("checksum",sim_checksum(st));add("hero",g_ui->game_st.hero_mode);add("team",g_ui->game_st.team_game);
 for(int i=0;i<12;i++){add("vision"+std::to_string(i),st.shared_vision[i]);for(int j=0;j<12;j++)add("ally"+std::to_string(i)+","+std::to_string(j),st.alliances[i][j]);}
 if(g_campaign){add("aiclock",g_campaign->ai_clock);add("airandom",g_campaign->ai_random);int i=0;for(auto& t:g_campaign->threads){std::string n="thread"+std::to_string(i++);add(n+"owner",t.owner);add(n+"pc",t.pc);add(n+"wake",t.wake);add(n+"file",t.file);add(n+"id",t.id);add(n+"done",t.done);for(auto c:t.calls)add(n+"call",c);}i=0;for(auto& t:g_campaign->towns){std::string n="town"+std::to_string(i++);add(n+"active",t.active);add(n+"x",t.center.x);add(n+"y",t.center.y);add(n+"built",t.built);add(n+"trained",t.trained);add(n+"attacks",t.attacks);add(n+"orders",t.orders);for(auto& q:t.builds){add(n+"qtype",q.type);add(n+"qamount",q.amount);add(n+"qpriority",q.priority);}}}
 for(int p=0;p<12;p++){std::string n="player"+std::to_string(p);add(n+"minerals",st.current_minerals[p]);add(n+"gas",st.current_gas[p]);add(n+"victory",st.players[p].victory_state);for(int j=0;j<61;j++)add(n+"upgrade"+std::to_string(j),st.upgrade_levels[p][(UpgradeTypes)j]);for(int j=0;j<44;j++)add(n+"tech"+std::to_string(j),st.tech_researched[p][(TechTypes)j]);for(auto supply:st.supply_used[p])add(n+"supply",supply.raw_value);
 for(auto* u:ptr(st.player_units[p])){std::string n="unit"+std::to_string(u->index);add(n+"generation",u->unit_id_generation);add(n+"type",int(u->unit_type->id));add(n+"flags",u->status_flags);add(n+"energy",u->energy.raw_value);add(n+"shield",u->shield_points.raw_value);add(n+"buildtime",u->remaining_build_time);add(n+"orderstate",u->order_state);add(n+"timer",u->main_order_timer);add(n+"targetx",u->order_target.pos.x);add(n+"targety",u->order_target.pos.y);add(n+"targetunit",g_ui->get_unit_id(u->order_target.unit).raw_value);for(auto* t:u->build_queue)add(n+"queue",int(t->id));}}
 return v;
}
static unit_t* unit(UnitTypes type,int owner=0){for(auto* u:ptr(g_ui->st.player_units[owner]))if(g_ui->unit_is(u,type)&&!g_ui->unit_dying(u))return u;return nullptr;}
static int workers(int owner){int n=0;for(auto* u:ptr(g_ui->st.player_units[owner]))if(g_ui->ut_worker(u)&&g_ui->u_completed(u)&&!g_ui->unit_dying(u))++n;return n;}
static void select(unit_t* u){check(u!=nullptr,"Expected starting unit absent");uint16_t id=g_ui->get_unit_id(u).raw_value;g_ui->cmds.select(&id,1);}
static const UnitTypes workerTypes[]={UnitTypes::Zerg_Drone,UnitTypes::Terran_SCV,UnitTypes::Protoss_Probe};
static const UnitTypes producerTypes[]={UnitTypes::Zerg_Larva,UnitTypes::Terran_Command_Center,UnitTypes::Protoss_Nexus};
static void inputs(int frame,int race,unit_id worker,xy initial){
 auto* u=g_ui->get_unit(worker);check(u&&!g_ui->unit_dying(u),"Starting worker unexpectedly died");
 if(frame==0){select(u);g_ui->cmds.order(Orders::Move,initial+xy(96,0),0,false);}
 if(frame==64){check(u->position!=initial,"Recorded move command did not move worker");select(u);g_ui->cmds.queued(26,false);}
 if(frame==96){
  unit_t* mineral=nullptr;int distance=1000000;
  for(auto* v:ptr(g_ui->st.visible_units))if(g_ui->unit_is_mineral_field(v)){int d=g_ui->xy_length(v->position-u->position);if(d<distance){mineral=v;distance=d;}}
  check(mineral!=nullptr,"Map has no mineral field");select(u);g_ui->cmds.default_order(mineral->position,g_ui->get_unit_id(mineral).raw_value,false);
 }
 if(frame==144){select(unit(producerTypes[race]));g_ui->cmds.type(race==0?35:31,workerTypes[race]);}
}
static void readonly_controls(){
 auto before=world_hash();
 for(int id:{2,7,9,10,11,12,13,14,15,16,17,18,20,23,24,25,29,30})command(id,1,1,1,1);
 command(1,1,3,320,240); // right click must not issue an order
 command(31,1,0,0,0);check(value_query(27,0)==1,"Viewpoint control failed");
 command(31,-1,0,0,0);check(value_query(27,0)==-1,"All-vision control failed");
 command(3,32,-16,0,0);command(4,320,240,0,0);command(0,320,240,0,0);
 command(8,1,0,0,0);command(19,1,0,0,0);command(21,96,0,0,0);
 check(world_hash()==before,"Replay view/input controls mutated simulation or AI");
 check(!g_ui->test_invincible&&!g_ui->test_unlimited_supply,"Replay enabled a cheat");
 check(g_ui->outgoing.empty(),"Replay controls produced live commands");
 command(6,1,0,0,0);int frame=g_ui->st.current_frame;native_step();check(g_ui->st.current_frame==frame,"Paused replay advanced");command(6,0,0,0,0);
}
static std::vector<uint8_t> roundtrip(int race,int difficulty,bool expansion,bool ffa,bool teams,bool heroes,bool defenders){
 constexpr int frames=2200;int races[]={race,(race+1)%3,(race+2)%3,1,1,1,1,1};
 int controllers[]={1,2,(ffa||teams)?2:0,0,0,0,0,0};int teamIds[]={1,2,1,1,1,1,1,1};
 nearby_defenders=defenders;configured_init(640,480,0,races,controllers,difficulty,expansion,ffa,false,teams?teamIds:nullptr,teams,heroes);
 check(native_replay::recording.present,"Recording not initialized");check(g_ui->st.current_minerals[0]==50,"Starting economy modified");
 auto* u=unit(workerTypes[race]);check(u!=nullptr,"Starting worker absent");auto id=g_ui->get_unit_id(u);auto initial=u->position;int initialWorkers=workers(0);
 auto initialWorld=world_hash();std::vector<uint64_t> checkpoints;std::vector<unsigned> sums;std::vector<std::string> observations;std::vector<std::pair<std::string,uint64_t>> expectedFields;
 for(int i=0;i<frames;i++){inputs(i,race,id,initial);native_step();if(!expansion&&i%64==0)openbw_render(i*42.0);if(i==0)expectedFields=fields();checkpoints.push_back(sync_hash());sums.push_back(sim_checksum(g_ui->st));auto* w=g_ui->get_unit(id);observations.push_back(std::to_string(w->position.x)+","+std::to_string(w->position.y)+" order="+std::to_string(int(w->order_type->id))+" RNG="+std::to_string(g_ui->st.lcg_rand_state)+" AI="+std::to_string(g_campaign->ai_clock)+","+std::to_string(g_campaign->ai_random));}
 check(g_ui->st.current_frame==frames,"Live game ended before test duration");check(g_campaign&&g_campaign->ai_error.empty(),"Recorded AI script failed");
 check(workers(0)>initialWorkers,"Recorded train/morph command did not produce worker");
 auto expected=world_hash(),expectedSync=sync_hash();std::vector<uint8_t> savedGame;if(!expansion)savedGame=save_game();auto original=native_replay::save();check(!original.empty(),"Replay not saved");
 auto parsed=native_replay::parse(original.data(),original.size());check(parsed.frames==frames&&parsed.expansion==expansion,"Replay duration/rules metadata wrong");
 check(parsed.actions.size()>30,"Real player inputs absent from replay");check(parsed.rules.difficulty==difficulty&&parsed.rules.ai==unsigned((ffa||teams)?6:2),"AI setup metadata missing");
 check(parsed.rules.heroes==heroes&&parsed.rules.teams==teams&&parsed.rules.defenders==defenders,"Mode/defender flags changed");
 native_replay::open(original.data(),original.size());check(native_replay::active&&value_query(25,0)&&value_query(26,0)==frames,"Replay state queries wrong");
 check(g_ui->game_st.hero_mode==heroes&&g_ui->game_st.team_game==teams,"Replay failed to restore modes");check(world_hash()==initialWorld,"Initial replay world or AI differs");
 readonly_controls();
 for(int i=0;i<frames;i++){
  if(i%211==0){command(31,(i/211)%4-1,0,0,0);command(3,16,-8,0,0);}
  native_step();if(!expansion&&i%64==0)openbw_render(i*42.0);if(sync_hash()!=checkpoints.at(i)){auto gotFields=fields();if(i==0)for(size_t j=0;j<std::min(gotFields.size(),expectedFields.size());j++)if(gotFields[j]!=expectedFields[j])std::cerr<<"FIELD "<<expectedFields[j].first<<"="<<expectedFields[j].second<<" got "<<gotFields[j].first<<"="<<gotFields[j].second<<"\n";auto* w=g_ui->get_unit(id);std::cerr<<"FIRST divergence frame="<<i+1<<" expected sim="<<sums[i]<<" got="<<sim_checksum(g_ui->st)<<" expected "<<observations[i]<<" got "<<w->position.x<<","<<w->position.y<<" order="<<int(w->order_type->id)<<" RNG="<<g_ui->st.lcg_rand_state<<" AI="<<g_campaign->ai_clock<<","<<g_campaign->ai_random<<"\n";check(false,"Replay simulation/AI diverged at checkpoint");}
 }
 check(sync_hash()==expectedSync,"Final replay sync hash differs");check(world_hash()==expected,"Full serialized replay world or AI differs");
 readonly_controls();native_step();check(g_ui->st.current_frame==frames,"Replay advanced beyond its final frame");
 rejected([]{save_game();},"Replay allowed a game save");if(!savedGame.empty()){rejected([&]{restore_game(savedGame);},"Replay allowed restoring a live save");check(native_replay::active&&world_hash()==expected,"Blocked restore changed replay state");}check(native_replay::save().empty(),"Replay playback recorded another replay");
 std::cout<<"PASS roundtrip race="<<race<<" difficulty="<<difficulty<<" expansion="<<expansion<<" ffa="<<ffa<<" teams="<<teams<<" heroes="<<heroes<<" defenders="<<defenders
  <<" frames="<<frames<<" actionBytes="<<parsed.actions.size()<<" worldHash="<<expected<<" syncHash="<<expectedSync<<"\n";
 if(!expansion){
  auto before=world_hash();native_replay::set_view(-1);openbw_render(frames*42.0);check(world_hash()==before,"Final replay render changed simulation");
  int width=openbw_framebuffer_width(),height=openbw_framebuffer_height();auto* pixels=openbw_framebuffer();check(pixels&&width==640&&height==480,"Replay framebuffer missing or incorrectly sized");
  size_t colored=0;for(int i=0;i<width*height;i++)if(pixels[i*4]||pixels[i*4+1]||pixels[i*4+2])++colored;check(colored>1000,"Replay renderer produced an empty frame");
  if(!capturePath.empty()){std::ofstream out(capturePath,std::ios::binary);out<<"P6\n"<<width<<" "<<height<<"\n255\n";for(int i=0;i<width*height;i++)out.write(reinterpret_cast<const char*>(pixels)+i*4,3);check(out.good(),"Could not write replay frame");}
  std::cout<<"PASS native renderer: periodic live/replay updates preserve world parity; 640x480 framebuffer coloredPixels="<<colored<<"\n";
 }
 ++scenarios;return original;
}
// Independent uncompressed classic-file writer permits format corruption with
// valid section CRCs, so tests exercise semantic bounds as well as checksums.
static std::vector<uint8_t> classic(const native_replay::Parsed& p){
 std::vector<uint8_t> out;out.reserve(p.map.size()+p.actions.size()+4096);
 auto push=[&](uint32_t n){size_t at=out.size();out.resize(at+4);put32(out,at,n);};
 auto block=[&](const uint8_t* b,size_t n){data_loading::crc32_t crc;push(crc(b,n));push((n+8191)/8192);for(size_t at=0;at<n;at+=8192){size_t size=std::min(size_t(8192),n-at);push(size);out.insert(out.end(),b+at,b+at+size);}};
 auto number=[&](uint32_t n){uint8_t b[]={uint8_t(n),uint8_t(n>>8),uint8_t(n>>16),uint8_t(n>>24)};block(b,4);};
 number(0x53526572);block(p.header.data(),p.header.size());number(p.actions.size());block(p.actions.data(),p.actions.size());number(p.map.size());block(p.map.data(),p.map.size());return out;
}
static void malformed(const std::vector<uint8_t>& original){
 auto p=native_replay::parse(original.data(),original.size());
 auto repack=[&](const native_replay::Parsed& changed){auto b=classic(changed);b.insert(b.end(),original.begin()+p.classicSize,original.end());rehash(b);return b;};
 auto baseline=repack(p);check(native_replay::parse(baseline.data(),baseline.size()).actions==p.actions,"Independent classic writer changed valid replay");
 auto reject=[&](const std::vector<uint8_t>& b,const char* why){rejected([&]{native_replay::parse(b.data(),b.size());},why);};
 auto damaged=original;damaged.back()^=1;reject(damaged,"Damaged footer checksum accepted");
 damaged=original;damaged[0]^=1;reject(damaged,"Corrupt classic section CRC accepted");
 for(size_t n:{size_t(0),size_t(20),size_t(40),p.classicSize-1,original.size()-1}){damaged.assign(original.begin(),original.begin()+n);reject(damaged,"Truncated replay accepted");}
 rejected([&]{native_replay::parse(original.data(),native_replay::MAX_FILE+1);},"Oversized replay accepted");
 damaged=original;put32(damaged,p.classicSize+8,native_replay::ENGINE+1);rehash(damaged);reject(damaged,"Future replay version accepted");
 damaged=original;damaged[p.classicSize+32]=3;rehash(damaged);reject(damaged,"Invalid AI difficulty accepted");
 damaged=original;put32(damaged,p.classicSize+28,0);rehash(damaged);reject(damaged,"Footer AI mask disagrees with player slots");
 damaged=original;damaged[p.classicSize+33]=1;rehash(damaged);reject(damaged,"Footer viewpoint selected computer as recorder");
 damaged=original;damaged[p.classicSize+35]=2;rehash(damaged);reject(damaged,"Non-boolean team flag accepted");
 damaged=original;damaged[p.classicSize+36]=2;rehash(damaged);reject(damaged,"Non-boolean defender flag accepted");
 damaged=original;damaged[p.classicSize+34]=2;rehash(damaged);reject(damaged,"Non-boolean hero flag accepted");
 damaged=original;damaged[p.classicSize+37]=2;rehash(damaged);reject(damaged,"Invalid alliance flag accepted");
 damaged=original;damaged.insert(damaged.end()-8,1,0);rehash(damaged);reject(damaged,"Unexpected footer bytes accepted");
 auto changed=p;changed.header[0]=2;reject(repack(changed),"Invalid expansion field accepted");
 changed=p;for(int i=1;i<5;i++)changed.header[i]=0;reject(repack(changed),"Zero-frame replay accepted");
 changed=p;changed.header[60]=10;reject(repack(changed),"Unsupported game type accepted");
 changed=p;changed.header[593]=16;reject(repack(changed),"Out-of-range player color accepted");
 changed=p;changed.actions.resize(4);reject(repack(changed),"Truncated action-frame header accepted");
 changed=p;changed.actions[4]=255;changed.actions.resize(8);reject(repack(changed),"Action frame beyond buffer accepted");
 changed=p;for(int i=0;i<4;i++)changed.actions[i]=uint8_t((p.frames+1)>>(i*8));reject(repack(changed),"Action past replay end accepted");
 changed=p;changed.map.clear();reject(repack(changed),"Missing map accepted");
 auto mapChunk=[&](const char* tag,std::initializer_list<uint8_t> body,const char* why){
  auto modified=p;modified.map.insert(modified.map.end(),tag,tag+4);uint32_t n=body.size();for(int i=0;i<4;i++)modified.map.push_back(uint8_t(n>>(i*8)));modified.map.insert(modified.map.end(),body.begin(),body.end());reject(repack(modified),why);
 };
 mapChunk("DIM ",{0,0,64,0},"Zero-width replay map accepted");
 mapChunk("DIM ",{1,1,64,0},"Oversized replay map accepted");
 mapChunk("DIM ",{64,0},"Truncated map dimensions accepted");
 mapChunk("MTXM",{0,0},"Truncated map terrain accepted");
 mapChunk("STRx",{255,255,255,255},"Unbounded extended string table accepted");
 mapChunk("STRx",{1,0,0,0},"Truncated extended string offsets accepted");
 mapChunk("STR ",{1,0},"Truncated classic string offsets accepted");
 mapChunk("STR ",{1,0,255,0,0},"Invalid classic string offset accepted");
 mapChunk("STRx",{1,0,0,0,255,255,255,255,0},"Invalid extended string offset accepted");
 mapChunk("STR ",{1,0,4,0,'x'},"Unterminated classic string accepted");
 mapChunk("STRx",{1,0,0,0,8,0,0,0,'x'},"Unterminated extended string accepted");
 mapChunk("OWNR",{0,0,0,0,0,0,0,0,0,0,0},"Truncated ownership table accepted");
 mapChunk("SIDE",{0,0,0,0,0,0,0,0,0,0,0,255},"Out-of-range map race accepted");
 // A small input with repeated offsets must not expand into gigabytes of strings.
 changed=p;std::vector<uint8_t> duplicated(4+4096*4+16385,'x');put32(duplicated,0,4096);
 for(int i=0;i<4096;i++)put32(duplicated,4+i*4,4+4096*4);duplicated.back()=0;
 changed.map.insert(changed.map.end(),{'S','T','R','x'});for(int i=0;i<4;i++)changed.map.push_back(uint8_t(duplicated.size()>>(i*8)));changed.map.insert(changed.map.end(),duplicated.begin(),duplicated.end());reject(repack(changed),"Duplicate offsets bypassed decoded string budget");

 changed=p;changed.map.push_back(0);reject(repack(changed),"Truncated chunk header accepted");
 changed=p;changed.map.insert(changed.map.end(),{'T','E','S','T',255,255,255,255});reject(repack(changed),"Chunk size outside embedded map accepted");
 reject(std::vector<uint8_t>(original.begin(),original.begin()+p.classicSize),"AI replay without AI settings accepted");
 auto action=[&](std::initializer_list<uint8_t> bytes,const char* why){auto modified=p;modified.actions={0,0,0,0,uint8_t(bytes.size())};modified.actions.insert(modified.actions.end(),bytes.begin(),bytes.end());reject(repack(modified),why);};
 action({0,210,0,0,0,0,0,0,0,0},"Extended cheat command accepted");
 action({0,18,0,0,0,0},"Classic cheat command accepted");
 action({0,255},"Unknown opcode accepted");
 action({0,9,1,0},"Truncated selection command accepted");
 action({0,9,13},"Oversized selection accepted");
 action({255,26,0},"Unknown player ID accepted");
 action({7,26,0},"Inactive player action accepted");
 action({0,31,255,255},"Invalid trained unit type accepted");
 action({0,21,0,0,0,0,0,0,228,0,255,0},"Invalid order index accepted");
 action({0,48,255},"Invalid research type accepted");
 action({0,50,255},"Invalid upgrade type accepted");
 action({0,19,3,0},"Invalid control-group operation accepted");
 action({0,19,0,10},"Out-of-range control group accepted");
 action({0,32,5,0},"Invalid cancelled build-queue slot accepted");
 for(auto bytes:std::vector<std::vector<uint8_t>>{{0,9,0},{0,31,227,0},{0,21,0,0,0,0,0,0,228,0,188,1},{0,48,43},{0,50,60},{0,19,2,9},{0,32,254,0}}){
  auto modified=p;modified.actions={0,0,0,0,uint8_t(bytes.size())};modified.actions.insert(modified.actions.end(),bytes.begin(),bytes.end());auto b=repack(modified);check(native_replay::parse(b.data(),b.size()).actions==modified.actions,"Valid command boundary rejected");
 }
 auto before=world_hash();damaged=original;damaged.back()^=1;rejected([&]{native_replay::open(damaged.data(),damaged.size());},"Corrupt replay opened");check(native_replay::active&&world_hash()==before,"Failed import discarded current playback");
 damaged=original;damaged[p.classicSize+12]^=1;rehash(damaged);rejected([&]{native_replay::open(damaged.data(),damaged.size());},"Different game data signature accepted");check(!g_ui&&!native_replay::active,"Incompatible replay left partial game active");
 std::cout<<"PASS corruption: classic CRC, truncation, total size, version, settings, frame/map/string bounds, command validation, footer integrity and asset mismatch\n";
}
static void map_boundaries(){
 auto chunk=[](native_replay::Parsed& p,const char* tag,const std::vector<uint8_t>& body){p.map.insert(p.map.end(),tag,tag+4);for(int i=0;i<4;i++)p.map.push_back(uint8_t(body.size()>>(i*8)));p.map.insert(p.map.end(),body.begin(),body.end());};
 for(int size:{1,256}){
  native_replay::Parsed p;chunk(p,"DIM ",{uint8_t(size),uint8_t(size>>8),uint8_t(size),uint8_t(size>>8)});chunk(p,"MTXM",std::vector<uint8_t>(size*size*2));
  native_replay::validate_map(p);check(true,"Valid map without strings rejected");
  chunk(p,"STRx",{2,0,0,0,12,0,0,0,12,0,0,0,'o','k',0});native_replay::validate_map(p);check(true,"Small valid shared STRx offsets rejected");
  chunk(p,"STR ",{1,0,4,0,0});native_replay::validate_map(p);check(true,"Valid empty classic string rejected");
 }
 std::cout<<"PASS map admission boundaries: 1/256 dimensions, absent string table, valid STRx and shared offsets\n";
}
static void classic_human(){
 int races[]={1,2,0,1,1,1,1,1},controllers[]={1,0,0,0,0,0,0,0};
 configured_init(640,480,0,races,controllers,2,true,false,false);auto* worker=unit(workerTypes[1]);auto id=g_ui->get_unit_id(worker);auto position=worker->position;
 for(int frame=0;frame<2200;frame++){inputs(frame,1,id,position);native_step();}
 auto expected=world_hash();auto bytes=native_replay::save();auto p=native_replay::parse(bytes.data(),bytes.size());bytes.resize(p.classicSize);
 check(!native_replay::parse(bytes.data(),bytes.size()).rules.present,"Classic human replay incorrectly needs extension");
 native_replay::open(bytes.data(),bytes.size());for(int frame=0;frame<2200;frame++)native_step();check(world_hash()==expected,"Classic human-only replay diverged");++scenarios;
 std::cout<<"PASS classic human-only replay without StarDroid footer; real commands and 2200-frame world parity\n";
}
static void nearby(){
 int races[]={0,1,2,1,1,1,1,1},controllers[]={1,1,2,0,0,0,0,0},teams[]={1,1,2,1,1,1,1,1};
 configured_init(640,480,1,races,controllers,1,true,false,true,teams,true,false);check(net_active,"Nearby recording did not start");
 std::array<unit_id,2> workers;for(int owner=0;owner<2;owner++){auto* w=unit(workerTypes[races[owner]],owner);check(w!=nullptr,"Nearby human worker absent");workers[owner]=g_ui->get_unit_id(w);}
 for(int frame=0;frame<2200;frame+=4){
  std::array<std::vector<uint8_t>,8> batches;
  if(frame==0||frame==64)for(int owner=0;owner<2;owner++){a_vector<uint8_t> bytes;bw_cmd cmd(bytes);uint16_t id=workers[owner].raw_value;cmd.select(&id,1);if(frame==0)cmd.order(Orders::Move,g_ui->get_unit(workers[owner])->position+xy(96,0),0,false);else cmd.queued(26,false);batches[owner].assign(bytes.begin(),bytes.end());}
  net_apply_all(batches);for(int i=0;i<4;i++)net_step();
 }
 auto expected=world_hash();auto bytes=native_replay::save();auto p=native_replay::parse(bytes.data(),bytes.size());check(p.rules.player==1&&p.rules.ai==4&&p.rules.teams,"Nearby player/AI/team metadata changed");
 check(p.actions.size()>40,"Nearby peer command stream was not recorded");native_replay::open(bytes.data(),bytes.size());check(!net_active&&g_ui->my_player==1,"Nearby replay retained network session or wrong viewpoint");
 for(int frame=0;frame<2200;frame++){if(frame%101==0)command(31,frame%3,0,0,0);native_step();}
 check(world_hash()==expected,"Nearby two-human plus AI replay diverged");++scenarios;
 std::cout<<"PASS nearby two-player command streams, allied vision, AI and nonzero local slot; 2200-frame world parity\n";
}
static void eligibility(){
 int races[]={1,2,0,1,1,1,1,1},controllers[]={1,2,0,0,0,0,0,0};
 for(int cheat:{9,10,11,13,29,30}){
  configured_init(640,480,0,races,controllers,2,true,false,false);native_step();command(cheat,1,0,0,0);check(!g_ui->rep_on&&native_replay::save().empty(),"Cheated game exported a replay");
 }
 configured_init(640,480,0,races,controllers,2,true,false,false);native_step();command(23,!nearby_defenders,0,0,0);check(!g_ui->rep_on&&native_replay::save().empty(),"Mid-game defence change exported inaccurate replay");
 configured_init(640,480,0,races,controllers,2,true,false,false);native_step();auto save=save_game();restore_game(save);check(!g_ui->rep_on&&native_replay::save().empty(),"Resumed save exported an incomplete replay");
 std::cout<<"PASS recording eligibility excludes cheats, changed AI behaviour and resumed saves\n";
}
int main(int argc,char** argv){try{
 std::cout.setf(std::ios::unitbuf);check(argc==3||argc==4,"Usage: native-replay81 CORE_DIR MAP [CAPTURE_PPM]");if(argc==4)capturePath=argv[3];std::string core=argv[1];
 open_archive(0,core+"/STARDAT.MPQ");open_archive(1,core+"/BROODAT.MPQ");open_archive(2,core+"/patch_rt.mpq");open_archive(3,argv[2]);
 std::vector<uint8_t> last;
 for(int race=0;race<3;race++)for(int difficulty=0;difficulty<3;difficulty++)
  last=roundtrip(race,difficulty,true,difficulty==1,difficulty==2,race==2&&difficulty==2,(race+difficulty)%2==0);
 last=roundtrip(1,2,false,false,false,false,true);malformed(last);map_boundaries();classic_human();nearby();eligibility();close_game();
 std::cout<<"PASS "<<checks<<" checks in "<<scenarios<<" replay scenarios\n";return 0;
 }catch(const std::exception& e){std::cerr<<"FAIL: "<<e.what()<<"\n";return 1;}}
