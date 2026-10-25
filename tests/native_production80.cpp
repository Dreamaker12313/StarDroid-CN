// Production regressions reuse the original-data, empty campaign fixture.
#define main abilities79_main
#include "native_abilities79.cpp"
#undef main
static decltype(game_state::unit_type_allowed) unitPermissions80;
static void reset80(bool melee=false){reset(melee);game_load_functions(g_ui->player.st()).game_st.unit_type_allowed=unitPermissions80;}
static unit_t* make80(U type,xy pos={1200,3300},int owner=1){
 auto* u=g_ui->create_initial_unit(g_ui->get_unit_type(type),pos,owner);check(u,"Fixture placement failed");
 u->sprite->visibility_flags=255;g_ui->u_set_status_flag(u,unit_t::status_flag_invincible);return u;
}
static int count80(unit_t* u){return g_ui->unit_is_carrier(u)?g_ui->unit_interceptor_count(u):g_ui->unit_scarab_count(u);}
static int capacity80(unit_t* u){return g_ui->unit_is_carrier(u)?g_ui->unit_max_interceptor_count(u):g_ui->unit_max_scarab_count(u);}
static void ammunition80(){
 for(bool melee:{false,true})for(U type:{U::Protoss_Carrier,U::Protoss_Reaver,U::Hero_Gantrithor,U::Hero_Warbringer}){
  reset80(melee);auto* u=make80(type);g_ui->issue_order(u,false,g_ui->get_order_type(g_ui->unit_is_carrier(u)?O::CarrierHoldPosition:O::ReaverHoldPosition),{});
  advance(2);auto order=u->order_type->id;int before=g_ui->st.current_minerals[1],capacity=capacity80(u);
  auto* ammo=g_ui->get_unit_type(g_ui->unit_is_carrier(u)?U::Protoss_Interceptor:U::Protoss_Scarab);
  check(wait([&]{return count80(u)==capacity&&u->build_queue.empty();},5000),"AI did not fill Carrier/Reaver ammunition");
  check(g_ui->st.current_minerals[1]==before-capacity*ammo->mineral_cost,"Ammunition did not charge exact price");
  check(u->order_type->id==order,"Fighter production changed primary Hold order");
  check(!g_campaign->towns[1].active,"Test accidentally activated town");
  before=g_ui->st.current_minerals[1];advance(240);check(count80(u)==capacity&&u->build_queue.empty()&&g_ui->st.current_minerals[1]==before,"Full capacity overfilled or charged");
  auto* lost=g_ui->release_fighter(u);check(lost,"Could not release ammunition");g_ui->kill_unit(lost);advance(8);
  check(wait([&]{return g_ui->st.current_minerals[1]<before&&count80(u)==capacity&&u->build_queue.empty();},1000),"Lost ammunition not replaced");
  if(g_ui->st.current_minerals[1]!=before-ammo->mineral_cost)std::cerr<<"replacement type="<<int(type)<<" count="<<count80(u)<<" minerals="<<g_ui->st.current_minerals[1]<<" expected="<<before-ammo->mineral_cost<<"\n";
  check(g_ui->st.current_minerals[1]==before-ammo->mineral_cost,"Replacement did not charge once");
  std::cout<<"PASS "<<(melee?"custom":"campaign")<<" type="<<int(type)<<" capacity="<<capacity<<" paid fill, replacement and preserved order without active town\n";
 }
 for(U type:{U::Protoss_Carrier,U::Protoss_Reaver}){
  reset80();g_ui->st.upgrade_levels[1][type==U::Protoss_Carrier?UpgradeTypes::Carrier_Capacity:UpgradeTypes::Reaver_Capacity]=1;
  auto* u=make80(type);check(capacity80(u)==(type==U::Protoss_Carrier?8:10),"Capacity upgrade fixture wrong");
  check(wait([&]{return count80(u)==capacity80(u)&&u->build_queue.empty();},5000),"Upgraded ammunition capacity not filled");
 }
 std::cout<<"PASS Carrier and Reaver capacity upgrades\n";
}
static void guards80(){
 reset80();auto* u=make80(U::Protoss_Carrier);int before=g_ui->st.current_minerals[1];
 game_load_functions f(g_ui->player.st());f.game_st.unit_type_allowed[1][U::Protoss_Interceptor]=false;advance(120);
 check(u->build_queue.empty()&&!count80(u)&&g_ui->st.current_minerals[1]==before,"Map-disallowed Interceptors purchased");f.game_st.unit_type_allowed[1][U::Protoss_Interceptor]=true;
 g_ui->st.current_minerals[1]=0;advance(120);check(u->build_queue.empty()&&!count80(u),"Unaffordable ammunition purchased");g_ui->st.current_minerals[1]=before;
 g_campaign->units_paused=true;g_campaign->ai_fighter_production(1);check(u->build_queue.empty(),"Paused scene bought ammunition");g_campaign->units_paused=false;
 g_ui->campaign_control_lock=true;g_campaign->ai_fighter_production(1);check(u->build_queue.empty(),"Locked scene bought ammunition");g_ui->campaign_control_lock=false;
 g_ui->my_player=1;g_campaign->ai_fighter_production(1);check(u->build_queue.empty(),"AI spent human resources");g_ui->my_player=3;
 g_ui->st.players[1].controller=player_t::controller_occupied;g_campaign->ai_fighter_production(1);check(u->build_queue.empty(),"AI controlled occupied player");g_ui->st.players[1].controller=player_t::controller_computer_game;
 g_ui->u_set_status_flag(u,unit_t::status_flag_hallucination);g_campaign->ai_fighter_production(1);check(u->build_queue.empty(),"Hallucination bought ammunition");g_ui->u_unset_status_flag(u,unit_t::status_flag_hallucination);
 g_ui->lockdown_unit(u);g_campaign->ai_fighter_production(1);check(u->build_queue.empty(),"Disabled Carrier bought ammunition");
 reset80();u=make80(U::Protoss_Carrier);g_ui->st.players[1].race=race_t::terran;g_campaign->ai_fighter_production(1);check(!u->build_queue.empty(),"Captured mixed-race Carrier omitted");
 auto snapshot=save_game();advance(600);auto expected=save_game();restore_game(snapshot);advance(600);check(save_game()==expected,"Ammo save continuation diverged");
 std::cout<<"PASS map restrictions, costs, scene locks, human exclusion, hallucination/disabled gates, mixed-race Carrier, deterministic saves\n";
}
static void supply80(){
 for(bool melee:{false,true}){
  reset80(melee);auto* nexus=make80(U::Protoss_Nexus,{1504,3312});make80(U::Protoss_Pylon,{1216,3328});auto* stargate=make80(U::Protoss_Stargate,{1344,3312});make80(U::Protoss_Fleet_Beacon,{1216,3456});make80(U::Protoss_Probe,{1408,3416});advance(32);
  check(g_ui->unit_can_build(stargate,g_ui->get_unit_type(U::Protoss_Carrier)),"Stargate fixture cannot build Carrier");
  auto& town=g_campaign->towns[1];town.active=true;town.center=nexus->position;town.supply=true;town.builds={{72,1,89}};
  g_ui->st.supply_available[1][2]=g_ui->st.supply_used[1][2]+fp1::integer(4);
  check(!g_ui->has_available_supply_for(1,g_ui->get_unit_type(U::Protoss_Carrier)),"Carrier fixture not blocked with 4 spare supply");
  check(g_campaign->ai_supply_demand(1,town.builds)==6,"Carrier supply demand is not 6");
  int pylons=g_campaign->ai_count(1,156);g_campaign->ai_manage(1);
  check(g_campaign->ai_count(1,156)>pylons,"AI did not queue supply for Carrier with 4 spare");
  check(wait([&]{return g_campaign->ai_count(1,72,true)>0;},6000),"AI did not complete Carrier after making supply");
  unit_t* carrier=nullptr;for(auto* v:ptr(g_ui->st.player_units[1]))if(g_ui->unit_is(v,U::Protoss_Carrier)&&g_ui->u_completed(v))carrier=v;
  check(carrier,"Carrier missing");check(wait([&]{return count80(carrier)==capacity80(carrier)&&carrier->build_queue.empty();},3000),"Newly trained Carrier did not train Interceptors");
  std::cout<<"PASS "<<(melee?"custom":"campaign")<<" Carrier request at 4 spare supply builds Pylon, completes Carrier and trains Interceptors\n";
 }
 reset80();make80(U::Protoss_Stargate,{1344,3312});make80(U::Protoss_Pylon,{1216,3328});advance(32);
 a_vector<campaign_ai::request> req{{72,1,89}};check(g_campaign->ai_supply_demand(1,req)==4,"Missing Fleet Beacon incorrectly raises demand");
 make80(U::Protoss_Fleet_Beacon,{1216,3456});advance(4);game_load_functions f(g_ui->player.st());f.game_st.unit_type_allowed[1][U::Protoss_Carrier]=false;
 check(!g_campaign->ai_produce(1,72)&&g_campaign->ai_supply_demand(1,req)==4,"Map-disabled Carrier produced or requested supply");
 std::cout<<"PASS Carrier prerequisite and map-permission restrictions\n";
}
static void naturalMelee80(const char* map){
 open_archive(3,map);g_terran_ai_level=2;custom_ai_race=2;custom_bot_slot=1;
 openbw_init_race_ai(640,480,1,1,2);g_ui->competitive=false;
 check(g_ui->st.current_minerals[1]==50&&g_ui->st.current_gas[1]==0,"Melee fixture must use normal economy");
 std::array<int,4> first{{-1,-1,-1,-1}};const int types[]={72,73,83,85};
 for(int frame=0;frame<60000;++frame){
  native_step();check(g_campaign->ai_error.empty(),g_campaign->ai_error.c_str());
  for(auto* u:ptr(g_ui->st.player_units[0]))if(!g_ui->unit_dying(u)){g_ui->set_unit_hp(u,u->unit_type->hitpoints);g_ui->set_unit_shield_points(u,fp8::integer(u->unit_type->shield_points));}
  for(auto* u:ptr(g_ui->st.player_units[1]))if(g_ui->u_completed(u)&&!g_ui->unit_dying(u))for(int i=0;i<4;++i)if(first[i]<0&&int(u->unit_type->id)==types[i])first[i]=frame;
  if(first[0]>=0&&first[1]>=0&&first[2]>=0&&first[3]>=0)break;
  if(frame%6000==0)std::cout<<"MELEE frame="<<frame<<" "<<g_campaign->ai_status();
 }
 for(int i=0;i<4;++i){std::cout<<"MELEE first completed type="<<types[i]<<" frame="<<first[i]<<"\n";check(first[i]>=0,"Natural melee AI omitted Carrier/Reaver ammunition");}
 std::cout<<"PASS natural hard Protoss melee economy builds Carrier/Interceptors and Reaver/Scarabs without resource boosts\n";
 close_game();
}
int main(int argc,char**argv){try{
 std::cout.setf(std::ios::unitbuf);check(argc==3||argc==4,"native-production80 CORE_DIR BROODWAR_MPQ | CORE_DIR melee MAP");std::string p=argv[1];open_archive(0,p+"/STARDAT.MPQ");open_archive(1,p+"/BROODAT.MPQ");open_archive(2,p+"/patch_rt.mpq");if(argc==4){naturalMelee80(argv[3]);return 0;}setup(argv[2]);
 g_ui->st.players[1].race=race_t::protoss;g_ui->my_player=3;g_ui->st.current_minerals[1]=g_ui->st.current_gas[1]=10000;
 game_load_functions f(g_ui->player.st());for(auto& v:f.game_st.unit_type_allowed[1])v=true;unitPermissions80=f.game_st.unit_type_allowed;clean=save_game();
 ammunition80();guards80();supply80();close_game();return 0;
}catch(const std::exception& e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
