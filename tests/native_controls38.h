#include <sstream>
// Regression checks for mixed-race orders and touch/cargo controls.
static void touch_at(xy p) {aim(p);auto s=screen(p);command(4,s.x,s.y,0,0);draw();step();}
static unit_t* controls_worker(U type) {
    xy p=one(worker_type())->position+xy(96,96);
    unit_t* u=nullptr;
    for(int y=4;y<60&&!u;y++)for(int x=4;x<60&&!u;x++)u=g_ui->trigger_create_unit(g_ui->get_unit_type(type),xy(x*32,y*32),1);
    require(u,"Captured worker fixture failed");
    if(race==2) {
        auto* caster=one(U::Protoss_Dark_Archon);g_ui->set_unit_energy(caster,g_ui->unit_max_energy(caster));
        openbw_debug_warp(g_ui->get_unit_id(caster).raw_value,u->position.x+64,u->position.y);select(caster);press("Mind Control");click(u->position);
        wait_for([&]{return u->owner==0;},1000,"Mind Control did not capture worker");
    } else require(g_ui->trigger_give_unit_to(u,0),"Worker handover failed");
    return u;
}
static void controls38(int starting_race) {
    for(auto pair:{std::make_pair(U::Terran_SCV,U::Terran_Supply_Depot),std::make_pair(U::Protoss_Probe,U::Protoss_Pylon),std::make_pair(U::Zerg_Drone,U::Zerg_Hatchery)}) {
        if(pair.first==worker_type())continue;
        check("Foreign worker constructs as starting race "+std::to_string(starting_race)+": "+name(pair.first),[&]{
            auto* w=controls_worker(pair.first);money();select(w);press("Build");press(card(pair.second));xy p=site(w,pair.second);auto* type=g_ui->get_unit_type(pair.second);
            xy near=pair.first==U::Zerg_Drone?p-xy(0,7):p-xy(type->placement_size.x/2+32,0);
            openbw_debug_warp(g_ui->get_unit_id(w).raw_value,near.x,near.y);click(p);
            wait_for([&]{return !units(pair.second).empty();},5000,"Foreign-race construction never completes");
            std::istringstream row(g_ui->resources());std::vector<int> values;int v;while(row>>v)values.push_back(v);
            int wr=int(g_ui->unit_race(g_ui->get_unit_type(pair.first)));
            require(values.size()==11&&(values[4]&(1<<wr))&&(values[4]&(1<<starting_race)),"Mixed supply mask omits an owned race");
            require(values[5+wr*2]==g_ui->st.supply_used[0][wr].raw_value/2&&values[6+wr*2]>0,"Foreign supply values wrong");
        });
    }
    if(starting_race==1)check("Default ground tap disabled; explicit Move and opt-in ground orders work",[]{
        auto* u=one(U::Terran_Marine);select(u);command(22,0,1,0,0);xy before=u->position,target=before+xy(128,80);
        touch_at(target);step(24);require(u->position==before,"Disabled ground tap moved unit");
        select(u);press("Move");touch_at(target);wait_for([&]{return u->position!=before;},120,"Explicit Move was blocked");
        press("Stop");step(6);before=u->position;command(22,0,0,1,0);touch_at(before+xy(-100,0));wait_for([&]{return u->position!=before;},120,"Opt-in ground tap ignored");
        command(22,28,1,0,0);
    });
    U transport=starting_race==1?U::Terran_Dropship:starting_race==2?U::Protoss_Shuttle:U::Zerg_Overlord;
    check("Tap to load and dedicated Load/Unload: "+name(transport),[&]{
        auto* ship=one(transport);auto* u=one(starting_race==1?U::Terran_Marine:starting_race==2?U::Protoss_Zealot:U::Zerg_Zergling);
        openbw_debug_warp(g_ui->get_unit_id(ship).raw_value,u->position.x+64,u->position.y);
        select(u);touch_at(ship->position);wait_for([&]{return g_ui->u_loaded(u);},800,"Tapping transport did not load selected unit");
        select(ship);require(label("Load").act==play_ui::C_LOAD&&label("Unload").act==play_ui::C_UNLOADALL,"Dedicated cargo commands missing");
        require(std::string(g_ui->cargo_status()).find(std::to_string(g_ui->get_unit_id(u).raw_value)+"\t")!=std::string::npos,"Cargo status omits passenger");
        for(auto c:g_ui->card)require(c.act!=play_ui::C_UNLOAD,"Passenger icon consumes command slot");
        press("Unload");require(g_ui->targeting,"Flying transport unload did not request location");click(ship->position);
        wait_for([&]{return !g_ui->u_loaded(u);},800,"Unload at selected location failed");
        select(ship);press("Load");click(u->position);wait_for([&]{return g_ui->u_loaded(u);},800,"Dedicated Load command failed");
        step(24);command(24,g_ui->get_unit_id(u).raw_value,0,0,0);step(240);require(!g_ui->u_loaded(u),"Individual cargo button did not unload");
    });
    if(starting_race==1)check("Bunker tap entry and immediate Unload",[]{
        // Use an open pad; the completed tech-tree fixture deliberately packs
        // buildings tightly and can wall off the original Bunker.
        auto* b=g_ui->create_initial_unit(g_ui->get_unit_type(U::Terran_Bunker),site(one(U::Terran_SCV),U::Terran_Bunker),0);
        require(b,"Bunker load fixture creation failed");auto* u=one(U::Terran_Marine);openbw_debug_warp(g_ui->get_unit_id(u).raw_value,b->position.x+80,b->position.y);
        select(u);touch_at(b->position);wait_for([&]{return g_ui->u_loaded(u);},800,"Bunker tap entry failed");select(b);press("Unload");step(24);
        require(!g_ui->u_loaded(u)&&!g_ui->targeting,"Bunker should unload immediately");select(b);press("Load");click(u->position);wait_for([&]{return g_ui->u_loaded(u);},800,"Bunker Load command failed");
        select(b);press("Unload");step(24);
    });
    if(starting_race==0)check("Linked Nydus tap entry, Load and View Exit",[]{
        auto* n=one(U::Zerg_Nydus_Canal);auto* exit=n->building.nydus.exit;require(exit,"Nydus fixture missing exit");auto* u=one(U::Zerg_Zergling);
        auto approach=[&]{openbw_debug_warp(g_ui->get_unit_id(u).raw_value,n->position.x+72,n->position.y);};
        approach();select(u);touch_at(n->position);wait_for([&]{return g_ui->units_distance(u,exit)<64;},800,"Nydus tap entry failed");
        approach();select(n);press("Load");click(u->position);wait_for([&]{return g_ui->units_distance(u,exit)<64;},800,"Nydus Load command failed");
        select(n);press("View Exit");require(g_ui->screen_pos.x<=exit->position.x&&g_ui->screen_pos.y<=exit->position.y,"View Exit camera failed");
    });
}
