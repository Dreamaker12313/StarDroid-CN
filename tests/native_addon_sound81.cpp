// Construction acknowledgements through real accepted BW command batches.
#include "../native/runtime.cpp"
#include <iostream>
using namespace bwgame;using U=UnitTypes;
static int checks=0;static void require(bool value,const char* why){++checks;if(!value)throw std::runtime_error(why);}
static void reset_audio(){for(size_t i=0;i<g_ui->sound_channels.size();i++){native_sound::stop(i);g_ui->sound_channels[i].playing=false;}std::fill(g_ui->last_played_sound.begin(),g_ui->last_played_sound.end(),decltype(g_ui->last_played_sound)::value_type{});}
static bool heard(int sound){for(auto& c:g_ui->sound_channels)if(c.playing&&int(c.sound_type->id)==sound)return true;return false;}
static void setup(){int races[]={1,1,1,1,1,1,1,1},slots[]={1,0,0,0,0,0,0,0};configured_init(640,480,0,races,slots,2,true,false,false);g_ui->competitive=false;g_ui->fog_player=-1;g_ui->st.current_minerals[0]=g_ui->st.current_gas[0]=10000;g_ui->st.current_minerals[1]=g_ui->st.current_gas[1]=10000;}
static unit_t* create(U type,int owner=0){auto* t=g_ui->get_unit_type(type);for(int y=6;y<int(g_ui->game_st.map_tile_height)-6;y++)for(int x=6;x<int(g_ui->game_st.map_tile_width)-6;x++){xy p=xy(x*32,y*32)+t->placement_size/2;if(g_ui->can_place_building(nullptr,owner,t,p,true,false,true))if(auto* u=g_ui->create_initial_unit(t,p,owner))return u;}throw std::runtime_error("No fixture space");}
static unit_t* parent(U type,U addon,int owner=0){auto* t=g_ui->get_unit_type(type);auto* a=g_ui->get_unit_type(addon);for(int y=6;y<int(g_ui->game_st.map_tile_height)-6;y++)for(int x=6;x<int(g_ui->game_st.map_tile_width)-6;x++){xy p=xy(x*32,y*32)+t->placement_size/2,ap=xy(x*32,y*32)+a->addon_position+a->placement_size/2;if(g_ui->can_place_building(nullptr,owner,t,p,true,false,true)&&g_ui->can_place_building(nullptr,owner,a,ap,true,false,true))if(auto* u=g_ui->create_initial_unit(t,p,owner))return u;}throw std::runtime_error("No addon fixture space");}
static xy socket(unit_t* u,U type){auto* t=g_ui->get_unit_type(type);return u->position-u->unit_type->placement_size/2+t->addon_position;}
static void queue(unit_t* u,U type,xy pos){uint16_t id=g_ui->get_unit_id(u).raw_value;g_ui->cmds.select(&id,1);g_ui->cmds.build(Orders::PlaceAddon,type,pos.x/32,pos.y/32);}
static void apply(int owner=0){auto bytes=std::move(g_ui->outgoing);g_ui->outgoing.clear();g_ui->apply_commands(owner,bytes.data(),bytes.size());}
static void select(unit_t* u){g_ui->current_selection_clear();g_ui->current_selection_add(u);g_ui->refresh_card();}
static xy screen(xy pos){return xy((fp16::integer(pos.x-g_ui->screen_pos.x)*g_ui->view_scale).integer_part(),(fp16::integer(pos.y-g_ui->screen_pos.y)*g_ui->view_scale).integer_part());}
static void valid(U type,U addon){
 setup();if(addon==U::Terran_Comsat_Station)create(U::Terran_Academy);
 if(addon==U::Terran_Nuclear_Silo){auto* tech=parent(U::Terran_Science_Facility,U::Terran_Covert_Ops);auto* at=g_ui->get_unit_type(U::Terran_Covert_Ops);auto* a=g_ui->create_initial_unit(at,socket(tech,U::Terran_Covert_Ops)+at->placement_size/2,0);require(a!=nullptr,"Prerequisite fixture failed");g_ui->connect_addon(tech,a);}
 auto* b=parent(type,addon);auto* a=g_ui->get_unit_type(addon);auto pos=socket(b,addon);require(g_ui->unit_can_build(b,a),"Fixture lacks addon requirements");
 select(b);g_ui->center_on(b->position);reset_audio();auto serial=g_ui->sound_play_serial;
 // The common command-card action is used by keyboard, touch and gamepad.
 char key=0;for(auto& c:g_ui->card)if(c.ut==addon&&c.act==g_ui->C_TRAIN)key=c.key;require(key!=0,"Addon command absent");
 require(g_ui->run_command(key)&&g_ui->pending_addon==a,"Addon command did not enter placement");require(g_ui->sound_play_serial==serial,"Opening placement played construction sound");
 native_window::event_t escape{};escape.type=native_window::event_t::type_key_down;escape.scancode=41;escape.sym=27;g_ui->handle_game_input(escape);require(!g_ui->pending_addon&&g_ui->outgoing.empty()&&g_ui->sound_play_serial==serial,"Cancelling placement played sound or issued build");
 g_ui->run_command(key);auto p=screen(b->position);require(g_ui->placement_valid(p.x,p.y),"Original addon site rejected");g_ui->place_pending(p.x,p.y);require(g_ui->sound_play_serial==serial,"Queued addon played before engine acceptance");apply();
 require(b->building.addon_build_type==a&&b->order_type->id==Orders::PlaceAddon,"Addon command not accepted");require(g_ui->sound_play_serial==serial+1&&heard(5),"Accepted addon did not play original Terran construction cue once");
 reset_audio();serial=g_ui->sound_play_serial;queue(b,addon,pos);apply();require(g_ui->sound_play_serial==serial&&!heard(5),"Repeated pending addon plays duplicate cue");
 for(int i=0;i<48;i++)native_step();require(b->current_build_unit&&g_ui->unit_is(b->current_build_unit,addon),"Addon never started construction");require(!heard(5),"Build frames replay construction acknowledgement");
 reset_audio();serial=g_ui->sound_play_serial;g_ui->cmds.cancel_addon();apply();require(g_ui->sound_play_serial==serial&&!heard(5),"Cancelling construction plays build cue");
 std::cout<<"PASS addon="<<int(addon)<<" parent="<<int(type)<<" originalSound="<<g_ui->sound_filenames[5].c_str()<<" accepted once; UI placement/cancel, queue delay, repeat and frames silent\n";
}
static void rejected_and_other(){
 for(int mode=0;mode<6;mode++){
  setup();int owner=mode==3?1:0;auto* b=parent(U::Terran_Factory,U::Terran_Machine_Shop,owner);auto pos=socket(b,U::Terran_Machine_Shop);auto* a=g_ui->get_unit_type(U::Terran_Machine_Shop);
  if(mode==0){auto* blocker=g_ui->create_initial_unit(g_ui->get_unit_type(U::Terran_Supply_Depot),pos+a->placement_size/2,owner);require(blocker!=nullptr,"Blocked-space fixture failed");require(!g_ui->can_place_building(b,owner,a,pos+a->placement_size/2,false,false),"Blocked-space fixture not blocked");}
  if(mode==1)g_ui->st.current_minerals[0]=0;
  if(mode==2)g_ui->st.current_gas[0]=0;
  if(mode==4)g_ui->spectator=true;
  if(mode==5)g_ui->st.players[0].controller=player_t::controller_computer_game;
  reset_audio();queue(b,U::Terran_Machine_Shop,pos);apply(owner);require(!heard(5),"Rejected, enemy, AI or replay order played local build cue");
  if(mode<=2)require(b->building.addon_build_type!=a,"Rejected addon order changed build intent");else require(b->building.addon_build_type==a,"Other-owner/spectator command lost simulation behavior");
 }
 setup();auto* b=parent(U::Terran_Factory,U::Terran_Machine_Shop);auto* a=g_ui->get_unit_type(U::Terran_Machine_Shop);auto pos=socket(b,U::Terran_Machine_Shop);reset_audio();
 // AI uses its own action_functions object, even when running for this slot.
 action_functions ai(g_ui->st,g_ui->current_action_state);ai.action_select(0,b);ai.action_build(0,g_ui->get_order_type(Orders::PlaceAddon),a,{size_t(pos.x/32),size_t(pos.y/32)});require(b->building.addon_build_type==a&&!heard(5),"AI action emitted UI acknowledgement");
 std::cout<<"PASS blocked space, missing minerals/gas, other player, AI controller/direct AI and replay spectator are silent\n";
}
int main(int argc,char**argv){try{require(argc==3,"Usage: native-addon_sound81 CORE MAP");std::string d=argv[1];open_archive(0,d+"/STARDAT.MPQ");open_archive(1,d+"/BROODAT.MPQ");open_archive(2,d+"/patch_rt.mpq");open_archive(3,argv[2]);for(auto pair:{std::pair<U,U>{U::Terran_Command_Center,U::Terran_Comsat_Station},{U::Terran_Command_Center,U::Terran_Nuclear_Silo},{U::Terran_Factory,U::Terran_Machine_Shop},{U::Terran_Starport,U::Terran_Control_Tower},{U::Terran_Science_Facility,U::Terran_Covert_Ops},{U::Terran_Science_Facility,U::Terran_Physics_Lab}})valid(pair.first,pair.second);rejected_and_other();close_game();std::cout<<"PASS "<<checks<<" add-on sound checks\n";return 0;}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
