// Regression checks using original DAT/CHK/GRP assets; no game assets distributed.
#define main revision41_main
#include "native_revision41.cpp"
#undef main
static void commands42(){
 openbw_init(640,480,2,0);g_ui->competitive=false;advance(2);
 g_ui->st.current_minerals[0]=50000;g_ui->st.current_gas[0]=50000;
 auto* archives=create(165);select(archives);require(!find("Feedback"),"Innate Feedback incorrectly researchable");
 auto* dark=create(63);select(dark);require(find("Feedback")&&find("Feedback")->enabled,"Innate Feedback unavailable");
 for(bool d:{false,true}){
  auto* a=create(d?61:67);select(a);const char* label=d?"Dark Archon":"Merge Archon";
  require(find(label)&&!find(label)->enabled,"Single Templar merge is not grey");
  auto* b=create(d?61:67);g_ui->current_selection.push_back(g_ui->get_unit_id(b));g_ui->refresh_card();
  require(find(label)&&find(label)->enabled,"Templar pair cannot merge");
  g_ui->kill_unit(b);advance(4);g_ui->refresh_card();require(!find(label)->enabled,"Dead partner permits merge");
 }
 for(int type:{72,83}){
  auto* full=create(type);auto* empty=create(type);select(full);action_state state;action_functions af(g_ui->st,state);af.action_select(0,full);
  int cap=type==72?g_ui->unit_max_interceptor_count(full):g_ui->unit_max_scarab_count(full);
  for(int n=0;n<cap;n++){require(af.action_train_fighter(0),"Cannot fill carrier/reaver");advance(320);}
  g_ui->current_selection.push_back(g_ui->get_unit_id(empty));g_ui->refresh_card();const char* label=type==72?"Build Interceptor":"Build Scarab";
  require(find(label),"Full primary hides group ammunition button");g_ui->run_command(find(label)->key);advance(3);
  require(!empty->build_queue.empty()||g_ui->unit_queued_fighter_units(empty)>0,"Group command did not train at empty producer");
 }
 auto* shuttle=create(69);select(shuttle);require(find("Load")&&!find("Unload"),"Empty shuttle cargo buttons wrong");
 for(int n=0;n<8;n++){auto* marine=create(0);g_ui->unit_load_target(shuttle,marine);}
 g_ui->refresh_card();require(!find("Load")&&find("Unload"),"Full shuttle cargo buttons wrong");
 auto* battery=create(172);create(156,battery->position);advance(32);select(battery);
 require(find("Recharge Shields")&&find("Recharge Shields")->enabled,"Battery recharge button absent");
 require(g_ui->card_text.find("\t308\t")!=a_string::npos,"Original battery icon absent");
 auto* zealot=create(65,battery->position);g_ui->set_unit_shield_points(zealot,0_fp8);battery->energy=200_fp8;
 g_ui->run_command(find("Recharge Shields")->key);g_ui->issue_target(zealot->position);advance(500);
 require(zealot->shield_points>30_fp8,"Recharge button did not replenish shields");
 snapshot();std::cout<<"PASS innate tech, group ammunition, merge pairs, cargo visibility, battery recharge\n";close_game();
}
static void visibility42(){
 openbw_init(640,480,1,0);g_ui->competitive=false;advance(2);
 auto* enemy=create(8);g_ui->set_unit_owner(enemy,1,false);enemy->sprite->visibility_flags=1;g_ui->u_set_status_flag(enemy,unit_t::status_flag_cloaked);enemy->detected_flags=2;
 require(g_ui->unit_hidden_by_fog(enemy),"Undetected enemy cloak is visible");
 require(g_ui->select_get_unit_at(enemy->position)!=enemy,"Undetected cloak selectable");
 enemy->detected_flags|=1;require(!g_ui->unit_hidden_by_fog(enemy),"Detected cloak is hidden");
 g_ui->set_unit_owner(enemy,0,false);enemy->detected_flags=0;require(!g_ui->unit_hidden_by_fog(enemy),"Own cloak hidden");
 auto* building=create(109);g_ui->set_unit_owner(building,1,false);building->sprite->visibility_flags=0;
 auto& tile=g_ui->st.tiles[(building->position.y/32)*g_ui->game_st.map_tile_width+building->position.x/32];tile.explored&=~1;tile.visible|=1;
 g_ui->seed_explored_structures();require(g_ui->fog_snapshots[building->sprite->index].valid,"Mission explored structure lacks initial snapshot");
 auto* unseen=create(109,{1600,1600});g_ui->set_unit_owner(unseen,1,false);unseen->sprite->visibility_flags=0;
 require(!g_ui->fog_snapshots[unseen->sprite->index].valid,"Later construction leaked into explored fog");
 auto* mobile=create(0,building->position);g_ui->set_unit_owner(mobile,1,false);mobile->sprite->visibility_flags=0;
 require(g_ui->unit_hidden_by_fog(mobile),"Explored terrain leaks mobile units");
 auto* reveal=create(101,mobile->position);advance(64);
 require(!g_ui->unit_hidden_by_fog(mobile),"Map Revealer fails to show ordinary unit");
 std::cout<<"PASS cloak detection, initial explored structures, current map-revealer vision\n";close_game();
}
static void placement42(){
 openbw_init(640,480,1,0);g_ui->competitive=false;advance(2);
 auto* worker=create(7);select(worker);g_ui->screen_pos=worker->position-xy(320,240);
 for(auto& t:g_ui->st.tiles){t.visible=0;t.explored=0;}
 for(auto spec:{std::pair<int,int>{160,860},{142,859},{110,858}}){
  g_ui->pending_build=g_ui->get_unit_type(UnitTypes(spec.first));int seq=g_ui->error_seq;
  require(!g_ui->placement_valid(320,160),"Invalid placement fixture unexpectedly valid");g_ui->place_pending(320,160);
  require(g_ui->error_seq==seq+1&&g_ui->error_text==g_ui->stat_name(spec.second),"Wrong placement warning");require(g_ui->pending_build,"Invalid placement cancels ghost");
 }
 g_ui->pending_build=g_ui->get_unit_type(UnitTypes::Terran_Barracks);int tx,ty;g_ui->placement_tile(worker->position,tx,ty);
 g_ui->st.tiles[ty*g_ui->game_st.map_tile_width+tx].flags|=tile_t::flag_unbuildable;
 g_ui->place_pending(320,240);require(g_ui->error_text==g_ui->stat_name(855),"Blocked terrain missing warning");
 std::cout<<"PASS original invalid terrain, creep, pylon and geyser warnings\n";close_game();
}
static void mission42(int code,int frames){
 openbw_init_campaign(640,480,code);int seeded=0;
 for(auto& snap:g_ui->fog_snapshots)if(snap.valid)++seeded;
 advance(frames);require(g_campaign&&g_campaign->ai_error.empty(),"Mission AI script failed");snapshot();
 std::cout<<"PASS mission "<<code<<" frames="<<frames<<" initialFogSnapshots="<<seeded<<" outcome="<<g_ui->outcome<<" saveContinuation=exact fullPlaythrough=false\n";
 close_game();
}
static void protoss43(int level,int frames,bool disrupt=false){
 g_terran_ai_level=level;custom_ai_race=2;custom_bot_slot=1;openbw_init_race_ai(640,480,1,1,2);g_ui->competitive=false;std::set<int> seen;int restoredPower=0,firstDamage=-1;
 require(g_ui->st.players[1].race==race_t::protoss,"Opponent race is not Protoss");
 require(g_ui->st.current_minerals[1]==50&&g_ui->st.current_gas[1]==0,"AI starting resources modified");
 for(int f=0;f<frames;f++){
  native_step();require(g_campaign->ai_error.empty(),g_campaign->ai_error.c_str());
  for(auto* u:ptr(g_ui->st.player_units[0]))if(!g_ui->unit_dying(u)){if(u->hp<u->unit_type->hitpoints&&firstDamage<0)firstDamage=f;g_ui->set_unit_hp(u,u->unit_type->hitpoints);}
  for(auto* u:ptr(g_ui->st.player_units[1]))if(g_ui->u_completed(u)&&!g_ui->unit_dying(u))seen.insert(int(u->unit_type->id));
  if(disrupt&&f==18000){std::vector<unit_t*> pylons;for(auto* u:ptr(g_ui->st.player_units[1]))if(g_ui->unit_is(u,UnitTypes::Protoss_Pylon))pylons.push_back(u);require(!pylons.empty(),"No power grid to disrupt");for(auto* u:pylons)g_ui->kill_unit(u);}
  if(disrupt&&f>18000&&restoredPower==0)for(auto* u:ptr(g_ui->st.player_units[1]))if(g_ui->ut_requires_psionic_matrix(u)&&g_ui->u_completed(u)&&g_ui->is_in_psionic_matrix(1,u->position)){restoredPower=f;break;}
  if(f%6000==0){std::cout<<"AI "<<f<<" "<<g_campaign->ai_status()<<" types:";for(int t:seen)std::cout<<t<<",";std::cout<<"\n";}
 }
 std::cout<<"FINAL types:";for(int t:seen)std::cout<<t<<",";std::cout<<"\n";
 for(auto* u:ptr(g_ui->st.player_units[1]))if(g_ui->ut_building(u))std::cout<<"BUILDING "<<int(u->unit_type->id)<<" "<<u->position.x<<","<<u->position.y<<" completed="<<g_ui->u_completed(u)<<" powered="<<g_ui->is_in_psionic_matrix(1,u->position)<<"\n";
 for(int i=0;i<228;i++)if(g_campaign->towns[1].wave[i]||g_campaign->towns[1].defence[i])std::cout<<"REQ "<<i<<" wave="<<g_campaign->towns[1].wave[i]<<" def="<<g_campaign->towns[1].defence[i]<<" count="<<g_campaign->ai_count(1,i)<<"\n";
 for(auto* u:ptr(g_ui->st.player_units[1]))if(g_ui->ut_worker(u))std::cout<<"WORKER "<<u->position.x<<","<<u->position.y<<" order="<<int(u->order_type->id)<<" build="<<(u->build_queue.empty()?-1:int(u->build_queue.front()->id))<<"\n";
 std::cout<<"METRICS bases="<<g_campaign->ai_count(1,154,true)<<" gas="<<g_campaign->ai_count(1,157,true)<<" attacks="<<g_campaign->towns[1].attacks<<" minerals="<<g_ui->st.total_minerals_gathered[1]<<" gasGathered="<<g_ui->st.total_gas_gathered[1]<<" firstDamage="<<firstDamage<<" powerRecovered="<<restoredPower<<"\n";
 for(auto id:g_campaign->towns[1].attackers)if(auto* u=g_ui->get_unit(id))require(!g_ui->unit_is_fighter(u),"AI detached ammunition from its parent");
 require(g_campaign->towns[1].attacks>=3&&firstDamage>=0,"Protoss failed to attack opponent");
 require(g_campaign->ai_count(1,154,true)>=2&&g_campaign->ai_count(1,157,true)>=2,"Protoss failed to expand mining");
 require(g_ui->st.total_gas_gathered[1]>3000,"Protoss gas harvesting stalled");
 for(int type:{64,65,66,84,72,73,83,85})require(seen.count(type),"Protoss missing core/support/ammunition unit");
 if(level==2)for(int type:{60,61,67,68,70,71})require(seen.count(type),"Protoss missing advanced unit");
 if(disrupt)require(restoredPower>18000&&restoredPower<24000,"Protoss failed to restore destroyed power grid");
 openbw_render(openbw_frame()*42.);auto saved=save_game();advance(32);auto expected=save_game();
 close_game();openbw_init_race_ai(640,480,1,1,2);restore_game(saved);require(save_game()==saved,"Fresh-init Protoss save round trip differs");advance(32);require(save_game()==expected,"Fresh-init Protoss save continuation differs");
 std::cout<<"PASS Protoss level="<<level<<" frames="<<frames<<" freshInitSave32=exact\n";close_game();
}
static void retired43(){
 openbw_init(640,480,0,0);advance(2);native_save::HostState old;old.bot_slot=1;old.bot_enabled=true;
 auto saved=native_save::save(*g_ui,g_campaign,old),before=save_game();bool rejected=false;
 try{restore_game(saved);}catch(const std::exception&e){rejected=std::string(e.what()).find("removed Zerg skirmish AI")!=std::string::npos;}
 require(rejected&&save_game()==before,"Retired bot save silently loaded or changed live state");
 require(g_ui->st.players[0].race==race_t::zerg,"Human Zerg race removed");close_game();
 std::cout<<"PASS retired bot save rejected before mutation; human Zerg remains playable\n";
}
#ifdef OPENBW_REVISION43_EMBEDDED
#define main revision43_main
#endif
int main(int argc,char**argv){std::cout.setf(std::ios::unitbuf);try{
 require(argc>=4,"usage: native-revision43 DATA MAP MODE");std::string d=argv[1];
 open_archive(0,d+"/STARDAT.MPQ");open_archive(1,d+"/BROODAT.MPQ");open_archive(2,d+"/patch_rt.mpq");open_archive(3,argv[2]);
 std::string mode=argv[3];if(mode=="protoss")protoss43(argc>4?std::atoi(argv[4]):2,argc>5?std::atoi(argv[5]):60000,argc>6);else if(mode=="retired")retired43();else if(mode=="mission")mission42(std::atoi(argv[4]),2400);else if(mode=="commands")commands42();else if(mode=="visibility")visibility42();else if(mode=="placement")placement42();else if(mode=="ai")ai(argc>4?std::atoi(argv[4]):2,argc>5?std::atoi(argv[5]):60000);else if(mode=="smoke")smoke();else if(mode=="cards")cards();else if(mode=="merging")merging();else if(mode=="cargo")cargo();else if(mode=="warnings")warnings();else throw std::runtime_error("Unknown mode");close_game();return 0;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
