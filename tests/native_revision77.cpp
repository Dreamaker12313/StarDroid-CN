// Actual archive/mission regressions. No game data is distributed with this test.
#define main retained_multiplayer_main77
#include "native_multiplayer.cpp"
#undef main
#include <sstream>
using U = bwgame::UnitTypes;
static unit_t* make77(U type,int owner,xy p) {
 auto* u=g_ui->create_initial_unit(g_ui->get_unit_type(type),p,owner);
 require(u,"Could not create regression unit");return u;
}
static unit_t* room77(U type,int owner,xy around) {
 auto* ut=g_ui->get_unit_type(type);
 for(int r=0;r<20;r++)for(int y=-r;y<=r;y++)for(int x=-r;x<=r;x++) {
  xy p=around+xy(x*32,y*32);if(!g_ui->unit_type_can_fit_at(ut,p))continue;
  bool free=true;for(auto* u:g_ui->find_units(g_ui->square_at(p,64)))if(!g_ui->unit_dying(u))free=false;
  if(free){auto* u=g_ui->create_initial_unit(ut,p,owner);if(u)return u;}
 }
 throw std::runtime_error("No free placement for regression unit");
}
static void setup77(const char* map) {
 close_game();open_archive(3,map);
 int races[8]={0,1},slots[8]={1,0};configured_init(640,480,0,races,slots,0,true,true,false);
 g_ui->competitive=false;if(g_campaign)g_campaign->threads.clear();
}
static void pickup77(const char* map) {
 int cases=0;
 for(auto worker:{U::Terran_SCV,U::Zerg_Drone,U::Protoss_Probe})
 for(auto itemType:{U::Powerup_Young_Chrysalis,U::Powerup_Psi_Emitter,U::Powerup_Data_Disk,U::Powerup_Khaydarin_Crystal,U::Powerup_Uraj_Crystal,U::Powerup_Khalis_Crystal}) {
  setup77(map);
  auto* workerUnit=make77(worker,0,{1100,1100});
  auto* item=make77(itemType,11,workerUnit->position);
  // Ownership, not unit type, assigned this order before the regression fix.
  g_ui->set_unit_order(item,g_ui->get_order_type(Orders::Neutral));item->main_order_timer=0;
  g_ui->execute_main_order(item);
  require(workerUnit->worker.powerup==item && workerUnit->carrying_flags==4,"Worker did not pick up neutral campaign item");
  require(g_ui->us_hidden(item)&&item->order_target.unit==workerUnit,"Item/carrier link missing");
  g_ui->move_unit(workerUnit,{1200,1200});g_ui->order_carried_powerup(item);
  require(item->position==workerUnit->position,"Carried object did not follow worker");
  auto snapshot=save_game();auto workerId=g_ui->get_unit_id(workerUnit),itemId=g_ui->get_unit_id(item);
  restore_game(snapshot);workerUnit=g_ui->get_unit(workerId);item=g_ui->get_unit(itemId);
  require(workerUnit && item && workerUnit->worker.powerup==item && item->order_target.unit==workerUnit,"Save/restore lost carried object");
  g_ui->kill_unit(workerUnit);
  require(!g_ui->us_hidden(item),"Worker death did not drop object");
  auto* replacement=make77(worker,0,item->position);item->main_order_timer=0;g_ui->execute_main_order(item);
  require(replacement->worker.powerup==item,"Dropped object cannot be picked up again");cases++;
 }
 std::cout<<"PASS "<<cases<<" campaign-item/worker combinations: neutral pickup, following, save/restore, death, reacquisition\n";
 setup77(map);auto* item=make77(U::Powerup_Psi_Emitter,6,{1100,1100});
 auto* worker=make77(U::Terran_SCV,0,item->position);worker->carrying_flags=1;item->main_order_timer=0;g_ui->execute_main_order(item);
 require(!worker->worker.powerup,"Resource-carrying worker picked up a second object");
 worker->carrying_flags=0;g_ui->set_unit_order(item,g_ui->get_order_type(Orders::Guard));item->main_order_timer=0;g_ui->execute_main_order(item);
 require(worker->worker.powerup==item,"Guard-owned campaign item cannot be picked up");
 auto* other=make77(U::Powerup_Data_Disk,11,item->position);other->main_order_timer=0;g_ui->execute_main_order(other);
 require(worker->worker.powerup==item&&!g_ui->us_hidden(other),"Worker picked up two mission objects");
 std::cout<<"PASS guard ownership and resource/double-carry exclusions\n";
}
static void larvae77(const char* map) {
 setup77(map);require(g_ui->original_larvae_selection,"Original larvae selection does not default on");
 std::vector<unit_t*> parents;
 for(auto type:{U::Zerg_Hatchery,U::Zerg_Lair,U::Zerg_Hive}) {
  auto* parent=room77(type,0,{1100+int(parents.size())*280,1100});parents.push_back(parent);
  for(int i=0;i<4;i++){auto* larva=room77(U::Zerg_Larva,0,{parent->position.x+i*25,parent->position.y+100});larva->connected_unit=parent;}
 }
 for(auto* parent:parents) {
  g_ui->current_selection_clear();g_ui->current_selection_add(parent);g_ui->select_units_of_type(U::Zerg_Larva);
  require(g_ui->current_selection.size()==3,"Original selection must contain at most 3 attached larvae");
  for(auto id:g_ui->current_selection)require(g_ui->get_unit(id)->connected_unit==parent,"Selected larvae from a different hatchery");
 }
 command(27,0,0,0,0);g_ui->current_selection_clear();g_ui->current_selection_add(parents[0]);g_ui->select_units_of_type(U::Zerg_Larva);
 require(g_ui->current_selection.size()==12,"Expanded selection no longer selects up to 12 larvae");
 command(27,1,0,0,0);g_ui->current_selection_clear();g_ui->current_selection_add(parents[0]);
 for(auto* u:ptr(g_ui->st.player_units[0]))if(g_ui->unit_is(u,U::Zerg_Larva)&&u->connected_unit==parents[0])u->connected_unit=nullptr;
 g_ui->select_units_of_type(U::Zerg_Larva);require(g_ui->current_selection.empty(),"Empty hatchery selected another hatchery's larvae");
 std::cout<<"PASS Hatchery/Lair/Hive parent filtering, 3-larva limit, empty parent and opt-out global selection\n";
}
static void audio77() {
 naudio::clear();auto clip=std::make_shared<naudio::Clip>();clip->rate=44100;clip->channels=1;clip->pcm.assign(441000,.01f);
 naudio::play_clip(clip,62);naudio::play_clip(clip,63);naudio::voices[63].loop=true;
 for(int i=0;i<32;i++) {naudio::play_clip(clip,i);auto& ch=g_ui->sound_channels[i];ch.playing=true;ch.priority=0;ch.flags=2;}
 require(g_ui->get_sound_channel(100)==nullptr,"Effects can evict unit voices");
 g_ui->sound_channels[5].flags=0;require(g_ui->get_sound_channel(100)==&g_ui->sound_channels[5],"Effect channel cannot be reused");
 for(int i=1;i<50;i++)naudio::play_effect(clip,i);
 require(naudio::voices[62].clip==clip && naudio::voices[62].effect_id==-1,"Trigger effect replaced dialogue");
 require(naudio::voices[63].clip==clip && naudio::voices[63].loop,"Trigger effect replaced music");
 require(naudio::effect_playing(49),"Effect did not start");
 auto before=naudio::voices;naudio::play_effect(clip,49);
 for(int i=48;i<=55;i++)require(naudio::voices[i].clip==before[i].clip&&naudio::voices[i].effect_id==before[i].effect_id,"Duplicate effect stole a voice");
 int16_t pcm[512];naudio::mix(pcm,256,44100);
 require(pcm[0]>0&&naudio::voices[62].position==256,"Mixer did not advance protected speech");
 std::cout<<"PASS protected unit speech, 32 game channels, separate trigger effects, dialogue/music isolation and duplicate coalescing\n";
}
static void reign77(const char* archive) {
 close_game();open_archive(3,archive);openbw_init_campaign(640,480,502);openbw_set_external_cursor(1);
 bool raynor=false,effectDuringRaynor=false,reportedLine=false;std::shared_ptr<naudio::Clip> voice;
 for(int f=0;f<6500;f++) {
  native_step();std::istringstream rows(g_campaign->events.c_str());std::string row;
  while(std::getline(rows,row)) {
   std::istringstream fields(row);int type,text,sound,duration,unit;fields>>type>>text>>sound>>duration>>unit;
   if(sound<=0)continue;
   if(type==7){auto& bytes=mission_sound(sound);voice=naudio::wav(bytes.data(),bytes.size());naudio::play_clip(voice,62);
    reportedLine=g_ui->game_st.map_strings[sound-1].find("Z2M20RAY")!=a_string::npos;raynor|=reportedLine;
    std::cout<<"MISSION transmission="<<g_ui->game_st.map_strings[sound-1]<<" triggerMs="<<duration<<" audioMs="<<voice->pcm.size()*1000/voice->channels/voice->rate<<"\n";}
   if(type==8 && voice) {auto& bytes=mission_sound(sound);naudio::play_effect(naudio::wav(bytes.data(),bytes.size()),sound);
    require(naudio::voices[62].clip==voice,"Real mission effects interrupted Raynor");effectDuringRaynor|=reportedLine;}
  }
  g_campaign->events.clear();
 }
 bool carrying=false;
 for(auto* u:ptr(g_ui->st.player_units[g_ui->my_player]))if(g_ui->unit_is(u,U::Terran_SCV)&&u->worker.powerup)
  carrying|=g_ui->unit_is(u->worker.powerup,U::Powerup_Psi_Emitter)&&u->carrying_flags==4;
 require(carrying,"Original Reign of Fire SCV did not pick up psi emitter");
 require(raynor&&effectDuringRaynor,"Real mission audio sequence not exercised");
 std::cout<<"PASS original Reign of Fire introduction, Raynor/effect overlap and mission SCV carrying psi emitter after 6500 frames\n";
}
int main(int argc,char**argv) {try {
 require(argc==4||argc==5,"native-revision77 DATA_DIRECTORY CUSTOM_MAP BROODWAR_MPQ [russian]");std::string d=argv[1];
 open_archive(0,d+"/STARDAT.MPQ");open_archive(1,d+"/BROODAT.MPQ");open_archive(2,d+"/patch_rt.mpq");
 if(argc==5) {
  open_archive(3,argv[3]);openbw_init_campaign(640,480,1);openbw_set_external_cursor(1);
  for(int i=0;i<1200;i++)native_step();openbw_render(1200*42.);
  require(g_campaign&&g_campaign->ai_error.empty(),"Russian campaign failed");
  require(openbw_frame()>=1200 && openbw_framebuffer_width()==640,"Russian mission/render did not advance");
  auto saved=save_game();restore_game(saved);require(save_game()==saved,"Russian mission save round trip differs");
  std::cout<<"PASS supplied Russian core archives and StarCraft.mpq: native first-mission load, 1200 frames, render and exact save round trip\n";
  close_game();return 0;
 }
 pickup77(argv[2]);larvae77(argv[2]);audio77();reign77(argv[3]);close_game();return 0;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
