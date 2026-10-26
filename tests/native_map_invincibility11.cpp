#include "../native/runtime.cpp"
#include <iostream>
#include <stdexcept>
using namespace bwgame;
static int checks=0;
static void check(bool v,const char* m){++checks;if(!v)throw std::runtime_error(m);}
static void setup(int race=1){int races[]={race,1,2,1,1,1,1,1},controllers[]={1,0,0,0,0,0,0,0};configured_init(640,480,0,races,controllers,0,true,false,false);}
static unit_t* add(UnitTypes type,xy p,int owner){
 auto* ut=g_ui->get_unit_type(type);
 if(!g_ui->ut_flyer(ut)){
  bool found=false;xy best{};int distance=100000;
  for(int y=-256;y<=256;y+=16)for(int x=-256;x<=256;x+=16){xy candidate=p+xy(x,y);int d=x*x+y*y;if(d>=distance||!g_ui->unit_type_can_fit_at(ut,candidate))continue;
   bool occupied=false;for(auto* other:ptr(g_ui->st.visible_units))if(!g_ui->u_flying(other)&&g_ui->xy_length(other->position-candidate)<80)occupied=true;
   if(!occupied){best=candidate;distance=d;found=true;}
  }
  check(found,"No free terrain for fixture");p=best;
 }
 auto* u=g_ui->create_initial_unit(ut,p,owner);check(u!=nullptr,"Fixture unit creation failed");return u;
}
static void select(unit_t* u){uint16_t id=g_ui->get_unit_id(u).raw_value;g_ui->cmds.select(&id,1);}
static void properties(){
 setup();int innate=0;
 for(int id=0;id<228;id++){
  unit_t u{};u.unit_type=g_ui->get_unit_type((UnitTypes)id);
  g_ui->apply_map_unit_flags(&u,16,0);check(g_ui->u_status_flag(&u,unit_t::status_flag_invincible)==g_ui->ut_invincible(&u),"Unchecked CHK property differs from original DAT default");
  if(g_ui->ut_invincible(&u))++innate;
  g_ui->apply_map_unit_flags(&u,16,16);check(g_ui->u_status_flag(&u,unit_t::status_flag_invincible),"Explicit map protection was ignored");
  g_ui->apply_map_unit_flags(&u,0,0);check(g_ui->u_status_flag(&u,unit_t::status_flag_invincible),"Invalid property changed unit state");
 }
 check(innate>20,"Original DAT invincibility flags missing");
 for(int id:{128,129,173,176,177,178,188,191,192,193,194,195,196,197,198,199,202,204,205,206,207,208,215,216,217,218,219})check(g_ui->ut_invincible(g_ui->get_unit_type((UnitTypes)id)),"Audited original protected object lacks DAT flag");
 for(int id:{110,145,149,157,174,175,189,190,200,201,203,209,210,211,212,213,220,221,222,223,224,225,226,227})check(!g_ui->ut_invincible(g_ui->get_unit_type((UnitTypes)id)),"Destructible objective/refinery/resource pickup unexpectedly protected");
 std::cout<<"PASS all228 DAT defaults; innate types="<<innate<<"; explicit map protection retained; refineries/destructible objectives remain normal\n";
}
static void combat(){
 setup();std::vector<unit_t*> resources;
 for(auto* u:ptr(g_ui->st.visible_units))if(g_ui->unit_is_mineral_field(u)||g_ui->unit_is(u,UnitTypes::Resource_Vespene_Geyser)){check(g_ui->u_invincible(u),"Map loader stripped resource invincibility");resources.push_back(u);}
 check(resources.size()>10,"Map resource fixture absent");
 auto* target=resources.front();auto origin=target->position;
 auto* muta=add(UnitTypes::Zerg_Mutalisk,origin+xy(0,96),0);
 auto* melee=add(UnitTypes::Terran_SCV,origin+xy(0,48),0);
 for(auto* u:resources){check(!g_ui->unit_can_attack_target(muta,u),"Mutalisk may attack resource");check(!g_ui->unit_can_attack_target(melee,u),"Worker may attack resource");check(!g_ui->weapon_can_target_unit(g_ui->get_weapon_type(WeaponTypes::Psionic_Storm),u),"Storm may target resource");}
 auto hp=target->hp;auto shields=target->shield_points;auto count=target->building.resource.resource_count;
 select(muta);g_ui->cmds.order(Orders::AttackUnit,target->position,g_ui->get_unit_id(target).raw_value,false);
 for(int i=0;i<120;i++)native_step();check(target->hp==hp&&target->shield_points==shields&&target->building.resource.resource_count==count,"Direct attack changed protected resource");
 select(muta);g_ui->cmds.default_order(target->position,g_ui->get_unit_id(target).raw_value,false);
 for(int i=0;i<120;i++)native_step();check(target->hp==hp,"Right-click damaged protected resource");
 select(melee);g_ui->cmds.order(Orders::AttackUnit,target->position,g_ui->get_unit_id(target).raw_value,false);
 for(int i=0;i<120;i++)native_step();check(target->hp==hp&&target->building.resource.resource_count==count,"Worker attack damaged protected resource");
 auto* weapon=g_ui->get_weapon_type(WeaponTypes::Arclite_Shock_Cannon);
 g_ui->weapon_deal_damage(weapon,fp8::integer(1000),1,target,0_dir,muta,0);check(target->hp==hp,"Direct damage bypassed protection");
 bullet_t b{};sprite_t sprite{};sprite.position=target->position;b.sprite=&sprite;b.owner=0;b.weapon_type=weapon;b.bullet_owner_unit=muta;
 g_ui->bullet_deal_splash_damage<false>(&b);check(target->hp==hp,"Splash damaged protected resource");
 // Put valid air targets directly beside the field so real glaives can bounce
 // without relying on ground placement or a synthetic bullet state.
 auto* enemy=add(UnitTypes::Zerg_Mutalisk,origin+xy(16,0),1);auto enemyId=g_ui->get_unit_id(enemy);auto enemyHp=enemy->hp;
 auto* bounceEnemy=add(UnitTypes::Zerg_Mutalisk,origin-xy(16,0),1);auto bounceId=g_ui->get_unit_id(bounceEnemy);auto bounceHp=bounceEnemy->hp;
 g_ui->st.shared_vision[1]|=1;g_ui->st.alliances[1][0]=1;
 select(muta);g_ui->cmds.order(Orders::AttackUnit,enemy->position,enemyId.raw_value,false);
 bool hit=false,bounced=false;
 for(int i=0;i<360;i++){
  native_step();auto* live=g_ui->get_unit(enemyId);if(!live||live->hp<enemyHp)hit=true;
  for(auto* bullet:ptr(g_ui->st.active_bullets))if(bullet->bullet_owner_unit==muta&&bullet->bullet_target){
   check(!g_ui->u_invincible(bullet->bullet_target),"Glaive bounced onto protected object");
   if(bullet->prev_bounce_unit&&bullet->bullet_target!=bullet->prev_bounce_unit)bounced=true;
  }
 }
 check(hit,"Valid enemy was not attacked");check(bounced,"No live glaive bounce was exercised");
 auto* bounceLive=g_ui->get_unit(bounceId);check(!bounceLive||bounceLive->hp<bounceHp,"Glaive did not damage second valid enemy");
 check(target->hp==hp,"Glaive damaged resource while attacking nearby enemies");
 // Original campaign crystals and carryable objectives use the same protection.
 int n=0;for(int id:{128,129,173,215,216,217,218,219}){
  auto* u=add((UnitTypes)id,{896+(n%4)*128,896+(n/4)*128},11);++n;g_ui->apply_map_unit_flags(u,16,0);
  auto before=u->hp;check(g_ui->u_invincible(u)&&!g_ui->unit_can_attack_target(muta,u),"Campaign crystal/powerup attackable");g_ui->weapon_deal_damage(weapon,fp8::integer(1000),1,u,0_dir,muta,0);check(u->hp==before,"Campaign crystal/powerup damaged");
 }
 auto* building=add(UnitTypes::Terran_Supply_Depot,{640,640},1);check(g_ui->unit_can_attack_target(muta,building),"Ordinary building made unattackable");g_ui->apply_map_unit_flags(building,16,16);check(!g_ui->unit_can_attack_target(muta,building),"Map-protected building attackable");g_ui->u_set_status_flag(building,unit_t::status_flag_invincible,false);check(g_ui->unit_can_attack_target(muta,building),"Runtime trigger removal of protection broken");
 for(auto type:{UnitTypes::Terran_Refinery,UnitTypes::Zerg_Extractor,UnitTypes::Protoss_Assimilator,UnitTypes::Special_Power_Generator,UnitTypes::Critter_Rhynadon}){auto* u=add(type,{1536,1536},1);g_ui->apply_map_unit_flags(u,16,0);check(!g_ui->u_invincible(u)&&g_ui->unit_can_attack_target(muta,u),"Refinery, destructible objective or critter made unattackable");}
 std::cout<<"PASS map resources, direct/right-click attacks, live glaive bounce, damage/splash guards, crystals, normal enemy, refineries, destructible objectives, critter and trigger-controlled building\n";
}
static void mining(){for(int race=0;race<3;race++){
 setup(race);unit_t* worker=nullptr;for(auto* u:ptr(g_ui->st.player_units[0]))if(g_ui->ut_worker(u)){worker=u;break;}check(worker!=nullptr,"Worker absent");
 unit_t* mineral=nullptr;int nearest=100000;for(auto* u:ptr(g_ui->st.visible_units))if(g_ui->unit_is_mineral_field(u)){int d=g_ui->xy_length(worker->position-u->position);if(d<nearest){nearest=d;mineral=u;}}
 check(mineral&&g_ui->u_invincible(mineral),"Protected harvest target absent");int before=mineral->building.resource.resource_count;select(worker);g_ui->cmds.default_order(mineral->position,g_ui->get_unit_id(mineral).raw_value,false);
 for(int i=0;i<700;i++)native_step();check(mineral->building.resource.resource_count<before,"Resource invincibility prevented mining");
 }std::cout<<"PASS SCV,Drone,Probe harvest protected mineral fields\n";}
int main(int argc,char**argv){try{check(argc==2,"Usage: test CORE_DIR");std::string core=argv[1];open_archive(0,core+"/STARDAT.MPQ");open_archive(1,core+"/BROODAT.MPQ");open_archive(2,core+"/patch_rt.mpq");open_archive(3,"app/src/main/assets/native/weave.scx");properties();combat();mining();close_game();std::cout<<"PASS "<<checks<<" map-invincibility checks\n";return 0;}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
