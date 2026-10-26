// Original Dylarian trigger regression plus isolated shared AI garrison cases.
#define main abilities79_main
#include "native_abilities79.cpp"
#undef main
static constexpr uint32_t ENBK=0x6b426e45u;
static unit_t* make11(U type,xy pos={1200,3300},int owner=1){
 try {auto* u=unit(type,owner,pos);g_ui->issue_order(u,false,g_ui->get_order_type(O::PlayerGuard),{});return u;}catch(...){std::cerr<<"Fixture type="<<int(type)<<" owner="<<owner<<" at "<<pos.x<<","<<pos.y<<"\n";throw;}
}
static int seated11(unit_t* b){return int(b->unit_type->space_provided-g_ui->unit_space_left(b));}
static int inbound11(unit_t* b){int n=0;for(auto*u:ptr(g_ui->st.player_units[b->owner]))if(!g_ui->unit_dying(u)&&!g_ui->u_loaded(u)&&u->order_type->id==O::EnterTransport&&u->order_target.unit==b)++n;return n;}
static void original11(const char* archive){
 open_archive(3,archive);openbw_init_campaign(640,480,402);openbw_set_external_cursor(1);advance(300);
 check(g_campaign->ai_error.empty(),"Dylarian original AI script failed");int n=0,occupants=0;
 for(auto*b:ptr(g_ui->st.player_units[0]))if(g_ui->unit_is(b,U::Terran_Bunker)&&!g_ui->unit_dying(b)){
  int expected=b->position.y<1300?3:4;check(seated11(b)==expected,"Original Dylarian bunker guards failed to enter");++n;occupants+=seated11(b);
 }
 check(n==12&&occupants==45,"Original Dylarian fixture differs");
 auto snap=save_game();advance(120);auto expected=save_game();restore_game(snap);advance(120);check(save_game()==expected,"Garrison save continuation diverged");
 std::cout<<"PASS unchanged Dylarian trigger loads45 original troops into12 bunkers, including full-map Anywhere, and deterministic save continuation\n";
}
static void bounds11(){
 reset();auto*b=make11(U::Terran_Bunker,{1248,3312});auto*inside=make11(U::Terran_Marine,{1184,3376});auto*outside=make11(U::Terran_Marine,{1376,3376});
 auto& loc=g_ui->st.locations[0];loc.area={{1120,3200},{1232,3456}};loc.elevation_flags=0;
 g_campaign->ai_start(1,ENBK,1);check(inside->order_target.unit==b&&inside->order_type->id==O::EnterTransport,"Region infantry not sent to closest bunker");check(outside->order_type->id==O::PlayerGuard,"Outside-region infantry redirected");
 g_campaign->ai_start(1,ENBK,1);check(inbound11(b)==1,"Repeated region script duplicated or changed order");advance(120);check(seated11(b)==1,"Region order failed to physically load");
 reset();b=make11(U::Terran_Bunker,{1248,3312});inside=make11(U::Terran_Marine,{1184,3376});g_ui->st.locations[0].area=g_ui->map_bounds();g_ui->st.locations[0].elevation_flags=7;g_campaign->ai_start(1,ENBK,1);check(inside->order_type->id==O::PlayerGuard,"Excluded ground elevation received EnBk");g_campaign->ai_start(1,ENBK,999);check(inside->order_type->id==O::PlayerGuard,"Invalid location became global");
 std::cout<<"PASS rectangular trigger bounds, elevation exclusions, invalid locations and repeat-script reservation\n";
}
static void capacity11(){
 reset();auto*b=make11(U::Terran_Bunker,{1248,3312});for(int i=0;i<6;++i)make11(U::Terran_Marine,{1184+i*32,3376});
 g_campaign->ai_start(1,ENBK,0);check(inbound11(b)==4,"Bunker seats were overbooked or omitted");g_campaign->ai_start(1,ENBK,0);check(inbound11(b)==4,"Repeated script overbooked travelling troops");advance(240);check(seated11(b)==4,"Bunker did not fill its four physical seats");g_campaign->ai_start(1,ENBK,0);check(inbound11(b)==0,"Full bunker accepted more infantry");
 reset();b=make11(U::Terran_Bunker,{1248,3312});auto*marine=make11(U::Terran_Marine,{1184,3376});g_ui->u_unset_status_flag(b,unit_t::status_flag_completed);g_campaign->ai_start(1,ENBK,0);check(marine->order_type->id==O::PlayerGuard,"Unfinished bunker accepted troops");g_ui->u_set_status_flag(b,unit_t::status_flag_completed);b->lockdown_timer=10;g_campaign->ai_start(1,ENBK,0);check(marine->order_type->id==O::PlayerGuard,"Disabled bunker accepted troops");b->lockdown_timer=0;g_ui->kill_unit(b);g_campaign->ai_start(1,ENBK,0);check(marine->order_type->id==O::PlayerGuard,"Dead bunker accepted troops");
 reset();make11(U::Terran_Bunker,{1248,3312},3);marine=make11(U::Terran_Marine,{1184,3376});g_campaign->ai_start(1,ENBK,0);check(marine->order_type->id==O::PlayerGuard,"Enemy bunker accepted troops");
 for(U type:{U::Protoss_Zealot,U::Zerg_Zergling,U::Terran_SCV,U::Terran_Vulture,U::Terran_Wraith}){reset();b=make11(U::Terran_Bunker,{1248,3312});auto*u=make11(type,{1376,3376});g_campaign->ai_start(1,ENBK,0);check(u->order_type->id==O::PlayerGuard,"Incompatible unit ordered into bunker");}
 std::cout<<"PASS four-seat capacity, existing inbound reservations, full/unfinished/disabled/dead/enemy bunkers and incompatible troops\n";
}
static void maintenance11(){
 for(bool melee:{false,true}){
  reset(melee);auto*b=make11(U::Terran_Bunker,{1248,3312});auto*m=make11(U::Terran_Marine,{1184,3376});g_campaign->ai_garrison(1);check(m->order_type->id==O::PlayerGuard,"Inactive campaign town changed authored guards");g_campaign->towns[1].active=true;advance(240);check(seated11(b)==1,"Scheduled active town failed to garrison nearby idle marine");
  auto*f=make11(U::Terran_Firebat,{1376,3376});advance(160);check(g_ui->u_loaded(f)&&seated11(b)==2,"Newly created infantry not garrisoned");
  auto*g=make11(U::Terran_Ghost,{1376,3440},3);g_ui->set_unit_owner(g,1,false);g_ui->issue_order(g,false,g_ui->get_order_type(O::PlayerGuard),{});advance(160);check(g_ui->u_loaded(g)&&seated11(b)==3,"Captured infantry not garrisoned by current owner");
  auto snapshot=save_game();advance(120);auto expected=save_game();restore_game(snapshot);advance(120);check(save_game()==expected,"Automatic garrison save continuation diverged");
  std::cout<<"PASS "<<(melee?"custom":"campaign")<<" scheduled garrison, infantry creation/transfer and save continuation\n";
 }
 reset();auto*m=make11(U::Terran_Marine,{1184,3376});g_campaign->towns[1].active=true;g_campaign->ai_garrison(1);check(m->order_type->id==O::PlayerGuard,"No bunker changed idle order");auto*b=make11(U::Terran_Bunker,{1248,3312});advance(160);check(g_ui->u_loaded(m),"Newly built bunker ignored existing guard");check(g_ui->unit_unload(m),"Fixture failed to unload surviving guard");g_ui->kill_unit(b);advance(32);g_ui->issue_order(m,false,g_ui->get_order_type(O::PlayerGuard),{});b=make11(U::Terran_Bunker,{1248,3312});advance(160);check(g_ui->u_loaded(m)&&seated11(b)==1,"Rebuilt bunker ignored surviving guard");
 std::cout<<"PASS newly constructed and replacement bunker re-acquires eligible local guard\n";
}
static void protected11(){
 reset();auto*b=make11(U::Terran_Bunker,{1248,3312});auto*m=make11(U::Terran_Marine,{1184,3376});g_campaign->towns[1].active=true;
 g_ui->my_player=1;g_campaign->ai_garrison(1);check(m->order_type->id==O::PlayerGuard,"Human player auto-garrisoned");g_ui->my_player=3;g_ui->st.players[1].controller=player_t::controller_occupied;g_campaign->ai_garrison(1);check(m->order_type->id==O::PlayerGuard,"Occupied player auto-garrisoned");g_ui->st.players[1].controller=player_t::controller_computer_game;
 g_campaign->units_paused=true;g_campaign->ai_garrison(1);check(m->order_type->id==O::PlayerGuard,"Paused scene auto-garrisoned");g_campaign->units_paused=false;g_ui->campaign_control_lock=true;g_campaign->ai_garrison(1);check(m->order_type->id==O::PlayerGuard,"Locked scene auto-garrisoned");g_ui->campaign_control_lock=false;
 for(O order:{O::Move,O::AttackMove,O::Patrol,O::HoldPosition}){g_ui->issue_order(m,false,g_ui->get_order_type(order),{{1500,3300},nullptr});g_campaign->ai_garrison(1);check(m->order_type->id==order,"Scripted/offensive order replaced by garrison");}
 g_ui->issue_order(m,false,g_ui->get_order_type(O::PlayerGuard),{});g_campaign->towns[1].attackers.push_back(g_ui->get_unit_id(m));g_campaign->ai_garrison(1);check(m->order_type->id==O::PlayerGuard,"Attack squad reclaimed by garrison");g_campaign->towns[1].attackers.clear();
 campaign_ai::airlift lift;lift.passengers.push_back(g_ui->get_unit_id(m));g_campaign->towns[1].lifts.push_back(lift);g_campaign->ai_garrison(1);check(m->order_type->id==O::PlayerGuard,"Airlift passenger reclaimed by garrison");g_campaign->towns[1].lifts.clear();
 g_campaign->towns[1].wave[0]=1;g_campaign->ai_garrison(1);check(m->order_type->id==O::PlayerGuard,"Pending attack-wave reserve consumed by bunker");auto*extra=make11(U::Terran_Marine,{1376,3376});g_campaign->ai_garrison(1);check(inbound11(b)==1&&g_campaign->ai_count(1,0,true,true)==1,"Bunker assignment did not retain exact pending wave reserve");g_campaign->ai_attack(1);check(inbound11(b)==1&&g_campaign->towns[1].attackers.size()==1,"Attack wave stole inbound bunker guard");advance(120);check(seated11(b)==1,"Reserved garrison did not complete");
 reset();b=make11(U::Terran_Bunker,{1248,3312});g_campaign->towns[1].active=true;auto*medic=make11(U::Terran_Medic,{1184,3376});auto*hero=make11(U::Hero_Jim_Raynor_Marine,{1376,3376});g_campaign->ai_garrison(1);check(medic->order_type->id==O::PlayerGuard&&hero->order_type->id==O::PlayerGuard,"Automatic bunker maintenance consumed support/story hero");
 reset();b=make11(U::Terran_Bunker,{1248,3312});m=make11(U::Terran_Marine,{1184,3376});auto*ship=make11(U::Terran_Dropship,{1376,3376});g_campaign->towns[1].active=true;g_ui->issue_order(m,false,g_ui->get_order_type(O::EnterTransport),{ship->position,ship});g_campaign->ai_garrison(1);check(m->order_target.unit==ship&&!g_campaign->ai_bunker_troop(m)&&g_campaign->ai_count(1,0,true,true)==1,"Dropship-bound infantry changed by bunker bookkeeping");g_ui->unit_load_target(ship,m);g_campaign->ai_garrison(1);check(m->connected_unit==ship&&g_ui->u_loaded(m)&&!g_campaign->ai_bunker_troop(m)&&g_campaign->ai_count(1,0,true,true)==1,"Loaded transport passenger changed by bunker bookkeeping");
 std::cout<<"PASS human/scene/scripted movement/combat/attack-wave/airlift/medic/hero protections and garrison versus wave accounting\n";
 std::cout<<"PASS ordinary Dropship inbound and loaded passenger orders/accounting unchanged\n";
}
int main(int argc,char**argv){try{
 std::cout.setf(std::ios::unitbuf);check(argc==3,"native-bunker11 CORE_DIR BROODWAR_MPQ");std::string p=argv[1];open_archive(0,p+"/STARDAT.MPQ");open_archive(1,p+"/BROODAT.MPQ");open_archive(2,p+"/patch_rt.mpq");original11(argv[2]);setup(argv[2]);bounds11();capacity11();maintenance11();protected11();close_game();return 0;
}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
