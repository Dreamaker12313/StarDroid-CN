// Original mission regressions; archives stay external. These are controlled
// objective checks, not full campaign playthroughs or Android device tests.
#include "../native/runtime.cpp"
#include <iostream>
#include <functional>
#include <set>
using namespace bwgame;
using U=UnitTypes;
static void require(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
static void step(int n){for(int i=0;i<n&&!g_ui->outcome;++i)native_step();}
static void until(const std::function<bool()>& done,int n,const char* why){for(int i=0;i<n&&!done()&&!g_ui->outcome;++i)native_step();require(done(),why);}
static std::vector<unit_t*> units(U t,int owner=-1){std::vector<unit_t*> r;for(auto& list:g_ui->st.player_units)for(auto* u:ptr(list))if(g_ui->unit_is(u,t)&&!g_ui->unit_dying(u)&&(owner<0||u->owner==owner))r.push_back(u);return r;}
static void load(const char* archive,int mission){close_game();open_archive(3,archive);openbw_init_campaign(640,480,mission);openbw_set_external_cursor(1);}
static void warp(unit_t* u,xy p){openbw_debug_warp(g_ui->get_unit_id(u).raw_value,p.x,p.y);}
static void rebuild(std::vector<uint8_t>& snapshot,const char* archive,int mission){load(archive,mission);restore_game(snapshot);require(save_game()==snapshot,"Fresh-load save round trip changed state");}
static int distance(xy p){return std::max(std::abs(p.x),std::abs(p.y));}
static xy site(unit_t* drone,U type){
 const auto* ut=g_ui->get_unit_type(type);xy best{};int score=1000000;
 if(type==U::Zerg_Extractor){
  for(auto* gas:units(U::Resource_Vespene_Geyser)){
   int d=distance(gas->position-drone->position);
   if(d<score&&d<700&&g_ui->can_place_building(drone,drone->owner,ut,gas->position,true,true)){best=gas->position;score=d;}
  }
  require(score<1000000,"No nearby original geyser for Extractor");return best;
 }
 for(int y=3;y<int(g_ui->game_st.map_tile_height)-5;++y)for(int x=3;x<int(g_ui->game_st.map_tile_width)-5;++x){
  xy p=xy(x*32,y*32)+ut->placement_size/2;int d=distance(p-drone->position);
  if(d<score&&d<700&&g_ui->can_place_building(drone,drone->owner,ut,p,true,true)){best=p;score=d;}
 }
 require(score<1000000,"No nearby legal build site");return best;
}
static void build(unit_t* drone,U type){
 auto* ut=g_ui->get_unit_type(type);size_t count=units(type,drone->owner).size();int owner=drone->owner;xy pos=site(drone,type);
 // Refineries replace a solid geyser; start beside it instead of warping inside.
 warp(drone,pos+(type==U::Zerg_Extractor?xy(96,0):xy(0,0)));
 action_state as;action_functions af(g_ui->st,as);af.action_select(drone->owner,drone);
 xy tile=(pos-ut->placement_size/2)/32;
 require(af.action_build(drone->owner,g_ui->get_order_type(Orders::DroneStartBuild),ut,{size_t(tile.x),size_t(tile.y)}),"Drone build command rejected");
 for(int i=0;i<1200&&units(type,owner).size()<=count&&!g_ui->outcome;++i)native_step();
 if(units(type,owner).size()<=count){
  std::cerr<<"Build failed type="<<int(type)<<" position="<<drone->position.x<<","<<drone->position.y<<" order="<<int(drone->order_type->id)<<" outcome="<<g_ui->outcome<<"\n";
  throw std::runtime_error("Drone never started construction");
 }
}
static void reign(const char* archive){
 load(archive,502);step(6500);require(!g_ui->outcome,"Opening ended unexpectedly");
 auto scvs=units(U::Terran_SCV,3),drones=units(U::Zerg_Drone,5);
 require(scvs.size()==1&&drones.size()==2,"Original emitter SCV/two Drones missing");
 require(scvs[0]->worker.powerup&&g_ui->unit_is(scvs[0]->worker.powerup,U::Powerup_Psi_Emitter),"SCV did not collect emitter");
 warp(scvs[0],drones[0]->position);
 until([&]{return g_campaign->switches[20]&&!g_campaign->units_paused;},4000,"Original Drone rescue/starting-resources sequence did not finish");
 require(units(U::Zerg_Drone,3).size()==2,"Two original Drones were not handed over");
 require(g_ui->st.current_minerals[3]==850&&g_ui->st.current_gas[3]==200,"Starting resource trigger wrong");
 std::cout<<"PASS Reign of Fire original introduction, emitter pickup, Drone handover and starting resources\n";
 auto before=save_game();
 drones=units(U::Zerg_Drone,3);build(drones[0],U::Zerg_Hatchery);build(drones[1],U::Zerg_Hatchery);
 until([&]{return units(U::Zerg_Drone,3).empty();},1200,"Second Drone never began morphing");
 require(units(U::Zerg_Hatchery,3).size()==2,"Both buildings did not start");
 require(g_ui->st.completed_building_counts[3]==0,"Fixture must have no completed building");
 trigger::condition ordinary{};ordinary.type=2;ordinary.group=13;ordinary.unit_id=231;ordinary.num_n=10;
 require(g_ui->test_trigger_condition(ordinary,3),"Ordinary Exactly condition semantics changed globally");
 ordinary.num_n=1;require(!g_ui->test_trigger_condition(ordinary,3),"At Most must include unfinished buildings");
 step(180);require(!g_ui->outcome,"False defeat while both rescued Drones construct buildings");
 auto construction=save_game();step(240);auto continued=save_game();
 rebuild(construction,archive,502);step(240);require(save_game()==continued,"Construction save continuation diverged");
 std::cout<<"PASS simultaneous Drone construction and exact save/load continuation without false defeat\n";
 auto hatch=units(U::Zerg_Hatchery,3).front();
 action_state as;action_functions af(g_ui->st,as);af.action_select(3,hatch);require(af.action_cancel_building_unit(3),"Cancel building rejected");
 step(80);require(units(U::Zerg_Drone,3).size()==1&&!g_ui->outcome,"Cancellation failed to return surviving Drone");
 until([&]{return g_ui->st.completed_building_counts[3]==1;},3000,"Remaining Hatchery never completed");
 until([&]{return !units(U::Zerg_Larva,3).empty();},1200,"Completed Hatchery did not produce larvae");
 std::cout<<"PASS cancel returns Drone; remaining Hatchery completes and produces larvae\n";
 rebuild(before,archive,502);
 drones=units(U::Zerg_Drone,3);build(drones[0],U::Zerg_Hatchery);build(drones[1],U::Zerg_Extractor);
 require(units(U::Zerg_Drone,3).empty()&&g_ui->st.completed_building_counts[3]==0,"Extractor fixture must leave only unfinished structures");
 step(180);require(!g_ui->outcome,"Hatchery plus Extractor falsely defeats player");
 auto* extractor=units(U::Zerg_Extractor,3).front();
 action_state gas_as;action_functions gas_af(g_ui->st,gas_as);gas_af.action_select(3,extractor);
 require(gas_af.action_cancel_building_unit(3),"Extractor cancel rejected");step(80);
 require(units(U::Zerg_Drone,3).size()==1&&!g_ui->outcome,"Extractor cancellation failed to return Drone");
 std::cout<<"PASS Hatchery plus Extractor construction and cancellation\n";
 rebuild(before,archive,502);
 for(auto* u:units(U::Zerg_Drone,3))g_ui->kill_unit(u);
 step(300);require(g_ui->outcome==2,"Actual loss of both Drones no longer defeats player");
 rebuild(construction,archive,502);
 for(auto* u:units(U::Zerg_Hatchery,3))g_ui->kill_unit(u);
 step(300);require(g_ui->outcome==2,"Actual loss of unfinished buildings no longer defeats player");
 std::cout<<"PASS genuine defeat after losing both Drones or both unfinished buildings\n";
 rebuild(before,archive,502);
 auto targets=units(U::Special_Psi_Disrupter);require(targets.size()==1,"Original Psi Disrupter absent");
 g_ui->kill_unit(targets[0]);step(1000);require(g_ui->outcome==1,"Original Psi Disrupter victory no longer fires");
 std::cout<<"PASS original Psi Disrupter destruction victory\n";
}
static void nydus(const char* archive){
 load(archive,108);auto canals=units(U::Zerg_Nydus_Canal,3);require(canals.size()==4,"Original four Nydus canals missing");
 std::vector<unit_id> ids;std::set<std::pair<unsigned,unsigned>> pairs;
 for(auto* u:canals){auto* exit=u->building.nydus.exit;
  require(exit&&exit!=u&&exit->building.nydus.exit==u,"Pre-placed Nydus canals are not linked on mission load");
  auto id=g_ui->get_unit_id(u),eid=g_ui->get_unit_id(exit);ids.push_back(id);pairs.insert(std::minmax(id.raw_value,eid.raw_value));
 }
 require(pairs.size()==2,"Original Nydus pairs are not distinct");
 for(auto* u:canals){
  xy expected=u->position==xy(800,384)?xy(3264,512):u->position==xy(3264,512)?xy(800,384):u->position==xy(3424,576)?xy(3808,3776):xy(3424,576);
  require(u->building.nydus.exit->position==expected,"Nydus connected to the wrong map endpoint");
 }
 auto snapshot=save_game();rebuild(snapshot,archive,108);
 auto passengers=units(U::Zerg_Drone,3);require(!passengers.empty(),"No original Drone for Nydus traversal");auto* u=passengers[0];
 for(auto id:ids){
  auto* entrance=g_ui->get_unit(id);auto* exit=entrance->building.nydus.exit;
  require(exit&&exit->building.nydus.exit==entrance,"Save/load lost Nydus link");
  warp(u,entrance->position+xy(96,0));
  action_state as;action_functions af(g_ui->st,as);af.action_select(3,u);
  require(af.action_default_order(3,entrance->position,entrance,nullptr,false),"Nydus right-click rejected");
  until([&]{return distance(u->position-exit->position)<180;},1800,"Drone did not traverse original Nydus link");
  require(!g_ui->us_hidden(u),"Nydus passenger stayed hidden");
 }
 require(g_campaign->ai_error.empty()&&!g_ui->outcome,"Eye for an Eye failed during Nydus traversal");
 std::cout<<"PASS Eye for an Eye: both pre-placed Nydus pairs, save/load and right-click traversal in all four directions\n";
 rebuild(snapshot,archive,108);auto* a=g_ui->get_unit(ids[0]);auto* b=a->building.nydus.exit;auto bid=g_ui->get_unit_id(b);g_ui->kill_unit(a);step(120);
 b=g_ui->get_unit(bid);require(!b||g_ui->unit_dying(b),"Destroying one Nydus did not remove linked exit");
 require(units(U::Zerg_Nydus_Canal,3).size()==2,"Nydus destruction affected unrelated pair");
 std::cout<<"PASS linked Nydus destruction cleanup preserves unrelated pair\n";
}
#include "native_nydus79_cases.h"
#include "native_heroes79_cases.h"
#include "native_fog_target79_cases.h"
int main(int argc,char**argv){try{
 std::cout.setf(std::ios::unitbuf);require(argc==5,"native-campaign79 CORE_DIR BROODWAR_MPQ STARCRAFT_MPQ reign|nydus|heroes|fog|all");std::string data=argv[1],mode=argv[4];
 open_archive(0,data+"/STARDAT.MPQ");open_archive(1,data+"/BROODAT.MPQ");open_archive(2,data+"/patch_rt.mpq");
 if(mode=="reign"||mode=="all")reign(argv[2]);if(mode=="nydus"||mode=="all"){nydus(argv[3]);nydus79::cases(argv[2],argv[3]);}
 if(mode=="heroes"||mode=="all")heroes79(argv[2]);
 if(mode=="fog"||mode=="all")fog_target79(argv[2]);
 require(mode=="reign"||mode=="nydus"||mode=="heroes"||mode=="fog"||mode=="all","Unknown mode");close_game();return 0;
}catch(std::exception& e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
