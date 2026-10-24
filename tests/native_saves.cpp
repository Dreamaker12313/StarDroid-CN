#include "native_fixture.h"
#include <fstream>
#include <execinfo.h>
#include <csignal>
struct SaveFixture : Fixture {
    SaveFixture() {
        st.units_container.grow(false);
        for(auto& block:st.units_container.list)for(auto& u:block){auto index=u.index;memset(&u,0,sizeof(u));new (&u)unit_t();u.index=index;st.units_container.free_list.push_back(u);}
        global.grps.resize(1);global.grps[0]=grp;global.sprite_types.vec.resize(1);global.image_types.vec.resize(1);
        global.flingy_types.vec.resize(1);game.weapon_types.vec.resize(1);game.regions.regions.resize(1);
        st.sprites_on_tile_line.resize(32);st.tiles_mega_tile_index.resize(1024);
        game.triggers.resize(1);game.triggers[0]={};game.triggers[0].conditions[0].type=22;
        ui->rep_map={1,2,3,4};ui->scripts[0]={1,2,3};
    }
    unit_t* add(UnitTypes type,int flags=0,int owner=0) {
        auto* u=unit(type,owner,{128,128},flags);u->sprite->sprite_type=&global.sprite_types.vec[0];
        u->sprite->main_image->grp=&global.grps[0];u->sprite->main_image->image_type=&global.image_types.vec[0];
        st.visible_units.push_back(*u);st.player_units[owner].push_back(*u);st.sprites_on_tile_line[4].push_back(*u->sprite);
        return u;
    }
};
int main(int argc,char** argv) {try {
    signal(SIGSEGV,[](int){void* trace[50];int n=backtrace(trace,50);backtrace_symbols_fd(trace,n,2);_exit(139);});
    using U=UnitTypes;auto f=std::make_unique<SaveFixture>();auto& ui=*f->ui;
    auto* hatch=f->add(U::Zerg_Lair,unit_type_t::flag_building);auto* drone=f->add(U::Zerg_Drone,unit_type_t::flag_worker);
    auto* mineral=f->add(U::Resource_Mineral_Field,unit_type_t::flag_resource,11);
    auto* marine=f->add(U::Terran_Marine,0,1);auto* carrier=f->add(U::Protoss_Carrier);auto* fighter=f->add(U::Protoss_Interceptor);
    carrier->carrier.inside_units.clear();carrier->carrier.outside_units.clear();carrier->carrier.inside_units.push_back(*fighter);carrier->carrier.inside_count=1;fighter->fighter.parent=carrier;
    mineral->building.resource.gather_queue.clear();drone->worker.gather_target=mineral;mineral->building.resource.gather_queue.push_back(*drone);mineral->building.resource.resource_count=1234;
    drone->current_build_unit=hatch;drone->order_target.unit=marine;marine->irradiated_by=drone;marine->irradiate_timer=55;
    hatch->build_queue.push_back(ui.get_unit_type(U::Zerg_Hive));hatch->status_flags&=~unit_t::status_flag_completed;hatch->remaining_build_time=234;
    hatch->building.larva_timer=19;hatch->building.hatchery.larva_spawn_side_values={1,2,3,4};
    auto* order=f->st.orders_container.top();f->st.orders_container.pop();order->order_type=ui.get_order_type(Orders::Move);order->target.unit=marine;order->target.position={400,300};drone->order_queue.push_back(*order);drone->order_queue_count=1;f->st.active_orders_size=1;
    f->st.paths.emplace_back();drone->path=&f->st.paths.back();drone->path->long_path.push_back(&f->game.regions.regions[0]);drone->path->short_path.push_back({7,8});drone->path->destination={300,400};
    auto* bullet=f->st.bullets_container.top();f->st.bullets_container.pop();bullet->bullet_owner_unit=marine;bullet->bullet_target=drone;bullet->weapon_type=&f->game.weapon_types.vec[0];bullet->remaining_time=12;f->st.active_bullets.push_back(*bullet);f->st.active_bullets_size=1;
    f->st.thingies.emplace_back();auto* dot=&f->st.thingies.back();dot->sprite=marine->sprite;f->st.active_thingies.push_back(*dot);
    auto* ghost=f->add(U::Terran_Ghost);ghost->ghost.nuke_dot=dot;
    auto* creep=&f->st.creep_life.free_list.front();f->st.creep_life.free_list.pop_front();--f->st.creep_life.free_list_size;
    creep->tile_pos={3,4};creep->n_neighboring_creep_tiles=2;f->st.creep_life.lists[2].push_back(*creep);f->st.creep_life.lists_size[2]++;f->st.creep_life.table.buckets[(4*7+3)%512].push_back(*creep);
    f->st.current_frame=777;f->st.current_minerals[0]=428;f->st.current_gas[0]=125;f->st.lcg_rand_state=9923921;
    f->st.upgrade_levels[0][UpgradeTypes::Zerg_Carapace]=2;f->st.tech_researched[0][TechTypes::Psionic_Storm]=true;
    f->st.trigger_wait_timers[0]=84;f->st.trigger_waiting[0]=true;running_trigger rt;rt.t=&f->game.triggers[0];rt.current_action_index=1;rt.actions[0].flags=1;f->st.running_triggers[0].push_back(rt);
    ui.switches[4]=true;ui.countdown_ms=10500;ui.deaths[2][7]=3;ui.kills[0][4]=7;ui.towns[1].active=true;ui.towns[1].builds.push_back({U::Terran_Barracks==U::Terran_Barracks?111:0,2,80});
    campaign_ai::thread thread;thread.pc=16;thread.wake=900;thread.calls={24,32};ui.threads.push_back(thread);ui.ai_clock=700;ui.ai_random=717;ui.defence_alerts[1]={ui.get_unit_id(drone),ui.get_unit_id(marine),748,892};
    ui.current_action_state.selection[0].push_back(drone);f->select(drone);ui.groups[2].push_back(ui.get_unit_id(drone));
    ui.ai_actions.selection[1].push_back(marine);ui.fog_snapshots[marine->sprite->index].valid=true;ui.fog_snapshots[marine->sprite->index].images.push_back(*marine->sprite->main_image);
    ui.rep_on=true;uint8_t command[]={26,0};ui.rep_record(0,command,2);ui.announced[ui.get_unit_id(marine).raw_value]=int(U::Terran_Marine);ui.events_seeded=true;
    native_save::HostState host;host.bot_slot=1;host.bot_enabled=true;host.bot_frame=12;host.turns[2]={1,2,3};
    auto saved=native_save::save(ui,&ui,host);native_save::verify(saved);
    if(argc>1&&std::string(argv[1])=="write") {std::ofstream out(argv[2],std::ios::binary);out.write((char*)saved.data(),saved.size());std::cout<<"PASS wrote persistent snapshot "<<saved.size()<<" bytes\n";return 0;}
    if(argc>1&&std::string(argv[1])=="read") {std::ifstream in(argv[2],std::ios::binary);saved.assign(std::istreambuf_iterator<char>(in),{});}
    auto id=ui.get_unit_id(drone);auto* old=drone;f->st.current_minerals[0]=0;ui.countdown_ms=0;ui.switches[4]=false;ui.threads.clear();
    auto restoredHost=native_save::restore(ui,&ui,saved);drone=ui.get_unit(id);
    require(drone&&drone!=old,"Restore reused stale unit addresses");require(drone->current_build_unit->remaining_build_time==234,"In-progress Hive lost");
    require(drone->current_build_unit->building.larva_timer==19,"Larva timer lost");require(drone->order_queue.front().target.unit==drone->order_target.unit,"Order target was not relocated");
    require(drone->worker.gather_target->building.resource.gather_queue.front().index==drone->index,"Worker gather links lost");
    require(drone->path->long_path.front()==&f->game.regions.regions[0]&&drone->path->short_path.front()==xy(7,8),"Paths not restored");
    require(f->st.active_bullets.front().bullet_target==drone,"Projectile target not restored");
    require(ui.current_action_state.selection[0].front()==drone&&ui.ai_actions.selection[1].front()==drone->order_target.unit,"Command selections not restored");
    require(ui.switches[4]&&ui.countdown_ms==10500&&ui.threads[0].calls.back()==32&&ui.ai_clock==700,"Mission/AI state missing");
    require(f->st.current_minerals[0]==428&&f->st.current_frame==777&&f->st.lcg_rand_state==9923921,"Resources/time/RNG lost");
    require(f->st.creep_life.table.find({3,4})&&f->st.creep_life.lists_size[2]==1,"Creep lists lost");
    require(restoredHost.turns[2]==host.turns[2],"Delayed bot commands lost");
    require(ui.defence_alerts[1].wake==748&&ui.defence_alerts[1].source==id,"Pending base defence lost in save");
    auto again=native_save::save(ui,&ui,restoredHost);require(saved==again,"Snapshot did not round trip exactly");
    std::cout<<"PASS persistent graph, pools, orders, cargo links, bullets, creep, fog, replay, AI and mission round trip\n";
    std::vector<uint8_t> legacy;native_save::Codec oldCodec(false,legacy,ui.st);oldCodec.version=1;
    native_save::header(oldCodec,ui,&ui);oldCodec.io(host);oldCodec.world();oldCodec.presentation(ui,&ui);
    uint64_t legacyHash=native_save::hash(legacy);oldCodec.io(legacyHash);
    native_save::restore(ui,&ui,legacy);require(ui.defence_alerts[1].until==0,"Legacy save has phantom defence alert");
    native_save::restore(ui,&ui,saved);drone=ui.get_unit(id);
    std::cout<<"PASS schema 1 compatibility and schema 2 pending defence restore\n";
    // Continue a real pending trigger Wait after restoring, without repeating the action.
    f->game.triggers[0].actions[1].type=13;f->game.triggers[0].actions[1].extra_n=8;f->game.triggers[0].actions[1].num_n=4;
    for(int i=0;i<8;i++)ui.process_triggers();require(!f->st.trigger_waiting[0],"Pending mission wait never resumed");
    std::cout<<"PASS pending mission wait resumes\n";
    for(int mode=0;mode<3;mode++) {auto bad=saved;if(mode==0)bad.resize(bad.size()/2);if(mode==1)bad[52]^=0x80;if(mode==2){bad[8]=9;auto hash=native_save::hash_bytes(bad.data(),bad.size()-8);for(int k=0;k<8;k++)bad[bad.size()-8+k]=uint8_t(hash>>(8*k));}
        int frame=f->st.current_frame;bool rejected=false;try {native_save::restore(ui,&ui,bad);}catch(const std::exception&){rejected=true;}require(rejected&&f->st.current_frame==frame&&ui.get_unit(id)==drone,"Bad save changed live world");}
    std::cout<<"PASS damaged/truncated files rejected before changing live world\n";
    auto other=std::make_unique<SaveFixture>();other->ui->rep_map={99};bool rejected=false;try{native_save::restore(*other->ui,other->ui.get(),saved);}catch(const std::exception&){rejected=true;}require(rejected,"Wrong map accepted");
    std::cout<<"PASS mismatched map/data rejected\n";return 0;
}catch(const std::exception& e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
