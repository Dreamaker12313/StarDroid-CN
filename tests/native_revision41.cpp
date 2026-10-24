// Original-data checks for ammunition, spell cards, archon timing, cargo and AI.
#include "../native/runtime.cpp"
#include <fstream>
#include <iostream>
#include <set>
using namespace bwgame;
static void require(bool ok,const char* message){if(!ok)throw std::runtime_error(message);}
static void advance(int n){for(int i=0;i<n;i++)native_step();}
static void select(unit_t* u){g_ui->current_selection.clear();g_ui->current_selection.push_back(g_ui->get_unit_id(u));g_ui->refresh_card();}
static unit_t* create(int type,xy around={1000,1000}){
 auto* ut=g_ui->get_unit_type(UnitTypes(type));
 for(int r=0;r<20;r++)for(int dy=-r;dy<=r;dy++)for(int dx=-r;dx<=r;dx++){
  xy p=around+xy(dx*32,dy*32);
  if(!g_ui->unit_type_can_fit_at(ut,p))continue;
  bool free=true;for(auto* u:g_ui->find_units(g_ui->square_at(p,32)))if(!g_ui->unit_dying(u))free=false;
  if(free){auto* u=g_ui->create_initial_unit(ut,p,0);if(u)return u;}
 }throw std::runtime_error("No fixture space");
}
static const play_ui::cmd_t* find(const char* name){for(auto& c:g_ui->card)if(std::string(c.label)==name)return &c;return nullptr;}
static void fixture(const char* name){auto b=save_game();std::ofstream o(std::string("build-native/revision41-fixtures/")+name+".bin",std::ios::binary);o.write((const char*)b.data(),b.size());}
static void snapshot(){openbw_render(openbw_frame()*42.);auto s=save_game();advance(32);auto expected=save_game();restore_game(s);require(save_game()==s,"Snapshot round trip differs");advance(32);auto actual=save_game();if(actual!=expected){
 for(auto pair:{std::make_pair("expected",&expected),std::make_pair("actual",&actual)}){std::ofstream o(std::string("build-native/revision42-")+pair.first+".bin",std::ios::binary);o.write((char*)pair.second->data(),pair.second->size());}
 }require(actual==expected,"Snapshot continuation differs");}
static void cards(){
 openbw_init(640,480,2,0);g_ui->competitive=false;advance(2);
 g_ui->st.current_minerals[0]=50000;g_ui->st.current_gas[0]=50000;
 for(int type:{72,82,83,81}){
  auto* u=create(type);select(u);action_state state;action_functions af(g_ui->st,state);af.action_select(0,u);
  bool carrier=g_ui->unit_is_carrier(u);int capacity=carrier?g_ui->unit_max_interceptor_count(u):g_ui->unit_max_scarab_count(u);
  const char* label=carrier?"Build Interceptor":"Build Scarab";
  for(int n=0;n<capacity;n++){
   g_ui->refresh_card();require(find(label),"Fighter button disappeared too early");require(af.action_train_fighter(0),"Fighter refused production");advance(320);
  }
  g_ui->refresh_card();require(!find(label),"Fighter button remains at full capacity");
  auto* fighter=g_ui->release_fighter(u);require(fighter,"No fighter to consume");g_ui->kill_unit(fighter);advance(3);
  g_ui->refresh_card();require(find(label),"Fighter button did not return after loss");
  require(af.action_train_fighter(0),"Cannot replace fighter");g_ui->refresh_card();require(!find(label),"Queued fighter ignored in capacity");
  require(af.action_cancel_build_queue(0,0),"Cannot cancel queued fighter");g_ui->refresh_card();require(find(label),"Cancel did not restore fighter button");
  std::cout<<"PASS ammunition type "<<type<<" capacity "<<capacity<<"\n";
 }
 struct Entry{int unit;TechTypes tech;const char* label;};
 for(auto e:{Entry{1,TechTypes::Lockdown,"Lockdown"},Entry{1,TechTypes::Personnel_Cloaking,"Cloak"},Entry{8,TechTypes::Cloaking_Field,"Cloak"},Entry{67,TechTypes::Psionic_Storm,"Psionic Storm"},Entry{9,TechTypes::Irradiate,"Irradiate"},Entry{63,TechTypes::Mind_Control,"Mind Control"},Entry{38,TechTypes::Burrowing,"Burrow"}}){
  auto* u=create(e.unit);const_cast<game_state&>(g_ui->game_st).tech_available[0][e.tech]=true;g_ui->st.tech_researched[0][e.tech]=false;u->energy=0_fp8;select(u);
  require(find(e.label)&&!find(e.label)->enabled,"Unresearched ability not visible/grey");if(e.unit==1&&e.tech==TechTypes::Lockdown)fixture("ghost-unresearched");int seq=g_ui->error_seq;g_ui->run_command(find(e.label)->key);require(g_ui->error_seq==seq,"Unresearched spell incorrectly reports energy");
  g_ui->st.tech_researched[0][e.tech]=true;g_ui->refresh_card();require(find(e.label)&&find(e.label)->enabled,"Low energy dims researched ability");
  if(e.unit==1&&e.tech==TechTypes::Lockdown)fixture("ghost-no-energy");
  if(g_ui->get_tech_type(e.tech)->energy_cost){g_ui->run_command(find(e.label)->key);require(g_ui->error_seq==seq+1&&std::string(g_ui->error_status()).find("energy")!=std::string::npos,"Low energy produces no feedback");}
  const_cast<game_state&>(g_ui->game_st).tech_available[0][e.tech]=false;g_ui->refresh_card();require(!find(e.label),"Scenario-disabled spell exposed");
 }
 std::cout<<"PASS research gates, energy feedback and scenario availability\n";close_game();
}
static void merging(){
 for(bool dark:{false,true}){
  openbw_init(640,480,2,0);g_ui->competitive=false;advance(2);
  auto* a=create(dark?61:67),*b=create(dark?61:67,a->position);advance(2);g_ui->poll_events();
  action_state state;action_functions af(g_ui->st,state);unit_t* pair[]={a,b};af.action_select(0,pair);
  require(dark?af.action_morph_dark_archon(0):af.action_morph_archon(0),"Merge action failed");
  int before=g_ui->ready_notifications;unit_t* merged=nullptr;bool partial=false;int first=-1,last=-1;
  for(int f=0;f<1500;f++){
   native_step();g_ui->poll_events();
   for(auto* u:ptr(g_ui->st.player_units[0]))if(int(u->unit_type->id)==(dark?63:68)&&!g_ui->unit_dying(u))merged=u;
   if(!merged)continue;
   select(merged);
   if(f%50==0)std::cout<<"MERGE "<<f<<" order="<<int(merged->order_type->id)<<" state="<<merged->order_state<<" time="<<merged->remaining_build_time<<" bt="<<merged->unit_type->build_time<<"\n";
   if(g_ui->archon_merging(merged)){
    require(g_ui->ready_notifications==before,"Ready sound precedes merge completion");
    require(openbw_production_kind()==5,"Merge lacks progress kind");int progress=std::atoi(g_ui->build_status());
    if(progress>=45&&progress<=47)fixture(dark?"dark-archon-merging":"archon-merging");
    if(first<0)first=progress;last=progress;if(progress>first)partial=true;
    require(g_ui->card.empty(),"Merging archon has command buttons");
   }else break;
  }
  std::cout<<"MERGE RESULT "<<(merged?int(merged->unit_type->id):-1)<<" first="<<first<<" last="<<last<<" A="<<int(a->unit_type->id)<<":"<<int(a->order_type->id)<<" B="<<int(b->unit_type->id)<<":"<<int(b->order_type->id)<<"\n";
  require(merged&&partial&&last>first,"Merge progress did not advance");require(!g_ui->archon_merging(merged),"Merge never finished");
  require(g_ui->ready_notifications==before+1&&g_ui->last_ready_type==(dark?63:68),"Ready sound missing or duplicated at completion");
  require(openbw_production_kind()==0&&std::string(g_ui->build_status()).empty(),"Finished merge retains progress");
  snapshot();std::cout<<"PASS "<<(dark?"Dark Archon":"Archon")<<" progress "<<first<<".."<<last<<" and completion sound\n";close_game();
 }
}
static void cargo(){
 openbw_init(640,480,1,0);g_ui->competitive=false;advance(2);
 auto* transport=create(11);int index=0;
 for(int type:{5,2,0,32}){
  auto* passenger=create(type);require(g_ui->unit_can_load_target(transport,passenger),"Cargo not loadable");g_ui->unit_load_target(transport,passenger);select(transport);
  auto* pixels=g_ui->render_cargo_wireframe(index++);require(pixels,"Missing original cargo wireframe");int alpha=0;for(int p=3;p<64*64*4;p+=4)alpha+=pixels[p]!=0;require(alpha>20,"Cargo wireframe blank");
 }
 require(g_ui->unit_space_left(transport)==0,"DAT cargo spaces differ");fixture("cargo");std::cout<<"CARGO\n"<<g_ui->cargo_status();snapshot();std::cout<<"PASS cargo DAT capacity and original transport wireframe pixels\n";close_game();
}
static void warnings(){
 openbw_init(640,480,2,0);advance(2);auto* ghost=create(1);select(ghost);
 for(auto kind:{play_ui::E_MINERALS,play_ui::E_GAS,play_ui::E_ENERGY}){
  g_ui->raise_error(kind);require(!g_ui->error_text.empty(),"Empty warning");require(g_ui->err_sound(kind)>=0,"Missing advisor sound");
 }
 require(g_ui->err_sound(play_ui::E_ENERGY)==g_ui->find_sound("tAdErr06"),"Energy uses wrong advisor line");
 for(auto spec:{std::pair<int,const char*>{37,"Overlords"},{0,"Supply Depots"},{65,"Pylons"}}){
  g_ui->st.current_minerals[0]=50000;g_ui->st.current_gas[0]=50000;
  for(int race=0;race<3;race++)g_ui->st.supply_available[0][race]=g_ui->st.supply_used[0][race];
  play_ui::cmd_t c{'x',"test",play_ui::C_TRAIN,UnitTypes(spec.first)};
  require(g_ui->block_reason(c)==play_ui::E_SUPPLY,"Supply did not block training");g_ui->raise_error(play_ui::E_SUPPLY);
  require(g_ui->error_text.find(spec.second)!=a_string::npos,"Mixed-race supply warning names wrong provider");
 }
 std::cout<<"PASS resource, energy and three mixed-race supply warnings with advisor sounds\n";close_game();
}
static void smoke(){
 g_terran_ai_level=2;openbw_init_terran_ai(640,480,1,1);g_ui->competitive=false;advance(6000);
 require(g_campaign&&g_campaign->ai_error.empty(),"Map AI startup failed");
 require(g_campaign->towns[1].built>2&&g_campaign->towns[1].trained>4,"Map lacks usable AI build space");
 snapshot();std::cout<<"PASS map terrain, AI economy/build space and save continuation\n";close_game();
}
static void ai(int level,int frames){
 g_terran_ai_level=level;openbw_init_terran_ai(640,480,1,1);g_ui->competitive=false;std::set<int> seen;
 for(int f=0;f<frames;f++){
  native_step();require(g_campaign->ai_error.empty(),g_campaign->ai_error.c_str());
  for(auto* u:ptr(g_ui->st.player_units[0]))if(!g_ui->unit_dying(u))g_ui->set_unit_hp(u,u->unit_type->hitpoints);
  for(auto* u:ptr(g_ui->st.player_units[1]))if(g_ui->u_completed(u)&&!g_ui->unit_dying(u))seen.insert(int(u->unit_type->id));
  if(f%6000==0){std::cout<<"AI "<<f<<" "<<g_campaign->ai_status()<<" types:";for(int type:seen)std::cout<<type<<",";std::cout<<"\n";}
 }
 std::cout<<"FINAL types:";for(int type:seen)std::cout<<type<<",";std::cout<<"\n";
 for(auto* u:ptr(g_ui->st.player_units[1]))if(g_ui->ut_building(u))std::cout<<"BUILDING "<<int(u->unit_type->id)<<" "<<u->position.x<<","<<u->position.y<<" completed="<<g_ui->u_completed(u)<<" addon="<<(u->building.addon?int(u->building.addon->unit_type->id):-1)<<"\n";
 for(auto* u:ptr(g_ui->st.player_units[1]))std::cout<<"U "<<int(u->unit_type->id)<<" pos="<<u->position.x<<","<<u->position.y<<" order="<<int(u->order_type->id)<<" target="<<u->order_target.pos.x<<","<<u->order_target.pos.y<<" queuedType="<<(u->build_queue.empty()?-1:int(u->build_queue.front()->id))<<" state="<<u->order_state<<" time="<<u->remaining_build_time<<" build="<<(u->current_build_unit?int(u->current_build_unit->unit_type->id):-1)<<" secondary="<<int(u->secondary_order_type->id)<<":"<<u->secondary_order_state<<" queue="<<u->build_queue.size()<<" status="<<u->status_flags<<" can5="<<g_ui->unit_can_build(u,g_ui->get_unit_type(UnitTypes(5)))<<"\n";
 for(int i=0;i<228;i++)if(g_campaign->towns[1].wave[i]||g_campaign->towns[1].defence[i])std::cout<<"REQ "<<i<<" wave="<<g_campaign->towns[1].wave[i]<<" def="<<g_campaign->towns[1].defence[i]<<" count="<<g_campaign->ai_count(1,i)<<"\n";
 std::cout<<"SUPPLY "<<g_ui->st.supply_used[1][1].raw_value<<"/"<<g_ui->st.supply_available[1][1].raw_value<<"\n";
 if(std::getenv("OPENBW_AI_DIAGNOSTICS")) {
  auto saved=save_game();std::ofstream out("build-native/ai-debug42.bin",std::ios::binary);out.write((char*)saved.data(),saved.size());out.close();
  openbw_resize(g_ui->game_st.map_width,g_ui->game_st.map_height);g_ui->fog_player=-1;g_ui->screen_pos={0,0};openbw_render(0);
  auto* pixels=openbw_framebuffer();int w=openbw_framebuffer_width(),h=openbw_framebuffer_height();std::ofstream ppm("build-native/ai-debug42.ppm",std::ios::binary);ppm<<"P6\n"<<w<<" "<<h<<"\n255\n";
  for(int i=0;i<w*h;i++){ppm.put(pixels[i*4]);ppm.put(pixels[i*4+1]);ppm.put(pixels[i*4+2]);}
 }
 require(g_campaign->towns[1].attacks>=3,"AI did not send waves");
 if(level==2)for(int type:{1,9,12,58,117,118})require(seen.count(type),"Hard AI did not reach advanced units/addons");
 snapshot();std::cout<<"PASS original AI level "<<level<<" frames "<<frames<<"\n";
}
int main(int argc,char**argv){std::cout.setf(std::ios::unitbuf);try{
 require(argc>=4,"usage: native-revision41 DATA MAP cards|merging|cargo|ai [level frames]");std::string d=argv[1];
 open_archive(0,d+"/STARDAT.MPQ");open_archive(1,d+"/BROODAT.MPQ");open_archive(2,d+"/patch_rt.mpq");open_archive(3,argv[2]);
 std::string mode=argv[3];if(mode=="cards")cards();else if(mode=="merging")merging();else if(mode=="cargo")cargo();else if(mode=="warnings")warnings();else if(mode=="smoke")smoke();else if(mode=="ai")ai(argc>4?std::atoi(argv[4]):2,argc>5?std::atoi(argv[5]):120000);else throw std::runtime_error("Unknown mode");
 close_game();return 0;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
