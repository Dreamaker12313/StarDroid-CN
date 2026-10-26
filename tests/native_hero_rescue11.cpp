// Original-data production/audio regressions. No game assets bundled.
#include "../native/runtime.cpp"
#include <iostream>
using namespace bwgame;using U=UnitTypes;
static int checks=0;
static void check(bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);}
static void silence(){for(size_t i=0;i<g_ui->sound_channels.size();i++){native_sound::stop(i);g_ui->sound_channels[i].playing=false;}std::fill(g_ui->last_played_sound.begin(),g_ui->last_played_sound.end(),decltype(g_ui->last_played_sound)::value_type{});}
static bool heard(int cue){for(auto& c:g_ui->sound_channels)if(c.playing&&int(c.sound_type->id)==cue)return true;return false;}
static void poll(){auto sum=sim_checksum(g_ui->st);auto rng=g_ui->st.lcg_rand_state;g_ui->poll_events();check(sim_checksum(g_ui->st)==sum&&g_ui->st.lcg_rand_state==rng,"Audio polling changed simulation/RNG");}
static void setup(bool heroes=true){int races[]={1,0,2,1,1,1,1,1},slots[]={1,0,0,0,0,0,0,0};configured_init(640,480,0,races,slots,0,true,false,false,nullptr,false,heroes);g_ui->competitive=false;g_ui->fog_player=-1;g_ui->st.current_minerals[0]=g_ui->st.current_gas[0]=50000;for(int race=0;race<3;race++)g_ui->st.supply_available[0][race]=fp1::integer(200);}
static unit_t* create(U type,int owner=0,xy around={1024,1024}){
 auto* ut=g_ui->get_unit_type(type);
 for(int r=0;r<30;r++)for(int y=-r;y<=r;y++)for(int x=-r;x<=r;x++){
  xy p=around+xy(x*32,y*32);if(!g_ui->unit_type_can_fit_at(ut,p))continue;
  bool free=true;for(auto*u:g_ui->find_units(g_ui->square_at(p,80)))if(!g_ui->unit_dying(u))free=false;
  if(free)if(auto*u=g_ui->create_initial_unit(ut,p,owner))return u;
 }throw std::runtime_error("No clear fixture position");
}
static void powered(){for(auto*u:ptr(g_ui->st.player_units[0]))g_ui->u_unset_status_flag(u,unit_t::status_flag_disabled);}
static void produced(){
 for(const auto& h:hero_roster()){
  setup();auto type=U(h.id);auto* producer=create(hero_producer(h.race),0,{900,900});
  for(int t:{h.tech1,h.tech2})if(t>=0){auto* req=create(U(t),0,{1100,1100});if(g_ui->ut_addon(req)){auto* parent=create(U(t==120?113:t==115?114:116),0,{1400,1200});parent->building.addon=req;}}
  powered();poll();silence();int cue=32+h.race;auto* ut=g_ui->get_unit_type(type);check(int(g_ui->unit_race(ut))==h.race,"Original hero race differs from Hero Mode roster");
  check(g_ui->sound_filenames[cue].find(h.race==0?"ZRescue":h.race==1?"TRescue":"PRescue")!=a_string::npos,"Original rescue DAT mapping differs");
  for(int generation=0;generation<2;generation++){
   int before=g_ui->ready_notifications;action_functions af(g_ui->st,g_ui->current_action_state);af.action_select(0,producer);check(af.action_train(0,ut),"Hero training refused");g_ui->st.cheat_operation_cwal=true;
   unit_t* hero=nullptr;
   for(int f=0;f<600&&!hero;f++){
    powered();native_step();silence();poll();
    for(auto*u:ptr(g_ui->st.player_units[0]))if(g_ui->unit_is(u,type)&&g_ui->u_completed(u)&&!g_ui->unit_dying(u))hero=u;
    if(!hero)check(g_ui->ready_notifications==before,"Hero cue before production completed");
   }
   check(hero,"Hero never completed production");check(g_ui->ready_notifications==before+1&&g_ui->last_ready_type==h.id&&g_ui->last_ready_sound==cue&&heard(cue),"Hero completion did not play exactly one race rescue cue");
   for(int wrong=32;wrong<=34;wrong++)if(wrong!=cue)check(!heard(wrong),"Hero completion played player/wrong-race cue");
   silence();poll();check(g_ui->ready_notifications==before+1&&!heard(cue),"Completion cue repeated at next poll");
   for(auto range:{std::make_pair(hero->unit_type->first_what_sound,hero->unit_type->last_what_sound),std::make_pair(hero->unit_type->first_yes_sound,hero->unit_type->last_yes_sound)}){
    silence();check(g_ui->play_unit_ack(hero,range.first,range.second),"Hero selection/order acknowledgement missing");check(g_ui->previous_ack_sound>=std::min(range.first,range.second)&&g_ui->previous_ack_sound<=std::max(range.first,range.second)&&heard(g_ui->previous_ack_sound),"Hero acknowledgement replaced by rescue cue");
   }
   g_ui->kill_unit(hero);for(int f=0;f<15;f++)native_step();
  }
  std::cout<<"PASS trained/rebuilt hero="<<h.id<<" localRace=Terran heroRace="<<h.race<<" cue="<<cue<<"; actual completion only\n";close_game();
 }
}
static void transitions(){
 setup();auto* a=create(U::Hero_Tassadar,0,{800,800});auto* b=create(U::Hero_Zeratul,0,a->position+xy(100,0));poll();silence();int before=g_ui->ready_notifications;
 action_functions af(g_ui->st,g_ui->current_action_state);unit_t* pair[]={a,b};af.action_select(0,pair);check(af.action_morph_archon(0),"Hero Archon merge refused");unit_t* archon=nullptr;bool merging=false;
 for(int f=0;f<1600;f++){
  native_step();silence();poll();
  for(auto*u:ptr(g_ui->st.player_units[0]))if(g_ui->unit_is(u,U::Hero_Tassadar_Zeratul_Archon)&&!g_ui->unit_dying(u))archon=u;
  if(archon&&g_ui->archon_merging(archon)){merging=true;check(g_ui->ready_notifications==before,"Hero Archon cue before merge completed");}
  if(archon&&!g_ui->archon_merging(archon))break;
 }
 check(archon&&merging&&!g_ui->archon_merging(archon),"Actual hero merge did not finish");check(g_ui->ready_notifications==before+1&&g_ui->last_ready_sound==34&&heard(34),"Hero Archon lacks one Protoss rescue completion cue");silence();poll();check(g_ui->ready_notifications==before+1&&!heard(34),"Hero Archon completion repeated");
 auto* duke=create(U::Hero_Edmund_Duke_Tank_Mode,0,{1200,1200});silence();poll();check(g_ui->last_ready_sound==33&&heard(33),"Duke spawn lacks Terran rescue cue");before=g_ui->ready_notifications;af.action_select(0,duke);check(af.action_siege(0,false),"Duke siege refused");
 for(int i=0;i<400;i++){native_step();poll();}check(g_ui->unit_is(duke,U::Hero_Edmund_Duke_Siege_Mode)&&g_ui->ready_notifications==before,"Siege pretended Duke spawned again");
 g_ui->announced[g_ui->get_unit_id(duke).raw_value]=int(U::Hero_Edmund_Duke_Siege_Mode);silence();poll();check(g_ui->ready_notifications==before&&!heard(33),"Old-save siege type generated spurious completion");
 af.action_select(0,duke);check(af.action_unsiege(0,false),"Duke unsiege refused");for(int i=0;i<400;i++){native_step();poll();}check(g_ui->unit_is(duke,U::Hero_Edmund_Duke_Tank_Mode)&&g_ui->ready_notifications==before,"Unsiege pretended Duke spawned again");
 auto* siegedSpawn=create(U::Hero_Edmund_Duke_Siege_Mode,0,{1300,1400});silence();poll();check(g_ui->ready_notifications==before+1&&g_ui->last_ready_sound==33&&heard(33),"Direct Duke siege-form spawn lacks rescue cue");
 auto saved=save_game();restore_game(saved);silence();before=g_ui->ready_notifications;poll();check(g_ui->ready_notifications==before&&!heard(33)&&!heard(34),"Save/load replayed hero completion");
 std::cout<<"PASS real hero Archon merge completion, Duke siege/unsiege and old announced25 save state; save/load no reannouncement\n";close_game();
}
static void isolation(){
 setup();poll();silence();int before=g_ui->ready_notifications;auto* ai=create(U::Hero_Hunter_Killer,1);poll();check(g_ui->ready_notifications==before&&!heard(32),"AI hero announced to player");
 g_ui->spectator=true;create(U::Hero_Fenix_Zealot);poll();check(g_ui->ready_notifications==before&&!heard(34),"Spectator hero announced");g_ui->spectator=false;poll();check(g_ui->ready_notifications==before,"Leaving spectator replayed old hero spawn");
 g_ui->st.players[0].controller=player_t::controller_computer_game;create(U::Hero_Jim_Raynor_Marine);poll();check(g_ui->ready_notifications==before&&!heard(33),"AI local slot hero announced");g_ui->st.players[0].controller=player_t::controller_occupied;poll();
 auto* illusion=create(U::Hero_Kukulza_Mutalisk);g_ui->make_unit_hallucination(illusion);poll();check(g_ui->ready_notifications==before&&!heard(32),"Hallucination pretended to be a real hero spawn");
 check(g_ui->trigger_give_unit_to(ai,0),"Hero transfer refused");poll();check(g_ui->ready_notifications==before&&!heard(32),"Scripted transfer emitted unsolicited production cue");
 g_ui->on_units_rescued(1,0,race_t::zerg);poll();check(g_ui->rescue_notifications==1&&g_ui->ready_notifications==before&&heard(32),"Real rescue missing or duplicated by hero completion");
 // Ordinary units retain their DAT ready voices with Hero Mode enabled.
 for(U type:{U::Terran_Marine,U::Zerg_Zergling,U::Protoss_Zealot}){auto*u=create(type);int expected=u->unit_type->ready_sound;check(expected>0&&expected!=32&&expected!=33&&expected!=34,"Ordinary ready fixture missing");before=g_ui->ready_notifications;silence();poll();check(g_ui->ready_notifications==before+1&&g_ui->last_ready_sound==expected&&heard(expected),"Ordinary unit ready voice changed");}
 // Preserve the pre-existing ordinary-unit observer behavior; the new gate
 // is restricted to Hero Mode hero completions.
 g_ui->spectator=true;auto* ordinary=create(U::Terran_Marine);before=g_ui->ready_notifications;silence();poll();check(g_ui->ready_notifications==before+1&&heard(ordinary->unit_type->ready_sound),"Hero-only observer guard changed ordinary completion audio");g_ui->spectator=false;
 close_game();setup(false);poll();
 for(const auto& h:hero_roster()){auto*u=create(U(h.id));int expected=u->unit_type->ready_sound>0?u->unit_type->ready_sound:-1;check(g_ui->ready_sound_for(u)==expected,"Campaign/ordinary hero cue changed with Hero Mode off");g_ui->kill_unit(u);for(int i=0;i<5;i++)native_step();}
 std::cout<<"PASS AI/spectator/hallucination suppression, scripted transfers and true rescues, ordinary ready voices, all18 campaign hero DAT voices unchanged\n";close_game();
}
int main(int argc,char**argv){try{check(argc==2,"Usage: hero-rescue11 CORE");std::string core=argv[1];open_archive(0,core+"/STARDAT.MPQ");open_archive(1,core+"/BROODAT.MPQ");open_archive(2,core+"/patch_rt.mpq");open_archive(3,"app/src/main/assets/native/weave.scx");produced();transitions();isolation();std::cout<<"PASS "<<checks<<" hero rescue checks; simulation/RNG unchanged by every poll\n";return 0;}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
