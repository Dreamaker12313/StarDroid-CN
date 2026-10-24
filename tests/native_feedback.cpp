// Executable engine regressions with explicit synthetic state; no original assets.
// These isolate logic. They do not claim to replay an original campaign map.
#include "native_fixture.h"
#include <sstream>

int main() {try {
  auto f=std::make_unique<Fixture>();auto& ui=*f->ui;
  using U=UnitTypes;using T=TechTypes;
  for(auto type:{U::Special_Floor_Gun_Trap,U::Special_Floor_Missile_Trap,U::Special_Wall_Missile_Trap,U::Special_Wall_Flame_Trap,U::Special_Right_Wall_Missile_Trap,U::Special_Right_Wall_Flame_Trap}) {
    auto* u=f->unit(type,1,{160,160},unit_type_t::flag_building);
    ui.u_set_status_flag(u,unit_t::status_flag_cloaked);ui.u_set_status_flag(u,unit_t::status_flag_requires_detector);
    require(ui.unit_hidden_by_fog(u),"Unrevealed trap visible on visible terrain");
    u->detected_flags=1;require(!ui.unit_hidden_by_fog(u),"Detected trap hidden in current vision");
    u->sprite->visibility_flags=0;require(ui.unit_hidden_by_fog(u),"Trap persists in explored fog");
    u->sprite->visibility_flags=1;ui.u_unset_status_flag(u,unit_t::status_flag_cloaked);ui.u_unset_status_flag(u,unit_t::status_flag_requires_detector);
    require(!ui.unit_hidden_by_fog(u),"Revealed trap remains hidden");
    f->select(u);require(std::string(ui.unit_details()).find("\narmor\t")==std::string::npos,"Trap armor placeholder leaked");
  }
  std::cout<<"PASS six trap types: hidden, detected, revealed, fog and no armor\n";
  const int hero=unit_type_t::flag_hero|unit_type_t::flag_has_energy;
  auto* k=f->unit(U::Hero_Infested_Kerrigan,0,{128,128},hero);
  auto c=f->card(k);for(auto label:{"Cloak","Psionic Storm","Ensnare","Consume"})require(c.count(label),"Infested Kerrigan ability missing");
  require(!c.count("Lockdown")&&!c.count("Nuclear Strike"),"Kerrigan inherited Ghost-only ability");
  f->game.tech_available[0][T::Psionic_Storm]=false;c=f->card(k);require(!c.count("Psionic Storm"),"Mission's disabled tech bypassed");
  f->game.tech_available[0][T::Psionic_Storm]=true;k->energy=0_fp8;f->card(k);
  for(auto& command:ui.card)if(command.act==ui.C_SPELL||command.act==ui.C_CLOAK)require(!command.enabled,"Low-energy hero spell enabled");
  // The actual cloak command must accept the hero, spend activation energy,
  // decline insufficient energy and permit decloaking again.
  action_state actionState;actionState.selection[0].push_back(k);
  action_functions actions(f->st,actionState);
  actions.action_cloak(0);
  require(k->secondary_order_type->id==Orders::Nothing,"Low-energy cloak executed");
  k->energy=fp8::integer(100);actions.action_cloak(0);
  require(k->secondary_order_type->id==Orders::Cloak&&k->energy==fp8::integer(75),"Kerrigan cloak action or activation cost failed");
  actions.action_decloak(0);require(k->secondary_order_type->id==Orders::Decloak,"Kerrigan cannot decloak");
  const std::pair<U,const char*> cases[]={
    {U::Hero_Sarah_Kerrigan,"Lockdown"},{U::Hero_Alexei_Stukov,"Cloak"},
    {U::Hero_Samir_Duran,"Lockdown"},{U::Hero_Infested_Duran,"Consume"},
    {U::Hero_Jim_Raynor_Marine,"Stim Pack"},{U::Hero_Gui_Montag,"Stim Pack"},
    {U::Hero_Edmund_Duke_Tank_Mode,"Siege Mode"},{U::Hero_Edmund_Duke_Siege_Mode,"Tank Mode"},
    {U::Hero_Magellan,"EMP Shockwave"},{U::Hero_Hyperion,"Yamato Gun"},
    {U::Hero_Norad_II,"Yamato Gun"},{U::Hero_Gerard_DuGalle,"Yamato Gun"},
    {U::Hero_Tom_Kazansky,"Cloak"},
    {U::Hero_Tassadar,"Psionic Storm"},{U::Hero_Danimoth,"Recall"},
    {U::Hero_Matriarch,"Ensnare"},{U::Hero_Unclean_One,"Plague"},
    {U::Hero_Raszagal,"Disruption Web"}};
  for(auto test:cases)require(f->card(f->unit(test.first,0,{128,128},hero)).count(test.second),test.second);
  auto* v=f->unit(U::Hero_Jim_Raynor_Vulture,0,{128,128},hero);v->vulture.spider_mine_count=3;
  require(f->card(v).count("Spider Mines"),"Raynor mines missing");
  auto* h=f->unit(U::Hero_Hunter_Killer,0,{128,128},hero|unit_type_t::flag_can_burrow);
  require(f->card(h).count("Burrow"),"Hunter Killer burrow missing");
  std::cout<<"PASS hero command cards, mission restrictions and energy gating\n";
  // Exercise the actual exported tap classifier and the simulation's resulting order.
  for(auto pair:{std::make_pair(U::Zerg_Drone,U::Zerg_Extractor),std::make_pair(U::Terran_SCV,U::Terran_Refinery),std::make_pair(U::Protoss_Probe,U::Protoss_Assimilator)}) {
    auto gas=std::make_unique<Fixture>();auto* worker=gas->unit(pair.first,0,{64,64},unit_type_t::flag_worker);
    gas->game.unit_types.vec[size_t(pair.first)].right_click_action=4;
    auto* building=gas->unit(pair.second,0,{512,512},unit_type_t::flag_building|unit_type_t::flag_resource);
    building->status_flags|=unit_t::status_flag_grounded_building;
    gas->select(worker);g_ui=gas->ui.get();
    require(openbw_touch_action(512,512)==1,"Refinery tap selects instead of gathering");
    auto* order=g_ui->get_default_order(g_ui->default_action(worker),worker,{512,512},building,nullptr);
    require(order&&order->id==Orders::MoveToGas,"Refinery context does not resolve to gas gathering");
    g_ui->u_unset_status_flag(building,unit_t::status_flag_completed);
    require(openbw_touch_action(512,512)==0,"Unfinished refinery accepts gather shortcut");
    building->owner=1;g_ui->u_set_status_flag(building,unit_t::status_flag_completed);
    order=g_ui->get_default_order(g_ui->default_action(worker),worker,{512,512},building,nullptr);
    require(!order||order->id!=Orders::MoveToGas,"Worker gathers from enemy refinery");
    g_ui=nullptr;
  }
  std::cout<<"PASS Drone/SCV/Probe refinery taps and gas orders\n";
  for(auto type:{U::Special_Upper_Level_Door,U::Special_Right_Upper_Level_Door,U::Special_Pit_Door,U::Special_Right_Pit_Door}) {
    auto door=std::make_unique<Fixture>();auto& d=*door->ui;
    auto* u=door->unit(type,0,{512,512},unit_type_t::flag_building);
    door->game.unit_types.vec[size_t(type)].elevation_level=4;
    auto& script=door->global.iscript.scripts[0];script.id=0;script.animation_pc.resize(32,1);
    // Retail door orders are non-interruptible. Completion arrives several
    // frames later; both transitions must explicitly release that order lock.
    door->global.order_types.vec[size_t(Orders::OpenDoor)].can_be_interrupted=false;
    door->global.order_types.vec[size_t(Orders::CloseDoor)].can_be_interrupted=false;
    constexpr int opcodeTag=0x808091;
    door->global.iscript.program_data={0,iscript_opcodes::opc_wait+opcodeTag,6,
      iscript_opcodes::opc_sigorder+opcodeTag,1,iscript_opcodes::opc_wait+opcodeTag,1,iscript_opcodes::opc_goto+opcodeTag,5};
    u->sprite->main_image->iscript_state.current_script=&script;
    auto animate=[&](){
      auto unitContext=d.make_thingy_setter(d.iscript_unit,u);
      auto flingyContext=d.make_thingy_setter(d.iscript_flingy,u);
      for(int i=0;i<24;++i){d.execute_main_order(u);d.iscript_execute_sprite(u->sprite);}
    };
    d.set_doodad_state(u,false);
    require(u->order_type->id==Orders::OpenDoor && !(u->order_signal&1),"Open animation did not wait for its frames");
    require(!d.unit_is_trap(u),"Door incorrectly treated as a cloaked trap");
    int wait=u->sprite->main_image->iscript_state.wait;
    d.set_doodad_state(u,false);
    require(u->sprite->main_image->iscript_state.wait==wait,"Repeated trigger restarts door animation");
    require(!d.u_no_collide(u),"Door became passable before its open order completed");
    animate();
    require(d.u_no_collide(u)&&u->sprite->elevation_level==1&&u->order_type->id==Orders::Nothing,"Open door keeps its order lock or collision");
    d.set_doodad_state(u,true);
    require(!d.u_no_collide(u)&&u->sprite->elevation_level==4&&u->order_type->id==Orders::CloseDoor,"Closing door remains passable or stuck");
    animate();
    require(!d.u_no_collide(u)&&u->order_type->id==Orders::Nothing,"Closed door collision/order mismatch");
    d.set_doodad_state(u,false);animate();
    require(d.u_no_collide(u)&&u->order_type->id==Orders::Nothing,"Door cannot open a second time");
  }
  std::cout<<"PASS four door types: iscript signal context and collision transitions\n";
  {
    auto allies=std::make_unique<Fixture>();auto& a=*allies->ui;
    for(int p=0;p<4;p++) {allies->st.players[p].controller=player_t::controller_computer_game;allies->st.players[p].force=p<3?1:2;}
    allies->game.forces[0].flags=2|8;
    a.apply_force_settings();
    for(int p=0;p<3;p++)for(int q=0;q<3;q++)require(allies->st.alliances[p][q]==1&&(allies->st.shared_vision[p]&(1<<q)),"Force alliance/vision missing for computer players");
    require(allies->st.alliances[1][3]==0,"Other force became allied");
    require(a.trigger_players_pred(1,15,2)&&!a.trigger_players_pred(1,14,2),"Allied trigger group excludes ally without shared victory");
    allies->game.forces[0].flags|=4;a.apply_force_settings();
    require(allies->st.alliances[1][2]==2,"Force shared victory flag ignored");
    auto* protectedBase=allies->unit(U::Terran_Command_Center,1,{400,400},unit_type_t::flag_building);
    a.apply_map_unit_flags(protectedBase,16,16);require(a.u_invincible(protectedBase),"Preplaced invincibility ignored");
    a.apply_map_unit_flags(protectedBase,16,0);require(!a.u_invincible(protectedBase),"Explicit invincibility reset ignored");
    auto* buried=allies->unit(U::Zerg_Lurker,1,{100,100},unit_type_t::flag_can_burrow);
    a.apply_map_unit_flags(buried,2,2);require(buried->order_type->id==Orders::Burrowing,"Preplaced burrow flag ignored");
  }
  std::cout<<"PASS force allies, shared victory/vision and map invincibility/burrow flags\n";
  for(auto type:{U::Special_Floor_Gun_Trap,U::Special_Floor_Missile_Trap,U::Special_Wall_Missile_Trap,U::Special_Wall_Flame_Trap,U::Special_Right_Wall_Missile_Trap,U::Special_Right_Wall_Flame_Trap}) {
    auto trap=std::make_unique<Fixture>();auto& t=*trap->ui;
    weapon_type_t weapon{};weapon.max_range=256;weapon.attack_angle=fp8::integer(128);weapon.cooldown=15;
    auto* u=trap->unit(type,1,{128,128},unit_type_t::flag_building);
    trap->game.unit_types.vec[size_t(type)].ground_weapon=&weapon;
    trap->game.unit_types.vec[size_t(type)].target_acquisition_range=8;
    auto* target=trap->unit(U::Terran_Marine,0,{176,128});
    auto& script=trap->global.iscript.scripts[0];script.id=0;script.animation_pc.resize(32,1);
    constexpr int tag=0x808091;
    trap->global.iscript.program_data={0,iscript_opcodes::opc_sigorder+tag,1,iscript_opcodes::opc_wait+tag,1,iscript_opcodes::opc_goto+tag,3};
    u->sprite->main_image->iscript_state.current_script=&script;
    t.set_unit_order(u,t.get_order_type(Orders::HiddenGun));
    t.execute_main_order(u);
    require(u->order_type->id==Orders::RevealTrap&&u->order_target.unit==target,"Hidden trap never acquires nearby enemy");
    for(int frame=0;frame<30&&u->order_type->id==Orders::RevealTrap;frame++)t.execute_main_order(u);
    if(u->order_type->id!=Orders::TowerAttack||!t.u_ready_to_attack(u))std::cerr<<"TRAP_STATE type="<<int(type)<<" order="<<int(u->order_type->id)<<" state="<<int(u->order_state)<<" signal="<<int(u->order_signal)<<" animation="<<u->sprite->main_image->iscript_state.animation<<" flags="<<u->status_flags<<'\n';
    require(u->order_type->id==Orders::TowerAttack&&t.u_ready_to_attack(u),"Trap reveal never enters armed attack order");
    t.execute_main_order(u);
    require(u->ground_weapon_cooldown>0&&u->sprite->main_image->iscript_state.animation==iscript_anims::GndAttkInit,"Trap did not begin firing animation/cooldown");
    require(!t.u_cloaked(u)&&!t.u_requires_detector(u),"Attacking trap stayed hidden");
  }
  std::cout<<"PASS six traps acquire enemies, animate reveal and begin firing\n";
  {
    auto lurker=std::make_unique<Fixture>();auto& l=*lurker->ui;
    auto* u=lurker->unit(U::Zerg_Lurker,1,{128,128},unit_type_t::flag_can_burrow);
    lurker->st.player_units[1].push_front(*u);
    auto* target=lurker->unit(U::Terran_Marine,0,{200,128});
    lurker->st.alliances[1][0]=1;l.ai_lurkers(1);
    require(u->order_type->id==Orders::Nothing,"Lurker burrows in response to an ally");
    lurker->st.alliances[1][0]=0;l.ai_lurkers(1);
    require(u->order_type->id==Orders::Burrowing,"Computer Lurker never burrows near ground enemy");
    (void)target;
  }
  std::cout<<"PASS Lurker combat burrow respects alliances\n";
  {
    auto sound=std::make_unique<Fixture>();auto& s=*sound->ui;
    auto* u=sound->unit(U::Terran_Marine,0,{900,900});
    s.play_unit_ack(u,10,10);
    require(s.sounds.size()==1&&s.sounds[0].position==xy()&&s.sounds[0].source==u,"Offscreen acknowledgment remains positional");
    auto* critter=sound->unit(U::Critter_Rhynadon,11,{128,128});
    auto& type=sound->game.unit_types.vec[size_t(U::Critter_Rhynadon)];type.first_what_sound=type.last_what_sound=20;type.group_flags=0;
    sound->select(critter);s.on_selection(false);
    require(s.sounds.size()==2&&s.sounds.back().id==20,"Neutral critter click is silent");
    require(std::string(s.unit_details()).find("\narmor\t")==std::string::npos,"Critter displays placeholder armor");
    s.sound_filenames={"terran/ADVISOR/TAdUpd02.wav","terran/ADVISOR/TAdUpd06.wav","protoss/ADVISOR/PAdUpd02.wav","protoss/ADVISOR/PAdUpd06.wav","zerg/ADVISOR/ZAdUpd02.wav"};
    for(int race=0;race<3;race++){
      s.my_race=race_t(race);
      auto* building=sound->unit(U::Terran_Academy,0,{900,900},unit_type_t::flag_building);
      s.u_set_status_flag(building,unit_t::status_flag_grounded_building);
      auto tech=T::Stim_Packs;auto upgrade=UpgradeTypes::Terran_Infantry_Weapons;
      sound->st.tech_researched[0][tech]=false;sound->st.upgrade_levels[0][upgrade]=0;
      sound->game.max_upgrade_levels[0][upgrade]=3;
      building->building.researching_type=&sound->game.tech_types.vec[size_t(tech)];building->building.upgrade_research_time=0;
      s.order_ResearchTech(building);
      building->building.upgrading_type=&sound->game.upgrade_types.vec[size_t(upgrade)];building->building.upgrading_level=1;building->building.upgrade_research_time=0;
      s.order_Upgrade(building);
      require(s.advisor_queue.size()==2,"Actual research/upgrade completion did not queue speech");
      s.poll_advisor();s.poll_advisor();
      int first=race==1?0:race==2?2:4, second=race==1?1:race==2?3:4;
      require(s.sounds[s.sounds.size()-2].id==first&&s.sounds.back().id==second&&s.sounds.back().position==xy(),"Completion speech has wrong race/type or is positional");
      s.order_ResearchTech(building);s.order_Upgrade(building);require(s.advisor_queue.empty(),"Empty/cancelled work announces completion");
    }
  }
  std::cout<<"PASS offscreen acknowledgments, neutral critter and race-specific completion speech\n";
  {
    auto tap=std::make_unique<Fixture>();auto& t=*tap->ui;
    auto* unit=tap->unit(U::Terran_Marine,0,{128,128});
    require(t.touch_selection_near(154,128,22,false)==unit,"Nearby tap misses selectable unit");
    require(t.touch_selection_near(180,128,22,false)==nullptr,"Tap snaps from too far away");
    t.targeting=true;require(!t.touch_selection_near(154,128,22,false),"Nearby selection intercepts explicit target order");t.targeting=false;
    unit->owner=1;unit->sprite->owner=1;unit->sprite->visibility_flags=0;t.fog_player=0;
    require(!t.touch_selection_near(154,128,22,false),"Nearby selection reveals hidden unit");
  }
  std::cout<<"PASS nearby selection radius, fog and explicit order protection\n";
  {
    auto f=std::make_unique<Fixture>();auto& s=*f->ui;
    s.sound_filenames={"zerg/bldg/ZChRdy00.wav"};
    auto* u=f->unit(U::Zerg_Hatchery,0,{900,900},unit_type_t::flag_building);f->st.player_units[0].push_back(*u);
    s.poll_events();require(s.sounds.empty(),"Starting Hatchery announces completion");
    for(auto type:{U::Zerg_Lair,U::Zerg_Hive,U::Zerg_Greater_Spire,U::Zerg_Sunken_Colony,U::Zerg_Spore_Colony}) {
      u->status_flags&=~unit_t::status_flag_completed;s.poll_events();size_t before=s.sounds.size();
      auto& t=f->game.unit_types.vec[size_t(type)];t.flags=unit_type_t::flag_building;t.ready_sound=0;u->unit_type=&t;
      s.poll_events();require(s.sounds.size()==before,"Incomplete morph announces too early");
      u->status_flags|=unit_t::status_flag_completed;s.poll_events();
      require(s.sounds.size()==before+1&&s.sounds.back().id==0&&s.sounds.back().position==xy(),"Building morph completion sound missing or positional");
      s.poll_events();require(s.sounds.size()==before+1,"Morph announces twice");
    }
    u->status_flags&=~unit_t::status_flag_completed;s.poll_events();u->status_flags|=unit_t::status_flag_completed;auto before=s.sounds.size();s.poll_events();
    require(s.sounds.size()==before,"Canceled morph announces completion");
  }
  std::cout<<"PASS five Zerg building morph completion sounds, offscreen, startup and cancellation\n";
  // A synthetic script protects delayed hatch/transmission ordering. It is not Zerg 3.
  f=std::make_unique<Fixture>();auto& scenario=*f->ui;scenario.units_paused=true;
  trigger t{};t.conditions[0].type=22;
  t.actions[0].type=14;t.actions[0].num_n=7;t.actions[0].time_n=5;
  t.actions[1].type=4;t.actions[1].time_n=2100;
  t.actions[2].type=13;t.actions[2].group2_n=3;t.actions[2].num_n=4;
  running_trigger r{};r.t=&t;f->st.running_triggers[0].push_back(r);
  for(int frame=0;frame<40;frame++){scenario.campaign_tick();scenario.process_triggers();}
  require(!scenario.switches[3]&&scenario.countdown_ms>3000,"Wait/countdown skipped early");
  for(int frame=0;frame<30;frame++){scenario.campaign_tick();scenario.process_triggers();}
  require(scenario.switches[3]&&scenario.countdown_ms>0,"Delayed script never resumed");
  std::cout<<"PASS synthetic countdown and delayed trigger resume\n";
  {
    auto data=std::make_unique<Fixture>();auto& ui=*data->ui;
    auto* larva=data->unit(U::Zerg_Larva);data->select(larva);
    auto& ling=data->game.unit_types.vec[size_t(U::Zerg_Zergling)];
    ling.flags=unit_type_t::flag_two_units_in_one_egg;ling.supply_required=fp1::from_raw(1);
    ling.mineral_cost=67;ling.gas_cost=9; // Deliberately customized scenario prices.
    data->game.unit_type_allowed[0][U::Zerg_Zergling]=true;
    data->game.unit_type_allowed[0][U::Zerg_Drone]=true;
    ui.refresh_card();bool found=false;
    std::istringstream rows(std::string(ui.card_text.c_str()));std::string row;
    while(std::getline(rows,row)) {
      std::vector<std::string> fields;std::istringstream columns(row);std::string field;
      while(std::getline(columns,field,'\t'))fields.push_back(field);
      if(fields.size()>=15&&fields[3]==std::to_string(int(U::Zerg_Zergling))) {
        require(fields[4]=="67"&&fields[5]=="9"&&fields[14]=="2","Command card loses actual scenario prices or paired supply");
        require(fields[8].find("two units per egg")!=std::string::npos,"Pair production description absent");found=true;
      }
    }
    require(found,"Serialized Zergling production button absent");
    auto* drone=data->unit(U::Zerg_Drone,0,{64,64},unit_type_t::flag_worker);
    for(auto& command:ui.card)if(command.ut==U::Zerg_Drone)
      require(ui.command_description(command).find("Harvests")!=a_string::npos,"Worker role absent");
    (void)drone;
  }
  std::cout<<"PASS command metadata: scenario costs, pair supply and unit descriptions\n";
  {
    auto dialog=std::make_unique<Fixture>();auto& s=*dialog->ui;
    a_vector<uint8_t> wav;s.sound_file=[&](int)->const a_vector<uint8_t>&{return wav;};
    trigger::action a{};a.type=7;a.sound_index=1;a.time_n=6284;a.group2_n=50;a.num_n=9;
    require(s.on_scenario_action(s.my_player,a)==6234,"Missing transmission recording collapses its editor duration");
    // Actual audio length takes precedence over stale editor metadata.
    wav.resize(4044);memcpy(wav.data()+12,"fmt ",4);wav[16]=16;wav[28]=0xd0;wav[29]=7;
    memcpy(wav.data()+36,"data",4);wav[40]=0xa0;wav[41]=15;
    require(s.on_scenario_action(s.my_player,a)==1950,"Transmission does not use actual recording length");
  }
  std::cout<<"PASS transmission timing with present and omitted recordings\n";
  {
    auto f=std::make_unique<Fixture>();auto& s=*f->ui;
    trigger::action a{};a.type=7;a.sound_index=1;a.time_n=1900;a.group2_n=0;a.num_n=7;
    require(s.on_scenario_action(s.my_player,a)==0,"Zero-wait rescue highlight incorrectly uses stale WAV duration");
    s.st.trigger_waiting[s.my_player]=true;s.st.trigger_wait_timers[s.my_player]=15000;
    state_functions::execute_trigger_struct ets;running_trigger rt{};running_trigger::action ra{};
    require(s.execute_trigger_action(ets,s.my_player,rt,ra,a),"Zero-wait rescue highlight blocks behind unrelated dialogue");
    require(s.st.trigger_wait_timers[s.my_player]==15000,"Zero-wait rescue highlight changes existing voice wait");
  }
  std::cout<<"PASS zero-wait rescue highlights do not delay campaign handover\n";
  {
    auto local=std::make_unique<Fixture>();auto& s=*local->ui;
    local->st.locations.push_back({{{96,96},{224,224}},0});
    auto* guard=local->unit(U::Terran_Marine,1,{128,128});
    auto* outside=local->unit(U::Terran_Marine,2,{500,500});
    local->st.alliances[6][1]=local->st.alliances[6][2]=local->st.alliances[1][6]=local->st.alliances[2][6]=1;
    s.ai_start(6,0x796d6e45u,1);
    require(!local->st.alliances[6][1]&&!local->st.alliances[1][6]&&local->st.alliances[6][2]&&local->st.alliances[2][6],"Enmy targets the human instead of local unit owners");
    s.ai_start(6,0x796c6c41u,1);
    require(local->st.alliances[6][1]&&local->st.alliances[1][6]&&local->st.alliances[6][2],"Ally does not restore the local alliance");
    require(s.ai_error.empty(),"Location alliance scripts need unavailable bytecode");
    (void)guard;(void)outside;
  }
  std::cout<<"PASS Enmy/Ally scripts target the trigger region's unit owners\n";
  {
    auto f=std::make_unique<Fixture>();auto& s=*f->ui;
    f->st.players[1].controller=player_t::controller_computer_game;s.towns[1].active=true;
    auto* base=f->unit(U::Terran_Command_Center,1,{128,128},unit_type_t::flag_building);
    auto* attacker=f->unit(U::Protoss_Zealot,0,{170,128});
    auto* defender=f->unit(U::Terran_Marine,1,{760,128});
    auto* scripted=f->unit(U::Terran_Marine,1,{760,220});
    weapon_type_t weapon{};f->game.unit_types.vec[size_t(U::Terran_Marine)].ground_weapon=&weapon;
    f->st.player_units[1].push_back(*base);f->st.player_units[1].push_back(*defender);f->st.player_units[1].push_back(*scripted);
    s.set_unit_order(scripted,s.get_order_type(Orders::Move),{900,400});
    f->st.alliances[1][0]=1;s.on_scenario_attack(base,attacker);
    require(s.defence_alerts[1].until==0,"Friendly fire mobilizes base defence");
    f->st.alliances[1][0]=0;s.base_defence_enabled=false;s.on_scenario_attack(base,attacker);
    require(s.defence_alerts[1].until==0,"Disabled base defence still creates alert");
    s.base_defence_enabled=true;s.on_scenario_attack(base,attacker);s.base_defence_enabled=false;s.ai_clock=48;s.ai_defend(1);
    require(s.defence_alerts[1].until==0&&defender->order_type->id==Orders::Nothing,"Disabled defence executes queued alert");
    s.base_defence_enabled=true;s.ai_clock=0;s.on_scenario_attack(base,attacker);s.ai_defend(1);
    require(defender->order_type->id==Orders::Nothing,"Base defence skips response delay");
    s.ai_clock=48;s.ai_defend(1);
    require(defender->order_type->id==Orders::AttackMove&&defender->order_target.pos==attacker->sprite->position,"Distant idle defender does not reinforce attacked base");
    require(scripted->order_type->id==Orders::Move&&scripted->order_target.pos==xy(900,400),"Base defence overrides scripted movement");
    f->st.alliances[1][0]=1;s.ai_clock=96;s.ai_defend(1);require(s.defence_alerts[1].until==0,"Ceasefire retains hostile defence alert");
  }
  std::cout<<"PASS base defence delay, reinforcement, allies and scripted movement\n";
  {
    auto f=std::make_unique<Fixture>();auto& s=*f->ui;
    f->st.players[3].controller=player_t::controller_inactive;
    trigger::action add{};add.type=27;add.group_n=3;add.extra_n=7;add.num_n=8;add.group2_n=6;
    s.on_scenario_action(0,add);
    trigger::condition score{};score.type=21;score.group=3;score.extra_n=7;score.num_n=0;score.count_n=6;
    require(s.test_trigger_condition(score,0),"Unused player slot ignores campaign score counter");
    add.type=45;add.extra_n=15;add.group2_n=3;s.on_scenario_action(0,add);
    score.type=15;score.unit_id=15;score.count_n=3;
    require(s.test_trigger_condition(score,0),"Unused slot ignores campaign death counter");
  }
  std::cout<<"PASS unused player slots hold original campaign counters\n";
  {
    auto f=std::make_unique<Fixture>();auto& s=*f->ui;
    s.sound_filenames={"terran/advisor/tAdErr00.wav","terran/advisor/tAdErr01.wav"};s.my_race=race_t::terran;
    auto& type=f->game.unit_types.vec[size_t(U::Terran_Barracks)];type.mineral_cost=150;type.gas_cost=25;
    s.card.push_back({'b',"Barracks",s.C_BUILD,U::Terran_Barracks,true});
    s.run_command('b');require(s.error_text=="Not enough minerals"&&s.sounds.back().id==0&&!s.pending_build,"Unaffordable building has no mineral feedback");
    f->st.current_minerals[0]=150;s.run_command('b');require(s.error_text=="Not enough vespene gas"&&s.sounds.back().id==1&&!s.pending_build,"Unaffordable building has no gas feedback");
    f->st.current_gas[0]=25;s.run_command('b');require(s.pending_build==&type,"Affordable building cannot enter placement");
  }
  std::cout<<"PASS construction buttons report mineral/gas errors before placement\n";
  {
    auto f=std::make_unique<Fixture>();auto& s=*f->ui;
    auto* shuttle=f->unit(U::Protoss_Shuttle,1,{128,128},0);
    auto* enemy=f->unit(U::Terran_Marine,0,{160,128},0);
    f->st.player_units[1].push_back(*shuttle);
    f->st.players[1].controller=player_t::controller_neutral;
    shuttle->order_type=s.get_order_type(Orders::Neutral);shuttle->auto_target_unit=enemy;
    s.order_Neutral(shuttle);
    require(f->st.players[1].controller==player_t::controller_computer_game&&!f->st.alliances[1][0]&&!f->st.alliances[0][1],"Provoked neutral does not become hostile");
    require(shuttle->order_type->id!=Orders::Neutral,"Provoked transport remains in unsupported neutral state");
  }
  std::cout<<"PASS provoked campaign neutral transport enters guard behavior\n";
  std::cout<<"FEEDBACK_RESULT PASS\n";return 0;
}catch(const std::exception& e){g_ui=nullptr;std::cerr<<"FEEDBACK_ERROR "<<e.what()<<'\n';return 1;}}
