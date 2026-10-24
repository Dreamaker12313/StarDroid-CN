#define main previous_multiplayer_main
#include "native_multiplayer.cpp"
#undef main
static void game(int slot,bool ffa,int aiRace,bool bw) {
 int races[]={1,2,aiRace,(aiRace+1)%3,1,1,1,1},controllers[]={1,1,2,2,0,0,0,0};
 configured_init(640,480,slot,races,controllers,2,bw,ffa,true);
 require(g_campaign&&g_campaign->melee_ai,"Multiple AI manager missing");
 for(int p=0;p<4;p++)require(count_units(g_ui->st,p)>=5,"Missing starting army");
 require(g_ui->st.alliances[2][3]==(ffa?0:1)&&g_ui->st.alliances[3][2]==(ffa?0:1),"FFA/melee computer alliances differ");
}
static void turns(int frames,bool render=false) {
 for(int n=0;n<frames;n+=4) {
  int frame=g_ui->st.current_frame;auto a=input(0,frame),b=input(1,frame);net_apply(a.data(),a.size(),b.data(),b.size());
  for(int k=0;k<4;k++){net_step();if(render&&(g_ui->my_player==0||(frame+k)%3==0))openbw_render((frame+k)*42.);}
  require(g_campaign->ai_error.empty(),g_campaign->ai_error.c_str());
 }
}
static void controls() {
 close_game();openbw_init(640,480,1,0);g_ui->st.current_minerals[0]=g_ui->st.current_gas[0]=10000;
 auto create=[](UnitTypes type,xy around){auto* ut=g_ui->get_unit_type(type);
 for(int r=0;r<20;r++)for(int dy=-r;dy<=r;dy++)for(int dx=-r;dx<=r;dx++){xy p=around+xy(dx*32,dy*32);if(!g_ui->unit_type_can_fit_at(ut,p))continue;bool free=true;for(auto* u:g_ui->find_units(g_ui->square_at(p,64)))if(!g_ui->unit_dying(u))free=false;if(free){auto* u=g_ui->create_initial_unit(ut,p,0);if(u)return u;}}throw std::runtime_error("No fixture space");};
 auto select=[](unit_t* u){g_ui->current_selection_clear();g_ui->current_selection_add(u);g_ui->on_selection(false);};
 auto* transport=create(UnitTypes::Terran_Dropship,{1000,1000});auto* marine=create(UnitTypes::Terran_Marine,{1000,1100});select(marine);
 g_ui->unit_load_target(transport,marine);g_ui->prune_selection();require(g_ui->current_selection.empty(),"Loaded passenger remains selected");
 auto* bunker=create(UnitTypes::Terran_Bunker,{1100,1200});marine=create(UnitTypes::Terran_Marine,{1100,1300});select(marine);
 g_ui->unit_load_target(bunker,marine);g_ui->prune_selection();require(g_ui->current_selection.empty(),"Bunker passenger remains selected");
 for(UnitTypes type:{UnitTypes::Terran_Command_Center,UnitTypes::Terran_Barracks,UnitTypes::Terran_Factory,UnitTypes::Terran_Starport,UnitTypes::Terran_Science_Facility,UnitTypes::Terran_Engineering_Bay}) {
  auto* building=create(type,{1400,1400});select(building);
  char lift=0;for(auto c:g_ui->card)if(c.act==play_ui::C_LIFT)lift=c.key;require(lift,"Lift missing");g_ui->run_command(lift);
  for(int n=0;n<120;n++)native_step();select(building);require(g_ui->u_flying(building),"Fixture did not lift");
  char land=0;for(auto c:g_ui->card) {
   require(c.act!=play_ui::C_RESEARCH&&c.act!=play_ui::C_UPGRADE,"Airborne research/upgrade shown");
   if(c.act==play_ui::C_TRAIN)require(g_ui->ut_addon(g_ui->get_unit_type(c.ut)),"Airborne unit roster shown");
   if(c.act==play_ui::C_LAND)land=c.key;
  }
  require(land,"Airborne Land missing");g_ui->pending_build=building->unit_type;g_ui->pending_addon=g_ui->get_unit_type(UnitTypes::Terran_Comsat_Station);
  g_ui->run_command(land);require(g_ui->pending_land&&g_ui->pending_build==building->unit_type&&!g_ui->pending_addon&&!g_ui->pending_nydus&&!g_ui->targeting,"Land does not replace addon placement");
  g_ui->clear_pending();g_ui->kill_unit(building);
 }
 close_game();std::cout<<"PASS transport/bunker deselection; six airborne command cards; plain landing replaces addon\n";
}
int main(int argc,char** argv){try{
 if(argc<8)throw std::runtime_error("data map slot ffa aiRace bw output");
 std::string d=argv[1];open_archive(0,d+"/STARDAT.MPQ");open_archive(1,d+"/BROODAT.MPQ");open_archive(2,d+"/patch_rt.mpq");open_archive(3,argv[2]);
 int slot=atoi(argv[3]),race=atoi(argv[5]);bool ffa=atoi(argv[4]),bw=atoi(argv[6]);game(slot,ffa,race,bw);
 std::ofstream trace(argv[7]);trace<<net_assets()<<"\n";
 for(int n=0;n<2400;n+=4){trace<<g_ui->st.current_frame<<" "<<net_hash()<<"\n";turns(4,true);}
 auto snapshot=net_save();long frame=g_ui->st.current_frame;auto hash=net_hash();
 turns(240,true);auto expected=net_hash();
 game(slot,ffa,race,bw);net_restore(snapshot);require(g_ui->st.current_frame==frame&&net_hash()==hash&&g_ui->my_player==slot&&g_ui->fog_player==slot,"Native save restoration differs");
 turns(240,true);require(net_hash()==expected,"Native AI save continuation differs");trace<<net_hash()<<"\n";
 // Restore the exact same snapshot into the other role. Local identity may change;
 // accepted simulation state and every AI thread must remain identical.
 game(1-slot,ffa,race,bw);net_restore(snapshot);require(net_hash()==hash&&g_ui->my_player==1-slot&&g_ui->fog_player==1-slot,"Cross-role restore leaks player identity");
 turns(240,true);require(net_hash()==expected,"Cross-role continuation differs");
 for(int p=2;p<4;p++)require(g_ui->st.total_minerals_gathered[p]>0,"Computer did not mine");
 net_peer_left();require(g_ui->outcome==0,"Leaving human falsely defeated surviving computers");
 trace.close();controls();
 // Single-player custom games retain all three independent original-script AIs.
 int races[]={1,0,1,2,1,1,1,1},controllers[]={1,2,2,2,0,0,0,0};configured_init(640,480,0,races,controllers,1,bw,ffa,false);
 for(int i=0;i<240;i++)native_step();openbw_render(openbw_frame()*42.);auto solo=save_game();for(int i=0;i<32;i++)native_step();auto exact=save_game();
 configured_init(640,480,0,races,controllers,1,bw,ffa,false);restore_game(solo);for(int i=0;i<32;i++)native_step();auto actual=save_game();if(actual!=exact){for(auto pair:{std::make_pair("solo54-expected.bin",&exact),std::make_pair("solo54-actual.bin",&actual)}){std::ofstream out(std::string("build-native/")+pair.first,std::ios::binary);out.write((char*)pair.second->data(),pair.second->size());}}require(actual==exact,"Multiple-computer solo continuation differs");close_game();
 std::cout<<"PASS 0.54 native AI, FFA, cross-role saves and controls slot="<<slot<<" ffa="<<ffa<<" AI="<<race<<" bw="<<bw<<"\n";return 0;
 }catch(const std::exception& e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
