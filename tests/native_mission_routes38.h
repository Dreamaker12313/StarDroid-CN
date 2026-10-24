// Four route-specific objective checks. No trigger switches, scores or victory
// state are written. Movement, healing, enemy removal and countdown advances
// are diagnostic assists, explicitly reported; this is not a manual playthrough.
static void route_note(const char* text) {++objective_assists;std::cout<<"ROUTE "<<text<<" frame="<<g_ui->st.current_frame<<"\n";}
static bwgame::xy route_center(int loc) {auto& l=g_ui->st.locations.at(loc-1);return(l.area.from+l.area.to)/2;}
static void route_move(bwgame::unit_t* u,int loc) {auto p=route_center(loc);openbw_debug_warp(g_ui->get_unit_id(u).raw_value,p.x,p.y);std::cout<<"MOVED type="<<int(u->unit_type->id)<<" owner="<<u->owner<<" location="<<loc<<" inside="<<objective_in_location(u,g_ui->st.locations[loc-1])<<" pos="<<u->position.x<<","<<u->position.y<<"\n";route_note("move original objective unit");}
static void route_advance(int frames) {
    for(int n=0;n<frames&&!g_ui->outcome;++n) {
        if(n%24==0)for(auto* u:ptr(g_ui->st.player_units[g_ui->my_player]))if(!g_ui->unit_dying(u)) {
            g_ui->set_unit_hp(u,u->unit_type->hitpoints);
            g_ui->u_set_status_flag(u,bwgame::unit_t::status_flag_invincible);
        }
        advance(1);
    }
}
template<class F>static void route_wait(F ready,int limit,const char* why) {for(int n=0;n<limit&&!ready()&&!g_ui->outcome;n+=24)route_advance(24);if(!ready()) {
 std::cout<<"ROUTE_WAIT_FAILURE "<<why<<" outcome="<<g_ui->outcome<<" paused="<<g_campaign->units_paused<<"\n";
 for(int p=0;p<8;p++){std::cout<<"PLAYER "<<p<<" controller="<<g_ui->st.players[p].controller<<" units="<<std::distance(g_ui->st.player_units[p].begin(),g_ui->st.player_units[p].end())<<" wait="<<g_ui->st.trigger_wait_timers[p]<<" score="<<g_campaign->scenario_score(p,7)<<"\n";
 for(auto& rt:g_ui->st.running_triggers[p])if((rt.flags&1)&&!(rt.flags&8))std::cout<<"RUNNING owner="<<p<<" action="<<rt.current_action_index<<" next="<<int(rt.t->actions[rt.current_action_index].type)<<" flags="<<rt.flags<<"\n";}
 }require(ready(),why);}
static bwgame::unit_t* route_unit(int type,int owner) {
    for(auto* u:ptr(g_ui->st.player_units[owner]))if(int(u->unit_type->id)==type&&!g_ui->unit_dying(u)&&!g_ui->us_hidden(u))return u;
    return nullptr;
}
static bwgame::unit_t* route_scout() {
    for(auto* u:ptr(g_ui->st.player_units[g_ui->my_player]))if(!g_ui->unit_dying(u)&&!g_ui->ut_building(u)&&!g_ui->us_hidden(u)&&!g_ui->u_flying(u)&&int(u->unit_type->id)!=101&&int(u->unit_type->id)!=35&&int(u->unit_type->id)!=36&&int(u->unit_type->id)!=97)return u;
    return nullptr;
}
static bool route_mission38(int code) {
    if(code!=402&&code!=403&&code!=501&&code!=508)return false;
    victory_attempted=true;route_note("protect player while checking original mission sequence");auto& f=*g_campaign;int me=f.my_player;
    if(code==403) {
        route_wait([&]{return route_unit(99,2)||route_unit(99,me);},6000,"Tarsonis: Duran never arrives");
        route_wait([&]{return route_scout()!=nullptr;},6000,"Tarsonis: base never transfers after Duran arrives");
        if(auto* duran=route_unit(99,2)) {
            auto* scout=route_scout();auto pos=duran->sprite->position;
            openbw_debug_warp(f.get_unit_id(scout).raw_value,pos.x+32,pos.y);route_note("approach rescuable Duran");
        }
        route_wait([&]{return route_unit(99,me)!=nullptr;},1200,"Tarsonis: Duran cannot be rescued");
        require(route_unit(7,me),"Tarsonis: starting SCVs lost during handover");
        for(auto& list:f.st.player_units)for(auto* u:ptr(list))if(f.unit_is(u,bwgame::UnitTypes::Zerg_Hive)&&u->owner!=me&&!f.unit_dying(u))f.kill_unit(u);
        route_note("remove the four enemy Hives");route_move(route_unit(99,me),5);
        route_wait([&]{return f.outcome==1;},12000,"Tarsonis: ending does not reach victory");
    } else if(code==501) {
        for(auto& list:f.st.player_units)for(auto* u:ptr(list))if(f.unit_is(u,bwgame::UnitTypes::Zerg_Hive)&&!f.unit_dying(u))
            f.u_set_status_flag(u,bwgame::unit_t::status_flag_invincible);
        route_note("protect the seven objective Hives during route traversal");
        auto* scout=route_scout();require(scout,"Vile Disruption: no original scout");
        int score=0;
        for(int loc:{4,5,7,9,11,15,84}) {
            route_move(scout,loc);++score;
            route_wait([&]{return f.scenario_score(me,7)>=score;},3000,"Vile Disruption: Hive rescue does not increment the original counter");
            route_advance(600);
        }
        require(f.scenario_score(me,7)==7,"Vile Disruption: capture counter is not seven");
        route_move(scout,85);
        route_wait([&]{return f.switches[50];},6000,"Vile Disruption: final wave never starts");
        route_wait([&]{return f.switches[55];},6000,"Vile Disruption: last wave never enables victory");
        for(int n=0;n<6000&&!f.outcome;n+=120) {
            for(int p=0;p<8;p++)if(p!=me&&!f.st.alliances[me][p])for(auto* u:ptr(f.st.player_units[p]))
                if(!f.unit_dying(u)&&!f.ut_building(u)&&!f.ut_turret(u)&&objective_in_location(u,f.st.locations[84]))f.kill_unit(u);
            route_advance(120);
        }
        route_note("remove spawned final-wave attackers in the last Hive area");require(f.outcome==1,"Vile Disruption: defended Hive ending does not win");
    } else if(code==402) {
        const int drops[4]={66,67,85,87};const std::vector<int> beacons[4]={{2,5,6},{28,29,35,49},{70,93,96,8,43},{77,104,107,113,110,116}};
        for(int stage=0;stage<4;stage++) {
            route_wait([&]{return route_unit(15,me)!=nullptr;},12000,"Dylarian: scripted pilots do not arrive");
            route_move(route_unit(15,me),drops[stage]);
            route_wait([&]{return f.switches[4+stage];},3000,"Dylarian: platform does not activate");
            int captured=0;
            for(int loc:beacons[stage]) {
                route_wait([&]{return route_unit(15,me)!=nullptr;},6000,"Dylarian: no remaining scripted pilot");
                route_move(route_unit(15,me),loc);++captured;
                route_wait([&]{return f.scenario_score(stage,7)>=captured;},3000,"Dylarian: ship capture does not count");
                route_advance(120);
            }
            route_wait([&]{return f.switches[8+stage];},3000,"Dylarian: platform completion is blocked");
            route_advance(1800);
        }
        f.countdown_ms=0;route_note("advance remaining enemy fleet countdown");
        route_wait([&]{return f.switches[2];},6000,"Dylarian: final fleet phase does not start");
        for(auto* u:ptr(f.st.player_units[0]))if(f.unit_is(u,bwgame::UnitTypes::Terran_Battlecruiser)&&!f.unit_dying(u))f.kill_unit(u);
        route_note("remove objective enemy fleet");route_wait([&]{return f.outcome==1;},12000,"Dylarian: final fleet defeat does not win");
    } else {
        // Rescue the original Protoss base by approaching its resource depot.
        if(!route_unit(61,me)) {
            for(int p=0;p<8;p++)if(f.st.players[p].controller==bwgame::player_t::controller_rescue_passive)
                for(auto* depot:ptr(f.st.player_units[p]))if(f.ut_resource_depot(depot)&&!f.unit_dying(depot)) {
                    auto* scout=route_scout();require(scout,"Beast: no scout for Protoss rescue");auto pos=depot->sprite->position;
                    openbw_debug_warp(f.get_unit_id(scout).raw_value,pos.x+80,pos.y);route_note("approach original Protoss base");route_advance(240);break;
                }
        }
        // Some base units transfer directly by the map's Bring trigger.
        route_wait([&]{return route_unit(61,me)!=nullptr;},3000,"Beast: original Dark Templars not rescued");
        auto* dt=route_unit(61,me);auto* overmind=route_unit(148,4);require(overmind,"Beast: Overmind absent");
        for(int p=0;p<8;p++)if(p!=me&&!f.st.alliances[me][p])for(auto* u:ptr(f.st.player_units[p]))
            if(u!=overmind&&!f.unit_dying(u)&&f.units_distance(u,overmind)<480)f.kill_unit(u);
        route_note("clear nearby Overmind defenders");route_move(dt,24);
        bwgame::action_state actions;bwgame::action_functions af(f.st,actions);af.action_select(me,dt);
        require(af.action_order(me,f.get_order_type(bwgame::Orders::AttackUnit),overmind->sprite->position,overmind,nullptr,false),"Beast: Dark Templar attack rejected");
        route_note("attack original Overmind with rescued Dark Templar");
        route_wait([&]{return f.switches[1];},16000,"Beast: Dark Templar kill fails to start ending");
        route_wait([&]{return f.outcome==1;},24000,"Beast: scripted Raszagal ending does not finish");
    }
    std::cout<<"ROUTE_VICTORY code="<<code<<" frame="<<f.st.current_frame<<" assists="<<objective_assists<<"\n";return true;
}
