// Exercise the actual Android command bridge and native UI with local game data.
#include "../native/runtime.cpp"
#include <iostream>
using namespace bwgame;using U=UnitTypes;
static int checks=0;static double clock_ms=100;
static void check(bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);}
static void flush(){openbw_render(clock_ms+=20);}
static void key(int down,int sym,int scan){command(32,down,sym,scan,0);}
static void tap(int sym,int scan){key(1,sym,scan);key(0,sym,scan);}
static void move(xy p){command(0,p.x,p.y,0,0);}
static void click(xy p,int button=1,int count=1){move(p);command(33,1,button,count,0);command(33,0,button,count,0);}
static xy screen(unit_t* u){return u->sprite->position-g_ui->screen_pos;}
static bool selected(unit_t* u){return g_ui->current_selection_is_selected(u);}
static void select(std::initializer_list<unit_t*> units){g_ui->current_selection_clear();for(auto*u:units)g_ui->current_selection_add(u);g_ui->on_selection(false);g_ui->refresh_card();g_ui->outgoing.clear();}
static unit_t* room(U type,int owner,xy around){auto*ut=g_ui->get_unit_type(type);for(int r=0;r<30;r++)for(int y=-r;y<=r;y++)for(int x=-r;x<=r;x++){xy p=around+xy(x*32,y*32);if(!g_ui->unit_type_can_fit_at(ut,p))continue;bool free=true;for(auto*u:g_ui->find_units(g_ui->square_at(p,48)))if(!g_ui->unit_dying(u))free=false;if(free)if(auto*u=g_ui->create_initial_unit(ut,p,owner))return u;}throw std::runtime_error("No fixture room");}
static int u16(const uint8_t*p){return p[0]|p[1]<<8;}
static uint64_t world_hash(){std::vector<uint8_t> bytes;native_save::Codec codec(false,bytes,g_ui->st);codec.world();codec.fields(g_ui->current_action_state.selection,g_ui->current_action_state.control_groups);return native_save::hash(bytes);}
static void order(bool queued,int opcode=20){int found=0;auto&raw=g_ui->outgoing;net_validate(raw.data(),raw.size());for(size_t p=0;p<raw.size();){int n=u16(raw.data()+p);p+=2;if(raw[p]==opcode){check(raw[p+n-1]==queued,"Wrong Shift queue flag");++found;}else check(raw[p]==9,"Unexpected input command");p+=n;}check(found==1,"Expected one standard BW order");}
int main(int argc,char**argv){try{
 check(argc==2,"Usage: desktop11 CORE");std::string core=argv[1];open_archive(0,core+"/STARDAT.MPQ");open_archive(1,core+"/BROODAT.MPQ");open_archive(2,core+"/patch_rt.mpq");open_archive(3,"app/src/main/assets/native/weave.scx");
 int races[]={1,0,2,1,1,1,1,1},slots[]={1,0,0,0,0,0,0,0};configured_init(640,480,0,races,slots,0,true,false,false);g_ui->fog_player=-1;g_ui->host_controls_edge_scroll=true;g_ui->view_scale=fp16::integer(1);command(34,0,0,0,0);
 auto*a=room(U::Terran_Marine,0,{640,640});auto*b=room(U::Terran_Marine,0,{760,640});auto*c=room(U::Terran_SCV,0,{880,640});g_ui->screen_pos={400,420};flush();
 check(screen(a).x>20&&screen(c).x<620,"Fixture outside viewport");
 click(screen(a));flush();check(selected(a)&&g_ui->current_selection.size()==1,"Physical left click did not select");
 key(1,0,225);click(screen(b));key(0,0,225);flush();check(selected(a)&&selected(b)&&g_ui->current_selection.size()==2,"Same-frame Shift click lost modifier");check(!g_ui->key_shift(),"Shift release remained stuck");
 key(1,0,229);click(screen(a));key(0,0,229);flush();check(!selected(a)&&selected(b),"Right Shift did not remove selection");
 click(screen(a),1,2);flush();check(selected(a)&&selected(b)&&!selected(c),"Double-click same-type selection failed");
 select({});key(1,0,228);click(screen(a));key(0,0,228);flush();check(selected(a)&&selected(b)&&!selected(c)&&!g_ui->key_ctrl(),"Ctrl-click same-type selection failed");
 select({});xy lo{std::min(screen(a).x,screen(b).x)-20,std::min(screen(a).y,screen(b).y)-20},hi{std::max(screen(a).x,screen(b).x)+20,std::max(screen(a).y,screen(b).y)+20};move(lo);command(33,1,1,1,0);move(hi);command(33,0,1,1,0);flush();check(selected(a)&&selected(b)&&!g_ui->is_drag_selecting,"Physical drag-box selection failed");
 std::cout<<"PASS left click, held drag/release, double-click, left/right Shift add/remove, right Ctrl same-type selection in a single frame\n";
 select({a});key(1,0,224);tap('1',30);key(0,0,224);flush();check(g_ui->group_count(1)==1,"Ctrl+1 did not assign group");select({b});key(1,0,225);tap('1',30);key(0,0,225);flush();check(g_ui->group_count(1)==2,"Shift+1 did not append group");key(1,0,225);tap('1',30);key(0,0,225);flush();check(g_ui->group_count(1)==2,"Append duplicated group unit");select({});tap('1',30);flush();check(selected(a)&&selected(b),"Digit did not recall group");
 auto old=g_ui->screen_pos;tap('1',30);flush();check(g_ui->screen_pos!=old,"Repeated group recall did not center camera");g_ui->screen_pos={400,420};
 std::cout<<"PASS Ctrl assignment, Shift append/deduplicate, digit recall, double recall camera center\n";
 select({a});xy destination{screen(a).x+30,screen(a).y+70};click(destination,3);flush();order(false);auto data=g_ui->outgoing;g_ui->outgoing.clear();g_ui->apply_commands(0,data.data(),data.size());check(a->order_type->id==Orders::Move,"Right click did not apply Move");
 key(1,0,225);click(destination+xy(25,20),3);key(0,0,225);flush();order(true);g_ui->outgoing.clear();
 tap('a',4);flush();check(g_ui->targeting,"Attack hotkey did not enter targeting");click(destination);flush();order(false,21);check(!g_ui->targeting,"Attack target mode did not finish");g_ui->outgoing.clear();
 tap('a',4);flush();tap(27,41);flush();check(!g_ui->targeting&&g_ui->outgoing.empty(),"Escape did not cancel targeting locally");
 tap('a',4);flush();click(destination,3);flush();check(!g_ui->targeting&&g_ui->outgoing.empty(),"Right click did not cancel targeting locally");
 auto terrain=g_ui->minimap_terrain;tap(0,43);flush();check(g_ui->minimap_terrain!=terrain,"Tab did not change minimap terrain");g_ui->have_last_event=true;g_ui->last_event_pos={1400,1400};old=g_ui->screen_pos;tap(' ',44);flush();check(g_ui->screen_pos!=old,"Space did not center latest alert");g_ui->screen_pos={400,420};
 std::cout<<"PASS physical right Move/Shift queue, Attack hotkey+target, Escape/right cancel, Tab minimap, Space recent alert\n";
 // Focus cleanup discards queued actions and real held state, preserving a mode.
 select({a});g_ui->start_target(play_ui::T_ATTACK);key(1,0,225);move(destination);command(33,1,1,1,0);g_ui->is_drag_selecting=true;g_ui->is_dragging_screen=true;g_ui->is_moving_minimap=true;g_ui->is_moving_replay_slider=true;command(34,0,0,0,0);flush();check(!g_ui->key_shift()&&!g_ui->wnd.get_mouse_button_state(1),"Focus cleanup left held input");check(g_ui->targeting&&g_ui->outgoing.empty(),"Focus cleanup committed/cancelled target");check(!g_ui->is_drag_selecting&&!g_ui->is_dragging_screen&&!g_ui->is_moving_minimap&&!g_ui->is_moving_replay_slider,"Focus cleanup left drag state");g_ui->clear_pending();g_ui->targeting=false;
 for(int locked=0;locked<2;locked++){g_ui->paused=locked==0;g_ui->campaign_control_lock=locked==1;auto before=g_ui->current_selection;click(screen(b));click(destination,3);tap('a',4);tap('p',19);key(1,0,225);key(0,0,225);flush();check(g_ui->outgoing.empty()&&g_ui->current_selection==before&&!g_ui->targeting&&!g_ui->key_shift(),"Paused/locked input mutated gameplay");terrain=g_ui->minimap_terrain;tap(0,43);flush();check(g_ui->minimap_terrain!=terrain,"Paused view Tab was blocked");}g_ui->paused=false;g_ui->campaign_control_lock=false;
 select({});auto speed=g_ui->game_speed;auto paused=g_ui->is_paused;tap('a',4);tap('p',19);tap('u',24);tap('d',7);flush();check(g_ui->game_speed==speed&&g_ui->is_paused==paused,"Unavailable command leaked into renderer debug keys");
 std::cout<<"PASS focus reset, paused/cutscene lock, view-only shortcuts, no hidden debug hotkey fall-through\n";
 select({a});native_replay::active=true;click(destination,3);tap('a',4);tap('1',30);click(screen(b));key(1,0,224);key(0,0,224);flush();check(g_ui->outgoing.empty()&&!g_ui->targeting&&selected(b)&&!selected(a),"Replay physical input allowed gameplay or blocked inspection");terrain=g_ui->minimap_terrain;tap(0,43);flush();check(g_ui->minimap_terrain!=terrain,"Replay Tab blocked");key(1,0,225);command(34,0,0,0,0);check(!g_ui->key_shift(),"Replay reset blocked");native_replay::active=false;
 std::cout<<"PASS replay left inspection/view keys; no right orders, attack or group hotkeys; cleanup allowed\n";
 // Existing touch/gamepad operations remain usable and share their old semantics.
 g_ui->screen_pos={400,420};select({});auto p=screen(a);command(0,p.x,p.y,0,0);command(1,1,1,p.x,p.y);command(1,0,1,p.x,p.y);flush();check(selected(a),"Legacy gamepad pointer op1 broken");command(2,'a',4,0,0);flush();check(g_ui->targeting,"Legacy instantaneous key op2 broken");command(2,27,41,0,0);flush();check(!g_ui->targeting,"Legacy Escape broken");select({});p=screen(b);command(4,p.x,p.y,0,1);flush();check(selected(b),"Legacy touch selection broken");
 // The new transport emits the same validated, replay-recordable commands.
 select({a});net_active=true;auto checksum=net_hash();click(destination,3);flush();order(false);check(net_hash()==checksum,"Physical event changed multiplayer simulation before lockstep apply");data=g_ui->outgoing;g_ui->outgoing.clear();g_ui->apply_commands(0,data.data(),data.size());check(a->order_type->id==Orders::Move,"Lockstep physical input failed to apply");key(1,0,225);command(34,0,0,0,0);check(!g_ui->key_shift(),"Network reset blocked");net_active=false;
 for(int i=0;i<3;i++)native_step();auto replay=native_replay::save();auto parsed=native_replay::parse(replay.data(),replay.size());check(parsed.rules.present&&!parsed.actions.empty(),"Physical command replay did not validate");check(native_replay::ENGINE==84,"Input changed simulation version");
 std::cout<<"PASS legacy touch/gamepad ops, multiplayer command validation/deferred application, replay save+parse, unchanged simulation 84\n";
 // Replay a new, unmodified match so this also proves actual deterministic playback.
 configured_init(640,480,0,races,slots,0,true,false,false);g_ui->host_controls_edge_scroll=true;g_ui->fog_player=-1;
 unit_t* worker=nullptr;for(auto*u:ptr(g_ui->st.player_units[0]))if(g_ui->unit_is(u,U::Terran_SCV)){worker=u;break;}
 check(worker!=nullptr,"Recorded match has no SCV");g_ui->center_on(worker->position);flush();xy first=screen(worker)+xy(96,32),second=screen(worker)+xy(64,96);std::vector<uint64_t> states;
 for(int frame=0;frame<60;frame++){
  if(frame==0){click(screen(worker));flush();click(first,3);flush();}
  if(frame==10){key(1,0,225);click(second,3);key(0,0,225);flush();}
  if(frame==30){tap('s',22);flush();}
  native_step();states.push_back(world_hash());
 }
 replay=native_replay::save();check(!replay.empty(),"Desktop input recording missing");native_replay::open(replay.data(),replay.size());
 for(int frame=0;frame<60;frame++){native_step();check(world_hash()==states[frame],"Physical controls diverged during replay playback");}
 check(g_ui->outgoing.empty()&&g_ui->spectator&&g_ui->st.current_frame==60,"Replay left read-only state");
 std::cout<<"PASS 60-frame full-world deterministic replay roundtrip with physical selection, right Move, Shift queue and Stop hotkey\n";
 command(6,1,0,0,0);worker=nullptr;for(auto*u:ptr(g_ui->st.player_units[0]))if(g_ui->unit_is(u,U::Terran_SCV)){worker=u;break;}
 check(worker!=nullptr,"Paused replay has no inspectable worker");g_ui->center_on(worker->position);g_ui->host_controls_edge_scroll=true;flush();select({});auto frozen=world_hash();
 click(screen(worker));flush();check(selected(worker)&&g_ui->paused,"Paused replay single-click inspection failed");
 select({});click(screen(worker),1,2);flush();check(selected(worker)&&g_ui->current_selection.size()>1,"Paused replay same-type inspection failed");
 select({});auto point=screen(worker);move(point-xy(24,24));command(33,1,1,1,0);move(point+xy(24,24));command(33,0,1,1,0);flush();check(selected(worker),"Paused replay drag inspection failed");
 click(point+xy(96,64),3);tap('a',4);tap('s',22);tap('1',30);flush();check(g_ui->outgoing.empty()&&!g_ui->targeting&&world_hash()==frozen,"Paused replay inspection emitted gameplay or changed world");
 terrain=g_ui->minimap_terrain;tap(0,43);flush();check(g_ui->minimap_terrain!=terrain&&g_ui->paused,"Paused replay Tab view action failed");
 native_replay::seek(0);for(int i=0;native_replay::seeking&&i<5;i++)native_replay::pump_seek();check(!native_replay::seeking&&g_ui->paused,"Paused replay rewind did not preserve pause");
 worker=nullptr;for(auto*u:ptr(g_ui->st.player_units[0]))if(g_ui->unit_is(u,U::Terran_SCV)){worker=u;break;}check(worker!=nullptr,"Rewound replay has no worker");g_ui->center_on(worker->position);select({});click(screen(worker));flush();check(selected(worker)&&g_ui->outgoing.empty(),"Paused inspection lost after checkpoint restore");
 std::cout<<"PASS paused replay single/double/drag inspection, gameplay rejection, Tab, checkpoint restoration; ordinary paused matches remain blocked\nPASS "<<checks<<" native desktop checks\n";close_game();return 0;
}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
