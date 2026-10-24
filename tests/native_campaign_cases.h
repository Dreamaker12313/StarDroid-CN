// Objective-branch checks use explicitly documented diagnostic actions. They
// preserve original triggers and are not full combat playthroughs.
#include <sstream>
using U=bwgame::UnitTypes;
static std::vector<bwgame::unit_t*> matching(U type,int owner=-1) {
    std::vector<bwgame::unit_t*> out;
    for(auto& list:g_ui->st.player_units)for(auto* u:ptr(list))
        if(g_ui->unit_is(u,type)&&!g_ui->unit_dying(u)&&(owner<0||u->owner==owner))out.push_back(u);
    return out;
}
static void preserve_player(int frames) {
    for(int i=0;i<frames&&!g_ui->outcome;++i) {
        if(i%24==0)for(auto* u:ptr(g_ui->st.player_units[g_ui->my_player]))if(!g_ui->unit_dying(u))g_ui->set_unit_hp(u,u->unit_type->hitpoints);
        advance(1);
    }
}
static bool next_scenario(const char* filename) {
    std::istringstream rows(g_campaign->events.c_str());std::string row;
    while(std::getline(rows,row)){std::istringstream fields(row);int type,index;fields>>type>>index;
        if(type==41&&index>0&&size_t(index)<=g_ui->game_st.map_strings.size()) {
            std::string path=g_ui->game_st.map_strings[index-1].c_str();
            std::transform(path.begin(),path.end(),path.begin(),[](unsigned char c){return std::tolower(c);});
            if(path.find(filename)!=std::string::npos)return true;
        }}return false;
}
static void campaign_case(const std::string& name) {
    if(name=="chrysalis") {
        require(!matching(U::Terran_Command_Center,2).empty(),"Raynor's Command Center was lost during the opening");
        require(g_ui->st.alliances[1][2]&&g_ui->st.alliances[2][1],"Militia and Raynor are hostile");
        require(!matching(U::Special_Mature_Chrysalis,g_ui->my_player).empty(),"Chrysalis absent before hatching");
        g_campaign->countdown_ms=0; // Exercise the original countdown ending now.
        preserve_player(3000);
        require(g_ui->outcome==0&&matching(U::Hero_Infested_Kerrigan,g_ui->my_player).size()==1,"Kerrigan hatch sequence fails or defeats the player");
        require(matching(U::Special_Mature_Chrysalis,g_ui->my_player).empty(),"Chrysalis remains after hatching");
        require(!g_campaign->units_paused,"Hatching leaves the mission paused");
        for(auto* u:matching(U::Hero_Infested_Kerrigan,g_ui->my_player))g_ui->kill_unit(u);
        advance(400);require(g_ui->outcome==2,"Kerrigan death does not trigger defeat");
    } else if(name=="true-colors") {
        auto hatch=matching(U::Zerg_Hatchery,g_ui->my_player);auto larvae=matching(U::Zerg_Larva,g_ui->my_player);
        std::cout<<"TRUE_COLORS hatcheries="<<hatch.size()<<" larvae="<<larvae.size()<<" burrowedLurkers="<<burrowed_lurkers.size()<<"\n";
        require(burrowed_lurkers.size()==3,"All three ambush Lurkers did not burrow");
        require(hatch.size()==2&&larvae.size()>=6,"Handed-over Hatcheries do not produce their larvae");
        // Remove larvae, then check both hatcheries independently produce replacements.
        for(auto* u:larvae)g_ui->kill_unit(u);preserve_player(1000);
        require(matching(U::Zerg_Larva,g_ui->my_player).size()>=2,"Larva generation stops after the initial handover");
        require(g_ui->outcome==0,"True Colors ends during its handover");
    } else if(name=="physics-lab"||name=="nuclear-silo") {
        U type=name=="physics-lab"?U::Terran_Physics_Lab:U::Terran_Nuclear_Silo;int destroyed=0;
        for(auto* u:matching(type))if(u->owner!=g_ui->my_player){g_ui->kill_unit(u);++destroyed;}
        require(destroyed>0,"Original branch target absent");preserve_player(6000);
        require(g_ui->outcome==1,"Assault on Korhal branch does not win");
        require(next_scenario(name=="physics-lab"?"terran05a.scx":"terran05b.scx"),"Assault on Korhal chooses the wrong next mission");
    } else if(name=="kelmorian") {
        g_ui->st.current_minerals[g_ui->my_player]=10000;preserve_player(6000);
        require(g_ui->outcome==1&&next_scenario("zerg04a.scx"),"Kel-Morian mineral objective or next branch fails");
    } else if(name=="khalis") {
        auto probes=matching(U::Protoss_Probe,g_ui->my_player);require(!probes.empty(),"Khalis test has no Probe");
        openbw_debug_warp(g_ui->get_unit_id(probes.front()).raw_value,3728,3455);preserve_player(6000);
        // This original map uses the campaign catalog's next entry, not a
        // Set Next Scenario action (unlike the branching Korhal missions).
        require(g_ui->outcome==1,"Khalis pickup does not reach victory");
    } else if(name=="duran") {
        require(matching(U::Hero_Samir_Duran,g_ui->my_player).size()==1,"Duran does not enter the mission");
        require(g_ui->outcome==0,"Patriot's Blood ends during Duran's entrance");
    } else if(name=="finale") {
        auto cc=matching(U::Terran_Command_Center,g_ui->my_player);
        require(cc.size()==1&&cc.front()->sprite->position==bwgame::xy(928,656),"Opening Command Center absent or misplaced");
        require(matching(U::Terran_Supply_Depot,g_ui->my_player).size()==3,"Opening supply depots absent");
        // Verify the original SCVs can complete a real harvest cycle at this depot.
        bwgame::action_state actions;bwgame::action_functions af(g_ui->st,actions);
        auto workers=matching(U::Terran_SCV,g_ui->my_player);require(workers.size()==4,"Opening SCVs absent");
        bwgame::unit_t* mineral=nullptr;
        for(auto* u:ptr(g_ui->st.player_units[11]))if(g_ui->unit_is_mineral_field(u)&&(!mineral||g_ui->units_distance(u,cc.front())<g_ui->units_distance(mineral,cc.front())))mineral=u;
        require(mineral,"No Terran minerals");int gathered=g_ui->st.total_minerals_gathered[g_ui->my_player];
        for(auto* u:workers){af.action_select(g_ui->my_player,u);af.action_default_order(g_ui->my_player,mineral->sprite->position,mineral,nullptr,false);}
        advance(1200);require(g_ui->st.total_minerals_gathered[g_ui->my_player]>gathered,"SCVs cannot return cargo to Command Center");
        // Mixed-race UI placement must issue a Terran build order even though
        // this campaign player starts as Protoss. Use the original acquired SCV.
        g_ui->st.current_minerals[g_ui->my_player]=10000;
        auto* builder=workers.front();auto* depot=g_ui->get_unit_type(U::Terran_Supply_Depot);
        bwgame::xy site;bool found=false;
        for(int y=10;y<35&&!found;y++)for(int x=10;x<45&&!found;x++) {
            bwgame::xy p(x*32+depot->placement_size.x/2,y*32+depot->placement_size.y/2);
            if(g_ui->can_place_building(builder,g_ui->my_player,depot,p,true,true)){site=p;found=true;}
        }
        require(found,"Finale has no SCV construction site");
        openbw_debug_warp(g_ui->get_unit_id(builder).raw_value,site.x-96,site.y);
        openbw_debug_select(g_ui->get_unit_id(builder).raw_value,0);g_ui->menu=1;g_ui->refresh_card();
        bool offered=false;for(auto c:g_ui->card)if(c.ut==U::Terran_Supply_Depot&&c.enabled){g_ui->run_command(c.key);offered=true;break;}
        require(offered,"Finale SCV has no enabled Supply Depot command");
        g_ui->center_on(site);auto pixel=site-g_ui->screen_pos;g_ui->place_pending(pixel.x,pixel.y);openbw_test_instant(1);
        preserve_player(600);openbw_test_instant(0);
        require(matching(U::Terran_Supply_Depot,g_ui->my_player).size()==4,"Finale SCV cannot build Supply Depot");
        std::istringstream supply(g_ui->resources());std::vector<int> values;int value;while(supply>>value)values.push_back(value);
        require(values.size()==11&&(values[4]&6)==6&&values[8]>=34,"Finale does not expose independent Terran/Protoss supply");
        auto ships=matching(U::Hero_Gantrithor,g_ui->my_player);require(ships.size()==1,"Gantrithor absent");auto* ship=ships.front();
        g_ui->st.current_minerals[g_ui->my_player]=10000;
        auto replenish=[&](){af.action_select(g_ui->my_player,ship);af.action_train_fighter(g_ui->my_player);};
        for(int i=0;i<6000&&g_ui->unit_interceptor_count(ship)<8;++i){if(i%24==0)replenish();advance(1);}
        require(g_ui->unit_interceptor_count(ship)==8,"Gantrithor cannot build eight Interceptors");
        auto home=ship->sprite->position;auto spores=matching(U::Zerg_Spore_Colony);require(!spores.empty(),"No original anti-air defence");auto* target=spores.back();
        // Documented assist: keep the hero alive and move it to a defended base.
        // Interceptors take ordinary damage and use the real train/launch/return code.
        g_ui->u_set_status_flag(ship,bwgame::unit_t::status_flag_invincible);
        openbw_debug_warp(g_ui->get_unit_id(ship).raw_value,target->sprite->position.x-160,target->sprite->position.y);
        g_ui->issue_order(ship,false,ship->unit_type->attack_unit,{target->sprite->position,target});
        advance(1600);openbw_render(openbw_frame()*42.);
        require(g_ui->unit_interceptor_count(ship)<8,"Combat fixture did not lose any Interceptors");
        openbw_debug_warp(g_ui->get_unit_id(ship).raw_value,home.x,home.y);af.action_select(g_ui->my_player,ship);af.action_carrier_stop(g_ui->my_player);
        for(int i=0;i<6000&&g_ui->unit_interceptor_count(ship)<8;++i){if(i%24==0)replenish();advance(1);}
        require(g_ui->unit_interceptor_count(ship)==8,"Cannot replace destroyed hero Interceptors");
        auto minds=matching(U::Special_Overmind_With_Shell);require(minds.size()==1,"Original Overmind missing");auto* mind=minds.front();auto mindId=g_ui->get_unit_id(mind);
        // The sustained anti-air regression above is complete. Clear nearby
        // defenders to isolate the original Overmind combat/victory sequence.
        std::vector<bwgame::unit_t*> guards;
        for(int p=0;p<8;p++)if(!g_ui->st.alliances[g_ui->my_player][p]&&p!=g_ui->my_player)
            for(auto* u:ptr(g_ui->st.player_units[p]))if(u!=mind&&!g_ui->ut_turret(u)&&!g_ui->unit_dying(u)&&g_ui->units_distance(u,mind)<1400)guards.push_back(u);
        for(auto* u:guards)g_ui->kill_unit(u);advance(240);
        g_ui->st.current_minerals[g_ui->my_player]=10000;
        openbw_debug_warp(g_ui->get_unit_id(ship).raw_value,mind->sprite->position.x-160,mind->sprite->position.y);
        for(int i=0;i<24000&&!g_ui->outcome;++i){
            if(i%24==0)replenish();
            if(i%240==0){auto* live=g_ui->get_unit(mindId);if(live&&!g_ui->unit_dying(live))g_ui->issue_order(ship,false,ship->unit_type->attack_unit,{live->sprite->position,live});}
            advance(1);if(i%240==0)openbw_render(openbw_frame()*42.);
        }
        std::cerr<<"FINALE outcome="<<g_ui->outcome<<" fighters="<<g_ui->unit_interceptor_count(ship)<<" order="<<int(ship->order_type->id)<<" ship="<<ship->sprite->position.x<<","<<ship->sprite->position.y;
        if(auto* m=g_ui->get_unit(mindId))std::cerr<<" overmindHP="<<m->hp.integer_part()<<" invincible="<<g_ui->u_invincible(m)<<" pos="<<m->sprite->position.x<<","<<m->sprite->position.y;
        std::cerr<<"\n";
        require(g_ui->outcome==1,"Carrier combat did not reach the original finale victory");
        require(matching(U::Hero_Gantrithor,g_ui->my_player).size()==1,"Tassadar lost during finale");
    } else throw std::runtime_error("Unknown campaign case");
    std::cout<<"PASS CASE "<<name<<"\n";
}
