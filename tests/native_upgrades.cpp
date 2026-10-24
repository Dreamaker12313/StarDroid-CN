#define OPENBW_REVISION58_EMBEDDED
#include "native_revision58.cpp"
#undef main

struct UpgradeCase {int id, race, producer, level2, level3;};
static const UpgradeCase upgrade_cases[] = {
 {0,1,122,116,116},{1,1,123,116,116},{2,1,123,116,116},
 {3,0,139,132,133},{4,0,141,132,133},{5,2,166,165,165},
 {6,2,164,169,169},{7,1,122,116,116},{8,1,123,116,116},
 {9,1,123,116,116},{10,0,139,132,133},{11,0,139,132,133},
 {12,0,141,132,133},{13,2,166,165,165},{14,2,164,169,169},
 {15,2,166,164,164}
};

static void probe_upgrades() {
 for(const auto& c:upgrade_cases){
  setup56(c.race,0);g_ui->competitive=false;
  auto* producer=create55(UnitTypes(c.producer),0,{1000,1000});
  g_ui->u_unset_status_flag(producer,unit_t::status_flag_disabled);
  auto id=UpgradeTypes(c.id);auto* up=g_ui->get_upgrade_type(id);
  std::cout<<"UPGRADE "<<c.id<<" "<<g_ui->upgrade_name(up)<<" max="<<g_ui->player_max_upgrade_level(0,id);
  for(int level=0;level<3;level++){
   g_ui->st.upgrade_levels[0][id]=level;
   auto* req=level?create55(UnitTypes(level==1?c.level2:c.level3),0,{1600,1600}):nullptr;
   select55(producer);bool shown=false;for(auto& b:g_ui->card)if(b.upg==id)shown=true;
   std::cout<<" level"<<level+1<<"="<<g_ui->unit_can_upgrade(producer,up)<<"/"<<shown;
   if(req){g_ui->kill_unit(req);steps56(48);g_ui->u_unset_status_flag(producer,unit_t::status_flag_disabled);}
  }
  g_ui->st.upgrade_levels[0][id]=1;select55(producer);bool shown=false;for(auto& b:g_ui->card)if(b.upg==id)shown=true;
  std::cout<<" missing-tech-visible="<<shown<<"\n";close_game();
 }
}

static int checks65=0, completions65=0;
static void check65(bool ok,const char* message){checks65++;require(ok,message);}
static void setup65(int race,bool bw,int mode,bool heroes){
 int races[8]={race,race,race,race,1,1,1,1},slots[8]={1,2,0,0,0,0,0,0},teams[8]={1,2,1,2,3,3,4,4};
 bool network=mode>=3,team=mode==2||mode==4;int local=network?3:0;
 if(network)for(int i=0;i<4;i++)slots[i]=1;
 configured_init(640,480,local,races,slots,2,bw,mode==1||mode==3,network,teams,team,heroes);
 g_ui->competitive=false;g_ui->fog_player=-1;
 if(g_campaign){for(auto& town:g_campaign->towns)town.active=false;g_campaign->threads.clear();}
 g_ui->st.current_minerals[local]=g_ui->st.current_gas[local]=100000;
}
static void ticks65(int frames){
 require(frames%4==0,"Frame fixture must preserve network turns");
 for(int i=0;i<frames;i+=4){
  if(net_active){std::array<std::vector<uint8_t>,8>empty;net_apply_all(empty);for(int k=0;k<4;k++)net_step();}
  else steps56(4);
 }
}
static void flush65(){
 auto out=g_ui->outgoing;g_ui->outgoing.clear();
 if(net_active){std::array<std::vector<uint8_t>,8>all;all[g_ui->my_player].assign(out.begin(),out.end());net_apply_all(all);for(int k=0;k<4;k++)net_step();}
 else {g_ui->apply_commands(g_ui->my_player,out.data(),out.size());steps56(4);}
}
static play_ui::cmd_t* button65(unit_t* producer,UpgradeTypes id){
 select55(producer);for(auto& c:g_ui->card)if(c.upg==id)return &c;return nullptr;
}
static void locked65(unit_t* producer,UpgradeTypes id,UnitTypes req){
 auto* c=button65(producer,id);check65(c&&!c->enabled,"Future upgrade vanished or was enabled without prerequisite");
 check65(c->req==req,"Wrong missing building in upgrade tooltip");
 int owner=producer->owner,m=g_ui->st.current_minerals[owner],g=g_ui->st.current_gas[owner],level=g_ui->player_upgrade_level(owner,id);
 g_ui->outgoing.clear();g_ui->run_command(c->key);
 check65(g_ui->outgoing.empty()&&g_ui->st.current_minerals[owner]==m&&g_ui->st.current_gas[owner]==g&&g_ui->player_upgrade_level(owner,id)==level,"Greyed upgrade changed resources, state or sent input");
}
static void matrix65(bool bw,int mode,bool heroes,const char* dump){
 std::vector<UpgradeCase>cases(std::begin(upgrade_cases),std::end(upgrade_cases));
 cases.push_back({4,0,int(UnitTypes::Zerg_Greater_Spire),132,133});cases.push_back({12,0,int(UnitTypes::Zerg_Greater_Spire),132,133});
 for(const auto& item:cases){
  setup65(item.race,bw,mode,heroes);int owner=g_ui->my_player;auto id=UpgradeTypes(item.id);auto* up=g_ui->get_upgrade_type(id);
  auto* producer=create55(UnitTypes(item.producer),owner,{1000,1000});
  if(item.race==2){create55(UnitTypes::Protoss_Pylon,owner,producer->position+xy(128,0));ticks65(24);g_ui->update_psionic_matrix();}
  check65(g_ui->player_max_upgrade_level(owner,id)==3,"Custom setup limits a three-level upgrade");
  for(int level=1;level<=3;level++){
   unit_t* tech=nullptr;
   if(level>1){
    auto required=UnitTypes(level==2?item.level2:item.level3);locked65(producer,id,required);
    if(dump&&bw&&mode==0&&!heroes&&level==2&&item.producer!=int(UnitTypes::Zerg_Greater_Spire)){
     std::ofstream file(std::string(dump)+"/upgrade-"+std::to_string(item.id)+".tsv");file<<g_ui->card_text.c_str();
    }
    auto* enemy=create55(required,(owner+1)%4,{2300,2300});locked65(producer,id,required);
    tech=create55(required,owner,{1600,1600});
    g_ui->add_completed_unit(tech,-1,false);g_ui->u_unset_status_flag(tech,unit_t::status_flag_completed);locked65(producer,id,required);
    g_ui->u_set_status_flag(tech,unit_t::status_flag_completed);g_ui->add_completed_unit(tech,1,false);
    auto* available=button65(producer,id);check65(available&&available->enabled,"Completed prerequisite does not restore upgrade");
    // Retail tech counting retains completed Protoss prerequisites when unpowered.
    if(item.race==2){g_ui->u_set_status_flag(tech,unit_t::status_flag_disabled);check65(button65(producer,id)->enabled,"Unpowered prerequisite lost completed tech");}
    auto* backup=create55(required,owner,{2000,1600});g_ui->kill_unit(tech);ticks65(48);tech=backup;
    check65(button65(producer,id)->enabled,"Second completed prerequisite did not retain upgrade");
    g_ui->kill_unit(enemy);
   }
   auto* c=button65(producer,id);if(!c||!c->enabled)std::cerr<<"UPGRADE DEBUG id="<<item.id<<" level="<<level<<" producer="<<item.producer<<" disabled="<<g_ui->unit_is_disabled(producer)<<" unpowered="<<g_ui->unit_unpowered(producer)<<" completed="<<g_ui->u_completed(producer)<<"\n";check65(c&&c->enabled,"Available upgrade missing from producer");
   check65(g_ui->card_text.find(format("(Level %d)",level))!=a_string::npos,"Tooltip does not show next level");
   check65(g_ui->card.size()<=9,"Upgrades and heroes no longer fit one card");
   int minerals=g_ui->st.current_minerals[owner],gas=g_ui->st.current_gas[owner];
   int mc=g_ui->upgrade_mineral_cost(owner,up),gc=g_ui->upgrade_gas_cost(owner,up),time=g_ui->upgrade_time_cost(owner,up);
   g_ui->outgoing.clear();g_ui->run_command(c->key);check65(!g_ui->outgoing.empty(),"Upgrade button emitted no command");flush65();
   check65(g_ui->unit_is_upgrading(producer)&&producer->building.upgrading_level==level,"Upgrade command did not start correct level");
   check65(g_ui->st.current_minerals[owner]==minerals-mc&&g_ui->st.current_gas[owner]==gas-gc,"Wrong next-level resource charge");
   check65(producer->building.upgrade_research_time>0&&producer->building.upgrade_research_time<=time,"Wrong upgrade duration");
   auto* busy=button65(producer,id);check65(busy&&!busy->enabled,"In-progress upgrade missing or repeatable");
   auto* other=create55(UnitTypes(item.producer),owner,{1300,1000});
   if(item.race==2){create55(UnitTypes::Protoss_Pylon,owner,other->position+xy(128,0));ticks65(24);g_ui->update_psionic_matrix();}
   auto* duplicate=button65(other,id);check65(duplicate&&!duplicate->enabled,"Second producer can duplicate in-progress upgrade");
   if(item.id==7&&level==2){
    auto unitId=g_ui->get_unit_id(producer);int remaining=producer->building.upgrade_research_time;
    auto saved=net_active?net_save():save_game();if(net_active)net_restore(saved);else restore_game(saved);
    producer=g_ui->get_unit(unitId);up=g_ui->get_upgrade_type(id);
    check65(producer&&producer->building.upgrading_level==2&&producer->building.upgrade_research_time==remaining&&g_ui->player_upgrade_level(owner,id)==1,"Saved upgrade lost level or progress");
    // Restoring relocates all units; recover the remaining fixture handles.
    tech=nullptr;other=nullptr;
   }
   // Exercise normal completion without waiting thousands of frames per matrix cell.
   producer->building.upgrade_research_time=0;
   for(int wait=0;wait<64&&g_ui->player_upgrade_level(owner,id)!=level;wait+=4)ticks65(4);
   check65(g_ui->player_upgrade_level(owner,id)==level&&!g_ui->player_is_upgrading(owner,id),"Research did not complete the next level");completions65++;
   if(other)g_ui->kill_unit(other);
   // Remove only this line's prerequisite; a later level must establish its own tech.
   std::vector<unit_t*>remove;
   for(auto* u:ptr(g_ui->st.player_units[owner]))if(u!=producer&&(int(u->unit_type->id)==item.level2||int(u->unit_type->id)==item.level3))remove.push_back(u);
   for(auto* u:remove)if(!g_ui->unit_dying(u))g_ui->kill_unit(u);
   ticks65(48);
   if(level<3)locked65(producer,id,UnitTypes(level==1?item.level2:item.level3));
  }
  check65(button65(producer,id)==nullptr,"Fully upgraded icon remains without a next level");
  close_game();
 }
 std::cout<<"PASS "<<checks65<<" checks, "<<completions65<<" actual research completions; 16 lines plus both Spire types; expansion="<<bw<<" mode="<<mode<<" heroes="<<heroes<<"\n";
}
int main(int argc,char**argv){try{
 require(argc>=4,"data map mode");std::string d=argv[1];
 open_archive(0,d+"/STARDAT.MPQ");open_archive(1,d+"/BROODAT.MPQ");open_archive(2,d+"/patch_rt.mpq");open_archive(3,argv[2]);
 std::string mode=argv[3];if(mode=="probe")probe_upgrades();
 else if(mode=="matrix")matrix65(std::atoi(argv[4]),std::atoi(argv[5]),std::atoi(argv[6]),argc>7?argv[7]:nullptr);
 else if(mode=="power")power58();else if(mode=="heroes")heroes58();else if(mode=="merge")merge58();else if(mode=="teams")teams58();else if(mode=="legacy")legacy58();else if(mode=="victory")victory56();else if(mode=="cargo")cargo56();else if(mode=="detection")detection56();else if(mode=="addons")addon57();else if(mode=="sound")sound56();else throw std::runtime_error("Unknown mode");
 return 0;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
