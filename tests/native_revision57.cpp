#define OPENBW_REVISION56_EMBEDDED
#include "native_revision56.cpp"
#undef main
using U = UnitTypes;
static void setup57(){setup56(1,0);g_ui->competitive=false;g_ui->fog_player=-1;}
static void reset_audio57(){
 for(size_t i=0;i<g_ui->sound_channels.size();i++){native_sound::stop(i);g_ui->sound_channels[i].playing=false;}
 std::fill(g_ui->last_played_sound.begin(),g_ui->last_played_sound.end(),decltype(g_ui->last_played_sound)::value_type{});
 g_ui->last_selection_ack={};
}
static int active_sound57(){for(auto& c:g_ui->sound_channels)if(c.playing&&native_sound::is_playing(&c-g_ui->sound_channels.data()))return int(c.sound_type->id);return -1;}
static void power57(){
 for(bool bw:{false,true}){
 setup56(1,0,1,true,bw);g_ui->competitive=false;g_ui->fog_player=-1;
 std::map<U,unit_t*> buildings;int n=0;
 for(auto& t:g_ui->game_st.unit_types.vec)if(g_ui->ut_building(&t)&&g_ui->unit_race(&t)==race_t::protoss&&int(t.id)>=154&&int(t.id)<=172&&int(t.id)!=158&&int(t.id)!=161&&int(t.id)!=168){
  auto* u=create55(t.id,0,{600+(n%5)*240,600+(n/5)*240});n++;buildings[t.id]=u;g_ui->u_unset_status_flag(u,unit_t::status_flag_disabled);
 }
 auto* probe=create55(U::Protoss_Probe,0,{1600,1700});
 int disabled=0,requirements=0;
 for(auto [type,u]:buildings){
  if(!g_ui->ut_requires_psionic_matrix(u)){require(!g_ui->unit_unpowered(u),"Nexus/Pylon/Assimilator classified unpowered");continue;}
  g_ui->u_set_status_flag(u,unit_t::status_flag_disabled);select55(u);require(g_ui->card.empty(),"Unpowered building command icons remain");
  require(g_ui->card_text.find(g_ui->stat_name(829))!=a_string::npos,"Original red Unpowered text absent");
  require(g_ui->build_status()==std::string(""),"Unpowered queue obscures status");
  require(!g_ui->player_has_active_tech(0,type),"Unpowered tech counted");
  reset_audio57();select55(u);require(active_sound57()==116,"Unpowered click sound is not PPwrDown");
  for(auto& t:g_ui->game_st.unit_types.vec)require(!g_ui->unit_can_build(u,&t),"Unpowered producer trains");
  for(auto& t:g_ui->game_st.tech_types.vec)require(!g_ui->unit_can_research(u,&t),"Unpowered building researches");
  for(auto& t:g_ui->game_st.upgrade_types.vec)require(!g_ui->unit_can_upgrade(u,&t),"Unpowered building upgrades");
  g_ui->u_unset_status_flag(u,unit_t::status_flag_disabled);require(g_ui->player_has_active_tech(0,type),"Repowered tech missing");disabled++;
 }
 struct Dep{U producer,target,tech;};
 for(auto d:{Dep{U::Protoss_Gateway,U::Protoss_Dragoon,U::Protoss_Cybernetics_Core},
  Dep{U::Protoss_Gateway,U::Protoss_High_Templar,U::Protoss_Templar_Archives},
  Dep{U::Protoss_Stargate,U::Protoss_Carrier,U::Protoss_Fleet_Beacon},
  Dep{U::Protoss_Stargate,U::Protoss_Arbiter,U::Protoss_Arbiter_Tribunal},
  Dep{U::Protoss_Robotics_Facility,U::Protoss_Reaver,U::Protoss_Robotics_Support_Bay},
  Dep{U::Protoss_Robotics_Facility,U::Protoss_Observer,U::Protoss_Observatory}}){
  auto* producer=buildings.at(d.producer);auto* tech=buildings.at(d.tech);auto* target=g_ui->get_unit_type(d.target);
  require(g_ui->unit_can_build(producer,target),"Powered prerequisite does not enable unit");
  g_ui->u_set_status_flag(tech,unit_t::status_flag_disabled);require(!g_ui->unit_can_build(producer,target),"Unpowered prerequisite enables unit");
  auto* backup=create55(d.tech,0,{1800,1500});g_ui->u_unset_status_flag(backup,unit_t::status_flag_disabled);
  require(g_ui->unit_can_build(producer,target),"Second powered prerequisite does not enable unit");
  g_ui->u_set_status_flag(backup,unit_t::status_flag_disabled);require(!g_ui->unit_can_build(producer,target),"Two unpowered prerequisites enable unit");
  g_ui->u_unset_status_flag(tech,unit_t::status_flag_disabled);g_ui->kill_unit(backup);requirements++;
 }
 // All Probe structures with power-dependent prerequisites.
 for(auto d:{Dep{U::Protoss_Probe,U::Protoss_Cybernetics_Core,U::Protoss_Gateway},Dep{U::Protoss_Probe,U::Protoss_Stargate,U::Protoss_Cybernetics_Core},Dep{U::Protoss_Probe,U::Protoss_Templar_Archives,U::Protoss_Citadel_of_Adun},Dep{U::Protoss_Probe,U::Protoss_Fleet_Beacon,U::Protoss_Stargate},Dep{U::Protoss_Probe,U::Protoss_Photon_Cannon,U::Protoss_Forge},Dep{U::Protoss_Probe,U::Protoss_Observatory,U::Protoss_Robotics_Facility}}){
  auto* tech=buildings.at(d.tech);auto* target=g_ui->get_unit_type(d.target);require(g_ui->unit_can_build(probe,target),"Powered structure dependency blocked");g_ui->u_set_status_flag(tech,unit_t::status_flag_disabled);require(!g_ui->unit_can_build(probe,target),"Unpowered structure dependency allowed");g_ui->u_unset_status_flag(tech,unit_t::status_flag_disabled);requirements++;
 }
 for(auto id:{UpgradeTypes::Protoss_Ground_Weapons,UpgradeTypes::Protoss_Ground_Armor,UpgradeTypes::Protoss_Air_Weapons,UpgradeTypes::Protoss_Air_Armor,UpgradeTypes::Protoss_Plasma_Shields}){
  bool air=id==UpgradeTypes::Protoss_Air_Weapons||id==UpgradeTypes::Protoss_Air_Armor;
  auto* producer=buildings.at(air?U::Protoss_Cybernetics_Core:U::Protoss_Forge);
  auto* tech=buildings.at(air?U::Protoss_Fleet_Beacon:id==UpgradeTypes::Protoss_Plasma_Shields?U::Protoss_Cybernetics_Core:U::Protoss_Templar_Archives);
  g_ui->st.upgrade_levels[0][id]=1;auto* up=g_ui->get_upgrade_type(id);require(g_ui->unit_can_upgrade(producer,up),"Powered level 2 upgrade blocked");g_ui->u_set_status_flag(tech,unit_t::status_flag_disabled);require(!g_ui->unit_can_upgrade(producer,up),"Unpowered level 2 prerequisite allowed");g_ui->u_unset_status_flag(tech,unit_t::status_flag_disabled);requirements++;
 }
 std::cout<<"PASS power expansion="<<bw<<" disabled building types="<<disabled<<" unit/building/upgrade dependencies="<<requirements<<" original red status and sound; second powered provider\n";close_game();
 }
 // Exercise real Pylon power transitions rather than just disabled-state fixtures.
 setup57();auto* gate=create55(U::Protoss_Gateway,0,{1000,1000});g_ui->update_psionic_matrix();require(g_ui->unit_unpowered(gate),"Unpowered fixture unexpectedly powered");
 auto* pylon=create55(U::Protoss_Pylon,0,gate->position+xy(128,0));steps56(24);g_ui->update_psionic_matrix();require(!g_ui->unit_unpowered(gate),"Pylon failed to power Gateway");g_ui->kill_unit(pylon);steps56(24);g_ui->update_psionic_matrix();require(g_ui->unit_unpowered(gate),"Destroyed Pylon retained power");
 auto saved=save_game();restore_game(saved);require(save_game()==saved,"Power-state save round trip differs");
 std::cout<<"PASS actual Pylon construction/destruction and saved power state\n";close_game();
}
static void addon57(){
 int cases=0;
 for(auto types:{std::pair<U,U>{U::Terran_Command_Center,U::Terran_Comsat_Station},{U::Terran_Command_Center,U::Terran_Nuclear_Silo},{U::Terran_Factory,U::Terran_Machine_Shop},{U::Terran_Starport,U::Terran_Control_Tower},{U::Terran_Science_Facility,U::Terran_Covert_Ops},{U::Terran_Science_Facility,U::Terran_Physics_Lab}}){
  setup57();auto* parent=create55(types.first,0,{1000,1000});xy socket=parent->position;
  auto* at=g_ui->get_unit_type(types.second);xy ap=socket-parent->unit_type->placement_size/2+at->addon_position+at->placement_size/2;
  auto* addon=g_ui->create_initial_unit(at,ap,0);require(addon,"Addon fixture failed");g_ui->connect_addon(parent,addon);
  require(g_ui->unit_has_addon(parent,types.second)&&g_ui->player_has_active_tech(0,types.second),"Attached addon unusable");
  g_ui->set_unit_order(parent,g_ui->get_order_type(Orders::BuildingLiftoff),socket);steps56(150);
  require(!g_ui->u_grounded_building(parent)&&addon->owner==11&&!parent->building.addon,"Lift failed to detach/neutralize addon");
  require(!g_ui->player_has_active_tech(0,types.second),"Detached addon grants old owner tech");select55(addon);require(g_ui->card.empty(),"Neutral addon command card visible");require(g_ui->card_text.find("Unpowered")==a_string::npos,"Terran addon says Unpowered");
  auto* thief=create55(types.first,1,{1500,1000});g_ui->set_unit_order(thief,g_ui->get_order_type(Orders::BuildingLiftoff),thief->position);steps56(150);
  g_ui->set_unit_order(thief,g_ui->get_order_type(Orders::BuildingLand),socket);steps56(600);
  require(g_ui->u_grounded_building(thief)&&thief->building.addon==addon&&addon->owner==1,"Opponent could not capture neutral addon by landing");
  require(g_ui->player_has_active_tech(1,types.second)&&!g_ui->player_has_active_tech(0,types.second),"Captured tech ownership wrong");
  auto save=save_game();restore_game(save);require(save_game()==save,"Captured addon save differs");cases++;close_game();
 }
 std::cout<<"PASS all "<<cases<<" addon types: actual lift, neutral tech/card, enemy landing capture, owner census, save round trip\n";
}
static void sound57(){
 setup57();auto* u=create55(U::Zerg_Ultralisk,0,{1000,1000});std::set<int> voices;int last=-1;
 for(int n=0;n<4;n++){
  reset_audio57();select55(u);int id=active_sound57();require(id>=883&&id<=886,"Normal selection is not an original Ultralisk voice");require(id!=last,"Normal voice repeats immediately");last=id;voices.insert(id);int count=g_ui->ack_count;
  for(int click=0;click<20;click++)select55(u);require(g_ui->ack_count==count,"Rapid clicks advanced annoyed count");
  g_ui->last_selection_ack={};select55(u);require(g_ui->ack_count==count,"Suppressed playing voice advanced annoyed count");
 }
 for(int i=0;i<3;i++){reset_audio57();select55(u);require(active_sound57()==879+i,"Annoyed voices out of order");}
 reset_audio57();select55(u);require(active_sound57()>=883&&active_sound57()<=886,"Annoyed cycle never returns to normal");
 for(int i=0;i<4;i++){
  a_vector<uint8_t>b;std::string p="sound/Zerg/Ultra/ZUlWht0"+std::to_string(i)+".wav";g_ui->load_data_file(b,p.c_str());auto clip=naudio::wav(b.data(),b.size());require(clip->rate==22050&&clip->channels==1,"Ultralisk sample rate changed");
  // The source WAVs are signed 16-bit PCM, not a lossy WAV decoder path.
  size_t off=12;while(off+8<=b.size()&&memcmp(b.data()+off,"data",4))off+=8+naudio::u32(b.data()+off+4)+(naudio::u32(b.data()+off+4)&1);
  require(off+8<=b.size(),"Missing PCM data");require(clip->pcm.size()==naudio::u32(b.data()+off+4)/2,"Ultralisk sample count changed");
  for(size_t k=0;k<clip->pcm.size();k++)require(clip->pcm[k]==int16_t(naudio::u16(b.data()+off+8+k*2))/32768.f,"PCM sample differs");
 }
 std::cout<<"PASS all four Ultralisk source PCM streams/rates; rapid click debounce; suppressed sounds do not advance annoyed cycle; no immediate normal repeats\n";close_game();
}
#ifdef OPENBW_REVISION57_EMBEDDED
#define main retained_revision57_main
#endif
int main(int argc,char**argv){try{
 require(argc>=4,"data map mode");std::string d=argv[1];open_archive(0,d+"/STARDAT.MPQ");open_archive(1,d+"/BROODAT.MPQ");open_archive(2,d+"/patch_rt.mpq");open_archive(3,argv[2]);std::string mode=argv[3];
 if(mode=="power")power57();else if(mode=="addons")addon57();else if(mode=="sound")sound57();else if(mode=="victory")victory56();else if(mode=="cargo")cargo56();else if(mode=="macro")macro56(std::atoi(argv[4]),60000,2,true);else throw std::runtime_error("Unknown test");return 0;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
