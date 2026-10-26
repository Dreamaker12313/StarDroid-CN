#include "../native/runtime.cpp"
#include <fstream>
#include <iostream>
#include <set>
#include <sstream>
using namespace bwgame;
static int checks=0;
static void check(bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);}
static std::vector<std::vector<std::string>> rows(const std::string& raw){
 std::istringstream input(raw);std::string line;std::getline(input,line);std::vector<std::vector<std::string>> result;
 while(std::getline(input,line)){std::vector<std::string> fields;size_t start=0;for(size_t p=0;p<=line.size();++p)if(p==line.size()||line[p]=='\t'){fields.emplace_back(line.substr(start,p-start));start=p+1;}check(fields.size()==20,"Score protocol changed");result.push_back(std::move(fields));}return result;
}
static std::string stats(){auto sum=sim_checksum(g_ui->st);auto rng=g_ui->st.lcg_rand_state;std::string result=g_ui->stats_text();check(sim_checksum(g_ui->st)==sum&&rng==g_ui->st.lcg_rand_state,"Score query mutated simulation/RNG");return result;}
static std::set<int> slots(const std::string& raw){std::set<int> out;for(auto& row:rows(raw)){int owner=std::stoi(row[16]);check(owner>=0&&owner<8,"Score slot outside bounds");check(out.insert(owner).second,"Duplicate score slot");}return out;}
static std::set<int> original_participants(){
 const auto& data=g_ui->rep_map;std::vector<unsigned char> owners;
 for(size_t p=0;p+8<=data.size();){size_t n=campaign_ui::u32(&data[p+4]);check(n<=data.size()-p-8,"Malformed original CHK");if(!memcmp(&data[p],"OWNR",4)){check(n>=8,"Missing original owners");owners.assign(data.begin()+p+8,data.begin()+p+16);}p+=n+8;}
 check(owners.size()==8,"No original OWNR");std::set<int> out;for(int i=0;i<8;i++)if(owners[i]==5||owners[i]==6)out.insert(i);return out;
}
static void write(const std::string& path,const std::string& data){std::ofstream out(path,std::ios::binary);check(bool(out),"Cannot open score fixture");out<<data;check(bool(out),"Cannot write score fixture");}
static void campaign(int code,const std::string& output){
 openbw_init_campaign(640,480,code);auto expected=original_participants();auto raw=stats();check(slots(raw)==expected,"Campaign score roster differs from original human/computer slots");check(expected.count(g_ui->my_player),"Local participant omitted");write(output,raw);
 for(auto& row:rows(raw)){int owner=std::stoi(row[16]),force=g_ui->st.players[owner].force;std::string name;if(force>=1&&force<=4)for(unsigned char c:g_ui->game_st.forces[force-1].name)if(c>=32&&c!=127)name+=char(c);
  if(name.find_first_not_of(" \t\r\n-")==std::string::npos)name.clear();check(row[19]==name,"Original faction name changed or lost");}
 // Scores are not a participation heuristic: inactive/helper owners may have
 // resources/buildings and true opponents may have zero scores at mission start.
 for(int i=0;i<8;i++){
  g_ui->st.unit_score[i]=g_ui->st.building_score[i]=expected.count(i)?0:500000;
  g_ui->st.total_minerals_gathered[i]=g_ui->st.total_gas_gathered[i]=expected.count(i)?0:500000;
  if(expected.count(i)){g_ui->st.players[i].controller=i==g_ui->my_player?player_t::controller_user_left:player_t::controller_computer_defeated;g_ui->st.players[i].victory_state=2;}
  else if(g_ui->st.players[i].initially_active)g_ui->st.players[i].controller=player_t::controller_computer_game;
 }
 check(slots(stats())==expected,"Defeat/neutral hostility changed original score roster");
 if(code==501){auto saved=save_game();auto sum=sim_checksum(g_ui->st);g_ui->rep.players={};restore_game(saved);check(sim_checksum(g_ui->st)==sum,"Save/load fixture changed simulation");check(slots(stats())==expected,"Saved neutral/rescue slots leaked into scores");}
 // A legitimate repeated faction represents independent AI players. Preserve
 // both rows, rather than merging their scores based on display text.
 game_load_functions edit(g_ui->st);auto a=*expected.begin(),b=*expected.rbegin();g_ui->st.players[a].force=g_ui->st.players[b].force=1;edit.game_st.forces[0].name="Shared Faction";
 int matches=0;for(auto& row:rows(stats()))if(row[19]=="Shared Faction")matches++;check(a==b||matches>=2,"Shared faction participants merged");
 edit.game_st.forces[0].name=" ---- ";check(g_campaign->score_faction_name(a).empty(),"Dash placeholder shown as faction");edit.game_st.forces[0].name="\xD0\xEE\xE9 \xE7\xE5\xF0\xE3\xEE\xE2";check(g_campaign->score_faction_name(a)==edit.game_st.forces[0].name,"Localized faction bytes altered");
 check(!g_ui->score_player_visible(-1)&&!g_ui->score_player_visible(8),"Invalid slot accepted");
 std::cout<<"PASS "<<checks<<" score roster checks; mission "<<code<<"; participants "<<expected.size()<<"\n";close_game();
}
static void melee(const std::string& output){
 int races[]={1,0,2,1,1,1,1,1},controllers[]={1,2,0,0,0,0,0,0};configured_init(640,480,0,races,controllers,0,true,false,false);check(slots(stats())==std::set<int>({0,1}),"Custom-game roster differs from occupied slots");for(auto& r:rows(stats()))check(r[19].empty(),"Melee exposed editor force names");
 g_ui->st.players[0].controller=player_t::controller_user_left;g_ui->st.players[1].controller=player_t::controller_computer_defeated;g_ui->st.players[0].initially_active=g_ui->st.players[1].initially_active=false;
 check(slots(stats())==std::set<int>({0,1}),"Left/defeated melee participant omitted");
 auto saved=save_game();restore_game(saved);check(slots(stats())==std::set<int>({0,1}),"Custom save lost initial score roster");
 // Playback/lightweight UIs have no recording header. Exercise every owner
 // category through that path, including a defeated player with zero score.
 g_ui->rep.slot_count=0;
 for(int c=0;c<=11;c++){for(auto& p:g_ui->st.players){p.controller=player_t::controller_inactive;p.initially_active=false;}g_ui->st.players[7].controller=c;g_ui->st.players[7].initially_active=true;
  bool included=c==1||c==2||c==10||c==11;check(g_ui->score_player_visible(7)==included,"Fallback controller filtering incorrect");check(slots(stats()).size()==(included?1:0),"Fallback score roster incorrect");}
 for(int i=0;i<8;i++){auto& p=g_ui->st.players[i];p.controller=i?player_t::controller_computer_game:player_t::controller_occupied;p.initially_active=true;p.race=race_t(i%3);p.color=i;}
 check(slots(stats()).size()==8,"Eight participants clipped");write(output,stats());
 close_game();configured_init(640,480,0,races,controllers,0,true,false,true);check(slots(stats())==std::set<int>({0,1}),"Nearby roster differs from occupied slots");for(auto& r:rows(stats()))check(r[19].empty(),"Nearby exposed editor force names");close_game();
 std::cout<<"PASS "<<checks<<" custom/Nearby score roster checks; saves, defeat, all controller categories, eight-row UI fixture\n";
}
int main(int argc,char** argv){try{check(argc==5,"Usage: score-slots11 CORE ARCHIVE CODE OUTPUT");std::string core=argv[1];open_archive(0,core+"/STARDAT.MPQ");open_archive(1,core+"/BROODAT.MPQ");open_archive(2,core+"/patch_rt.mpq");open_archive(3,argv[2]);int code=std::stoi(argv[3]);if(code)campaign(code,argv[4]);else melee(argv[4]);return 0;}catch(const std::exception& e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
