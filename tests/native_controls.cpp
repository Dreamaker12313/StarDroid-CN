#include "../native/runtime.cpp"
#include <sstream>
#include <iostream>
#include <cassert>
static double test_time=0;
static void draw(){openbw_render(test_time+=42);}
static bwgame::unit_t* find_unit(const char* name,int owner=-1){for(int i=0;i<12;i++)for(auto* u:bwgame::ptr(g_ui->st.player_units[i]))if((owner<0||u->owner==owner)&&std::string(g_ui->unit_name(u->unit_type->id))==name)return u;return nullptr;}
static void select(const char* name,int owner=-1){auto* u=find_unit(name,owner);if(!u)throw std::runtime_error(std::string("Missing ")+name);openbw_debug_select(g_ui->get_unit_id(u).raw_value,0);draw();}
static void key(const char* label){std::istringstream in(openbw_card());std::string line;while(std::getline(in,line)){auto first=line.find('\t');if(first!=std::string::npos&&line.substr(first+1).find(label)==0){command(2,line[0],0,0,0);draw();native_step();draw();return;}}throw std::runtime_error(std::string("Missing command ")+label+": "+openbw_card());}
static void advance(int frames){for(int i=0;i<frames;i++){native_step();if(i%24==0)draw();}}
static void require(bool cond,const char* message){if(!cond)throw std::runtime_error(message);}
int main(int argc,char** argv){try{
 std::string dir=argv[1];open_archive(0,dir+"/STARDAT.MPQ");open_archive(1,dir+"/BROODAT.MPQ");open_archive(2,dir+"/patch_rt.mpq");open_archive(3,dir+"/StarCraft.mpq");openbw_init_campaign(640,480,102);openbw_set_external_cursor(1);advance(24);openbw_debug_resources(9000,9000);
 select("Hatchery",3);require(std::string(openbw_card()).find("Lair")!=std::string::npos,"Lair missing");
 select("Larva",3);require(std::string(openbw_card()).find("Mutalisk\t0")!=std::string::npos,"Locked Mutalisk missing");key("Drone");advance(4);select("Egg",3);require(openbw_production_queue_type(0)==41,"Egg does not identify Drone");require(openbw_production_icon()==41,"Egg icon incorrect");openbw_cancel(0);advance(5);
 select("Young Chrysalis");require(std::string(openbw_unit_details()).empty(),"Chrysalis shows armor info");
 select("Hatchery",3);openbw_test_instant(1);key("Lair");advance(180);require(find_unit("Lair",3),"Lair did not morph through native command stream");
 select("Drone",3);auto* gas=find_unit("Vespene Geyser");require(gas,"Geyser missing");openbw_reveal_map();openbw_pan(-65536,-65536);openbw_pan(std::max(0,gas->position.x-300),std::max(0,gas->position.y-150));key("Build");key("Extractor");bool placed=false;for(int y=20;y<280&&!placed;y+=8)for(int x=40;x<600&&!placed;x+=8)if(openbw_placement_valid(x,y)){command(0,x,y,0,0);command(1,1,1,x,y);command(1,0,1,x,y);draw();native_step();placed=true;}
 require(placed,"No Extractor site");
 auto place_wav=read_asset(-1,"sound/misc/ZBldgPlc.wav");
 auto place_clip=naudio::wav(place_wav.data(),place_wav.size());bool thump=false;
 for(const auto& voice:naudio::voices)if(voice.clip&&voice.clip->rate==place_clip->rate&&voice.clip->channels==place_clip->channels&&voice.clip->pcm==place_clip->pcm)thump=true;
 require(thump,"Native building command did not play original DON cue");
 advance(1700);select("Extractor",3);require(std::string(openbw_card()).find("750")!=std::string::npos,"Extractor HP missing");require(std::string(openbw_card()).find("Gas")!=std::string::npos,"Extractor gas missing");
 bwgame::unit_t* beacon=nullptr;
 for(int owner=0;owner<12;owner++)for(auto* u:bwgame::ptr(g_ui->st.player_units[owner]))
  if(owner!=3&&std::string(g_ui->unit_name(u->unit_type->id)).find("Beacon")!=std::string::npos)beacon=u;
 require(beacon,"No beacon for rescue check");auto* worker=find_unit("Drone",3);require(worker,"No worker for beacon check");
 int notifications=g_ui->rescue_notifications;auto beacon_id=g_ui->get_unit_id(beacon);
 openbw_debug_warp(g_ui->get_unit_id(worker).raw_value,beacon->position.x,beacon->position.y);advance(160);
 beacon=g_ui->get_unit(beacon_id);require(beacon&&beacon->owner==3,"Beacon did not transfer");
 require(g_ui->rescue_notifications==notifications,"Beacon transfer made rescue sound");
 auto wav=read_asset(-1,"sound/misc/youwin.wav");int id=naudio::add(wav.data(),wav.size());naudio::play(id,61,128,0);std::vector<int16_t> samples(96000);naudio::mix(samples.data(),48000,48000);int audible=0;for(auto n:samples)audible+=n!=0;require(audible>1000,"Victory mix is silent");
 std::cout<<"NATIVE_CONTROLS_OK Lair, disabled technology, Egg target, Chrysalis, Extractor placement/HP/gas, original build thump, silent beacon transfer, audible victory ("<<audible<<" nonzero samples)\n";close_game();

 openbw_init_campaign(640,480,1);openbw_set_external_cursor(1);advance(24);openbw_debug_resources(9000,9000);openbw_reveal_map();select("SCV",1);openbw_pan(400,400);
 key("Move");command(4,290,170,0,0);draw();advance(2);
 std::cerr<<"NATIVE_TOUCH resize zoom in\n";openbw_resize(457,343);openbw_set_view_scale(1.4);draw();
 command(5,0,0,0,0);std::cerr<<"NATIVE_TOUCH resize reset\n";openbw_resize(640,480);openbw_set_view_scale(1);draw();
 select("SCV",1);key("Build");command(2,27,41,0,0);draw();advance(2);
 std::cerr<<"NATIVE_TOUCH build after cancel\n";key("Build");key("Supply Depot");draw();advance(30);
 require(openbw_cursor()==2,"Build cursor lost after zoom/cancel");command(2,27,41,0,0);draw();close_game();
 std::cout<<"NATIVE_TOUCH_OK targeting, resize, cancellation and building after zoom\n";
 auto intro=read_asset(3,"smk/starintr.smk");require(intro.size()>104,"Introduction asset missing");int movie=open_movie(intro.data(),intro.size(),true);auto* picture=movie_frame(movie,2000,false);require(picture&&picture->width==naudio::u32(intro.data()+4)&&picture->height==naudio::u32(intro.data()+8)&&picture->frames>30&&picture->current>20&&picture->rgba.size()==picture->width*picture->height*4,"Native movie frames invalid");require(naudio::playing(60),"Native movie audio missing");audible=0;for(int second=0;second<5;second++){naudio::mix(samples.data(),48000,48000);for(auto v:samples)audible+=v!=0;}require(audible>1000,"Native movie audio is silent");std::cout<<"NATIVE_MEDIA_OK "<<picture->width<<"x"<<picture->height<<" / "<<picture->frames<<" frames / "<<audible<<" audible samples\n";movies[movie].reset();return 0;
 }catch(const std::exception& e){std::cerr<<"NATIVE_CONTROLS_ERROR "<<e.what()<<"\n";return 1;}}
