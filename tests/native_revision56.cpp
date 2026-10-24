#define OPENBW_REVISION55_EMBEDDED
#include "native_revision55.cpp"
#undef main
static void steps56(int n){for(int i=0;i<n;i++){openbw_step();g_ui->poll_events();}}
static void setup56(int race,int bots,int humans=1,bool ffa=true,bool bw=true,int level=2,int local=0){
 int races[8],slots[8];for(int i=0;i<8;i++){races[i]=i<humans?1:race;slots[i]=i<humans?1:i<humans+bots?2:0;}
 configured_init(640,480,local,races,slots,level,bw,ffa,humans>1);
}
static void eliminate56(int owner){a_vector<unit_t*> units;for(auto* u:ptr(g_ui->st.player_units[owner]))units.push_back(u);for(auto* u:units)if(!g_ui->unit_dying(u))g_ui->kill_unit(u);steps56(72);}
static void victory56(){
 int cases=0;for(bool bw:{false,true})for(bool ffa:{false,true})for(int race=0;race<3;race++)for(int level=0;level<3;level++){
  setup56(race,3,1,ffa,bw,level);steps56(24);require(!g_ui->outcome,"Premature custom result");
  for(int p=1;p<=3;p++){eliminate56(p);if(p<3)require(!g_ui->outcome,"Victory with remaining opponent");}
  require(g_ui->outcome==1,"No custom victory after all enemies eliminated");cases++;close_game();
 }
 for(bool ai:{false,true})for(bool ffa:{false,true})for(int local=0;local<3;local++){
  setup56(0,ai?2:0,3,ffa,true,2,local);steps56(24);
  for(int p=1;p<(ai?5:3);p++)eliminate56(p);
  require(g_ui->outcome==(local==0?1:2),"Multiplayer result incorrect");cases++;close_game();
 }
 std::cout<<"PASS "<<cases<<" victory cases: original/BW, 3 difficulties, 3 races, Melee/FFA, mixed/all-human network perspectives\n";
}
static void cargo56(){
 setup56(1,0);steps56(2);g_ui->st.upgrade_levels[0][UpgradeTypes::Ventral_Sacs]=1;
 for(auto type:{UnitTypes::Terran_Bunker,UnitTypes::Terran_Dropship,UnitTypes::Protoss_Shuttle,UnitTypes::Zerg_Overlord}){
  auto* carrier=create55(type,0,{1800,1800});select55(carrier);
  auto load=[&](){g_ui->refresh_card();for(auto& c:g_ui->card)if(c.act==play_ui::C_LOAD)return c.enabled?1:-1;return 0;};
  require(load()==1,"Empty transport Load disabled");
  int n=g_ui->unit_space_left(carrier);a_vector<unit_t*> passengers;
  for(int i=0;i<n;i++){auto* u=create55(UnitTypes::Terran_Marine,0,{1800,1600});passengers.push_back(u);g_ui->unit_load_target(carrier,u);}
  require(g_ui->unit_space_left(carrier)==0,"Cargo fixture not full");require(load()==0,"Full transport still offers Load");
  g_ui->unit_unload(passengers.back());require(load()==1,"Load not restored after unload");
 }
 std::cout<<"PASS Bunker/Dropship/Shuttle/transport Overlord empty, full and unload command states\n";close_game();
}
static void detection56(){
 for(bool campaign:{false,true})for(int race=0;race<3;race++)for(bool scan:{false,true}){
  if(scan&&race!=1)continue;setup56(race,1);steps56(2);g_campaign->melee_ai=!campaign;g_campaign->threads.clear();
  auto* victim=create55(UnitTypes::Terran_Marine,1,{1500,1400});auto* enemy=create55(UnitTypes::Protoss_Dark_Templar,0,{1600,1400});
  g_ui->u_set_status_flag(enemy,unit_t::status_flag_cloaked);enemy->detected_flags=1;
  auto* detector=create55(scan?UnitTypes::Terran_Comsat_Station:race==0?UnitTypes::Zerg_Overlord:race==1?UnitTypes::Terran_Science_Vessel:UnitTypes::Protoss_Observer,1,{1200,1400});
  if(scan){auto* cc=create55(UnitTypes::Terran_Command_Center,1,{1000,1400});cc->building.addon=detector;}
  detector->energy=fp8::integer(200);g_ui->stop_unit(detector);g_ui->set_unit_order(detector,g_ui->get_order_type(Orders::Guard));g_campaign->towns[1].active=true;
  g_campaign->on_scenario_attack(victim,enemy);
  require(detector->order_type->id==(scan?Orders::CastScannerSweep:Orders::Move),"AI did not send available detection");
  if(scan){steps56(3);require(detector->energy<fp8::integer(160),"Scan did not spend energy");}
  g_ui->stop_unit(detector);g_ui->set_unit_order(detector,g_ui->get_order_type(Orders::Move),{1000,1000});auto target=detector->order_target.pos;
  g_campaign->ai_detect(victim,enemy);require(detector->order_target.pos==target,"Detection interrupted scripted movement");
  close_game();
 }
 std::cout<<"PASS reactive detection for three races, Comsat energy, campaign existing detectors only, scripted movement retained\n";
}
static void macro56(int race,int frames,int level,bool bw){
 setup56(race,1,1,true,bw,level);g_ui->competitive=false;std::set<int> seen;
 for(int f=0;f<frames;f++){
  steps56(1);require(g_campaign->ai_error.empty(),g_campaign->ai_error.c_str());
  for(auto* u:ptr(g_ui->st.player_units[0]))if(!g_ui->unit_dying(u))g_ui->set_unit_hp(u,u->unit_type->hitpoints);
  for(auto* u:ptr(g_ui->st.player_units[1]))if(g_ui->u_completed(u)&&!g_ui->unit_dying(u))seen.insert(int(u->unit_type->id));
  if(f%6000==0)std::cout<<"AI "<<f<<" "<<g_campaign->ai_status();
 }
 int upgrades=0;for(auto n:g_ui->st.upgrade_levels[1])upgrades+=n;
 int bases=race==0?g_campaign->ai_zerg_bases(1):int(g_campaign->ai_depots(1).size());
 std::cout<<"MACRO race="<<race<<" level="<<level<<" bases="<<bases<<" upgrades="<<upgrades<<" attacks="<<g_campaign->towns[1].attacks<<" types=";for(int t:seen)std::cout<<t<<",";std::cout<<"\n";
 if(bases<2||!seen.count(race==0?39:race==1?9:84))for(auto* u:ptr(g_ui->st.player_units[1]))if(g_ui->ut_worker(u)||!u->build_queue.empty()||!g_ui->u_completed(u))std::cout<<"UNIT type="<<int(u->unit_type->id)<<" order="<<int(u->order_type->id)<<" queue="<<(u->build_queue.empty()?-1:int(u->build_queue.front()->id))<<" pos="<<u->position.x<<","<<u->position.y<<" target="<<u->order_target.pos.x<<","<<u->order_target.pos.y<<"\n";
 if(bases<2||!seen.count(race==0?39:race==1?9:84)){
  std::ofstream svg("build-native/probe56/macro-failure-"+std::to_string(bw)+"-"+std::to_string(race)+"-"+std::to_string(level)+".svg");svg<<"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 2048 2048'><rect width='2048' height='2048' fill='#101820'/>";
  for(int y=0;y<int(g_ui->game_st.map_tile_height*32);y+=8)for(int x=0;x<int(g_ui->game_st.map_tile_width*32);x+=8)if(g_ui->is_walkable({x+4,y+4}))svg<<"<rect x='"<<x<<"' y='"<<y<<"' width='8' height='8' fill='#384651'/>";
  for(int p:{0,1,11})for(auto* u:ptr(g_ui->st.player_units[p]))if(!g_ui->unit_dying(u)){
   auto size=u->unit_type->placement_size;auto pos=u->position-size/2;
   if(g_ui->ut_building(u)||g_ui->unit_is_mineral_field(u))svg<<"<rect x='"<<pos.x<<"' y='"<<pos.y<<"' width='"<<size.x<<"' height='"<<size.y<<"' fill='"<<(p==1?"#338833":p==0?"#aa3333":"#3399aa")<<"' stroke='white'/><text x='"<<u->position.x<<"' y='"<<u->position.y<<"' fill='white' font-size='20'>"<<int(u->unit_type->id)<<"</text>";
   else if(g_ui->ut_worker(u))svg<<"<circle cx='"<<u->position.x<<"' cy='"<<u->position.y<<"' r='6' fill='yellow'/>";
  }svg<<"</svg>";
 }
 require(bases>=2,"AI did not expand");require(upgrades>=5,"AI upgrades stalled");require(g_campaign->towns[1].attacks>=2,"AI did not attack");
 if(!seen.count(race==0?39:race==1?9:84))for(auto* u:ptr(g_ui->st.player_units[1]))if(!u->build_queue.empty()||!g_ui->u_completed(u))std::cout<<"PENDING type="<<int(u->unit_type->id)<<" order="<<int(u->order_type->id)<<" queue="<<(u->build_queue.empty()?-1:int(u->build_queue.front()->id))<<" distance="<<g_ui->xy_length(u->position-u->order_target.pos)<<"\n";
 require(seen.count(race==0?39:race==1?9:84),"AI missing Ultralisk/detector");
 openbw_render(openbw_frame()*42.);auto saved=net_active?net_save():save_game();steps56(48);auto expected=save_game();setup56(race,1,1,true,bw,level);restore_game(saved);require(save_game()==saved,"AI immediate save round trip differs");steps56(48);auto actual=save_game();if(actual!=expected){std::ofstream a("build-native/probe56/expected.sav",std::ios::binary);a.write((char*)expected.data(),expected.size());std::ofstream b("build-native/probe56/actual.sav",std::ios::binary);b.write((char*)actual.data(),actual.size());}require(actual==expected,"AI save continuation differs");
 std::cout<<"PASS macro expansion, upgrades, advanced unit, attacks and exact saved continuation\n";close_game();
}
static void sound56(){
 setup56(1,0);g_ui->fog_player=-1;auto* u=create55(UnitTypes::Zerg_Ultralisk,0,{1500,1500});
 int annoyed=u->unit_type->last_pissed_sound-u->unit_type->first_pissed_sound+1;
 for(int n=0;n<4+annoyed+4;n++){
  naudio::clear_game();for(auto& c:g_ui->sound_channels)c.playing=false;
  std::fill(g_ui->has_loaded_sound.begin(),g_ui->has_loaded_sound.end(),false);
  std::fill(g_ui->last_played_sound.begin(),g_ui->last_played_sound.end(),decltype(g_ui->last_played_sound)::value_type{});
  g_ui->last_selection_ack = {};
  select55(u);int sound=-1;for(auto& c:g_ui->sound_channels)if(c.playing)sound=int(c.sound_type->id);
  if(n<4||n>=4+annoyed)require(sound>=883&&sound<=886,"Ultralisk did not use original normal voice");
  else require(sound==u->unit_type->first_pissed_sound+n-4,"Annoyed sound sequence differs");
 }
 auto clip=[&](const char* path){a_vector<uint8_t>b;g_ui->load_data_file(b,path);return naudio::wav(b.data(),b.size());};
 auto fill=clip("sound/glue/scorefill.wav"),end=clip("sound/glue/scorefillend.wav");
 auto score=naudio::score_clip(*fill,*end,2200);require(score->pcm.size()/score->channels==size_t(score->rate)*2200/1000,"Score clip not exactly count duration");
 require(score->pcm.back()==0,"Score clip cuts off without fade");naudio::clear();naudio::play_clip(score,57);
 std::vector<int16_t> pcm(48000*2);naudio::mix(pcm.data(),48000,48000);require(std::abs(naudio::position_ms(57)-1000)<.1,"Score playback clock drift");
 naudio::mix(pcm.data(),48000,48000);naudio::mix(pcm.data(),9602,48000);require(!naudio::playing(57),"Score audio outlasts counter");
 auto swish=clip("sound/glue/swishin.wav"),lock=clip("sound/glue/swishlock.wav");naudio::play_clip(swish,58);naudio::play_clip(lock,60);naudio::clear_game();require(naudio::playing(58)&&naudio::playing(60),"Lobby reload interrupts menu audio");
 naudio::mix(pcm.data(),48000,48000);require(!naudio::playing(58)&&!naudio::playing(60),"Menu sounds fail to finish");
 std::cout<<"PASS original Ultralisk selection/annoyed/normal cycle; original score fill/end composed to 2200 ms; playback clock; independent complete lobby sounds\n";close_game();
}
#ifdef OPENBW_REVISION56_EMBEDDED
#define main retained_revision56_main
#endif
int main(int argc,char**argv){try{
 require(argc>=4,"data map mode");std::string d=argv[1];open_archive(0,d+"/STARDAT.MPQ");open_archive(1,d+"/BROODAT.MPQ");open_archive(2,d+"/patch_rt.mpq");open_archive(3,argv[2]);std::string mode=argv[3];
 if(mode=="victory")victory56();else if(mode=="cargo")cargo56();else if(mode=="detection")detection56();else if(mode=="sound")sound56();else if(mode=="macro")macro56(std::atoi(argv[4]),argc>5?std::atoi(argv[5]):60000,argc>6?std::atoi(argv[6]):2,argc>7?std::atoi(argv[7])!=0:true);else throw std::runtime_error("Unknown test");return 0;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
