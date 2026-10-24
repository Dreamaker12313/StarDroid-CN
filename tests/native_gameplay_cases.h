// Included by native_gameplay.cpp after its common helpers.
static void initial_constraints() {
  check("Missing prerequisite stays disabled, race "+std::to_string(race),[]{
    select(worker());press("Advanced");U t=race==1?U::Terran_Factory:race==2?U::Protoss_Robotics_Facility:U::Zerg_Spire;
    auto c=card(t);require(!c.enabled,"Technology is enabled before its prerequisite");int m=minerals(),g=gas();press(c,false);require(!g_ui->pending_build&&minerals()==m&&gas()==g,"Disabled technology accepts an order");
  });
  check("Blocked placement and empty minerals, race "+std::to_string(race),[]{
    auto* w=worker();U t=race==0?U::Zerg_Creep_Colony:supply_type();xy valid=site(w,t);select(w);press("Build");press(card(t));
    U base=race==1?U::Terran_Command_Center:race==2?U::Protoss_Nexus:U::Zerg_Hatchery;xy blocked=one(base)->position;aim(blocked);auto s=screen(blocked);require(!openbw_placement_valid(s.x,s.y),"Preview accepts overlap with base");int m=minerals(),g=gas();click(blocked);require(g_ui->pending_build&&minerals()==m&&gas()==g,"Blocked placement spends or exits preview");
    openbw_debug_resources(0,0);int seq=g_ui->error_seq;click(valid);require(g_ui->pending_build&&minerals()==0&&gas()==0&&g_ui->error_seq>seq,"Unaffordable placement is not rejected");command(2,27,41,0,0);draw();step();require(!g_ui->pending_build,"Escape leaves building preview active");money();
  });
  if(race!=1)check(race==0?"Creep required for Zerg buildings":"Power required for Protoss buildings",[]{
    auto* w=worker();U needs=race==0?U::Zerg_Spawning_Pool:U::Protoss_Gateway;U free=race==0?U::Zerg_Hatchery:U::Protoss_Pylon;xy far=site(w,free);select(w);press("Build");press(card(needs));aim(far);auto s=screen(far);require(!openbw_placement_valid(s.x,s.y),"Construction allowed without creep/power");g_ui->clear_pending();
  });
}
static void negative_production() {
  check("Construction resource errors race "+std::to_string(race),[&]{
    select(worker());money();press("Build");auto c=card(race==0?U::Zerg_Creep_Colony:supply_type());openbw_debug_resources(0,0);
    int seq=g_ui->error_seq;press(c);require(g_ui->error_seq>seq&&g_ui->error_text=="Not enough minerals"&&!g_ui->pending_build,"Construction shortage is silent");
    require(g_ui->err_sound(g_ui->E_MINERALS)>=0,"Original advisor mineral error missing");money();
  });
  U t=race==1?U::Terran_Firebat:race==2?U::Protoss_Dragoon:U::Zerg_Hydralisk;
  check("Mineral, gas and supply rejection, race "+std::to_string(race),[=]{
    auto* u=one(play_ui::bw_what_builds(t));select(u);auto c=card(t);require(c.enabled,"Fixture technology locked");
    for(int mode=0;mode<3;++mode) {
      money();if(mode==0)openbw_debug_resources(0,50000);if(mode==1)openbw_debug_resources(50000,0);
      auto saved=g_ui->st.supply_available[0][race];if(mode==2)g_ui->st.supply_available[0][race]=g_ui->st.supply_used[0][race];
      int m=minerals(),g=gas(),seq=g_ui->error_seq;press(c);require(minerals()==m&&gas()==g&&u->build_queue.empty()&&g_ui->error_seq>seq,"Unaffordable production accepted (mode "+std::to_string(mode)+")");g_ui->st.supply_available[0][race]=saved;
    }money();
  });
  if(race!=0)check("Five-slot queue and exact cancellation refunds, race "+std::to_string(race),[=]{
    auto* u=one(play_ui::bw_what_builds(t));select(u);money();openbw_test_instant(0);int m=minerals(),g=gas();for(int i=0;i<5;++i)press(card(t));require(u->build_queue.size()==5,"Queue did not reach five slots");auto c=card(t);require(!c.enabled,"Full queue remains enabled");press(c,false);require(u->build_queue.size()==5,"Queue exceeds five slots");
    openbw_cancel(2);step(2);require(u->build_queue.size()==4,"Middle queue cancellation failed");openbw_cancel(99);step(2);require(u->build_queue.size()==4,"Invalid queue slot changes queue");while(!u->build_queue.empty()){openbw_cancel(0);step(2);}require(minerals()==m&&gas()==g,"Queue cancellation refund not exact");openbw_test_instant(1);
  });
  else check("Egg identity, cancellation and full refund",[]{
    auto* larva=one(U::Zerg_Larva);select(larva);auto id=g_ui->get_unit_id(larva);money();int m=minerals(),g=gas();openbw_test_instant(0);press(card(U::Zerg_Hydralisk));wait_for([&]{return larva->unit_type->id==U::Zerg_Egg;},120,"No Egg");select(larva);require(openbw_production_icon()==int(U::Zerg_Hydralisk)&&openbw_production_queue_type(0)==int(U::Zerg_Hydralisk),"Egg target is incorrect");press("Cancel");step(10);require(minerals()==m&&gas()==g,"Egg cancellation refund not 100%");auto* old=g_ui->get_unit(id);require(!old||g_ui->unit_dying(old)||old->unit_type->id==U::Zerg_Larva,"Cancelled egg remains");openbw_test_instant(1);
  });
}
static void removed_refinery() {
  check("Scripted refinery removal restores geyser, race "+std::to_string(race),[]{
    auto* u=one(race==1?U::Terran_Refinery:race==2?U::Protoss_Assimilator:U::Zerg_Extractor);
    auto id=g_ui->get_unit_id(u);g_ui->hide_unit(u);g_ui->kill_unit(u);step(120);
    auto* gas=g_ui->get_unit(id);require(gas&&g_ui->unit_is(gas,U::Resource_Vespene_Geyser)&&gas->owner==11&&!g_ui->us_hidden(gas),"Removed refinery leaves a dead/hidden geyser");
  });
}
static void terran_special() {
  for(U type:{U::Terran_Goliath,U::Terran_Siege_Tank_Tank_Mode})check("Loaded turret unit death: "+name(type),[=]{
    auto* u=one(type);auto id=g_ui->get_unit_id(u);auto* transport=one(U::Terran_Dropship);
    g_ui->unit_load_target(transport,u);require(g_ui->u_loaded(u)&&g_ui->us_hidden(u),"Transport fixture did not hide cargo");
    g_ui->kill_unit(u);step(60);
    auto* old=g_ui->get_unit(id);require(!old||g_ui->unit_dying(old),"Killed cargo remains alive");
    for(auto loaded:transport->loaded_units)require(!(loaded==id),"Destroyed cargo remains in transport");
    produce(type);
  });
  check("Busy building Lift Off is disabled",[]{
    auto* b=one(U::Terran_Barracks);select(b);openbw_test_instant(0);press(card(U::Terran_Marine));auto c=label("Lift Off");require(!c.enabled,"Busy Barracks offers active Lift Off");openbw_cancel(0);step(4);openbw_test_instant(1);
  });
  // Clean up even if the previous assertion failed.
  select(U::Terran_Barracks);while(!one(U::Terran_Barracks)->build_queue.empty()){openbw_cancel(0);step(2);}openbw_test_instant(1);
  check("Lift, blocked landing, free landing and producer lock",[]{
    auto* b=one(U::Terran_Barracks);xy home=b->position;select(b);money();int m=minerals(),g=gas();press("Lift Off");wait_for([&]{return !g_ui->u_grounded_building(b);},240,"Lift off failed");select(b);require(!card(U::Terran_Marine).enabled,"Flying Barracks can produce");press("Land");xy blocked=one(U::Terran_Supply_Depot)->position;aim(blocked);auto s=screen(blocked);require(!openbw_placement_valid(s.x,s.y),"Landing preview accepts occupied terrain");click(home);wait_for([&]{return g_ui->u_grounded_building(b);},600,"Landing failed");require(minerals()==m&&gas()==g,"Landing costs resources");
  });
  check("Addon preview rejects blocked parent/addon footprints",[]{
    auto* parent=build(U::Terran_Factory);select(parent);press(card(U::Terran_Machine_Shop));xy blocked=one(U::Terran_Supply_Depot)->position;aim(blocked);auto s=screen(blocked);require(!openbw_placement_valid(s.x,s.y),"Addon preview accepts occupied footprint");g_ui->clear_pending();
  });
  check("Tank requires attached Machine Shop, not another Factory's addon",[]{
    unit_t* parent=nullptr;for(auto* b:units(U::Terran_Factory))if(!g_ui->unit_addon(b)){parent=b;break;}require(parent,"No bare Factory");select(parent);require(!card(U::Terran_Siege_Tank_Tank_Mode).enabled,"Remote addon unlocks Tank");
  });
  check("Siege Tank transforms both directions",[]{
    auto* t=one(U::Terran_Siege_Tank_Tank_Mode);select(t);press("Siege Mode");wait_for([&]{return t->unit_type->id==U::Terran_Siege_Tank_Siege_Mode;},240,"Siege failed");select(t);press("Tank Mode");wait_for([&]{return t->unit_type->id==U::Terran_Siege_Tank_Tank_Mode;},240,"Unsiege failed");
  });
  check("SCV can halt and resume construction",[]{
    auto* w=worker();auto t=U::Terran_Supply_Depot;xy p=site(w,t);xy near=p-xy(96,0);auto free=g_ui->find_unit_placement(w,near,{near-xy(96,96),near+xy(96,96)},true,false);require(free.first,"No accessible SCV fixture position");openbw_debug_warp(g_ui->get_unit_id(w).raw_value,free.second.x,free.second.y);select(w);press("Build");openbw_test_instant(0);press(card(t));click(p);wait_for([&]{return w->order_type->id==Orders::ConstructingBuilding;},4000,"SCV never constructs");auto* b=w->current_build_unit?w->current_build_unit:w->order_target.unit;require(b&&!g_ui->u_completed(b),"Missing unfinished shell");select(w);press("Halt Construction");step(48);int remaining=b->remaining_build_time;step(48);require(b->remaining_build_time==remaining,"Halted construction keeps progressing");select(w);aim(b->position);auto s=screen(b->position);command(1,1,3,s.x,s.y);command(1,0,3,s.x,s.y);draw();step(8);openbw_test_instant(1);wait_for([&]{return g_ui->u_completed(b);},600,"SCV did not resume construction");
  });
}
static void protoss_special() {
  for(U hero:{U::Hero_Gantrithor,U::Hero_Warbringer}) check("Hero fighter lifetime "+name(hero),[&]{
    unit_t* u=nullptr;for(int y=128;y<int(g_ui->game_st.map_height)-128&&!u;y+=128)for(int x=128;x<int(g_ui->game_st.map_width)-128&&!u;x+=128)u=g_ui->trigger_create_unit(g_ui->get_unit_type(hero),{x,y},0);require(u,"Hero fixture creation failed");
    money();select(u);const char* button=hero==U::Hero_Gantrithor?"Build Interceptor":"Build Scarab";
    for(int i=0;i<3;++i){press(button);wait_for([&]{return u->carrier.inside_count==i+1;},700,"Hero ammo production failed");}
    auto* released=g_ui->release_fighter(u);require(released&&u->carrier.outside_count==1,"Hero fighter did not launch");
    g_ui->kill_unit(released);step(60);
    require(u->carrier.outside_count==0&&u->carrier.outside_units.empty(),"Destroyed hero fighter remains in hangar list");
    auto* inside=&u->carrier.inside_units.front();g_ui->kill_unit(inside);step(60);
    require(u->carrier.inside_count==1,"Destroyed inside fighter remains counted");
    select(u);press(button);wait_for([&]{return u->carrier.inside_count==2;},700,"Replacement hero fighter failed");
    g_ui->kill_unit(u);step(60);
  });
  for(U t:{U::Protoss_Carrier,U::Protoss_Reaver})check("Ammunition cost and capacity: "+name(t),[=]{
    auto* u=one(t);select(u);U ammo=t==U::Protoss_Carrier?U::Protoss_Interceptor:U::Protoss_Scarab;int max=t==U::Protoss_Carrier?8:10;for(int i=0;i<max;++i){int m=minerals();press(t==U::Protoss_Carrier?"Build Interceptor":"Build Scarab");wait_for([&]{return int(u->carrier.inside_count)==i+1;},600,"Ammunition did not finish");require(m-minerals()==g_ui->get_unit_type(ammo)->mineral_cost,"Wrong ammunition cost");}int m=minerals();press(t==U::Protoss_Carrier?"Build Interceptor":"Build Scarab");step(60);require(int(u->carrier.inside_count)==max&&minerals()==m,"Ammunition exceeds capacity or charges when full");
  });
  for(U t:{U::Protoss_High_Templar,U::Protoss_Dark_Templar})check("Merge "+name(t),[=]{
    auto* second=produce(t);auto first=units(t);require(first.size()>=2,"Two Templar needed");unit_t* other=nullptr;for(auto* x:first)if(x!=second){other=x;break;}select(other);openbw_debug_select(g_ui->get_unit_id(second).raw_value,1);draw();U out=t==U::Protoss_High_Templar?U::Protoss_Archon:U::Protoss_Dark_Archon;press(t==U::Protoss_High_Templar?"Merge Archon":"Dark Archon");wait_for([&]{return !units(out).empty();},1500,"Templar merge failed");
  });
  check("Power loss blocks production and restoration enables it",[]{
    auto* b=one(U::Protoss_Gateway);xy restore(-1,-1);for(auto* p:units(U::Protoss_Pylon))if(g_ui->is_in_psionic_matrix_range(b->position-p->position))restore=p->position;require(restore.x>=0,"Missing original power source");for(auto* p:units(U::Protoss_Pylon))openbw_debug_kill(g_ui->get_unit_id(p).raw_value);step(120);select(b);require(!card(U::Protoss_Zealot).enabled,"Unpowered Gateway can train");build(U::Protoss_Pylon,false,restore);step(120);select(b);require(card(U::Protoss_Zealot).enabled,"Restored power does not enable Gateway");
  });
}
static void zerg_special() {
  check("Infest damaged Command Center and produce Infested Terran",[]{
    auto* queen=one(U::Zerg_Queen);auto* drone=worker();xy p=site(drone,U::Terran_Command_Center);
    // A damaged enemy base is the prerequisite fixture; infestation and training
    // still use the same commands a player issues.
    auto* cc=g_ui->create_initial_unit(g_ui->get_unit_type(U::Terran_Command_Center),p,1);
    require(cc,"Enemy Command Center fixture failed");g_ui->set_unit_hp(cc,fp8::integer(400));
    openbw_debug_warp(g_ui->get_unit_id(queen).raw_value,p.x-160,p.y);select(queen);press("Infest CC");click(p);
    wait_for([&]{return cc->owner==0&&cc->unit_type->id==U::Zerg_Infested_Command_Center&&g_ui->u_completed(cc);},1800,"Infestation failed");
    produce(U::Zerg_Infested_Terran,cc);
  });
  check("Nydus exit placement, free cost and bidirectional link",[]{
    auto* n=one(U::Zerg_Nydus_Canal);select(n);money();int m=minerals(),g=gas();press("Build Nydus Exit");xy p=site(n,U::Zerg_Nydus_Canal);click(p);wait_for([&]{return n->building.nydus.exit&&g_ui->u_completed(n->building.nydus.exit);},1000,"Nydus exit not built");require(n->building.nydus.exit->building.nydus.exit==n,"Nydus endpoints not linked");require(minerals()==m&&gas()==g,"Nydus exit charged resources");select(n);for(auto c:g_ui->card)require(std::string(c.label)!="Build Nydus Exit","Linked Nydus offers another exit");
  });
  check("Building morph cancellation retains building and 75% refund",[]{
    auto* h=one(U::Zerg_Hatchery);auto id=g_ui->get_unit_id(h);select(h);money();int m=minerals(),g=gas();openbw_test_instant(0);press(card(U::Zerg_Lair));step(8);select(h);press("Cancel");step(8);require(h==g_ui->get_unit(id)&&h->unit_type->id==U::Zerg_Hatchery&&g_ui->u_completed(h),"Cancelled Lair did not return completed Hatchery");auto* t=g_ui->get_unit_type(U::Zerg_Lair);require(minerals()==m-t->mineral_cost+t->mineral_cost*3/4&&gas()==g-t->gas_cost+t->gas_cost*3/4,"Lair refund wrong");openbw_test_instant(1);
  });
  check("Lurker burrows and unburrows",[]{auto* u=one(U::Zerg_Lurker);select(u);press("Burrow");wait_for([&]{return g_ui->u_burrowed(u);},240,"Burrow failed");step(48);select(u);press("Unburrow");wait_for([&]{return !g_ui->u_burrowed(u);},240,"Unburrow failed");});
}
