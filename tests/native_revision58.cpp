#define OPENBW_REVISION57_EMBEDDED
#include "native_revision57.cpp"
#undef main
static void setup58(int race=1,bool heroes=true,bool teams=false,bool network=false,int local=0){
 int races[8]={race,race,race,race,1,1,1,1},controllers[8]={1,network?1:2,network?1:2,network?1:2,0,0,0,0},sides[8]={1,1,2,2,3,3,4,4};
 configured_init(640,480,local,races,controllers,2,true,!teams,network,sides,teams,heroes);
 g_ui->competitive=false;g_ui->fog_player=-1;
 if(g_campaign)for(auto& t:g_campaign->towns)t.active=false;
 if(g_campaign)g_campaign->threads.clear();
}
static void deplete58(int race){
 setup56(race,1);g_ui->competitive=false;steps56(24);
 xy home=g_ui->game_st.start_locations[1];
 // Reproduce a spent main with less than the cost of a depot, while fresh
 // mineral fields elsewhere remain. No grants during the recovery phase.
 for(auto* u:ptr(g_ui->st.player_units[11]))if(g_ui->unit_is_mineral_field(u)&&g_ui->xy_length(u->position-home)<800)u->building.resource.resource_count=0;
 g_ui->st.current_minerals[1]=75;g_ui->st.current_gas[1]=0;
 int before=g_ui->st.total_minerals_gathered[1];
 for(int f=0;f<30000;f++) {
  steps56(1);
  for(auto* u:ptr(g_ui->st.player_units[0]))if(!g_ui->unit_dying(u))g_ui->set_unit_hp(u,u->unit_type->hitpoints);
  if(f%3000==0)std::cout<<"DEPLETED "<<race<<" "<<f<<" "<<g_campaign->ai_status()<<std::flush;
 }
 int gathered=g_ui->st.total_minerals_gathered[1]-before;
 int bases=race==0?g_campaign->ai_zerg_bases(1):g_campaign->ai_depots(1).size();
 std::cout<<"RECOVERY race="<<race<<" minerals="<<gathered<<" bases="<<bases<<"\n";
 require(gathered>=600,"AI stopped mining after main depletion with insufficient expansion funds");
 if(bases<2)for(auto* u:ptr(g_ui->st.player_units[1]))if(g_ui->ut_resource_depot(u)||g_ui->ut_worker(u))std::cout<<"ZDBG type="<<int(u->unit_type->id)<<" pos="<<u->position.x<<","<<u->position.y<<" order="<<int(u->order_type->id)<<" target="<<u->order_target.pos.x<<","<<u->order_target.pos.y<<" queue="<<(u->build_queue.empty()?-1:int(u->build_queue.front()->id))<<" busy="<<g_campaign->ai_busy_worker(u)<<" carried="<<u->worker.resources_carried<<" completed="<<g_ui->u_completed(u)<<"\n";
 require(bases>=2,"AI did not construct a fresh base after depletion");
 std::cout<<"PASS depleted main recovery race="<<race<<"\n";close_game();
}

static void legacy58(){
 setup58(1,false,false,false);steps56(24);auto current=save_game();auto legacy=current;
 // Schema 3 appends two rule flags to the four-word schema 2 header.
 legacy[8]=2;legacy.erase(legacy.begin()+32,legacy.begin()+48);
 uint64_t checksum=native_save::hash_bytes(legacy.data(),legacy.size()-8);
 for(int k=0;k<8;k++)legacy[legacy.size()-8+k]=uint8_t(checksum>>(8*k));
 restore_game(legacy);require(save_game()==current,"Schema 2 save did not restore unchanged");
 std::cout<<"PASS previous schema 2 save compatibility\n";close_game();
}
static void power58(){
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
  g_ui->u_set_status_flag(tech,unit_t::status_flag_disabled);require(g_ui->unit_can_build(producer,target),"Retail unpowered prerequisite lost its tech");
  auto* backup=create55(d.tech,0,{1800,1500});g_ui->u_unset_status_flag(backup,unit_t::status_flag_disabled);
  require(g_ui->unit_can_build(producer,target),"Second powered prerequisite does not enable unit");
  g_ui->u_set_status_flag(backup,unit_t::status_flag_disabled);require(g_ui->unit_can_build(producer,target),"Two completed prerequisites lost tech");
  g_ui->u_unset_status_flag(tech,unit_t::status_flag_disabled);g_ui->kill_unit(backup);requirements++;
 }
 // All Probe structures with power-dependent prerequisites.
 for(auto d:{Dep{U::Protoss_Probe,U::Protoss_Cybernetics_Core,U::Protoss_Gateway},Dep{U::Protoss_Probe,U::Protoss_Stargate,U::Protoss_Cybernetics_Core},Dep{U::Protoss_Probe,U::Protoss_Templar_Archives,U::Protoss_Citadel_of_Adun},Dep{U::Protoss_Probe,U::Protoss_Fleet_Beacon,U::Protoss_Stargate},Dep{U::Protoss_Probe,U::Protoss_Photon_Cannon,U::Protoss_Forge},Dep{U::Protoss_Probe,U::Protoss_Observatory,U::Protoss_Robotics_Facility}}){
  auto* tech=buildings.at(d.tech);auto* target=g_ui->get_unit_type(d.target);require(g_ui->unit_can_build(probe,target),"Powered structure dependency blocked");g_ui->u_set_status_flag(tech,unit_t::status_flag_disabled);require(g_ui->unit_can_build(probe,target),"Retail unpowered structure dependency blocked");g_ui->u_unset_status_flag(tech,unit_t::status_flag_disabled);requirements++;
 }
 for(auto id:{UpgradeTypes::Protoss_Ground_Weapons,UpgradeTypes::Protoss_Ground_Armor,UpgradeTypes::Protoss_Air_Weapons,UpgradeTypes::Protoss_Air_Armor,UpgradeTypes::Protoss_Plasma_Shields}){
  bool air=id==UpgradeTypes::Protoss_Air_Weapons||id==UpgradeTypes::Protoss_Air_Armor;
  auto* producer=buildings.at(air?U::Protoss_Cybernetics_Core:U::Protoss_Forge);
  auto* tech=buildings.at(air?U::Protoss_Fleet_Beacon:id==UpgradeTypes::Protoss_Plasma_Shields?U::Protoss_Cybernetics_Core:U::Protoss_Templar_Archives);
  g_ui->st.upgrade_levels[0][id]=1;auto* up=g_ui->get_upgrade_type(id);require(g_ui->unit_can_upgrade(producer,up),"Powered level 2 upgrade blocked");g_ui->u_set_status_flag(tech,unit_t::status_flag_disabled);require(g_ui->unit_can_upgrade(producer,up),"Retail level 2 prerequisite blocked");g_ui->u_unset_status_flag(tech,unit_t::status_flag_disabled);requirements++;
 }
 std::cout<<"PASS power expansion="<<bw<<" disabled building types="<<disabled<<" unit/building/upgrade dependencies="<<requirements<<" original red status and sound; retail completed-tech counting\n";close_game();
 }
 // Exercise real Pylon power transitions rather than just disabled-state fixtures.
 setup57();auto* gate=create55(U::Protoss_Gateway,0,{1000,1000});g_ui->update_psionic_matrix();require(g_ui->unit_unpowered(gate),"Unpowered fixture unexpectedly powered");
 auto* pylon=create55(U::Protoss_Pylon,0,gate->position+xy(128,0));steps56(24);g_ui->update_psionic_matrix();require(!g_ui->unit_unpowered(gate),"Pylon failed to power Gateway");g_ui->kill_unit(pylon);steps56(24);g_ui->update_psionic_matrix();require(g_ui->unit_unpowered(gate),"Destroyed Pylon retained power");
 auto saved=save_game();restore_game(saved);require(save_game()==saved,"Power-state save round trip differs");
 std::cout<<"PASS actual Pylon construction/destruction and saved power state\n";close_game();
}
static void heroes58(){
 for(const auto& h:hero_roster()) {
  setup58(h.race);auto id=U(h.id);auto* type=g_ui->get_unit_type(id);
  auto* producer=create55(hero_producer(h.race),0,{1200,1200});
  auto* second=create55(hero_producer(h.race),0,{1500,1200});
  for(int t:{h.tech1,h.tech2})if(t>=0) {
   auto* req=create55(U(t),0,{800+(t%4)*220,1800});
   if(g_ui->ut_addon(req)) {
    int parent=t==120?113:t==115?114:116;
    auto* p=create55(U(parent),0,{1800,2100});p->building.addon=req;
   }
  }
  auto powered=[&](){for(auto* u:ptr(g_ui->st.player_units[0]))g_ui->u_unset_status_flag(u,unit_t::status_flag_disabled);};powered();
  g_ui->st.current_minerals[0]=10000;g_ui->st.current_gas[0]=10000;g_ui->st.supply_available[0][h.race]=fp1::integer(200);
  require(g_ui->unit_can_build(producer,type),"Hero unavailable with tech");
  select55(producer);int buttons=0,heroes=0;for(auto& c:g_ui->card){buttons++;if(c.ut!=U::None&&hero_definition(c.ut))heroes++;}
  require(heroes==6&&buttons<=9,"Hero producer must fit six heroes on one command card");
  action_functions af(g_ui->st,g_ui->current_action_state);af.action_select(0,producer);
  require(af.action_train(0,type),"Could not queue hero");
  require(g_ui->st.current_minerals[0]==10000-h.minerals&&g_ui->st.current_gas[0]==10000-h.gas,"Hero charged wrong cost");
  af.action_select(0,second);require(!af.action_train(0,type),"Duplicate hero queued at second producer");
  af.action_select(0,producer);require(af.action_cancel_build_queue(0,0),"Hero queue cannot cancel");
  require(g_ui->st.current_minerals[0]==10000&&g_ui->st.current_gas[0]==10000,"Unstarted hero cancellation refund wrong");
  require(g_ui->unit_can_build(second,type),"Cancelled hero still reserved");require(af.action_train(0,type),"Requeue cancelled hero failed");
  auto secondId=g_ui->get_unit_id(second);auto saved=save_game();restore_game(saved);second=g_ui->get_unit(secondId);require(save_game()==saved,"Queued hero save differs");
  powered();g_ui->st.cheat_operation_cwal=true;for(int f=0;f<600;f++){powered();steps56(1);}g_ui->st.cheat_operation_cwal=false;
  unit_t* hero=nullptr;for(auto* u:ptr(g_ui->st.player_units[0]))if(g_ui->unit_is(u,id)&&g_ui->u_completed(u)&&!g_ui->unit_dying(u))hero=u;
  if(!hero)std::cerr<<"hero failed id="<<h.id<<"\n";
  require(hero,"Hero training never completed");require(hero->unit_type->supply_required.raw_value==h.supply2,"Hero supply differs");
  require(!g_ui->unit_can_build(second,type),"Living hero allows duplicate");
  g_ui->kill_unit(hero);powered();require(g_ui->unit_can_build(second,type),"Dead hero cannot be replaced");
  std::cout<<"PASS hero "<<h.id<<" cost="<<h.minerals<<"/"<<h.gas<<" six-button card, queue, save, train, death cap\n";
  close_game();
 }
}
static void merge58(){
 setup58(2);auto* a=create55(U::Hero_Tassadar,0,{1200,1000});auto* b=create55(U::Hero_Zeratul,0,{1240,1000});
 action_functions af(g_ui->st,g_ui->current_action_state);unit_t* pair[]={a,b};
 af.action_select(0,pair);g_ui->current_selection_clear();g_ui->current_selection_add(a);g_ui->current_selection_add(b);g_ui->refresh_card();
 bool button=false;for(auto c:g_ui->card)if(c.act==play_ui::C_ARCHON&&c.ut==U::Hero_Tassadar_Zeratul_Archon&&c.enabled)button=true;
 require(button,"Hero merge command absent");require(af.action_morph_archon(0),"Hero merge rejected");
 steps56(900);unit_t* archon=nullptr;
 for(auto* u:ptr(g_ui->st.player_units[0]))if(g_ui->unit_is(u,U::Hero_Tassadar_Zeratul_Archon)&&!g_ui->unit_dying(u))archon=u;
 require(archon&&!g_ui->archon_merging(archon),"Hero merge never completed");
 require(g_ui->hero_reserved(0,U::Hero_Tassadar)&&g_ui->hero_reserved(0,U::Hero_Zeratul),"Merged heroes can be rebuilt early");
 auto id=g_ui->get_unit_id(archon);auto saved=save_game();restore_game(saved);require(save_game()==saved,"Merged save round trip");archon=g_ui->get_unit(id);
 require(g_ui->hero_reserved(0,U::Hero_Tassadar)&&g_ui->hero_reserved(0,U::Hero_Zeratul),"Merged cap lost in save");
 g_ui->kill_unit(archon);require(!g_ui->hero_reserved(0,U::Hero_Tassadar)&&!g_ui->hero_reserved(0,U::Hero_Zeratul),"Merged death did not release both heroes");
 auto* duke=create55(U::Hero_Edmund_Duke_Tank_Mode,0,{1400,1500});af.action_select(0,duke);require(af.action_siege(0,false),"Duke cannot siege");steps56(240);
 require(g_ui->unit_is(duke,U::Hero_Edmund_Duke_Siege_Mode)&&g_ui->hero_reserved(0,U::Hero_Edmund_Duke_Tank_Mode),"Sieged Duke lost cap");
 require(duke->unit_type->supply_required==fp1::integer(2),"Siege changes supply");
 std::cout<<"PASS Tassadar/Zeratul merge, complete hero Archon, save, paired cap/death release, Duke siege cap and supply\n";close_game();
}
static void teams58(){
 uint64_t expected=0;std::vector<uint8_t> snapshot;
 for(int slot=0;slot<4;slot++) {
  setup58(2,true,true,true,slot);
  for(int i=0;i<4;i++)for(int j=0;j<4;j++)require(bool(g_ui->st.alliances[i][j])==(i/2==j/2),"Team alliances differ");
  require((g_ui->st.shared_vision[0]&3)==3&&(g_ui->st.shared_vision[2]&12)==12,"Team vision not shared");
  if(slot==0){expected=net_hash();snapshot=net_save();}else {require(net_hash()==expected,"Initial team/hero world differs by perspective");net_restore(snapshot);require(net_hash()==expected,"Team hero save differs by perspective");}
  g_ui->competitive=true;steps56(24);eliminate56(0);require(!g_ui->outcome,"Lost one teammate ended the team match");
  eliminate56(2);require(!g_ui->outcome,"Team result before last enemy dies");eliminate56(3);
  require(g_ui->outcome==(slot<2?1:2),"Incorrect shared team result");close_game();
 }
 setup58(1,false,false,false);auto* bay=create55(U::Terran_Engineering_Bay,0,{1000,1000});require(!g_ui->unit_can_build(bay,g_ui->get_unit_type(U::Hero_Jim_Raynor_Marine)),"Hero Mode off trains heroes");
 require(g_ui->get_unit_type(U::Hero_Jim_Raynor_Marine)->mineral_cost==50,"Hero cost leaks into ordinary game");
 bool rejected=false;try{restore_game(snapshot);}catch(...){rejected=true;}require(rejected,"Hero/team save accepted with different rules");
 std::cout<<"PASS four native perspectives: teams, vision, saved rules, shared victory and defeat, default-off isolation\n";close_game();
}

#ifdef OPENBW_REVISION58_EMBEDDED
#define main retained_revision58_main
#endif
int main(int argc,char**argv){try{
 require(argc>=4,"data map mode");std::string d=argv[1];open_archive(0,d+"/STARDAT.MPQ");open_archive(1,d+"/BROODAT.MPQ");open_archive(2,d+"/patch_rt.mpq");open_archive(3,argv[2]);std::string mode=argv[3];
 if(mode=="merge")merge58();else if(mode=="teams")teams58();else if(mode=="legacy")legacy58();else if(mode=="deplete")deplete58(std::atoi(argv[4]));else if(mode=="heroes")heroes58();else if(mode=="power")power58();else if(mode=="addons")addon57();else if(mode=="cargo")cargo56();else if(mode=="detection")detection56();else if(mode=="macro")macro56(std::atoi(argv[4]),60000,argc>5?std::atoi(argv[5]):2,argc>6?std::atoi(argv[6])!=0:true);else if(mode=="sound")sound56();else if(mode=="victory")victory56();else throw std::runtime_error("Unknown test");return 0;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
