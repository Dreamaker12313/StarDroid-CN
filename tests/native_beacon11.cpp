// Real command-stream tests: no copyrighted data bundled in the fixture.
#include "../native/runtime.cpp"
#include <iostream>
using namespace bwgame;using U=UnitTypes;
static int checks=0;
static void check(bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);}
static unit_t* room(U type,int owner,xy around){
 auto* ut=g_ui->get_unit_type(type);
 for(int radius=0;radius<30;radius++)for(int y=-radius;y<=radius;y++)for(int x=-radius;x<=radius;x++){
  xy p=around+xy(x*32,y*32);if(!g_ui->unit_type_can_fit_at(ut,p))continue;
  bool free=true;for(auto* u:g_ui->find_units(g_ui->square_at(p,96)))if(!g_ui->unit_dying(u))free=false;
  if(free)if(auto* u=g_ui->create_initial_unit(ut,p,owner))return u;
 }throw std::runtime_error("No clear fixture position");
}
static void select(std::initializer_list<unit_t*> units){g_ui->current_selection_clear();for(auto*u:units)g_ui->current_selection_add(u);g_ui->on_selection(false);g_ui->refresh_card();g_ui->outgoing.clear();}
static xy focus(unit_t* u){g_ui->screen_pos=u->sprite->position-xy(320,160);g_ui->view_scale=fp16::integer(1);return {320,160};}
static int u16(const uint8_t* p){return p[0]|p[1]<<8;}
static void check_move(xy destination,bool queued){
 int moves=0;auto& raw=g_ui->outgoing;
 for(size_t p=0;p<raw.size();){check(p+2<=raw.size(),"Truncated frame");size_t n=u16(raw.data()+p);p+=2;check(n&&p+n<=raw.size(),"Truncated command");const auto* b=raw.data()+p;
  if(b[0]==21){++moves;check(n==11,"Invalid order length");check(u16(b+1)==destination.x&&u16(b+3)==destination.y,"Move missed beacon center");check(u16(b+5)==0,"Beacon became a Follow/unit target");check(b[9]==int(Orders::Move)&&b[10]==queued,"Wrong order or Shift queue flag");}
  else check(b[0]==9,"Unexpected command alongside beacon Move");p+=n;
 }check(moves==1,"Beacon tap must emit one Move");
}
int main(int argc,char**argv){try{
 check(argc==2,"Usage: beacon11 CORE");std::string core=argv[1];open_archive(0,core+"/STARDAT.MPQ");open_archive(1,core+"/BROODAT.MPQ");open_archive(2,core+"/patch_rt.mpq");open_archive(3,"app/src/main/assets/native/weave.scx");
 int races[]={1,0,2,1,1,1,1,1},slots[]={1,0,0,0,0,0,0,0};configured_init(640,480,0,races,slots,0,true,false,false);openbw_set_external_cursor(1);g_ui->fog_player=-1;g_ui->host_controls_edge_scroll=true;
 auto* worker=room(U::Terran_SCV,0,{640,640});auto* combat=room(U::Terran_Marine,0,{800,640});auto* civilian=room(U::Terran_Civilian,0,{960,640});
 unit_t* beacon=nullptr;
 for(int type=int(U::Special_Zerg_Beacon);type<=int(U::Special_Protoss_Flag_Beacon);++type){
  beacon=room(U(type),0,{1024,1024});auto p=focus(beacon);check(g_ui->select_get_unit_at(beacon->sprite->position)==beacon,"Beacon center not hittable");
  for(int owner:{0,1,11}){g_ui->set_unit_owner(beacon,owner,false);
   for(auto* selected:{worker,combat,civilian}){
    select({selected});auto before=g_ui->current_selection;command(4,p.x,p.y,0,0);check(g_ui->current_selection==before,"Beacon stole mobile selection");check_move(beacon->sprite->position,false);check(g_ui->marker_pos==beacon->sprite->position,"Move marker not at beacon center");
    auto input=std::move(g_ui->outgoing);g_ui->outgoing.clear();g_ui->apply_commands(0,input.data(),input.size());check(selected->order_type->id==Orders::Move&&selected->order_target.pos==beacon->sprite->position&&!selected->order_target.unit,"Applied command not a ground Move");
   }
  }
  // Reuse space without accumulating clickable beacon sprites.
  if(type<int(U::Special_Protoss_Flag_Beacon)){g_ui->kill_unit(beacon);for(int i=0;i<10;i++)native_step();}
 }
 std::cout<<"PASS all six beacon types, owned/enemy/neutral ownership, SCV/Marine/Civilian; selection retained and actual center Move applied\n";
 auto p=focus(beacon);select({worker,combat});auto before=g_ui->current_selection;
 openbw_key(1,0,225);command(4,p.x,p.y,0,0);openbw_key(0,0,225);check_move(beacon->sprite->position,true);check(g_ui->current_selection==before,"Group selection changed");
 std::cout<<"PASS grouped units and Shift queued Move\n";
 // No owned mobile selection: retain ordinary inspection behavior.
 select({});command(4,p.x,p.y,0,0);openbw_render(1000);check(g_ui->current_selection.size()==1&&g_ui->get_unit(g_ui->current_selection.front())==beacon,"Empty-selection tap did not select beacon");check(g_ui->outgoing.empty(),"Inspecting beacon emitted an order");
 select({worker});command(4,p.x,p.y,0,1);openbw_render(1010);check(g_ui->current_selection.size()==1&&g_ui->get_unit(g_ui->current_selection.front())==beacon,"Explicit select gesture did not inspect beacon");check(g_ui->outgoing.empty(),"Explicit select gesture issued Move");
 auto* enemy=room(U::Terran_Marine,1,{1280,800});select({enemy});check(!touch_beacon_move(p.x,p.y)&&g_ui->outgoing.empty(),"Enemy selection issued beacon Move");
 auto* building=room(U::Terran_Supply_Depot,0,{1280,1200});select({building});check(!touch_beacon_move(p.x,p.y)&&g_ui->outgoing.empty(),"Immobile building issued beacon Move");
 select({worker});native_replay::active=true;command(4,p.x,p.y,0,0);openbw_render(1015);native_replay::active=false;check(g_ui->outgoing.empty()&&g_ui->current_selection.size()==1&&g_ui->get_unit(g_ui->current_selection.front())==beacon,"Replay tap issued Move instead of inspecting");
 std::cout<<"PASS no-selection, explicit/replay selection-only inspection, enemy selection, immobile building\n";
 select({worker});
 for(int state=0;state<5;state++){
  g_ui->paused=state==0;g_ui->campaign_control_lock=state==1;g_ui->spectator=state==2;g_ui->pending_build=state==3?g_ui->get_unit_type(U::Terran_Supply_Depot):nullptr;g_ui->targeting=state==4;
  check(!touch_beacon_move(p.x,p.y)&&g_ui->outgoing.empty(),"Beacon shortcut bypassed input/targeting guard");
 }
 g_ui->paused=false;g_ui->campaign_control_lock=false;g_ui->spectator=false;g_ui->pending_build=nullptr;g_ui->targeting=false;
 g_ui->fog_player=0;beacon->sprite->visibility_flags=0;auto& tile=g_ui->st.tiles[(beacon->sprite->position.y/32)*g_ui->game_st.map_tile_width+beacon->sprite->position.x/32];auto visible=tile.visible,explored=tile.explored;tile.visible|=1;tile.explored|=1;
 check(g_ui->unit_hidden_by_fog(beacon),"Fog fixture not actually hidden");check(!touch_beacon_move(p.x,p.y)&&g_ui->outgoing.empty(),"Hidden beacon leaked through fog");tile.visible=visible;tile.explored=explored;g_ui->fog_player=-1;
 // Explicit orders must keep their original semantics instead of becoming Move.
 for(auto mode:{play_ui::T_ATTACK,play_ui::T_SPELL}){
  select({combat});g_ui->start_target(mode);g_ui->pending_spell_order=Orders::CastPsionicStorm;g_ui->pending_spell_unit=false;command(4,p.x,p.y,0,0);openbw_render(1020);
  bool found=false;auto& raw=g_ui->outgoing;for(size_t at=0;at<raw.size();){int n=u16(raw.data()+at);at+=2;if(raw[at]==21){check(raw[at+9]==int(mode==play_ui::T_ATTACK?Orders::AttackDefault:Orders::CastPsionicStorm),"Explicit targeting was rewritten to Move");found=true;}at+=n;}
  check(found&&!g_ui->targeting,"Explicit targeting failed to run");
 }
 std::cout<<"PASS explicit Attack and spell target commands retain their order types\n";
 auto other=focus(combat);select({worker});check(!touch_beacon_move(other.x,other.y)&&g_ui->outgoing.empty(),"Normal unit intercepted as beacon");command(4,other.x,other.y,0,0);openbw_render(1020);check(g_ui->current_selection.size()==1&&g_ui->get_unit(g_ui->current_selection.front())==combat,"Normal owned-unit selection changed");
 std::cout<<"PASS pause/control lock/spectator/build/target/fog guards and ordinary unit selection\nPASS "<<checks<<" beacon checks\n";close_game();return 0;
}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
