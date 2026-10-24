// Broad gameplay regression harness. Uses the production command card and command
// stream, then checks simulation state, costs and refunds. Original data is external.
#include "../native/runtime.cpp"
#include <iostream>
#include <fstream>
#include <set>
#include <functional>
#include <algorithm>
#include <execinfo.h>
#include <signal.h>
using namespace bwgame;
using U = UnitTypes;
using T = TechTypes;
using G = UpgradeTypes;
static double clock_ms = 0;
static int passed = 0, failed = 0, race = 0;
static std::vector<std::string> results;
static xy origin;
static void require(bool ok, const std::string& why) { if (!ok) throw std::runtime_error(why); }
static void draw() { openbw_render(clock_ms += 42); }
static void step(int n = 1) { for (int i=0;i<n;++i) { native_step(); if(i%48==0) draw(); } draw(); }
static std::string name(U t) { return g_ui->unit_name(t); }
static std::string quote(const std::string& s) { std::string r="\"";for(unsigned char c:s) {if(c=='"'||c=='\\')r+='\\'; if(c=='\n')r+="\\n";else if(c>=32)r+=c;}return r+'"'; }
static void check(const std::string& label, const std::function<void()>& f) {
  try { f(); ++passed; results.push_back("{\"test\":"+quote(label)+",\"passed\":true}"); std::cout<<"PASS "<<label<<std::endl; }
  catch(const std::exception& e) { ++failed; results.push_back("{\"test\":"+quote(label)+",\"passed\":false,\"error\":"+quote(e.what())+"}"); std::cout<<"FAIL "<<label<<": "<<e.what()<<std::endl; g_ui->clear_pending();g_ui->menu=0;g_ui->targeting=false;draw(); }
}
static std::vector<unit_t*> units(U t, bool complete=true) { std::vector<unit_t*> out; for(auto* u:ptr(g_ui->st.player_units[0]))if(u->unit_type->id==t&&!g_ui->unit_dying(u)&&(!complete||g_ui->u_completed(u)))out.push_back(u);return out; }
static unit_t* one(U t) { auto v=units(t);if(v.empty()&&t==U::Zerg_Larva){for(int i=0;i<20&&v.empty();++i){step(48);v=units(t);}} require(!v.empty(),"Missing completed "+name(t));return v.front(); }
static void select(unit_t* u) { require(u,"Null selection");g_ui->clear_pending();g_ui->menu=0;g_ui->targeting=false;openbw_debug_select(g_ui->get_unit_id(u).raw_value,0);draw(); }
static void select(U t) { select(one(t)); }
static int minerals() { return int(g_ui->st.current_minerals[0]); }
static int gas() { return int(g_ui->st.current_gas[0]); }
static void money() { openbw_debug_resources(50000,50000); }
static play_ui::cmd_t card(U t) { draw();for(auto c:g_ui->card)if(c.ut==t)return c;throw std::runtime_error("Command missing for "+name(t)+" in "+openbw_card()); }
static play_ui::cmd_t label(const std::string& s) { draw();for(auto c:g_ui->card)if(c.label==s)return c;throw std::runtime_error("Command missing: "+s+" in "+openbw_card()); }
static void press(play_ui::cmd_t c, bool enabled=true) { if(enabled)require(c.enabled,"Disabled command: "+std::string(c.label));command(2,c.key,0,0,0);draw();step(); }
static void press(const std::string& s) { press(label(s)); }
static void wait_for(const std::function<bool()>& f, int limit, const std::string& error) { for(int i=0;i<limit;++i) {if(f()){draw();return;}native_step();if(i%96==0)draw();}draw();if(!f()){auto* u=g_ui->primary_selected();std::string diag=u?" type="+name(u->unit_type->id)+" order="+std::to_string(int(u->order_type->id))+" state="+std::to_string(u->order_state)+" pos="+std::to_string(u->position.x)+","+std::to_string(u->position.y)+" target="+std::to_string(u->order_target.pos.x)+","+std::to_string(u->order_target.pos.y):" no selection";throw std::runtime_error(error+diag+" card="+openbw_card());} }
static void aim(xy p) { g_ui->screen_pos=xy(std::max(0,std::min(p.x-320,int(g_ui->game_st.map_width)-640)),std::max(0,std::min(p.y-180,int(g_ui->game_st.map_height)-480)));draw(); }
static xy screen(xy p) { return p-g_ui->screen_pos; }
static void click(xy p) { aim(p);auto s=screen(p);command(0,s.x,s.y,0,0);command(1,1,1,s.x,s.y);command(1,0,1,s.x,s.y);draw();step(); }
static U worker_type() { return race==0?U::Zerg_Drone:race==1?U::Terran_SCV:U::Protoss_Probe; }
static U supply_type() { return race==0?U::Zerg_Overlord:race==1?U::Terran_Supply_Depot:U::Protoss_Pylon; }
static unit_t* produce(U t, unit_t* producer=nullptr) {
  if(!producer) { U parent=t==U::Zerg_Infested_Terran?U::Zerg_Infested_Command_Center:t==U::Terran_Nuclear_Missile?U::Terran_Nuclear_Silo:play_ui::bw_what_builds(t);if(parent==U::Zerg_Larva)wait_for([&]{return !units(parent).empty();},900,"Larvae did not replenish");producer=one(parent); }
  auto old=units(t);std::set<uint16_t> before;for(auto* u:old)before.insert(g_ui->get_unit_id(u).raw_value);
  select(producer);auto c=card(t);auto* type=g_ui->get_unit_type(t);int m=minerals(),g=gas();press(c);
  require(m-minerals()==type->mineral_cost&&g-gas()==type->gas_cost,"Production cost wrong for "+name(t));
  unit_t* result=nullptr;wait_for([&]{for(auto* u:units(t))if(!before.count(g_ui->get_unit_id(u).raw_value)){result=u;return true;}return false;},1800,"Production failed: "+name(t));return result;
}
static unit_t* worker() { if(units(worker_type()).empty())produce(worker_type());return one(worker_type()); }
static xy site(unit_t* builder, U t, bool reserve_addon=false) {
  const auto* type=g_ui->get_unit_type(t); std::vector<xy> candidates;
  for(int y=2;y<int(g_ui->game_st.map_tile_height)-6;++y)for(int x=2;x<int(g_ui->game_st.map_tile_width)-6;++x) {
    xy p(x*32+type->placement_size.x/2,y*32+type->placement_size.y/2);
    bool spawn_lane=false;
    if(race==0)for(auto* h:ptr(g_ui->st.player_units[0]))if(h->unit_type->id==U::Zerg_Hatchery||h->unit_type->id==U::Zerg_Lair||h->unit_type->id==U::Zerg_Hive) {
      // Larvae move/spawn along the south edge after the preview's check.
      if(p.x+type->placement_size.x/2>h->position.x-104&&p.x-type->placement_size.x/2<h->position.x+104&&p.y+type->placement_size.y/2>h->position.y+32&&p.y-type->placement_size.y/2<h->position.y+112)spawn_lane=true;
    }
    if(!spawn_lane&&g_ui->can_place_building(builder,0,type,p,true,true))candidates.push_back(p);
  }
  std::sort(candidates.begin(),candidates.end(),[](xy a,xy b){auto d=[](xy p){int x=p.x-origin.x,y=p.y-origin.y;return x*x+y*y;};return d(a)<d(b);});
  for(auto p:candidates) {
    // Leave a one-tile walking lane. Terran producers additionally reserve their addon footprint.
    bool crowded=false;for(auto* b:ptr(g_ui->st.player_units[0]))if(g_ui->ut_building(b)&&b!=builder) {
      xy gap=p-b->position;xy extent=(type->placement_size+b->unit_type->placement_size)/2+xy(40,40);
      if(reserve_addon)extent.x+=80;
      if(std::abs(gap.x)<extent.x&&std::abs(gap.y)<extent.y){crowded=true;break;}
    }
    if(!crowded)return p;
  }
  require(!candidates.empty(),"No valid site for "+name(t));return candidates.front();
}
static unit_t* build(U t, bool cancel=false, xy forced=xy(-1,-1)) {
  unit_t* w=worker();select(w);press(play_ui::bw_build_advanced(t)?"Advanced":"Build");auto c=card(t);
  require(c.enabled,"Prerequisite unavailable for "+name(t));const auto* type=g_ui->get_unit_type(t);
  xy p=forced.x>=0?forced:site(w,t,race==1);std::set<uint16_t> before;for(auto* u:units(t,false))before.insert(g_ui->get_unit_id(u).raw_value);
  auto wid=g_ui->get_unit_id(w);int wc=int(units(worker_type()).size());money();int m=minerals(),g=gas();
  // Place the test worker beside the site so a crowded tech-tree fixture cannot
  // turn a construction test into a long-distance pathfinding test.
  xy near=race==0?p-xy(0,7):p-xy(type->placement_size.x/2+32,0);
  auto free=g_ui->find_unit_placement(w,near,{near-xy(96,96),near+xy(96,96)},true,false);
  require(free.first,"No worker access for construction fixture");openbw_debug_warp(wid.raw_value,free.second.x,free.second.y);
  if(cancel)openbw_test_instant(0);
  press(c);aim(p);auto s=screen(p);require(openbw_placement_valid(s.x,s.y),"Valid site rejected by preview: "+name(t));click(p);
  unit_t* result=nullptr;try {wait_for([&]{for(auto* u:units(t,false))if(!before.count(g_ui->get_unit_id(u).raw_value)){result=u;return true;}return false;},5000,"Building did not start: "+name(t));}catch(...) {std::cerr<<"BUILD_DIAG "<<name(t)<<" site="<<p.x<<","<<p.y<<" can="<<g_ui->can_place_building(w,0,type,p,true,true)<<" immovable="<<g_ui->u_immovable(w)<<" queue="<<w->build_queue.size()<<std::endl;for(auto* n:g_ui->find_units_noexpand({p-xy(96,96),p+xy(96,96)}))std::cerr<<"NEAR "<<name(n->unit_type->id)<<" "<<n->position.x<<","<<n->position.y<<" dying="<<g_ui->unit_dying(n)<<std::endl;throw;}
  require(m-minerals()==type->mineral_cost&&g-gas()==type->gas_cost,"Building cost wrong: "+name(t));
  if(cancel) {
    auto id=g_ui->get_unit_id(result);select(result);press("Cancel");step(8);
    require(!g_ui->get_unit(id)||g_ui->get_unit(id)->unit_type->id!=t||g_ui->unit_dying(g_ui->get_unit(id)),"Cancelled structure remains");
    require(minerals()==m-type->mineral_cost+(type->mineral_cost*3/4)&&gas()==g-type->gas_cost+(type->gas_cost*3/4),"Building cancellation refund is not 75%");
    require(int(units(worker_type()).size())==wc,"Worker not returned by cancellation");openbw_test_instant(1);return nullptr;
  }
  wait_for([&]{return g_ui->u_completed(result);},2400,"Building did not finish: "+name(t));
  if(race==0)require(int(units(worker_type()).size())==wc-1,"Zerg construction did not consume one Drone");
  else require(g_ui->get_unit(wid)&&g_ui->get_unit(wid)->unit_type->id==worker_type(),"Construction consumed the worker");
  step(8);return result;
}
static unit_t* morph_building(U from,U to) { auto* u=one(from);auto id=g_ui->get_unit_id(u);select(u);int m=minerals(),g=gas();const auto* t=g_ui->get_unit_type(to);press(card(to));require(m-minerals()==t->mineral_cost&&g-gas()==t->gas_cost,"Morph cost wrong");wait_for([&]{auto* q=g_ui->get_unit(id);return q&&q->unit_type->id==to&&g_ui->u_completed(q);},1200,"Building morph failed: "+name(to));return g_ui->get_unit(id); }
static unit_t* addon(U parent,U t) {
  unit_t* u=nullptr;for(auto* b:units(parent))if(!g_ui->unit_addon(b)){u=b;break;}if(!u)u=build(parent);
  const auto* type=g_ui->get_unit_type(t);auto valid=[&](xy p){xy ap=p-u->unit_type->placement_size/2+type->addon_position+type->placement_size/2;return g_ui->can_place_building(u,0,u->unit_type,p,true,true)&&g_ui->can_place_building(u,0,type,ap,true,true);};
  xy p=u->position;if(!valid(p)) {bool found=false;for(int y=4;y<int(g_ui->game_st.map_tile_height)-6&&!found;++y)for(int x=4;x<int(g_ui->game_st.map_tile_width)-6&&!found;++x){xy q(x*32+u->unit_type->placement_size.x/2,y*32+u->unit_type->placement_size.y/2);if(valid(q)){p=q;found=true;}}require(found,"No valid combined addon footprint");}
  select(u);money();int m=minerals(),g=gas();press(card(t));click(p);wait_for([&]{return g_ui->unit_addon(u)&&g_ui->unit_addon(u)->unit_type->id==t&&g_ui->u_completed(g_ui->unit_addon(u));},5000,"Addon failed: "+name(t));require(m-minerals()==type->mineral_cost&&g-gas()==type->gas_cost,"Addon cost wrong");return g_ui->unit_addon(u);
}
static void fresh(int r,const std::string& map) {close_game();open_archive(3,map);race=r;openbw_init(640,480,r,0);openbw_set_external_cursor(1);openbw_reveal_map();money();openbw_test_instant(1);step(24);origin=one(worker_type())->position;}
static void tech_tree() {
  auto b=[](U t){check("Build "+name(t),[=]{build(t);});};
  auto a=[](U p,U t){check("Addon "+name(t),[=]{addon(p,t);});};
  auto m=[](U p,U t){check("Morph "+name(t),[=]{morph_building(p,t);});};
  if(race==1) {
    for(U t:{U::Terran_Supply_Depot,U::Terran_Refinery,U::Terran_Barracks,U::Terran_Engineering_Bay,U::Terran_Academy,U::Terran_Bunker,U::Terran_Missile_Turret,U::Terran_Factory,U::Terran_Starport,U::Terran_Science_Facility,U::Terran_Armory,U::Terran_Command_Center})b(t);
    a(U::Terran_Command_Center,U::Terran_Comsat_Station);a(U::Terran_Factory,U::Terran_Machine_Shop);a(U::Terran_Starport,U::Terran_Control_Tower);a(U::Terran_Science_Facility,U::Terran_Covert_Ops);a(U::Terran_Science_Facility,U::Terran_Physics_Lab);a(U::Terran_Command_Center,U::Terran_Nuclear_Silo);
  } else if(race==2) {
    for(U t:{U::Protoss_Pylon,U::Protoss_Assimilator,U::Protoss_Gateway,U::Protoss_Forge,U::Protoss_Cybernetics_Core,U::Protoss_Photon_Cannon,U::Protoss_Shield_Battery,U::Protoss_Pylon,U::Protoss_Citadel_of_Adun,U::Protoss_Robotics_Facility,U::Protoss_Stargate,U::Protoss_Pylon,U::Protoss_Robotics_Support_Bay,U::Protoss_Observatory,U::Protoss_Fleet_Beacon,U::Protoss_Templar_Archives,U::Protoss_Pylon,U::Protoss_Arbiter_Tribunal,U::Protoss_Nexus})b(t);
  } else {
    for(U t:{U::Zerg_Hatchery,U::Zerg_Spawning_Pool,U::Zerg_Extractor,U::Zerg_Evolution_Chamber,U::Zerg_Hydralisk_Den,U::Zerg_Creep_Colony})b(t);
    m(U::Zerg_Creep_Colony,U::Zerg_Sunken_Colony);b(U::Zerg_Creep_Colony);m(U::Zerg_Creep_Colony,U::Zerg_Spore_Colony);
    m(U::Zerg_Hatchery,U::Zerg_Lair);b(U::Zerg_Spire);b(U::Zerg_Queens_Nest);m(U::Zerg_Lair,U::Zerg_Hive);
    b(U::Zerg_Hatchery);for(U t:{U::Zerg_Nydus_Canal,U::Zerg_Defiler_Mound,U::Zerg_Ultralisk_Cavern})b(t);m(U::Zerg_Spire,U::Zerg_Greater_Spire);
  }
}
static void research_all() {
  // Expected IDs are the ordinary multiplayer research roster, independent of card enumeration.
  std::vector<T> techs=race==1?std::vector<T>{T::Stim_Packs,T::Lockdown,T::EMP_Shockwave,T::Spider_Mines,T::Tank_Siege_Mode,T::Irradiate,T::Yamato_Gun,T::Cloaking_Field,T::Personnel_Cloaking,T::Restoration,T::Optical_Flare}:race==2?std::vector<T>{T::Psionic_Storm,T::Hallucination,T::Recall,T::Stasis_Field,T::Disruption_Web,T::Mind_Control,T::Maelstrom}:std::vector<T>{T::Burrowing,T::Spawn_Broodlings,T::Ensnare,T::Plague,T::Consume,T::Lurker_Aspect};
  for(T t:techs)check("Research "+std::string(g_ui->tech_name(g_ui->get_tech_type(t))),[=]{
    unit_t* producer=nullptr;play_ui::cmd_t c{};for(auto* u:ptr(g_ui->st.player_units[0]))if(g_ui->ut_building(u)){select(u);for(auto x:g_ui->card)if(x.act==play_ui::C_RESEARCH&&x.tech==t&&x.enabled){producer=u;c=x;break;}if(producer)break;}
    require(producer,"Research command absent from all completed buildings");money();openbw_test_instant(0);int m=minerals(),g=gas();const auto* type=g_ui->get_tech_type(t);press(c);require(g_ui->player_is_researching(0,t),"Research did not start");require(m-minerals()==type->mineral_cost&&g-gas()==type->gas_cost,"Research cost wrong");openbw_cancel(0);step(4);require(!g_ui->player_is_researching(0,t)&&!g_ui->player_has_researched(0,t),"Research cancellation failed");require(minerals()==m&&gas()==g,"Research refund not 100%");select(producer);for(auto x:g_ui->card)if(x.act==play_ui::C_RESEARCH&&x.tech==t)c=x;press(c);openbw_test_instant(1);wait_for([&]{return g_ui->player_has_researched(0,t);},180,"Research never finished");select(producer);for(auto x:g_ui->card)require(x.act!=play_ui::C_RESEARCH||x.tech!=t,"Completed research still offered");
  });
}
static void upgrades_all() {
  for(int id=0;id<61;++id) { auto t=G(id);auto* type=g_ui->get_upgrade_type(t);if(!type||int(type->race)!=race||type->max_level==0)continue;
    check("Upgrade "+std::string(g_ui->upgrade_name(type)),[=]{
      for(int level=0;level<type->max_level;++level) {
        unit_t* producer=nullptr;play_ui::cmd_t c{};for(auto* u:ptr(g_ui->st.player_units[0]))if(g_ui->ut_building(u)){select(u);for(auto x:g_ui->card)if(x.act==play_ui::C_UPGRADE&&x.upg==t&&x.enabled){producer=u;c=x;break;}if(producer)break;}
        require(producer,"Upgrade command absent at level "+std::to_string(level+1));money();openbw_test_instant(0);int m=minerals(),g=gas();press(c);require(g_ui->player_is_upgrading(0,t),"Upgrade did not start");require(m-minerals()==type->mineral_cost_base+level*type->mineral_cost_factor&&g-gas()==type->gas_cost_base+level*type->gas_cost_factor,"Upgrade cost wrong");openbw_cancel(0);step(4);require(!g_ui->player_is_upgrading(0,t)&&g_ui->player_upgrade_level(0,t)==level,"Upgrade cancellation failed");require(minerals()==m&&gas()==g,"Upgrade refund not 100%");select(producer);for(auto x:g_ui->card)if(x.act==play_ui::C_UPGRADE&&x.upg==t)c=x;press(c);openbw_test_instant(1);wait_for([&]{return g_ui->player_upgrade_level(0,t)==level+1;},180,"Upgrade never finished");
      }
    });
  }
}
static void production_all() {
  // Supply is built through ordinary production; keep capacity below the engine's 200 cap.
  for(int n=0;n<7;++n) {if(race==0)produce(U::Zerg_Overlord);else build(supply_type());}
  std::vector<U> roster=race==1?std::vector<U>{U::Terran_SCV,U::Terran_Marine,U::Terran_Firebat,U::Terran_Medic,U::Terran_Ghost,U::Terran_Vulture,U::Terran_Goliath,U::Terran_Siege_Tank_Tank_Mode,U::Terran_Wraith,U::Terran_Dropship,U::Terran_Science_Vessel,U::Terran_Battlecruiser,U::Terran_Valkyrie,U::Terran_Nuclear_Missile}:race==2?std::vector<U>{U::Protoss_Probe,U::Protoss_Zealot,U::Protoss_Dragoon,U::Protoss_High_Templar,U::Protoss_Dark_Templar,U::Protoss_Shuttle,U::Protoss_Reaver,U::Protoss_Observer,U::Protoss_Scout,U::Protoss_Carrier,U::Protoss_Arbiter,U::Protoss_Corsair}:std::vector<U>{U::Zerg_Drone,U::Zerg_Zergling,U::Zerg_Hydralisk,U::Zerg_Mutalisk,U::Zerg_Overlord,U::Zerg_Queen,U::Zerg_Scourge,U::Zerg_Defiler,U::Zerg_Ultralisk,U::Zerg_Lurker,U::Zerg_Guardian,U::Zerg_Devourer};
  for(U t:roster)check("Produce "+name(t),[=]{money();if(t==U::Zerg_Devourer)produce(U::Zerg_Mutalisk);produce(t);});
}
#include "native_gameplay_cases.h"
#include "native_controls38.h"
#include "native_polish39.h"
int main(int argc,char** argv) {try {
  signal(SIGSEGV, [](int){void* trace[50];int n=backtrace(trace,50);backtrace_symbols_fd(trace,n,2);_exit(139);});
  require(argc>=3,"Usage: native-gameplay DATA_DIR WEAVE_SCX [REPORT]");std::string dir=argv[1];open_archive(0,dir+"/STARDAT.MPQ");open_archive(1,dir+"/BROODAT.MPQ");open_archive(2,dir+"/patch_rt.mpq");
  if(argc<5||std::string(argv[4])!="polish-only")for(int r:{1,2,0}) {fresh(r,argv[2]);check("Race fixture completes "+std::to_string(r),[&]{initial_constraints();tech_tree();research_all();upgrades_all();production_all();negative_production();if(r==1)terran_special();else if(r==2)protoss_special();else zerg_special();removed_refinery();controls38(r);check("Cancel construction race "+std::to_string(r),[&]{build(r==0?U::Zerg_Creep_Colony:supply_type(),true);});});}
  fresh(1,argv[2]);polish39();
  close_game();std::string report="{\"passed\":"+std::string(failed?"false":"true")+",\"passCount\":"+std::to_string(passed)+",\"failCount\":"+std::to_string(failed)+",\"checks\":[";for(size_t i=0;i<results.size();++i){if(i)report+=',';report+=results[i];}report+="]}\n";if(argc>3)std::ofstream(argv[3])<<report;std::cout<<"GAMEPLAY_RESULT "<<passed<<" passed, "<<failed<<" failed\n";return failed?1:0;
}catch(const std::exception& e){std::cerr<<"HARNESS_ERROR "<<e.what()<<'\n';return 2;}}
