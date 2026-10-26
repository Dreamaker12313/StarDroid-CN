// Exercise the production command stream with original, locally supplied data.
#define main controls80_main
#include "native_controls80.cpp"
#undef main
#include <sstream>
static std::vector<int> columns(const char* raw){std::vector<int> out;std::istringstream in(raw);std::string x;while(std::getline(in,x,'\t'))out.push_back(std::stoi(x));return out;}
static void supply_boundaries(const char* archive){
 setup(archive);int p=g_ui->my_player;auto before=g_ui->st.supply_available;
 for(int race=0;race<3;race++){g_ui->st.supply_available[p][race]=fp1::zero();g_ui->st.supply_used[p][race]=fp1::zero();}
 auto tracked=g_ui->st.supply_available;
 require(!value_query(24,0),"Supply cheat enabled by default");
 for(U t:{U::Zerg_Drone,U::Terran_SCV,U::Protoss_Probe})require(!g_ui->has_available_supply_for(p,g_ui->get_unit_type(t)),"Baseline fixture has supply");
 command(30,1,0,0,0);require(value_query(24,0)&&!g_ui->rep_on,"Cheat did not enable or invalidate recording");
 for(U t:{U::Zerg_Drone,U::Terran_SCV,U::Protoss_Probe})require(g_ui->has_available_supply_for(p,g_ui->get_unit_type(t)),"Cheat failed for one race");
 require(g_ui->st.supply_available==tracked,"Cheat altered real supply counts");
 auto hud=columns(g_ui->resources());require(hud.size()>=11&&hud[3]==200&&hud[6]==200&&hud[8]==200&&hud[10]==200,"Multi-race HUD did not show effective 200 limits");
 for(int race=0;race<3;race++)g_ui->st.supply_used[p][race]=fp1::integer(199);
 for(U t:{U::Zerg_Drone,U::Terran_SCV,U::Protoss_Probe,U::Zerg_Zergling,U::Zerg_Lurker})require(g_ui->has_available_supply_for(p,g_ui->get_unit_type(t)),"Legal final supply rejected");
 require(!g_ui->has_available_supply_for(p,g_ui->get_unit_type(U::Protoss_Zealot)),"Two-supply unit passed 199/200");
 g_ui->st.supply_used[p][0]=fp1::integer(199)+fp1::from_raw(1);
 require(!g_ui->has_available_supply_for(p,g_ui->get_unit_type(U::Zerg_Zergling)),"Two Zerglings exceeded remaining half supply");
 for(int race=0;race<3;race++)g_ui->st.supply_used[p][race]=fp1::integer(200);
 for(U t:{U::Zerg_Drone,U::Terran_SCV,U::Protoss_Probe,U::Zerg_Lurker})require(!g_ui->has_available_supply_for(p,g_ui->get_unit_type(t)),"Hard 200 cap bypassed");
 require(g_ui->has_available_supply_for(p,g_ui->get_unit_type(U::Zerg_Overlord)),"Supply-free Overlord blocked at 200");
 for(int race=0;race<3;race++){g_ui->st.supply_available[1][race]=fp1::zero();g_ui->st.supply_used[1][race]=fp1::zero();}
 require(!g_ui->has_available_supply_for(1,g_ui->get_unit_type(U::Terran_SCV)),"Enemy received free supply");
 g_ui->spectator=true;require(g_ui->available_supply(p,0)==fp1::zero(),"Spectator retained cheat effect");g_ui->spectator=false;
 command(30,0,0,0,0);require(!value_query(24,0)&&g_ui->st.supply_available[p]==tracked[p],"Disabling changed tracked counts");
 std::cout<<"PASS all races: effective 200 HUD, real supply preserved, 199/200 and half-supply boundaries, Lurker delta, enemy/spectator isolation\n";
}
static void supply_training(const char* archive){
 for(auto pair:{std::make_pair(U::Terran_Command_Center,U::Terran_SCV),std::make_pair(U::Protoss_Nexus,U::Protoss_Probe)}){
  setup(archive);int p=g_ui->my_player;auto* hatch=units(U::Zerg_Hatchery,p).front();auto* factory=room(pair.first,p,hatch->position+xy(320,320));
  auto* type=g_ui->get_unit_type(pair.second);int race=int(g_ui->unit_race(type));auto& game=const_cast<game_state&>(g_ui->game_st);game.unit_type_allowed[p][pair.second]=true;
  g_ui->st.supply_available[p][race]=fp1::zero();g_ui->st.supply_used[p][race]=fp1::integer(199);int money=g_ui->st.current_minerals[p];
  g_ui->action_select(p,factory);require(!g_ui->action_train(p,type)&&factory->build_queue.empty()&&g_ui->st.current_minerals[p]==money,"Baseline supply block failed");
  command(30,1,0,0,0);select(factory);g_ui->sync_selection();g_ui->cmd_type(31,pair.second);native_step();
  require(!factory->build_queue.empty()&&g_ui->st.current_minerals[p]==money-type->mineral_cost,"Cheat training did not charge normal cost");
  for(int i=0;i<20&&!factory->current_build_unit;i++)native_step();require(factory->current_build_unit,"Cheat could enqueue but not start training");
  require(g_ui->st.supply_used[p][race]==fp1::integer(200),"Training failed to consume final supply");
  auto id=g_ui->get_unit_id(factory->current_build_unit);for(int i=0;i<800&&!g_ui->u_completed(g_ui->get_unit(id));i++)native_step();
  auto* built=g_ui->get_unit(id);require(built&&g_ui->u_completed(built)&&g_ui->unit_is(built,pair.second),"Normal training did not finish");
  require(factory->build_queue.empty()&&!g_ui->action_train(p,type),"Training continued over hard200cap");
  g_ui->st.supply_used[p][race]=fp1::integer(10);game.unit_type_allowed[p][pair.second]=false;money=g_ui->st.current_minerals[p];require(!g_ui->action_train(p,type)&&g_ui->st.current_minerals[p]==money,"Cheat bypassed map permission");game.unit_type_allowed[p][pair.second]=true;
  g_ui->st.current_minerals[p]=0;require(!g_ui->action_train(p,type)&&factory->build_queue.empty(),"Cheat bypassed resource costs");
  std::cout<<"PASS race="<<race<<" production command starts/finishes paid worker at 199/200 without provider; hardcap, map restrictions and money retained\n";
 }
}
static void supply_morph(const char* archive){
 setup(archive);int p=g_ui->my_player;auto* hatch=units(U::Zerg_Hatchery,p).front();if(units(U::Zerg_Spawning_Pool,p).empty())room(U::Zerg_Spawning_Pool,p,hatch->position+xy(256,96));
 auto larvae=units(U::Zerg_Larva,p);require(larvae.size()>=2,"Fixture needs multiple larvae");larvae.resize(std::min<size_t>(3,larvae.size()));
 auto& game=const_cast<game_state&>(g_ui->game_st);game.unit_type_allowed[p][U::Zerg_Zergling]=true;
 g_ui->st.supply_available[p][0]=fp1::zero();g_ui->st.supply_used[p][0]=fp1::integer(199);auto* ling=g_ui->get_unit_type(U::Zerg_Zergling);int money=g_ui->st.current_minerals[p];size_t before=units(U::Zerg_Zergling,p).size();
 command(30,1,0,0,0);g_ui->action_select(p,larvae);require(g_ui->action_morph(p,ling),"Cheat cannot morph larvae without provider");
 int morphs=0;unit_id egg;for(auto* u:larvae)if(u->order_type->id==Orders::ZergUnitMorph){morphs++;egg=g_ui->get_unit_id(u);}require(morphs==1&&g_ui->st.current_minerals[p]==money-ling->mineral_cost,"Multi-larva selection overreserved supply or overcharged");
 for(int i=0;i<700&&units(U::Zerg_Zergling,p).size()<before+2;i++)native_step();
 require(units(U::Zerg_Zergling,p).size()==before+2&&g_ui->st.supply_used[p][0]==fp1::integer(200),"Two-unit egg did not finish at exact200");
 require(g_ui->st.supply_available[p][0]==fp1::zero(),"Morph fabricated supply providers");
 std::cout<<"PASS multi-larva Zergling command reserves one two-unit egg at199, charges once and finishes at200\n";
}
static void supply_lifecycle(const char* archive){
 setup(archive);int p=g_ui->my_player;auto* hatch=units(U::Zerg_Hatchery,p).front();command(30,1,0,0,0);auto old=g_ui->st.supply_available[p][0];auto* provider=room(U::Zerg_Overlord,p,hatch->position+xy(64,64));auto plus=g_ui->get_unit_type(U::Zerg_Overlord)->supply_provided;
 require(g_ui->st.supply_available[p][0]==old+plus,"Providers stopped updating during cheat");select(provider);auto details=columns(g_ui->unit_details());require(details[7]==plus.integer_part()&&details[9]==200,"Provider details fabricated contribution or hid effective cap");
 g_ui->kill_unit(provider);native_step();command(30,0,0,0,0);require(g_ui->st.supply_available[p][0]==old&&g_ui->available_supply(p,0)==old,"Disabling failed to expose supply lost during cheat");
 auto bytes=save_game();command(30,1,0,0,0);restore_game(bytes);require(!value_query(24,0),"Save restore retained cheat");command(30,1,0,0,0);setup(archive);require(!value_query(24,0),"Newgame retained cheat");net_active=true;command(30,1,0,0,0);require(!value_query(24,0),"Nearby accepted cheat");net_active=false;
 std::cout<<"PASS provider creation/death accounting, original provider contribution, toggle-off, save/newgame reset and multiplayer rejection\n";
}
int main(int argc,char** argv){try{require(argc==3,"Usage: native-supply81 CORE_DIR STARCRAFT_MPQ");std::string data=argv[1];open_archive(0,data+"/STARDAT.MPQ");open_archive(1,data+"/BROODAT.MPQ");open_archive(2,data+"/patch_rt.mpq");supply_boundaries(argv[2]);supply_training(argv[2]);supply_morph(argv[2]);supply_lifecycle(argv[2]);close_game();return 0;}catch(const std::exception& e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
