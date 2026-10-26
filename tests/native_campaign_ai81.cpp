// Original mission scripts/triggers run unchanged. Controlled movement and
// destruction exercise activation branches; this is not a full playthrough.
#include "../native/runtime.cpp"
#include <iostream>
#include <functional>
using namespace bwgame;
using U=UnitTypes;
static void check(bool ok,const char* message){if(!ok)throw std::runtime_error(message);}
static void advance(int n){for(int i=0;i<n&&!g_ui->outcome;++i){native_step();check(g_campaign->ai_error.empty(),g_campaign->ai_error.c_str());}}
static std::vector<unit_t*> units(U type,int owner=-1){std::vector<unit_t*> out;for(auto& list:g_ui->st.player_units)for(auto*u:ptr(list))if(g_ui->unit_is(u,type)&&!g_ui->unit_dying(u)&&(owner<0||u->owner==owner))out.push_back(u);return out;}
static void warp(unit_t* u,xy pos){openbw_debug_warp(g_ui->get_unit_id(u).raw_value,pos.x,pos.y);}
static void dump(){std::cout<<"FRAME "<<g_ui->st.current_frame<<" clock="<<g_campaign->ai_clock<<" outcome="<<g_ui->outcome<<" AIERR="<<g_campaign->ai_error<<"\n"<<g_campaign->ai_status();}
static void revolution(){
 advance(2400);check(!g_campaign->switches[6]&&!g_campaign->towns[6].active,"Confederates activated before original mission event");
 check(g_campaign->towns[6].built==0&&g_campaign->towns[6].trained==0,"Inactive campaign economy produced units");
 std::cout<<"PASS Revolution waits for its original activation event\n";
 // Preserve original heroes while their normal rescue and briefing triggers run.
 for(U type:{U::Hero_Sarah_Kerrigan,U::Hero_Jim_Raynor_Vulture})for(auto*u:units(type))g_ui->u_set_status_flag(u,unit_t::status_flag_invincible);
 auto* marine=units(U::Terran_Marine,0).front();g_ui->u_set_status_flag(marine,unit_t::status_flag_invincible);
 warp(marine,{256,2600});advance(120);
 check(!g_campaign->switches[6],"Ground unit incorrectly activated aircraft-only region");
 warp(marine,{149,1233});advance(1800);
 auto kerrigan=units(U::Hero_Sarah_Kerrigan,0);check(kerrigan.size()==1,"Original Kerrigan rescue failed");
 warp(kerrigan[0],{2720,464});advance(3000);
 check(!g_campaign->units_paused&&g_ui->st.completed_building_counts[0]>0,"Antigan rebellion/handover failed");
 auto beforeActivation=save_game();
 // Clearing the Confederate bunkers near Antiga is the other original path.
 std::vector<unit_t*> guards;for(auto*u:g_ui->find_units(g_ui->st.locations[19].area))if(u->owner==6&&g_ui->ut_building(u)&&!g_ui->ut_turret(u))guards.push_back(u);
 check(!guards.empty(),"Original Antigan Confederate guards absent");for(auto*u:guards)g_ui->kill_unit(u);advance(120);
 check(g_campaign->switches[6]&&g_campaign->towns[6].active,"Clearing the original Confederate guard location did not activate AI");
 restore_game(beforeActivation);check(!g_campaign->switches[6]&&!g_campaign->towns[6].active,"Pre-activation state did not restore");
 std::cout<<"PASS original cleared-guard activation path and inactive snapshot restoration\n";
 // Original location18 excludes ground elevations: an aircraft can activate
 // it, while ground troops cannot. Exercise the rescued original Wraith.
 auto wraiths=units(U::Terran_Wraith,0);check(!wraiths.empty(),"Original Antigan Wraith was not rescued");
 auto* ship=wraiths.front();g_ui->u_set_status_flag(ship,unit_t::status_flag_invincible);warp(ship,{2100,2400});advance(120);
 check(g_campaign->switches[6]&&g_campaign->towns[6].active,"Original aircraft-entry trigger did not activate Confederate AI");
 std::cout<<"PASS Kerrigan rescue, Antigan rebellion and original aircraft activation trigger\n";
 // Keep the player's original objective heroes alive; no AI resources granted.
 check(g_campaign->towns[6].attacks==0,"Original first-attack delay was bypassed");
 int activationClock=g_campaign->ai_clock,firstAttack=-1;
 for(int i=0;i<10000&&!g_ui->outcome;i++){advance(1);if(g_campaign->ai_clock-activationClock<5800)check(!g_campaign->towns[6].attacks,"AI attacked before original script wait");if(firstAttack<0&&g_campaign->towns[6].attacks)firstAttack=g_ui->st.current_frame;}
 dump();std::cout<<"REVOLUTION firstAttack="<<firstAttack<<"\n";
 for(auto*u:units(U::Terran_SCV,6))std::cout<<"WORKER "<<u->position.x<<","<<u->position.y<<" order="<<int(u->order_type->id)<<" target="<<(u->worker.gather_target?int(u->worker.gather_target->unit_type->id):-1)<<"\n";
 check(!g_ui->outcome&&g_campaign->towns[6].built>0&&g_campaign->towns[6].trained>0&&firstAttack>=0,"Activated Confederates did not build/train/attack");
 check(g_ui->st.total_minerals_gathered[6]>6000&&g_ui->st.total_gas_gathered[6]>6000,"Activated Confederates did not gather both resources");
 std::cout<<"PASS original Confederate production, mining and delayed first attack\n";
 auto barracks=units(U::Terran_Barracks,6);check(barracks.size()==1,"Original Confederate Barracks fixture differs");g_ui->kill_unit(barracks[0]);advance(5000);
 bool rebuilt=false;for(auto*u:units(U::Terran_Barracks,6))if(g_ui->u_completed(u))rebuilt=true;check(rebuilt,"Confederate script did not replace lost Barracks");
 auto snapshot=save_game();advance(240);auto expected=save_game();restore_game(snapshot);advance(240);check(save_game()==expected,"Campaign AI save continuation diverged");
 std::cout<<"PASS original build request replaces destroyed Barracks and deterministic save continuation\n";
}
int main(int argc,char**argv){try{
 std::cout.setf(std::ios::unitbuf);check(argc>=4,"native-campaign_ai81 CORE_DIR MAP_ARCHIVE MISSION_CODE [FRAMES]");std::string p=argv[1];open_archive(0,p+"/STARDAT.MPQ");open_archive(1,p+"/BROODAT.MPQ");open_archive(2,p+"/patch_rt.mpq");open_archive(3,argv[2]);int code=std::stoi(argv[3]);openbw_init_campaign(640,480,code);openbw_set_external_cursor(1);
 if(argc==4){check(code==5,"Focused case is Revolution");revolution();}else{advance(std::stoi(argv[4]));dump();}
 close_game();return 0;
}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
