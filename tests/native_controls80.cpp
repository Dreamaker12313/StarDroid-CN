// Production command-stream regressions using locally supplied original archives.
// No copyrighted map/data bytes are included in this harness.
#include "../native/runtime.cpp"
#include <iostream>
#include <functional>
using namespace bwgame;
using U=UnitTypes;
static void require(bool ok,const char* message){if(!ok)throw std::runtime_error(message);}
static void step(int n){for(int i=0;i<n;i++)native_step();}
static void select(unit_t* u){g_ui->current_selection_clear();g_ui->current_selection_add(u);g_ui->on_selection(false);g_ui->refresh_card();}
static const play_ui::cmd_t* cancel(){for(auto& c:g_ui->card)if(c.act==g_ui->C_CANCEL)return &c;return nullptr;}
static std::vector<unit_t*> units(U type,int owner){std::vector<unit_t*> out;for(auto* u:ptr(g_ui->st.player_units[owner]))if(g_ui->unit_is(u,type)&&!g_ui->unit_dying(u))out.push_back(u);return out;}
static unit_t* room(U type,int owner,xy around){
 auto* ut=g_ui->get_unit_type(type);
 for(int r=0;r<20;r++)for(int y=-r;y<=r;y++)for(int x=-r;x<=r;x++){
  xy p=around+xy(x*32,y*32);if(!g_ui->unit_type_can_fit_at(ut,p))continue;
  bool free=true;for(auto* u:g_ui->find_units(g_ui->square_at(p,32)))if(!g_ui->unit_dying(u))free=false;
  if(free)if(auto* u=g_ui->create_initial_unit(ut,p,owner))return u;
 }
 throw std::runtime_error("No clear fixture position");
}
static xy site(unit_t* u,U type){
 auto* t=g_ui->get_unit_type(type);xy best{};int score=1000000;
 for(int y=3;y<int(g_ui->game_st.map_tile_height)-5;y++)for(int x=3;x<int(g_ui->game_st.map_tile_width)-5;x++){
  xy p=xy(x*32,y*32)+t->placement_size/2;int d=g_ui->xy_length(p-u->position);
  if(d>160&&d<score&&g_ui->can_place_building(u,u->owner,t,p,true,true)){best=p;score=d;}
 }
 require(score<1000000,"No legal fixture build site");return best;
}
static void build(unit_t* u,U type,xy p){
 select(u);auto* t=g_ui->get_unit_type(type);xy tile=(p-t->placement_size/2)/32;
 g_ui->sync_selection();g_ui->cmd_build(g_ui->unit_is(u,U::Zerg_Drone)?Orders::DroneStartBuild:g_ui->unit_is(u,U::Terran_SCV)?Orders::PlaceBuilding:Orders::PlaceProtossBuilding,t,tile.x,tile.y);native_step();g_ui->refresh_card();
}
static void setup(const char* archive){
 close_game();open_archive(3,archive);openbw_init_campaign(640,480,102);openbw_set_external_cursor(1);
 auto& game=const_cast<game_state&>(g_ui->game_st);for(auto& list:g_ui->st.running_triggers)list.clear();game.triggers.clear();
 g_campaign->threads.clear();g_campaign->towns={};g_campaign->units_paused=false;g_ui->campaign_control_lock=false;g_ui->competitive=false;
 step(10);g_ui->st.current_minerals[g_ui->my_player]=g_ui->st.current_gas[g_ui->my_player]=10000;
}
static void drone(const char* archive){
 setup(archive);int owner=g_ui->my_player;auto ds=units(U::Zerg_Drone,owner);require(!ds.empty(),"Original Drone absent");auto* d=ds[0];select(d);
 require(!cancel(),"Idle Drone has perpetual Cancel");
 // Reproduce stale queues left by stopped/failed construction in older saves.
 d->build_queue.push_back(g_ui->get_unit_type(U::Zerg_Hatchery));g_ui->refresh_card();require(!cancel(),"Stale saved build intent displays Cancel on idle Drone");d->build_queue.clear();
 xy p=site(d,U::Zerg_Hatchery);int minerals=g_ui->st.current_minerals[owner];size_t hatcheries=units(U::Zerg_Hatchery,owner).size();
 build(d,U::Zerg_Hatchery,p);require(cancel()&&cancel()->unit==32&&cancel()->enabled,"Walking Drone lacks queue-cancel command");
 require(g_ui->run_command(27),"Walking Drone Cancel not handled");native_step();require(d->build_queue.empty()&&d->order_queue.empty(),"Cancel failed to clear pending build/order queue");
 step(250);select(d);require(!cancel()&&units(U::Zerg_Hatchery,owner).size()==hatcheries,"Cancelled walking Drone still built");require(g_ui->st.current_minerals[owner]==minerals,"Unstarted build cancellation fabricated a refund or charged resources");
 std::cout<<"PASS Drone idle/stale queue card and real walking-build Cancel: no future building, no resource change\n";
 // Beginning placement and backing out is UI-only, preserving worker's old order.
 select(d);auto old=d->order_type;g_ui->pending_build=g_ui->get_unit_type(U::Zerg_Hatchery);command(2,27,41,0,0);openbw_render(42);require(!g_ui->pending_build&&d->order_type==old,"Esc did not cancel placement independently");
 std::cout<<"PASS building-placement Escape exits placement without changing worker order\n";
 // Failed placement must remove queue intent instead of leaving a permanent Cancel.
 select(d);d->build_queue.push_back(g_ui->get_unit_type(U::Zerg_Hatchery));g_ui->set_unit_order(d,g_ui->get_order_type(Orders::DroneBuild),d->position+xy(64,0));
 g_ui->order_DroneBuild(d);require(d->build_queue.empty(),"Failed Drone placement retained build queue");step(50);select(d);require(!cancel(),"Failed Drone build retained Cancel");
 std::cout<<"PASS failed Drone placement discards stale construction queue\n";
 p=site(d,U::Zerg_Hatchery);openbw_debug_warp(g_ui->get_unit_id(d).raw_value,p.x,p.y-48);build(d,U::Zerg_Hatchery,p);g_ui->st.current_minerals[owner]=0;
 for(int i=0;i<1600&&g_ui->pending_worker_construction(d);i++)native_step();
 require(g_ui->unit_is(d,U::Zerg_Drone)&&d->build_queue.empty()&&g_ui->st.current_minerals[owner]==0,"Insufficient funds on arrival retained construction intent or changed money");select(d);require(!cancel(),"No-money arrival left permanent Cancel");g_ui->st.current_minerals[owner]=10000;
 std::cout<<"PASS resources spent during walk: failed construction clears intent without charge/refund\n";

 // A real building morph cancels through the morph opcode and returns a Drone.
 p=site(d,U::Zerg_Hatchery);openbw_debug_warp(g_ui->get_unit_id(d).raw_value,p.x,p.y-48);int before=g_ui->st.current_minerals[owner];auto id=g_ui->get_unit_id(d);build(d,U::Zerg_Hatchery,p);
 bool atomic=false;for(int i=0;i<1600&&g_ui->unit_is(d,U::Zerg_Drone);i++){
  select(d);if(cancel()&&cancel()->unit==32&&(g_ui->u_order_not_interruptible(d)||g_ui->u_iscript_nobrk(d))){require(!cancel()->enabled,"Atomic landing offered nonfunctional Cancel");atomic=true;}
  native_step();d=g_ui->get_unit(id);require(d&&!g_ui->unit_dying(d),"Drone disappeared while starting Hatchery");
 }
 require(g_ui->unit_is(d,U::Zerg_Hatchery)&&!g_ui->u_completed(d),"Actual Drone did not begin Hatchery");select(d);require(cancel()&&cancel()->enabled&&(cancel()->unit==24||cancel()->unit==25),"Morphing Hatchery lacks functional Cancel");
 int cost=g_ui->get_unit_type(U::Zerg_Hatchery)->mineral_cost;require(g_ui->st.current_minerals[owner]==before-cost,"Hatchery resource charge wrong");require(g_ui->run_command(27),"Morph Cancel not handled");native_step();step(50);d=g_ui->get_unit(id);require(d&&g_ui->unit_is(d,U::Zerg_Drone)&&g_ui->u_completed(d),"Morph Cancel did not return Drone");require(g_ui->st.current_minerals[owner]==before-cost+cost*3/4,"Morph cancellation refund wrong");select(d);require(!cancel(),"Returned Drone shows Cancel");
 std::cout<<"PASS actual Hatchery morph Cancel returns Drone, refunds 75%, leaves idle card clean; atomic landing seen="<<atomic<<"\n";
 // The same pending-worker cancellation also serves SCVs and Probes.
 for(auto types:{std::make_pair(U::Terran_SCV,U::Terran_Supply_Depot),std::make_pair(U::Protoss_Probe,U::Protoss_Pylon)}){
  auto* w=room(types.first,owner,d->position+xy(160,160));auto pos=site(w,types.second);int money=g_ui->st.current_minerals[owner];build(w,types.second,pos);
  require(cancel()&&cancel()->unit==32,"Other worker lacks pending-build Cancel");g_ui->run_command(27);native_step();require(w->build_queue.empty()&&w->order_queue.empty(),"Other worker Cancel did not clear intent");step(90);require(g_ui->st.current_minerals[owner]==money,"Other worker Cancel altered resources");
 }
 std::cout<<"PASS SCV and Probe pending-build cancellation shares deterministic cleanup\n";
}
static void invincibility(const char* archive){
 setup(archive);int owner=g_ui->my_player;auto* base=units(U::Zerg_Hatchery,owner).front();xy p=base->position;
 auto* own=room(U::Protoss_Dragoon,owner,p+xy(220,120));auto* enemy=room(U::Terran_Marine,1,p+xy(320,220));auto* ally=room(U::Terran_Marine,5,p+xy(450,250));
 g_ui->st.alliances[owner][5]=g_ui->st.alliances[5][owner]=1;
 auto* weapon=g_ui->get_weapon_type(WeaponTypes::Gauss_Rifle);auto hp=own->hp,shield=own->shield_points;own->defensive_matrix_hp=fp8::integer(100);auto matrix=own->defensive_matrix_hp;
 require(!value_query(22,0),"Invincibility enabled by default");command(29,1,0,0,0);require(value_query(22,0)&&!g_ui->rep_on,"Cheat command did not enable immunity or disable replay capture");
 for(int i=0;i<20;i++)g_ui->weapon_deal_damage(weapon,fp8::integer(500),1,own,0_dir,enemy,enemy->owner);
 g_ui->unit_deal_damage(own,fp8::integer(5000),nullptr,~0);require(own->hp==hp&&own->shield_points==shield&&own->defensive_matrix_hp==matrix,"Player health, shields or Matrix damaged with cheat on");require(!g_ui->u_invincible(own),"Cheat rewrote scenario invincibility flags");
 auto bhp=base->hp;g_ui->unit_deal_damage(base,fp8::integer(10000),enemy,enemy->owner);require(base->hp==bhp&&!g_ui->unit_dying(base),"Owned building not protected");
 auto* spawned=room(U::Terran_Marine,owner,p+xy(500,100));auto shp=spawned->hp;g_ui->weapon_deal_damage(weapon,fp8::integer(1000),1,spawned,0_dir,enemy,1);require(spawned->hp==shp,"Newly created owned unit not protected");
 auto ehp=enemy->hp,ahp=ally->hp;g_ui->unit_deal_damage(enemy,fp8::integer(5),own,owner);g_ui->unit_deal_damage(ally,fp8::integer(5),enemy,1);require(enemy->hp<ehp&&ally->hp<ahp,"Cheat protected computer/enemy/allied players");
 std::cout<<"PASS invincibility protects owned/new units and buildings before HP/shield/Matrix loss; AI/allied players remain vulnerable\n";
 auto shields=own->shield_points;own->energy=fp8::integer(150);g_ui->emp_shockwave(own->position,enemy);require(own->shield_points==shields&&own->energy==0_fp8,"EMP did not preserve protected shields while draining energy");
 size_t broodlings=units(U::Zerg_Broodling,1).size();g_ui->spawn_broodlings(spawned,enemy);require(!g_ui->unit_dying(spawned)&&units(U::Zerg_Broodling,1).size()==broodlings,"Spawn Broodlings bypassed invincibility");
 std::cout<<"PASS combat spell edge cases: EMP shields and Broodlings instant kill protected; energy drain retained\n";

 g_ui->set_unit_owner(spawned,1,true);g_ui->unit_deal_damage(spawned,fp8::integer(5),own,owner);require(spawned->hp<shp,"Given-away unit retained protection");
 command(29,0,0,0,0);require(!value_query(22,0),"Cheat did not turn off");g_ui->unit_deal_damage(own,fp8::integer(5),enemy,1);require(own->hp<hp,"Disabling cheat did not restore damage");
 command(29,1,0,0,0);auto doomed=g_ui->get_unit_id(own);g_ui->kill_unit(own);require(g_ui->unit_dying(own),"Cheat blocked scripted Kill action");
 std::cout<<"PASS owner transfer and disabling restore damage; scripted kills remain effective\n";
 auto save=save_game();restore_game(save);require(!value_query(22,0),"Load retained session-only cheat");
 command(29,1,0,0,0);setup(archive);require(!value_query(22,0),"New game retained cheat");net_active=true;auto before=g_ui->st.current_minerals[g_ui->my_player];command(29,1,0,0,0);require(!value_query(22,0)&&g_ui->st.current_minerals[g_ui->my_player]==before,"Multiplayer accepted invincibility cheat");net_active=false;
 std::cout<<"PASS save/load and new match reset cheat; multiplayer command gate rejects it\n";
}
int main(int argc,char** argv){try{
 require(argc==3,"Usage: native-controls80 CORE_DIR STARCRAFT_MPQ");std::string data=argv[1];open_archive(0,data+"/STARDAT.MPQ");open_archive(1,data+"/BROODAT.MPQ");open_archive(2,data+"/patch_rt.mpq");
 drone(argv[2]);invincibility(argv[2]);close_game();return 0;
}catch(const std::exception& e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
