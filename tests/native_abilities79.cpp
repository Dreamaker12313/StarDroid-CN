// Real engine combat-spell regressions, with caller-supplied original archives.
// Controlled placements isolate casting; these are not complete AI playthroughs.
#include "../native/runtime.cpp"
#include <iostream>
#include <functional>
using namespace bwgame;
using U=UnitTypes;using T=TechTypes;using O=Orders;
static void check(bool ok,const char* message){if(!ok)throw std::runtime_error(message);}
static std::vector<uint8_t> clean;
static const char* archivePath;
static decltype(game_state::tech_available) permissions;
static void reset(bool melee=false){restore_game(clean);game_load_functions(g_ui->player.st()).game_st.tech_available=permissions;g_campaign->melee_ai=melee;g_campaign->units_paused=false;g_ui->campaign_control_lock=false;g_ui->competitive=false;}
static unit_t* unit(U type,int owner,xy pos){
 auto* u=g_ui->create_initial_unit(g_ui->get_unit_type(type),pos,owner);check(u,"Could not place test unit");
 u->sprite->visibility_flags=255;u->energy=fp8::integer(250);u->ground_weapon_cooldown=10000;u->air_weapon_cooldown=10000;
 g_ui->issue_order(u,false,g_ui->get_order_type(O::HoldPosition),{});return u;
}
static void enable(T tech){game_load_functions f(g_ui->player.st());f.game_st.tech_available[1][tech]=true;g_ui->st.tech_researched[1][tech]=true;}
static void advance(int frames){for(int i=0;i<frames;++i)native_step();}
static bool wait(const std::function<bool()>& yes,int frames=300){for(int i=0;i<frames&&!yes();++i)native_step();return yes();}
static unit_t* caster(U type){auto* u=unit(type,1,{1200,3300});g_ui->u_set_status_flag(u,unit_t::status_flag_invincible);return u;}
static void setup(const char* archive){
 archivePath=archive;open_archive(3,archive);openbw_init_campaign(640,480,502);openbw_set_external_cursor(1);
 game_load_functions f(g_ui->player.st());f.game_st.triggers.clear();for(auto& list:g_ui->st.running_triggers)list.clear();
 g_campaign->threads.clear();g_campaign->spawned.clear();g_campaign->towns={};g_campaign->units_paused=false;g_ui->campaign_control_lock=false;
 for(int p=0;p<12;++p){a_vector<unit_t*> dead;for(auto* u:ptr(g_ui->st.player_units[p]))if(!g_ui->ut_turret(u))dead.push_back(u);for(auto* u:dead)if(!g_ui->unit_dying(u))g_ui->kill_unit(u);}
 for(int i=0;i<80;++i)g_ui->state_functions::next_frame();g_ui->outcome=0;
 for(int p=0;p<12;++p){g_ui->st.alliances[p].fill(0);g_ui->st.alliances[p][p]=1;g_ui->st.alliances[p][11]=1;g_ui->st.players[p].controller=player_t::controller_inactive;}
 g_ui->st.players[1].controller=player_t::controller_computer_game;g_ui->st.players[3].controller=player_t::controller_occupied;
 g_ui->st.current_minerals[1]=g_ui->st.current_gas[1]=0;permissions=g_ui->game_st.tech_available;clean=save_game();
}
static void storms(){
 for(bool melee:{false,true})for(U type:{U::Protoss_High_Templar,U::Hero_Tassadar,U::Hero_Infested_Kerrigan}){
  reset(melee);auto* u=caster(type);enable(T::Psionic_Storm);
  // Heroes retain their innate ability even without normal-unit research.
  if(type!=U::Protoss_High_Templar)g_ui->st.tech_researched[1][T::Psionic_Storm]=false;
  auto* a=unit(U::Terran_Marine,3,{1360,3284});unit(U::Terran_Marine,3,{1360,3316});
  fp8 energy=u->energy,hp=a->hp;
  if(!wait([&]{return u->energy<energy-fp8::integer(60)&&a->hp<hp;})) {
   std::cerr<<"Storm debug type="<<int(type)<<" melee="<<melee<<" energy="<<u->energy.integer_part()<<" hp="<<a->hp.integer_part()<<" order="<<int(u->order_type->id)<<" clock="<<g_campaign->ai_clock<<" frame="<<g_ui->st.current_frame<<" outcome="<<g_ui->outcome<<" paused="<<g_campaign->units_paused<<" lock="<<g_ui->campaign_control_lock<<" see="<<g_ui->unit_can_see_target(u,a)<<" ready="<<g_campaign->ai_spell_ready(u,O::CastPsionicStorm)<<" ability="<<g_campaign->ai_area_spell(u,O::CastPsionicStorm)<<"\n";
   throw std::runtime_error("AI Storm did not spend energy and damage targets");
  }
  check(!g_campaign->towns[1].active,"Fixture accidentally activated town");
 }
 std::cout<<"PASS scheduled campaign and melee Storm casting for High Templar, Tassadar/Aldaris and Infested Kerrigan without an active town\n";
}
static void targeted(){
 struct Test{U caster;T tech;O order;U target;};
 Test cases[]={
 {U::Terran_Ghost,T::Lockdown,O::CastLockdown,U::Terran_Goliath},
 {U::Terran_Science_Vessel,T::Irradiate,O::CastIrradiate,U::Zerg_Ultralisk},
 {U::Terran_Battlecruiser,T::Yamato_Gun,O::FireYamatoGun,U::Terran_Battlecruiser},
 {U::Protoss_Dark_Archon,T::Feedback,O::CastFeedback,U::Terran_Science_Vessel},
 {U::Protoss_Dark_Archon,T::Mind_Control,O::CastMindControl,U::Terran_Battlecruiser},
 {U::Zerg_Queen,T::Spawn_Broodlings,O::CastSpawnBroodlings,U::Terran_Goliath},
 {U::Zerg_Queen,T::Parasite,O::CastParasite,U::Terran_Battlecruiser},
 {U::Terran_Medic,T::Optical_Flare,O::CastOpticalFlare,U::Terran_Science_Vessel}
 };
 for(auto c:cases){
  reset();auto* u=caster(c.caster);enable(c.tech);auto* target=unit(c.target,3,{1360,3300});auto id=g_ui->get_unit_id(target);
  // Isolate this learned ability from other innate/prioritized choices.
  game_load_functions f(g_ui->player.st());for(auto& t:f.game_st.tech_types.vec)if(t.id!=c.tech)f.game_st.tech_available[1][t.id]=false;
  if(c.tech==T::Feedback)target->energy=fp8::integer(150);
  if(c.tech==T::Parasite)target->detected_flags=255;
  fp8 energy=u->energy,hp=target->hp;
  // The scheduled combat manager must choose and execute the learned ability.
  check(wait([&]{auto* v=g_ui->get_unit(id);return u->energy<energy-fp8::integer(10)&&(!v||g_ui->unit_dying(v)||v->owner==1||v->hp<hp||v->lockdown_timer||v->irradiate_timer||v->parasite_flags||v->blinded_by);},600),"Targeted spell failed to resolve its actual effect");
  std::cout<<"PASS target spell "<<int(c.tech)<<" actual energy/effect\n";
 }
}
static void areas(){
 struct Test{U caster;T tech;O order;U target;};
 Test cases[]={
 {U::Terran_Science_Vessel,T::EMP_Shockwave,O::CastEMPShockwave,U::Protoss_Zealot},
 {U::Zerg_Defiler,T::Plague,O::CastPlague,U::Terran_Marine},
 {U::Zerg_Queen,T::Ensnare,O::CastEnsnare,U::Terran_Marine},
 {U::Protoss_Arbiter,T::Stasis_Field,O::CastStasisField,U::Terran_Marine},
 {U::Protoss_Dark_Archon,T::Maelstrom,O::CastMaelstrom,U::Terran_Marine},
 {U::Protoss_Corsair,T::Disruption_Web,O::CastDisruptionWeb,U::Terran_Marine}
 };
 for(auto c:cases){
  reset();auto* u=caster(c.caster);enable(c.tech);auto* target=unit(c.target,3,{1360,3284});unit(c.target,3,{1360,3316});
  game_load_functions f(g_ui->player.st());for(auto& t:f.game_st.tech_types.vec)if(t.id!=c.tech)f.game_st.tech_available[1][t.id]=false;
  fp8 energy=u->energy,shields=target->shield_points;
  check(wait([&]{if(u->energy>=energy-fp8::integer(20))return false;if(c.tech==T::Disruption_Web){for(auto* v:ptr(g_ui->st.player_units[11]))if(g_ui->unit_is(v,U::Spell_Disruption_Web))return true;return false;}
   return target->shield_points<shields||target->plague_timer||target->ensnare_timer||target->stasis_timer||target->maelstrom_timer;}),"Area spell failed to resolve its actual effect");
  if(c.tech==T::Disruption_Web){
   check(wait([&]{return g_ui->u_cannot_attack(target);},24),"Web did not disable targets");u->energy=fp8::integer(200);
   check(!g_campaign->ai_area_spell(u,O::CastDisruptionWeb),"AI recast Web on already-webbed targets");
  }
  std::cout<<"PASS area spell "<<int(c.tech)<<" actual energy/effect\n";
 }
}
static void support(){
 for(T tech:{T::Defensive_Matrix,T::Restoration,T::Dark_Swarm,T::Consume,T::Stim_Packs,T::Cloaking_Field}){
  reset();U type=tech==T::Defensive_Matrix?U::Terran_Science_Vessel:tech==T::Restoration?U::Terran_Medic:tech==T::Stim_Packs?U::Terran_Marine:tech==T::Cloaking_Field?U::Terran_Wraith:U::Zerg_Defiler;
  auto* u=caster(type);enable(tech);game_load_functions f(g_ui->player.st());
  for(auto& t:f.game_st.tech_types.vec)if(t.id!=tech)f.game_st.tech_available[1][t.id]=false;
  unit_t* ally=nullptr;
  if(tech==T::Defensive_Matrix||tech==T::Restoration){ally=unit(U::Terran_Goliath,1,{1312,3300});g_ui->set_unit_hp(ally,fp8::integer(50));}
  if(tech==T::Restoration)g_ui->lockdown_unit(ally);
  if(tech==T::Dark_Swarm)ally=unit(U::Zerg_Zergling,1,{1344,3300});
  if(tech==T::Consume){u->energy=0_fp8;ally=unit(U::Zerg_Zergling,1,{1248,3300});g_campaign->towns[1].attackers.push_back(g_ui->get_unit_id(ally));}
  if(tech!=T::Restoration&&tech!=T::Consume)unit(U::Terran_Marine,3,{1392,3300});
  check(wait([&]{switch(tech){
   case T::Defensive_Matrix:return ally->defensive_matrix_timer>0;
   case T::Restoration:return !ally->lockdown_timer;
   case T::Dark_Swarm:for(auto* v:ptr(g_ui->st.player_units[11]))if(g_ui->unit_is(v,U::Spell_Dark_Swarm))return true;return false;
   case T::Consume:return g_ui->unit_dying(ally)&&u->energy>=fp8::integer(50);
   case T::Stim_Packs:return u->stim_timer>0;
   case T::Cloaking_Field:return g_ui->u_requires_detector(u);
   default:return false;
  }},600),"Support ability failed to resolve");
  std::cout<<"PASS support ability "<<int(tech)<<" actual effect\n";
 }
}
static void safety(){
 reset();auto* u=caster(U::Protoss_High_Templar);auto* a=unit(U::Terran_Marine,3,{1360,3284});auto* b=unit(U::Terran_Marine,3,{1360,3316});
 enable(T::Psionic_Storm);g_ui->st.tech_researched[1][T::Psionic_Storm]=false;g_campaign->ai_combat_abilities(1);check(u->order_type->id==O::HoldPosition,"Unresearched spell issued");
 enable(T::Psionic_Storm);
 game_load_functions rules(g_ui->player.st());rules.game_st.tech_available[1][T::Psionic_Storm]=false;
 g_campaign->ai_combat_abilities(1);check(u->order_type->id==O::HoldPosition,"Unavailable map tech issued");rules.game_st.tech_available[1][T::Psionic_Storm]=true;
 int human=g_ui->my_player;g_ui->my_player=1;g_campaign->ai_combat_abilities(1);check(u->order_type->id==O::HoldPosition,"AI controlled human owner");g_ui->my_player=human;
 u->energy=fp8::integer(50);g_campaign->ai_combat_abilities(1);check(u->order_type->id==O::HoldPosition,"Unaffordable spell issued");u->energy=fp8::integer(250);
 a->sprite->visibility_flags=b->sprite->visibility_flags=0;g_campaign->ai_combat_abilities(1);check(u->order_type->id==O::HoldPosition,"Unseen enemies targeted");a->sprite->visibility_flags=b->sprite->visibility_flags=255;
 auto* ally=unit(U::Terran_Marine,1,{1344,3300});g_campaign->ai_combat_abilities(1);check(u->order_type->id==O::HoldPosition,"Friendly-heavy Storm chosen");g_ui->kill_unit(ally);
 g_ui->issue_order(u,false,g_ui->get_order_type(O::Move),{{1100,3300},nullptr});g_campaign->ai_combat_abilities(1);check(u->order_type->id==O::Move,"Scripted Move interrupted");
 g_ui->issue_order(u,false,g_ui->get_order_type(O::HoldPosition),{});g_campaign->units_paused=true;g_campaign->ai_combat_abilities(1);check(u->order_type->id==O::HoldPosition,"Paused scene changed");g_campaign->units_paused=false;
 g_campaign->ai_combat_abilities(1);check(u->order_type->id==O::CastPsionicStorm,"Valid caster failed after restrictions removed");auto pos=u->order_target.pos;
 auto* second=unit(U::Protoss_High_Templar,1,{1200,3364});second->energy=fp8::integer(250);g_campaign->ai_combat_abilities(1);check(second->order_type->id!=O::CastPsionicStorm,"Duplicate Storm reserved same group");
 g_campaign->ai_combat_abilities(1);check(u->order_type->id==O::CastPsionicStorm&&u->order_target.pos==pos,"In-progress cast restarted");
 g_campaign->ai_attack(1,true);check(u->order_type->id==O::CastPsionicStorm&&u->order_target.pos==pos,"Army enrollment interrupted spell");
 auto snapshot=save_game();advance(100);auto future=save_game();restore_game(snapshot);advance(100);check(save_game()==future,"Combat ability save continuation diverged");
 std::cout<<"PASS research/permission/energy/fog/friendly-fire/human-owner gates, scene/script preservation, duplicate reservation, army enrollment, stable casting and deterministic save/load\n";
}
int main(int argc,char**argv){try{
 std::cout.setf(std::ios::unitbuf);check(argc==3,"native-abilities79 CORE_DIR BROODWAR_MPQ");std::string p=argv[1];open_archive(0,p+"/STARDAT.MPQ");open_archive(1,p+"/BROODAT.MPQ");open_archive(2,p+"/patch_rt.mpq");setup(argv[2]);storms();targeted();areas();support();safety();close_game();return 0;
}catch(const std::exception& e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
