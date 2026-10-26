// Stock original Dylarian AI, then its unmodified silo-handover trigger.
// Controlled switches exercise the reward without pretending this is a playthrough.
#include "../native/runtime.cpp"
#include <iostream>
#include <fstream>
using namespace bwgame;using U=UnitTypes;
static int checks=0;
static void check(bool b,const char* why){++checks;if(!b)throw std::runtime_error(why);}
static void advance(int n){for(int i=0;i<n;++i){native_step();if(!g_campaign->ai_error.empty())throw std::runtime_error(g_campaign->ai_error.c_str());}}
static std::vector<unit_t*> units(U type,int owner=-1){std::vector<unit_t*> r;for(auto& list:g_ui->st.player_units)for(auto*u:ptr(list))if(g_ui->unit_is(u,type)&&!g_ui->unit_dying(u)&&(owner<0||u->owner==owner))r.push_back(u);return r;}
static int ready(int owner){int n=0;for(auto*s:units(U::Terran_Nuclear_Silo,owner))if(s->building.silo.ready&&s->building.silo.nuke){auto*m=s->building.silo.nuke;check(m->owner==owner&&m->connected_unit==s&&g_ui->u_completed(m)&&g_ui->us_hidden(m),"Stored missile identity/ownership invalid");++n;}return n;}
static void dump(){std::cout<<"frame="<<g_ui->st.current_frame<<" outcome="<<g_ui->outcome<<" AI="<<g_campaign->ai_status()<<"\n";for(auto*s:units(U::Terran_Nuclear_Silo))std::cout<<"silo "<<s->owner<<" ready="<<s->building.silo.ready<<" nuke="<<bool(s->building.silo.nuke)<<" queued="<<s->build_queue.size()<<" order="<<int(s->order_type->id)<<"\n";}

static void shared_cases(const char* map){
 close_game();open_archive(3,map);openbw_init_race_ai(640,480,1,1,1);g_ui->competitive=false;g_ui->rep_on=false;g_ui->clamp_viewport(); // Injected fixture is not a replay; saved-game loads disable recording.
 check(g_campaign,"Custom-game AI missing");g_campaign->threads.clear();g_campaign->spawned.clear();g_campaign->towns={};
 g_ui->st.players[7].controller=player_t::controller_computer_game;g_ui->st.players[7].race=race_t::terran;
 game_load_functions rules(g_ui->player.st());rules.game_st.unit_type_allowed[7][U::Terran_Nuclear_Missile]=true;
 unit_t* silo=nullptr;auto* siloType=g_ui->get_unit_type(U::Terran_Nuclear_Silo);auto* ccType=g_ui->get_unit_type(U::Terran_Command_Center);
 for(int y=128;y<1800&&!silo;y+=64)for(int x=128;x<1800&&!silo;x+=64){
  xy ccPos{x,y},siloPos=ccPos-ccType->placement_size/2+siloType->addon_position+siloType->placement_size/2;
  if(!g_ui->can_place_building(nullptr,7,ccType,ccPos,true,false,true)||!g_ui->can_place_building(nullptr,7,siloType,siloPos,true,false,true))continue;
  auto* cc=g_ui->create_initial_unit(ccType,ccPos,7);silo=g_ui->create_initial_unit(siloType,siloPos,7);check(cc&&silo,"Custom CC/silo pair failed");g_ui->connect_addon(cc,silo);
 }
 check(silo&&g_ui->addon_is_attached(silo),"Custom-map silo fixture failed");g_campaign->melee_ai=false;
 auto siloId=g_ui->get_unit_id(silo);g_campaign->towns[7].supply=false;g_ui->st.current_minerals[7]=0;g_ui->st.current_gas[7]=0;g_ui->st.supply_available[7][1]=fp1::integer(16);
 g_campaign->ai_manage(7);check(silo->build_queue.empty(),"Inactive scripted town stocked silo");g_campaign->towns[7].active=true;
 g_campaign->ai_manage(7);check(silo->build_queue.empty(),"AI created unpaid missile");g_ui->st.current_minerals[7]=200;g_ui->st.current_gas[7]=200;
 g_ui->st.supply_available[7][1]=fp1::zero();g_campaign->ai_manage(7);check(silo->build_queue.empty(),"AI bypassed supply");g_ui->st.supply_available[7][1]=fp1::integer(16);
 rules.game_st.unit_type_allowed[7][U::Terran_Nuclear_Missile]=false;g_campaign->ai_manage(7);check(silo->build_queue.empty(),"AI bypassed map unit availability");rules.game_st.unit_type_allowed[7][U::Terran_Nuclear_Missile]=true;
 g_campaign->melee_ai=true;g_campaign->ai_manage(7);check(silo->build_queue.size()==1&&g_ui->st.current_minerals[7]==0&&g_ui->st.current_gas[7]==0,"Custom-map silo did not pay for normal missile production");
 g_campaign->towns[7].active=false;advance(8);check(silo->building.silo.nuke&&!silo->building.silo.ready,"Computer silo failed to track in-progress missile");
 g_ui->cancel_build_queue(silo);advance(4);check(!silo->building.silo.nuke&&!silo->building.silo.ready&&g_ui->st.current_minerals[7]==200&&g_ui->st.current_gas[7]==200,"Cancelled missile lost refund or left stale silo pointer");
 g_campaign->towns[7].active=true;g_campaign->ai_manage(7);g_campaign->towns[7].active=false;advance(8);check(silo->building.silo.nuke,"Retry missile missing");
 g_ui->give_unit_to(silo,0);advance(4);check(silo->build_queue.empty()&&!silo->building.silo.nuke&&g_ui->st.current_minerals[7]==200&&g_ui->st.current_gas[7]==200,"Early ownership transfer did not cancel/refund old owner's unfinished missile");
 g_ui->give_unit_to(silo,7);g_campaign->towns[7].active=true;advance(2400);check(ready(7)==1,"Custom-game silo failed shared stocking path");g_campaign->towns[7].active=false;
 auto missileId=g_ui->get_unit_id(silo->building.silo.nuke);check(g_ui->st.supply_used[7][1]==fp1::integer(8),"Missile supply was not tracked");
 g_ui->st.current_minerals[7]=g_ui->st.current_gas[7]=1000;action_state state;action_functions af(g_ui->st,state);af.action_select(7,silo);check(!af.action_train(7,g_ui->get_unit_type(U::Terran_Nuclear_Missile)),"Full silo accepted another missile");
 g_ui->give_unit_to(silo,0);check(ready(0)==1&&ready(7)==0&&g_ui->st.supply_used[7][1]==fp1::zero(),"Full silo capture lost missile or original-owner supply");check(silo->building.silo.nuke->owner==0&&g_ui->get_unit_id(silo->building.silo.nuke)==missileId,"Capture duplicated/replaced loaded missile");
 auto before=save_game();advance(48);auto after=save_game();restore_game(before);advance(48);auto actual=save_game();
 if(actual!=after){for(auto p:{std::pair<const char*,std::vector<uint8_t>*>{"before",&before},{"expected",&after},{"actual",&actual}}){std::ofstream f(std::string("build-native/nukes11/")+p.first+".save",std::ios::binary);f.write((char*)p.second->data(),p.second->size());}size_t at=0;while(at<std::min(actual.size(),after.size())&&actual[at]==after[at])++at;std::cerr<<"snapshot difference offset="<<at<<" expected size="<<after.size()<<" actual size="<<actual.size()<<"\n";}
 check(actual==after,"Captured missile state failed deterministic snapshot continuation");
 silo=g_ui->get_unit(siloId);g_ui->kill_unit(silo);advance(20);auto* missile=g_ui->get_unit(missileId);check(!missile||g_ui->unit_dying(missile),"Destroyed silo leaked loaded missile");
 std::cout<<"PASS shared custom-map silo production: inactive, affordability, supply, allowed units, cancellation/refund, early and complete capture, capacity, save continuation, destruction\n";
}

int main(int argc,char**argv){try{
 std::cout.setf(std::ios::unitbuf);check(argc==4,"Usage: native_nukes11 CORE BROODWAR CUSTOM");std::string core=argv[1];open_archive(0,core+"/STARDAT.MPQ");open_archive(1,core+"/BROODAT.MPQ");open_archive(2,core+"/patch_rt.mpq");open_archive(3,argv[2]);openbw_init_campaign(640,480,402);
 check(g_ui->my_player==6,"Dylarian player changed");check(g_ui->get_unit_type(U::Terran_Nuclear_Missile)->supply_required==fp1::integer(8),"Original DAT missile supply changed");std::cout<<"DAT missile supply: 8 displayed supply, 16 half-supply internal units; 200 minerals + 200 gas\n";check(units(U::Terran_Nuclear_Silo,0).size()==4,"Original four enemy silos missing");check(ready(0)==0,"Mission starts with unexpectedly preloaded silos");
 advance(2700);dump();std::cout<<"missiles="<<units(U::Terran_Nuclear_Missile,0).size()<<" supply="<<g_ui->st.supply_used[0][1].integer_part()<<"/"<<g_ui->st.supply_available[0][1].integer_part()<<"\n";check(!g_ui->outcome,"Unattended Dylarian startup ended");check(ready(0)==3,"Original opening supply should allow three missiles until a defender dies");check(g_ui->st.supply_used[0][1]==fp1::integer(129)&&g_ui->st.supply_available[0][1]==fp1::integer(136),"Opening supply fixture changed");g_ui->kill_unit(units(U::Terran_Marine,0).front());advance(2400);check(ready(0)==4,"Original TB2B did not fill fourth silo after real supply became available");check(g_campaign->towns[0].trained==4,"AI duplicated missiles or trained unintended units");check(g_ui->st.current_minerals[0]==9200&&g_ui->st.current_gas[0]==9200,"Four nukes were not paid for from original resources");
 std::cout<<"PASS original TB2B stocks four silos using ordinary build time, costs and supply\n";
 g_campaign->switches[5]=true;g_campaign->scores[1][7]=4;advance(1800);dump();check(ready(6)==4&&ready(0)==0,"Original platform-B handover did not give four usable missiles");check(g_ui->has_ready_nuke(6),"Ghost command unavailable after handover");std::cout<<"PASS original reward transfers four armed silos and their owned ammunition\n";
 auto ghosts=units(U::Terran_Ghost,6);check(ghosts.size()>=4,"Original ghost reinforcement missing");auto* ghost=ghosts.front();g_ui->u_set_status_flag(ghost,unit_t::status_flag_invincible);auto ghostId=g_ui->get_unit_id(ghost);xy target=ghost->position+xy(0,-288);auto* victim=g_ui->create_initial_unit(g_ui->get_unit_type(U::Terran_Supply_Depot),target,0);check(victim,"Nuke target fixture failed");auto victimId=g_ui->get_unit_id(victim);auto hp=victim->hp;
 openbw_debug_select(ghostId.raw_value,0);g_ui->refresh_card();bool offered=false;for(auto c:g_ui->card)if(c.label=="Nuclear Strike"&&c.enabled){g_ui->run_command(c.key);offered=true;break;}check(offered,"Reward ghost has no enabled Nuclear Strike command");g_ui->issue_target(target);
 bool launched=false,damaged=false;for(int i=0;i<1800;++i){advance(1);ghost=g_ui->get_unit(ghostId);victim=g_ui->get_unit(victimId);if(ghost&&ghost->connected_unit&&!launched){launched=true;check(ready(6)==3,"One launch did not consume exactly one missile");check(ghost->connected_unit->owner==6,"Launched missile retained enemy ownership");}if(!victim||victim->hp<hp){damaged=true;break;}}
 check(launched&&damaged,"Reward missile failed actual launch/explosion");check(ready(6)==3,"Player ammunition was automatically replenished");auto snapshot=save_game();advance(120);auto expected=save_game();restore_game(snapshot);advance(120);check(save_game()==expected,"Nuke state save continuation diverged");std::cout<<"PASS reward Ghost command launches an owned missile, damages enemy, consumes exactly one and restores deterministically\n";
 shared_cases(argv[3]);close_game();std::cout<<"PASS "<<checks<<" nuke checks\n";return 0;
}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
