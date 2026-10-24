// Assisted objective traversal, NOT an unassisted campaign playthrough.
// This changes units/resources/time, never switches, trigger code or victory state.
// Every successful outcome must be produced by the original scenario triggers.
static bool objective_in_location(bwgame::unit_t* u,const bwgame::location& loc) {
    return g_ui->is_intersecting(g_ui->unit_sprite_inner_bounding_box(u),loc.area)
        &&g_ui->unit_is_at_elevation_flags(u,loc.elevation_flags);
}
static int objective_assists=0;
static bool victory_attempted=false;
static bool satisfy_objective(const bwgame::trigger::condition&,int,std::set<const bwgame::trigger*>&,int);

static bool attempt_trigger(const bwgame::trigger& t,int owner,std::set<const bwgame::trigger*>& stack,int depth) {
    if(depth>24||stack.count(&t))return false;
    stack.insert(&t);
    for(auto& c:t.conditions) {
        if(!c.type)break;
        if(!g_ui->test_trigger_condition(c,owner)&&satisfy_objective(c,owner,stack,depth+1)) {
            stack.erase(&t);return true;
        }
    }
    stack.erase(&t);return false;
}
static bool satisfy_objective(const bwgame::trigger::condition& c,int owner,std::set<const bwgame::trigger*>& stack,int depth) {
    auto& f=*g_campaign;
    auto note=[&](const char* what){++objective_assists;std::cout<<"ASSIST "<<what<<" condition="<<c.type<<" owner="<<owner<<" group="<<c.group<<" type="<<c.unit_id<<" count="<<c.count_n<<" location="<<c.location<<" frame="<<f.st.current_frame<<"\n";return true;};
    if(c.type==11) { // Resolve switches through their original producer triggers.
        struct Candidate {const bwgame::trigger* t;int owner,unmet;};std::vector<Candidate> options;
        for(int p=0;p<8;p++)if(f.player_slot_active(p))for(auto& rt:f.st.running_triggers[p]) {
            if(rt.flags&8||stack.count(rt.t))continue;
            bool matches=false,defeat=false;int unmet=0;
            for(auto& a:rt.t->actions){if(!a.type)break;if(a.type==2)defeat=true;
                if(a.type==13&&a.group2_n==c.extra_n&&a.num_n==(c.num_n==2?4:5))matches=true;}
            if(!matches||defeat)continue;
            for(auto& pre:rt.t->conditions){if(!pre.type)break;if(!f.test_trigger_condition(pre,p))++unmet;}
            options.push_back({rt.t,p,unmet});
        }
        std::stable_sort(options.begin(),options.end(),[](const Candidate& a,const Candidate& b){return a.unmet<b.unmet;});
        // A satisfied producer may be partway through its dialogue. Let it finish.
        if(!options.empty()&&options.front().unmet==0)return false;
        for(auto x:options)if(attempt_trigger(*x.t,x.owner,stack,depth))return true;
    } else if(c.type==1) {
        if(c.num_n==1||c.num_n==10){f.countdown_ms=c.count_n*1000;return note("advance countdown");}
    } else if(c.type==4) {
        for(int p:f.trigger_players(owner,c.group))if(p<8) {
            if(c.extra_n==0||c.extra_n==2)f.st.current_minerals[p]=c.count_n;
            else f.st.current_gas[p]=c.count_n;
            return note("set objective resources");
        }
    } else if(c.type==2||c.type==3) {
        std::vector<bwgame::unit_t*> units;
        for(int p:f.trigger_players(owner,c.group))for(auto* u:ptr(f.st.player_units[p])) {
            if(!f.unit_dying(u)&&!f.ut_turret(u)&&f.trigger_unit_pred(owner,u,c.group,c.unit_id))units.push_back(u);
        }
        if(c.num_n==1||(c.num_n==10&&c.count_n==0)) {
            int remaining=c.count_n;
            for(auto* u:units) {
                if(c.type==3&&!objective_in_location(u,f.st.locations[c.location-1]))continue;
                if(remaining-->0)continue;
                // Don't erase the player's army or mandatory heroes to manufacture a win.
                if(u->owner==f.my_player)return false;
                f.kill_unit(u);
            }
            if(int(units.size())>c.count_n)return note("remove objective enemies");
        } else if(c.num_n==0||c.num_n==10) {
            if(c.type==3&&c.location>0&&size_t(c.location)<=f.st.locations.size()) {
                auto& loc=f.st.locations[c.location-1];auto pos=(loc.area.from+loc.area.to)/2;
                int count=0;
                for(auto* u:units)if(objective_in_location(u,loc))++count;
                for(auto* u:units)if(count<c.count_n&&!f.ut_building(u)&&!objective_in_location(u,loc)) {
                    openbw_debug_warp(f.get_unit_id(u).raw_value,pos.x,pos.y);++count;
                    return note("move objective unit");
                }
            }
            // Powerups remain neutral while carried. Move an actual worker to
            // pick one up, then move the carrier to the objective location.
            if(c.type==3&&c.unit_id>=215&&c.unit_id<228) {
                auto& loc=f.st.locations[c.location-1];auto dest=(loc.area.from+loc.area.to)/2;
                for(auto* worker:ptr(f.st.player_units[f.my_player]))if(f.ut_worker(worker)&&!f.unit_dying(worker)) {
                    if(worker->worker.powerup&&int(worker->worker.powerup->unit_type->id)==c.unit_id) {
                        openbw_debug_warp(f.get_unit_id(worker).raw_value,dest.x,dest.y);return note("deliver carried objective");
                    }
                    if(!worker->carrying_flags)for(auto& list:f.st.player_units)for(auto* item:ptr(list))
                        if(int(item->unit_type->id)==c.unit_id&&!f.unit_dying(item)&&!f.us_hidden(item)) {
                            openbw_debug_warp(f.get_unit_id(worker).raw_value,item->sprite->position.x,item->sprite->position.y);
                            return note("collect neutral objective");
                        }
                }
            }
            // Missing scripted heroes/transports must arrive through their own
            // original creation trigger; do not synthesize their switch state.
            if(units.empty()&&c.unit_id<228)for(int p=0;p<8;p++)if(f.player_slot_active(p))
                for(auto& rt:f.st.running_triggers[p])if(!(rt.flags&8)&&!stack.count(rt.t)) {
                    bool creates=false;
                    for(auto& a:rt.t->actions)if((a.type==11||a.type==44)&&a.extra_n==c.unit_id)creates=true;
                    if(creates&&attempt_trigger(*rt.t,p,stack,depth))return true;
                }
            // If a rescuable copy exists, approach it instead of creating a hero.
            if(c.unit_id>=0&&c.unit_id<228)for(int p=0;p<8;p++)
                if(f.st.players[p].controller==bwgame::player_t::controller_rescue_passive)
                    for(auto* u:ptr(f.st.player_units[p]))if(int(u->unit_type->id)==c.unit_id&&!f.unit_dying(u))
                        for(auto* scout:ptr(f.st.player_units[f.my_player]))if(!f.unit_dying(scout)&&!f.ut_building(scout)&&!f.us_hidden(scout)) {
                            openbw_debug_warp(f.get_unit_id(scout).raw_value,u->sprite->position.x+32,u->sprite->position.y);
                            return note("approach rescue");
                        }
            if(c.unit_id>=0&&c.unit_id<228&&int(units.size())<c.count_n&&c.count_n<=20) {
                auto* ut=f.get_unit_type(bwgame::UnitTypes(c.unit_id));if(f.ut_hero(ut))return false;
                for(int p:f.trigger_players(owner,c.group))if(p==f.my_player) {
                    auto center=f.game_st.start_locations[p];
                    if(f.unit_is_refinery(ut))for(auto* gas:ptr(f.st.player_units[11]))
                        if(f.unit_is(gas,bwgame::UnitTypes::Resource_Vespene_Geyser)) {
                            if(f.trigger_create_unit(ut,gas->sprite->position,p))return note("create objective refinery");
                        }
                    for(int r=64;r<768;r+=32)for(int dx:{-r,0,r})for(int dy:{-r,0,r}) {
                        auto* u=f.trigger_create_unit(ut,center+bwgame::xy(dx,dy),p);
                        if(u)return note("create objective production unit");
                    }
                }
            }
        }
    }
    return false;
}

#include "native_mission_routes38.h"
static void attempt_mission_objectives(int code) {
    if(route_mission38(code))return;
    victory_attempted=true;auto& f=*g_campaign;
    std::vector<const bwgame::trigger*> victories;
    for(auto& rt:f.st.running_triggers[f.my_player])for(auto& a:rt.t->actions)if(a.type==1){victories.push_back(rt.t);break;}
    for(int frame=0;frame<36000&&!f.outcome;++frame) {
        if(frame%24==0)for(auto* u:ptr(f.st.player_units[f.my_player]))if(!f.unit_dying(u)) {
            f.u_set_status_flag(u,bwgame::unit_t::status_flag_invincible);
            f.set_unit_hp(u,u->unit_type->hitpoints);
            if(u->unit_type->has_shield)f.set_unit_shield_points(u,bwgame::fp8::integer(u->unit_type->shield_points));
        }
        if(frame%120==0&&!f.units_paused) {
            std::set<const bwgame::trigger*> stack;
            for(auto* t:victories)if(attempt_trigger(*t,f.my_player,stack,0))break;
        }
        advance(1);
        if(frame%600==0)openbw_render(openbw_frame()*42.);
    }
    std::cout<<"OBJECTIVE_ATTEMPT outcome="<<f.outcome<<" assists="<<objective_assists<<" frame="<<f.st.current_frame<<"\n";
    if(!f.outcome)for(auto* t:victories)for(auto& c:t->conditions)if(c.type&&!f.test_trigger_condition(c,f.my_player))
        std::cout<<"UNRESOLVED condition="<<c.type<<" group="<<c.group<<" type="<<c.unit_id<<" count="<<c.count_n<<" switch="<<c.extra_n<<" location="<<c.location<<"\n";
}
