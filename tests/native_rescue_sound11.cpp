// Verify original rescue cues through actual ownership transfer, not a sound-name mock.
#include "../native/runtime.cpp"
#include <iostream>
#include <fstream>
using namespace bwgame; using U=UnitTypes;
static int checks=0;
static void check(bool value,const char* why){++checks;if(!value)throw std::runtime_error(why);}
static void silence(){for(size_t i=0;i<g_ui->sound_channels.size();i++){native_sound::stop(i);g_ui->sound_channels[i].playing=false;}std::fill(g_ui->last_played_sound.begin(),g_ui->last_played_sound.end(),decltype(g_ui->last_played_sound)::value_type{});}
static bool heard(int sound){for(auto& c:g_ui->sound_channels)if(c.playing&&int(c.sound_type->id)==sound)return true;return false;}
static void setup(){int races[]={1,1,1,1,1,1,1,1},slots[]={1,0,0,0,0,0,0,0};configured_init(640,480,0,races,slots,2,true,false,false);g_ui->st.players[1].controller=player_t::controller_rescue_passive;}
static xy free_pair(U type){
 for(int y=128;y<1800;y+=64)for(int x=128;x<1800;x+=64){xy p{x,y};
  if(!g_ui->unit_type_can_fit_at(g_ui->get_unit_type(U::Terran_SCV),p)||!g_ui->unit_type_can_fit_at(g_ui->get_unit_type(type),p+xy(48,0)))continue;
  bool occupied=false;for(auto*u:ptr(g_ui->st.visible_units))if(g_ui->xy_length(u->position-p)<160)occupied=true;
  if(!occupied)return p;
 }throw std::runtime_error("No open ground for rescue fixture");
}
static unit_t* make(U type,int owner,xy p){auto*u=g_ui->create_initial_unit(g_ui->get_unit_type(type),p,owner);check(u!=nullptr,"Unit fixture creation failed");return u;}
int main(int argc,char**argv){try{
 check(argc==5,"Usage: rescue_sound CORE MAP BROODWAR REIGN_WAV");std::string root=argv[1];open_archive(0,root+"/STARDAT.MPQ");open_archive(1,root+"/BROODAT.MPQ");open_archive(2,root+"/patch_rt.mpq");open_archive(3,argv[2]);
 for(auto fixture: {std::make_pair(U::Zerg_Zergling,32),{U::Zerg_Drone,32},{U::Hero_Hunter_Killer,32},{U::Protoss_Zealot,34},{U::Hero_Fenix_Zealot,34},{U::Terran_Marine,33}}){
  U type=fixture.first;
  setup();auto p=free_pair(type);auto*visitor=make(U::Terran_SCV,0,p);auto*u=make(type,1,p+xy(48,0));silence();int before=g_ui->rescue_notifications;int cue=fixture.second;
  check(cue>=32&&cue<=34,"Fixture has no race");u->main_order_timer=0;g_ui->order_RescuePassive(u);
  check(u->owner==0,"Proximity rescue failed");check(g_ui->rescue_notifications==before+1,"Rescue did not notify once");check(g_ui->last_rescue_sound==cue&&heard(cue),"Rescue emitted wrong race cue");
  for(int wrong=32;wrong<=34;wrong++)if(wrong!=cue)check(!heard(wrong),"Rescue emitted second race cue");
  auto filename=g_ui->sound_filenames[cue];check(filename.find(cue==32?"ZRescue":cue==33?"TRescue":"PRescue")!=a_string::npos,"Original DAT maps wrong cue");
  std::cout<<"PASS rescue type="<<int(type)<<" localPlayerRace=Terran cue="<<cue<<" filename="<<filename.c_str()<<"\n";
 }
 setup();auto*u=make(U::Zerg_Zergling,1,free_pair(U::Zerg_Zergling));silence();int before=g_ui->rescue_notifications;
 check(g_ui->trigger_give_unit_to(u,0),"Scripted transfer failed");check(g_ui->rescue_notifications==before,"Scripted transfer added an unsolicited rescue cue");check(!heard(32)&&!heard(33)&&!heard(34),"Scripted transfer duplicates authored WAV");
 for(bool observer:{false,true}){silence();before=g_ui->rescue_notifications;g_ui->spectator=observer;g_ui->on_units_rescued(1,observer?0:2,race_t::protoss);check(g_ui->rescue_notifications==before&&!heard(34),"Other-owner or spectator rescue cue leaked");}
 close_game();open_archive(3,argv[3]);openbw_init_campaign(640,480,502);
 const auto& authored=mission_sound(229);std::ifstream input(argv[4],std::ios::binary);std::vector<uint8_t> expected((std::istreambuf_iterator<char>(input)),{});
 check(expected.size()==83852,"Original Reign of Fire rescue fixture missing");check(authored.size()==expected.size()&&std::equal(authored.begin(),authored.end(),expected.begin()),"Campaign audio changed its explicitly authored Terran rescue WAV");
 std::cout<<"PASS "<<checks<<" original-data rescue audio checks; original Reign WAV preserved byte-for-byte; scripted transfers add no duplicate cue; other-owner/spectator suppressed\n";close_game();return 0;
}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
