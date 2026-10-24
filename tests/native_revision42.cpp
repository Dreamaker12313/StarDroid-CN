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
int main(int argc,char**argv){std::cout.setf(std::ios::unitbuf);try{
 require(argc>=4,"usage: native-revision42 DATA MAP commands|visibility|placement|ai|smoke");std::string d=argv[1];
 open_archive(0,d+"/STARDAT.MPQ");open_archive(1,d+"/BROODAT.MPQ");open_archive(2,d+"/patch_rt.mpq");open_archive(3,argv[2]);
 std::string mode=argv[3];if(mode=="mission")mission42(std::atoi(argv[4]),argc>5?std::atoi(argv[5]):2400);else if(mode=="commands")commands42();else if(mode=="visibility")visibility42();else if(mode=="placement")placement42();else if(mode=="ai")ai(argc>4?std::atoi(argv[4]):2,argc>5?std::atoi(argv[5]):60000);else if(mode=="smoke")smoke();else if(mode=="cards")cards();else if(mode=="merging")merging();else if(mode=="cargo")cargo();else if(mode=="warnings")warnings();else throw std::runtime_error("Unknown mode");
 close_game();return 0;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
