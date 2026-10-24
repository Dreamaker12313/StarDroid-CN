// Original-data regressions: airborne mission arrival, physically hidden traps,
// computer tank stance, and an original-script Terran skirmish economy/attack.
#include "../native/runtime.cpp"
#include <fstream>
#include <iostream>
using namespace bwgame;
static void require(bool v,const char* s){if(!v)throw std::runtime_error(s);}
static void advance(int n){for(int i=0;i<n&&!g_ui->outcome;i++)native_step();}
static unit_t* unit(int type,int owner){for(auto* u:ptr(g_ui->st.player_units[owner]))if(int(u->unit_type->id)==type&&!g_ui->unit_dying(u))return u;return nullptr;}
static void snapshot(){
 openbw_render(openbw_frame()*42.);
 auto saved=save_game();advance(240);auto expected=save_game();
 restore_game(saved);auto restored=save_game();
 auto dump=[](const char* name,const std::vector<uint8_t>& bytes){std::ofstream out(std::string("build-native/")+name,std::ios::binary);out.write((const char*)bytes.data(),bytes.size());};
 if(restored!=saved){dump("revision40-before.bin",saved);dump("revision40-restored.bin",restored);}
 require(restored==saved,"Immediate snapshot round trip differs");
 advance(240);auto actual=save_game();
 if(actual!=expected){dump("revision40-expected.bin",expected);dump("revision40-actual.bin",actual);}
 require(actual==expected,"Snapshot continuation differs");
 if(g_campaign&&g_campaign->melee_ai){
  close_game();openbw_init_terran_ai(640,480,1,1);restore_game(saved);
  require(save_game()==saved,"Fresh Terran setup round trip differs");
  advance(240);require(save_game()==expected,"Fresh Terran setup continuation differs");
 }
}
static void viewport(){
 openbw_init(640,480,1,0);
 for(auto size:{xy(640,480),xy(1280,960),xy(960,480),xy(427,320)}){
  openbw_resize(size.x,size.y);int inset=(104*size.y+240)/480;command(21,inset,0,0,0);
  openbw_pan(65536,65536);openbw_render(0);
  require(int(g_ui->camera_height())==size.y-inset,"Map height does not match center console");
  require(g_ui->screen_pos.y+int(g_ui->camera_height())==int(g_ui->game_st.map_height),"Bottom map clamp differs from center console");
 }
 std::cout<<"PASS camera boundary: classic, widescreen, zoom out, zoom in\n";
}
static void mission(){
 openbw_init_campaign(640,480,406);int seen=0,transferred=0;bool sieged=false;
 for(int f=0;f<6000&&!g_ui->outcome;f++){
  native_step();
  for(int p:{2,3,6})for(auto* u:ptr(g_ui->st.player_units[p])){
   int t=int(u->unit_type->id);
   if(t==30)sieged=true;
   const int ids[]={106,111,113,114,122};
   for(int k=0;k<5;k++)if(t==ids[k]&&!g_ui->unit_dying(u)){
    require(g_ui->u_flying(u),"Reinforcement building not airborne");seen|=1<<k;
    if(p==6){transferred|=1<<k;require(u->position.x<1600&&u->position.y>2400,"Base not in southwest");}
   }
  }
  if(f%1000==0)std::cout<<"MISSION frame "<<f<<" seen "<<seen<<" given "<<transferred<<" siege "<<sieged<<"\n";
 }
 require(seen==31,"Not all five original buildings spawned");
 require(transferred==31,"Not all five original buildings handed to player");
 require(sieged,"Opening computer tanks never used siege mode");
 require(g_campaign->ai_error.empty(),g_campaign->ai_error.c_str());snapshot();
 std::cout<<"PASS Emperor's Flight: five flying buildings arrive and transfer; opening tanks siege; deterministic save\n";
}
static void traps(){
 for(auto trapid:{UnitTypes::Special_Floor_Missile_Trap,UnitTypes::Special_Floor_Gun_Trap,UnitTypes::Special_Wall_Missile_Trap,UnitTypes::Special_Wall_Flame_Trap,UnitTypes::Special_Right_Wall_Missile_Trap,UnitTypes::Special_Right_Wall_Flame_Trap}){
  int type=int(trapid);
  xy approach=type>=212?xy(-32,0):xy(32,0);
  openbw_init(640,480,1,0);g_ui->competitive=false;
  g_ui->st.players[1].controller=player_t::controller_computer_game;
  xy p;bool found=false;
  auto* traptype=g_ui->get_unit_type(UnitTypes(type));
  auto* marine=g_ui->get_unit_type(UnitTypes::Terran_Marine);
  for(int y=256;y<1700&&!found;y+=64)for(int x=256;x<1700&&!found;x+=64){
   xy at{x,y};if(!g_ui->unit_type_can_fit_at(traptype,at)||!g_ui->unit_type_can_fit_at(marine,at+approach))continue;
   bool free=true;for(auto* u:g_ui->find_units(g_ui->square_at(at,240)))if(!g_ui->unit_dying(u))free=false;
   if(free){p=at;found=true;}
  }
  require(found,"No free terrain for trap fixture");
  auto* trap=g_ui->create_initial_unit(g_ui->get_unit_type(UnitTypes(type)),p,1);require(trap,"Trap missing");
  g_ui->fog_player=-1;
  for(int f=0;f<90;f++){native_step();require(g_ui->unit_hidden_by_fog(trap),"Closed trap visible before activation");}
  require(trap->order_type->id==Orders::HiddenGun,"Trap not waiting in HiddenGun");
  g_ui->screen_pos=p-xy(320,240);g_ui->clamp_viewport();openbw_render(0);
  auto* pixels=openbw_framebuffer();size_t bytes=size_t(openbw_framebuffer_width())*openbw_framebuffer_height()*4;
  std::vector<uint8_t> closed(pixels,pixels+bytes);
  std::vector<std::pair<image_t*,unsigned>> flags;
  for(auto* im:ptr(trap->sprite->images)){flags.push_back({im,im->flags});im->flags|=image_t::flag_hidden;}
  openbw_render(0);require(std::equal(closed.begin(),closed.end(),openbw_framebuffer()),"Closed trap artwork rendered with map reveal");
  for(auto entry:flags)entry.first->flags=entry.second;
  auto* target=g_ui->create_initial_unit(g_ui->get_unit_type(UnitTypes::Terran_Marine),p+approach,0);require(target,"Trap target missing");
  target->hp=10000_fp8;target->lockdown_timer=1000;bool opening=false,attacking=false;
  for(int f=0;f<300;f++){native_step();if(trap->order_type->id==Orders::RevealTrap){opening=true;require(!g_ui->unit_hidden_by_fog(trap),"Opening trap still invisible");}if(target->hp<10000_fp8)attacking=true;}
  std::cout<<"TRAP "<<type<<" opening="<<opening<<" damage="<<attacking<<" order="<<int(trap->order_type->id)<<"\n";
  require(opening&&attacking,"Trap failed to open and deal damage");close_game();
 }
 std::cout<<"PASS six trap types: hidden for 90 frames, opening visible, real weapon damage\n";
}
static void skirmish(){
 openbw_init_terran_ai(640,480,1,1);g_ui->competitive=false;
 // Keep the passive test player alive while the opponent runs its real economy.
 for(auto* u:ptr(g_ui->st.player_units[0]))g_ui->set_unit_hp(u,u->unit_type->hitpoints);
 require(g_ui->st.current_minerals[1]==50&&g_ui->st.current_gas[1]==0,"Nonstandard starting resources");
 bool combat=false;
 for(int f=0;f<60000;f++){
  native_step();require(g_campaign->ai_error.empty(),g_campaign->ai_error.c_str());
  for(auto* u:ptr(g_ui->st.player_units[0]))if(!g_ui->unit_dying(u)){if(u->hp<u->unit_type->hitpoints)combat=true;g_ui->set_unit_hp(u,u->unit_type->hitpoints);}
  if(f%3000==0){std::cout<<"AI "<<f<<" "<<g_campaign->ai_status();for(auto& r:g_campaign->towns[1].builds)std::cout<<r.type<<":"<<g_campaign->ai_count(1,r.type)<<"/"<<r.amount<<" ";std::cout<<"\n";}
 }
 for(auto* u:ptr(g_ui->st.player_units[1]))std::cout<<"UNIT "<<int(u->unit_type->id)<<" complete="<<g_ui->u_completed(u)<<" order="<<int(u->order_type->id)<<" state="<<u->order_state<<" pos="<<u->position.x<<","<<u->position.y<<" build="<<(u->current_build_unit?int(u->current_build_unit->unit_type->id):-1)<<" queue="<<u->build_queue.size()<<" attacker="<<g_campaign->ai_attacking(g_campaign->towns[1],u)<<"\n";
 std::cout<<"SUPPLY "<<g_ui->st.supply_used[1][1].raw_value<<"/"<<g_ui->st.supply_available[1][1].raw_value<<"\n";
 for(int i=0;i<228;i++)if(g_campaign->towns[1].wave[i])std::cout<<"WAVE "<<i<<" want="<<g_campaign->towns[1].wave[i]<<" defense="<<g_campaign->towns[1].defence[i]<<" home="<<g_campaign->ai_count(1,i,true,true)<<"\n";
 require(g_ui->st.total_minerals_gathered[1]>1000,"Terran did not mine minerals");
 require(g_ui->st.total_gas_gathered[1]>100,"Terran did not mine gas");
 require(unit(111,1)&&unit(113,1)&&unit(114,1),"Terran did not build production tech");
 require(g_campaign->towns[1].attacks>=5,"Terran did not launch repeated attacks");
 require(unit(120,1),"Terran did not build Machine Shop");
 require(combat,"Terran waves never fought the player");
 snapshot();std::cout<<"PASS original TLOx Terran: normal economy, ground/air tech, repeated waves, deterministic save\n";
}
int main(int argc,char**argv){std::cout.setf(std::ios::unitbuf);try{
 require(argc>=4,"Usage: native-revision40 DATA_DIR MAP_MPQ mission|traps|skirmish");
 std::string d=argv[1];open_archive(0,d+"/STARDAT.MPQ");open_archive(1,d+"/BROODAT.MPQ");open_archive(2,d+"/patch_rt.mpq");open_archive(3,argv[2]);
 std::string mode=argv[3];if(mode=="mission")mission();else if(mode=="traps")traps();else if(mode=="skirmish")skirmish();else if(mode=="viewport")viewport();else throw std::runtime_error("Unknown case");
 close_game();return 0;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
