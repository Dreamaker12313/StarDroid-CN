// Original CHK records with synthetic engine data. No terrain, audio, combat
// simulation or campaign playthrough is claimed. Pass an external CHK directory.
#include "native_fixture.h"
#include <filesystem>
#include <fstream>
#include <map>

using Reader = data_loading::data_reader_le;
using U = UnitTypes;
struct MapUnit {int owner, type;xy pos;};
struct Mission {
  std::array<int,12> owners{};
  std::array<int,8> forces{};
  std::array<int,4> forceFlags{};
  unsigned starts=0;
  xy tiles{};
  std::vector<MapUnit> units;
  std::vector<location> locations;
  std::vector<trigger> triggers;
  explicit Mission(const std::filesystem::path& path) {
    std::ifstream in(path,std::ios::binary);
    require(bool(in),"Missing external CHK");
    std::vector<uint8_t> bytes((std::istreambuf_iterator<char>(in)),{});
    Reader all(bytes.data(),bytes.data()+bytes.size());
    while(all.left()) {
      auto tag=all.get<std::array<char,4>>();auto size=all.get<uint32_t>();
      require(size<=all.left(),"Truncated CHK section");
      Reader r(all.ptr,all.ptr+size);all.skip(size);
      std::string name(tag.data(),4);
      if(name=="OWNR")for(auto& p:owners)p=r.get<uint8_t>();
      if(name=="DIM "){tiles.x=r.get<uint16_t>();tiles.y=r.get<uint16_t>();}
      if(name=="FORC") {
        for(auto& p:forces)p=r.get<uint8_t>()+1;
        r.skip(8);for(auto& f:forceFlags)f=r.get<uint8_t>();
      }
      if(name=="UNIT")while(r.left()) {
        r.skip(4);MapUnit u;u.pos.x=r.get<uint16_t>();u.pos.y=r.get<uint16_t>();
        u.type=r.get<uint16_t>();r.skip(6);u.owner=r.get<uint8_t>();r.skip(19);
        if(u.type==int(U::Special_Start_Location))starts|=1u<<u.owner;
        else units.push_back(u);
      }
      if(name=="MRGN")while(r.left()) {
        location l{};l.area.from.x=r.get<int32_t>();l.area.from.y=r.get<int32_t>();
        l.area.to.x=r.get<int32_t>();l.area.to.y=r.get<int32_t>();r.skip(2);
        l.elevation_flags=r.get<uint16_t>();locations.push_back(l);
      }
      if(name=="TRIG")while(r.left()) {
        trigger t{};
        for(auto& c:t.conditions) {
          c.location=r.get<uint32_t>();c.group=r.get<uint32_t>();c.count_n=r.get<uint32_t>();
          c.unit_id=r.get<uint16_t>();c.num_n=r.get<uint8_t>();c.type=r.get<uint8_t>();
          c.extra_n=r.get<uint8_t>();c.flags=r.get<uint8_t>();c.unk=r.get<uint16_t>();
        }
        for(auto& a:t.actions) {
          a.location=r.get<uint32_t>();a.string_index=r.get<uint32_t>();a.sound_index=r.get<uint32_t>();
          a.time_n=r.get<uint32_t>();a.group_n=r.get<uint32_t>();a.group2_n=r.get<uint32_t>();
          a.extra_n=r.get<uint16_t>();a.type=r.get<uint8_t>();a.num_n=r.get<uint8_t>();
          a.flags=r.get<uint8_t>();a.unk=r.get<uint16_t>();r.skip(1);
        }
        t.execution_flags=r.get<uint32_t>();for(auto& p:t.enabled)p=r.get<uint8_t>()!=0;
        triggers.push_back(t);
      }
    }
  }
  void setup(Fixture& f) const {
    auto& ui=*f.ui;
    f.game.map_tile_width=tiles.x;f.game.map_tile_height=tiles.y;
    f.game.map_width=tiles.x*32;f.game.map_height=tiles.y*32;
    f.st.tiles.resize(tiles.x*tiles.y);f.st.players={};f.st.alliances={};
    // Synthetic flat ground supports location elevation filters only.
    f.game.gfx_tiles.resize(tiles.x*tiles.y);f.game.cv5.resize(1);f.game.vf4.resize(1);
    for(int p=0;p<12;p++) {
      auto& player=f.st.players[p];player.controller=owners[p];
      if(player.controller==player_t::controller_computer)player.controller=player_t::controller_computer_game;
      if(player.controller==player_t::controller_open){player.controller=player_t::controller_occupied;ui.my_player=p;}
      if(p<8)player.force=forces[p];
      f.st.alliances[p][p]=f.st.alliances[p][11]=f.st.alliances[11][p]=1;
      f.st.shared_vision[p]=1<<p;
    }
    for(int p=0;p<12;p++)if(owners[p]==player_t::controller_neutral||owners[p]==player_t::controller_rescue_passive)
      for(int q=0;q<12;q++)f.st.alliances[p][q]=f.st.alliances[q][p]=1;
    for(int n=0;n<4;n++)f.game.forces[n].flags=forceFlags[n];
    ui.apply_force_settings();ui.apply_computer_alliances(starts);
    f.st.locations.assign(locations.begin(),locations.end());
    // Command conditions use actual placed type counts; no fake world is run.
    for(auto& u:units)if(u.type<int(U::None)&&u.owner<12) {
      ++f.st.unit_counts[u.owner][U(u.type)];++f.st.completed_unit_counts[u.owner][U(u.type)];
    }
  }
};
static bool conditions(campaign_ui& ui,const trigger& t,int owner) {
  for(auto& c:t.conditions){if(!c.type)break;if(!ui.test_trigger_condition(c,owner))return false;}
  return true;
}
static void action(campaign_ui& ui,int owner,const trigger::action& a) {
  state_functions::execute_trigger_struct ets;running_trigger rt{};running_trigger::action ra{};
  require(ui.execute_trigger_action(ets,owner,rt,ra,a),"Unexpected wait in single-action fixture");
}
static xy center(const location& l){return (l.area.from+l.area.to)/2;}
static void relocate(Fixture& f,unit_t* u,xy p) {
  f.ui->unit_finder_remove(u);u->position=u->sprite->position=p;f.ui->unit_finder_insert(u);
}

int main(int argc,char** argv) {try {
  require(argc==2,"Usage: native-missions EXTERNAL_CHK_DIRECTORY");
  std::filesystem::path directory(argv[1]);int mapCount=0,computerPairs=0,conditionChecks=0;std::set<int> conditionTypes;
  for(auto& entry:std::filesystem::directory_iterator(directory))if(entry.path().extension()==".chk") {
    Mission m(entry.path());auto f=std::make_unique<Fixture>();m.setup(*f);mapCount++;
    // Every actual condition record is dispatched by the shipped engine for
    // each owning player, with switches/time in both initial and later states.
    // Counts/terrain here remain synthetic: this is not a mission playthrough.
    for(auto& t:m.triggers)for(int owner=0;owner<8;owner++) {
      if(!t.enabled[owner]&&!t.enabled[17]&&!t.enabled[17+m.forces[owner]])continue;
      for(auto& c:t.conditions) {
        if(!c.type)break;if(c.flags&2)continue;conditionTypes.insert(c.type);
        f->ui->switches.fill(false);f->st.current_frame=0;f->ui->countdown_ms=0;
        f->ui->test_trigger_condition(c,owner);
        f->ui->switches.fill(true);f->st.current_frame=240000;f->ui->countdown_ms=60000;
        f->ui->test_trigger_condition(c,owner);conditionChecks+=2;
      }
    }
    for(int p=0;p<8;p++)for(int q=0;q<8;q++) {
      if(p!=q&&m.owners[p]==5&&m.owners[q]==5&&(m.starts&(1<<p))&&(m.starts&(1<<q))) {
        require(f->st.alliances[p][q]!=0,"Original computer participants start hostile");computerPairs++;
      }
      if(m.forces[p]==m.forces[q]&&(m.forceFlags[m.forces[p]-1]&2))
        require(f->st.alliances[p][q]==((m.forceFlags[m.forces[p]-1]&4)?2:1),"Default computers overwrite force victory setting");
    }
  }
  require(mapCount==64,"Expected all 64 exported campaign maps");
  std::cout<<"PASS 64 original maps: "<<computerPairs<<" directed computer alliances and force flags\n";
  require(conditionTypes.size()==13,"Unexpected original condition coverage");
  std::cout<<"PASS 64 original maps: "<<conditionChecks<<" condition dispatches across all 13 used types, with initial/later switch and timer states\n";
  {
    auto f=std::make_unique<Fixture>();
    for(int p=0;p<3;p++)f->st.players[p].controller=player_t::controller_computer_game;
    f->st.players[3].controller=player_t::controller_occupied;
    f->ui->apply_computer_alliances((1<<0)|(1<<1)|(1<<3));
    require(f->st.alliances[0][1]&&f->st.alliances[1][0],"Computer alliance absent");
    require(!f->st.alliances[0][2]&&!f->st.alliances[2][0],"Trap owner without start became allied");
    require(!f->st.alliances[0][3]&&!f->st.alliances[3][0],"Human was allied automatically");
  }
  std::cout<<"PASS human and no-start trap slots stay outside default computer alliance\n";
  {
    Mission m(directory/"zerg04.chk");auto f=std::make_unique<Fixture>();m.setup(*f);auto& ui=*f->ui;
    auto* marine=f->unit(U::Terran_Marine,1,{2880,400});
    auto* base=f->unit(U::Terran_Command_Center,2,{2912,400},unit_type_t::flag_building);
    require(!ui.unit_target_is_enemy(marine,base)&&!ui.unit_target_is_enemy(base,marine),"Militia can attack Raynor's command center");
    require(!conditions(ui,m.triggers.at(4),3),"Early Raynor ending starts with intact command center");
    f->st.unit_counts[2][U::Terran_Command_Center]=0;
    require(conditions(ui,m.triggers.at(4),3),"Original Raynor loss condition was not exercised");
    f->st.unit_counts[2][U::Terran_Command_Center]=1;
    ui.switches[0]=true;ui.countdown_ms=0;
    require(conditions(ui,m.triggers.at(3),3),"Original hatch countdown condition missing");
    require(!conditions(ui,m.triggers.at(6),3),"Intact Chrysalis defeats player");
    // Check the original one-second Wait / switch-clear pair after scripted
    // Chrysalis destruction. World death processing is represented by counts.
    trigger hatch{};hatch.conditions[0].type=22;
    hatch.actions[0]=m.triggers[3].actions[4];hatch.actions[1]=m.triggers[3].actions[5];
    require(hatch.actions[0].type==4&&hatch.actions[0].time_n==1000&&hatch.actions[1].type==13,"Hatch fixture changed");
    running_trigger a{};a.t=&hatch;f->st.running_triggers[3].push_back(a);
    running_trigger b{};b.t=&m.triggers[6];f->st.running_triggers[3].push_back(b);
    ui.process_triggers(); // Kill marks a unit dying; counts change next frame.
    f->st.unit_counts[3][U::Special_Mature_Chrysalis]=0;
    for(int frame=0;frame<30;frame++)ui.process_triggers();
    require(!ui.switches[0]&&!(f->st.running_triggers[3][1].flags&1)&&ui.outcome==0,"Hatching latches the Chrysalis-destroyed failure");
  }
  std::cout<<"PASS Agent of the Swarm: Raynor alliance, original ending condition and hatch wait ordering\n";
  {
    Mission m(directory/"expzerg05.chk");auto f=std::make_unique<Fixture>();m.setup(*f);auto& ui=*f->ui;
    f->game.unit_types.vec[size_t(U::Zerg_Lurker)].right_click_action=2;
    std::vector<unit_t*> lurkers;
    for(auto& u:m.units)if(u.type==int(U::Zerg_Lurker)&&u.owner==4) {
      auto* l=f->unit(U::Zerg_Lurker,4,u.pos,unit_type_t::flag_can_burrow|unit_type_t::flag_can_move);
      l->status_flags|=unit_t::status_flag_can_move;f->st.player_units[4].push_front(*l);lurkers.push_back(l);
    }
    require(lurkers.size()==3,"True Colors opening Lurkers missing");
    for(auto& a:m.triggers.at(16).actions)if(a.type==46)action(ui,4,a);
    for(auto* l:lurkers)require(l->order_type->id==Orders::Move,"Original ambush approach order missing");
    for(auto* l:lurkers) {
      // Advance to the destination selected by the actual mission order.
      relocate(*f,l,l->order_target.pos);ui.set_unit_order(l,ui.get_order_type(Orders::Nothing));
      auto* victim=f->unit(U::Terran_Marine,0,l->position+xy(32,0));(void)victim;
    }
    require(conditions(ui,m.triggers.at(17),4),"Three original ambush locations do not satisfy Bring conditions");
    ui.ai_lurkers(4);
    for(auto* l:lurkers)require(l->order_type->id==Orders::Nothing,"Lurker attacks before scripted betrayal");
    for(auto& a:m.triggers[17].actions)if(a.type==57)action(ui,4,a);
    require(f->st.alliances[4][0]==0&&f->st.alliances[4][1]==0,"Original betrayal did not override initial alliance");
    require(f->st.alliances[0][1]&&f->st.alliances[1][0],"Terrans and Protoss attack each other");
    ui.ai_lurkers(4);
    for(auto* l:lurkers) {
      require(l->order_type->id==Orders::Burrowing,"Lurker never starts combat burrow after betrayal");
      // Animation is outside this fixture; model its completed state.
      ui.set_unit_order(l,ui.get_order_type(Orders::Burrowed));l->status_flags|=unit_t::status_flag_burrowed;
    }
    for(auto& a:m.triggers.at(18).actions)if(a.type==46)action(ui,4,a);
    for(auto* l:lurkers) {
      require(l->order_type->id==Orders::Unburrowing&&!l->order_queue.empty()&&l->order_queue.front().order_type->id==Orders::Move,"Original exit Move cannot unburrow Lurker");
      l->status_flags&=~unit_t::status_flag_burrowed;l->order_state=3;ui.order_Unburrowing(l);
      require(l->order_type->id==Orders::Move,"Exit move lost after unburrowing");
    }
    ui.ai_lurkers(4);
    for(auto* l:lurkers)require(l->order_type->id==Orders::Move,"Automatic burrow interrupts scripted exit Move");
    auto* l=lurkers.front();ui.set_unit_order(l,ui.get_order_type(Orders::AttackMove),l->order_target.pos);
    ui.ai_lurkers(4);require(l->order_type->id==Orders::Burrowing,"AttackMove no longer permits combat burrow");
    require(f->st.alliances[4][0]==0,"AI overwrites scripted hostility");
    // Use the original P1 -> human ceasefire action, after a hostile attack.
    auto* soldier=f->unit(U::Terran_Marine,0,{600,600});f->st.player_units[0].push_front(*soldier);
    auto* human=f->unit(U::Zerg_Zergling,3,{632,600});
    f->global.order_types.vec[size_t(Orders::AttackUnit)].targets_enemies=true;
    ui.set_unit_order(soldier,ui.get_order_type(Orders::AttackUnit),human);
    bool ceasefire=false;
    for(auto& a:m.triggers.at(9).actions)if(a.type==57){action(ui,0,a);ceasefire=true;}
    require(ceasefire&&f->st.alliances[0][3]&&soldier->order_target.unit==nullptr,"Alliance trigger leaves an ally under attack");
  }
  std::cout<<"PASS True Colors: three ambush locations, betrayal, burrow, unburrow/exit, Move priority and ceasefire\n";
  {
    Mission m(directory/"expzerg05.chk");auto f=std::make_unique<Fixture>();m.setup(*f);auto& ui=*f->ui;
    require(m.owners[5]==player_t::controller_neutral,"True Colors base no longer starts neutral");
    auto& type=f->game.unit_types.vec[size_t(U::Zerg_Hatchery)];
    type.human_ai_idle=ui.get_order_type(Orders::InitCreepGrowth);
    std::vector<unit_t*> hatcheries;
    for(auto& placed:m.units)if(placed.type==int(U::Zerg_Hatchery)&&placed.owner==5) {
      auto* u=f->unit(U::Zerg_Hatchery,5,placed.pos,unit_type_t::flag_building);
      u->status_flags|=unit_t::status_flag_grounded_building;
      ui.set_unit_order(u,ui.get_order_type(Orders::Neutral));
      f->st.player_units[5].push_front(*u);hatcheries.push_back(u);
    }
    require(hatcheries.size()==2,"Expected both original neutral Hatcheries");
    bool given=false;
    for(auto& a:m.triggers.at(2).actions)if(a.type==48&&a.group_n==5) {action(ui,3,a);given=true;}
    require(given,"Original base handover action absent");
    for(auto* u:hatcheries) {
      require(u->owner==3&&u->sprite->owner==3,"Hatchery ownership/colour not transferred");
      require(u->order_type->id==Orders::InitCreepGrowth,"Transferred Hatchery never initializes larva production");
      ui.execute_main_order(u);
      require(u->secondary_order_type->id==Orders::SpreadCreep,"Creep/larva secondary order not initialized");
      // Avoid claiming real terrain placement: this fixture has no creep.
      // The production scheduler must still tick and retry a blocked spawn.
      u->order_process_timer=0;u->building.creep_timer=100;u->building.larva_timer=1;
      ui.execute_secondary_order(u);
      require(u->building.larva_timer==0,"Transferred Hatchery's larva timer is stalled");
      ui.execute_secondary_order(u);
      require(u->building.larva_timer==3,"Transferred Hatchery does not attempt larva spawning");
      std::vector<unit_t*> larvae;
      for(int i=0;i<3;i++) {auto* l=f->unit(U::Zerg_Larva,3,u->position+xy(16+i*16,32));l->connected_unit=u;larvae.push_back(l);}
      u->building.larva_timer=1;ui.execute_secondary_order(u);
      require(u->building.larva_timer==1,"Three-larva limit ignored after handover");
      ui.unit_finder_remove(larvae.back());ui.execute_secondary_order(u);
      require(u->building.larva_timer==0,"Larva production does not resume when one is consumed");
    }
    require(f->st.completed_unit_counts[5][U::Zerg_Hatchery]==0&&f->st.completed_unit_counts[3][U::Zerg_Hatchery]>=2,"Completed Hatchery counts not transferred");
  }
  std::cout<<"PASS True Colors: both original Hatchery transfers initialize creep/larva orders, tick production, cap three and resume after consumption\nMISSIONS_RESULT PASS\n";
  return 0;
}catch(const std::exception& e){std::cerr<<"MISSIONS_ERROR "<<e.what()<<'\n';return 1;}}
