#include "../native/runtime.cpp"
#include <iostream>
#include <sstream>
using namespace bwgame;
static int checks=0;
static void check(bool ok,const char* message){++checks;if(!ok)throw std::runtime_error(message);}
int main(int argc,char**argv){try{
 if(argc!=4)return 2;std::string core=argv[1];
 open_archive(0,core+"/STARDAT.MPQ");open_archive(1,core+"/BROODAT.MPQ");open_archive(2,core+"/patch_rt.mpq");open_archive(3,argv[2]);
 openbw_init_campaign(640,480,std::stoi(argv[3]));
 std::string stats=g_ui->stats_text();std::istringstream lines(stats);std::string line;std::getline(lines,line);int count=0;
 while(std::getline(lines,line)){
  std::vector<std::string> fields;size_t start=0;
  for(size_t p=0;p<=line.size();++p)if(p==line.size()||line[p]=='\t'){fields.emplace_back(line.substr(start,p-start));start=p+1;}
  check(fields.size()==20,"score transport missing optional faction column");int slot=std::stoi(fields[16]);int force=g_ui->st.players[slot].force;
  std::string expected;if(force>=1&&force<=4)for(unsigned char c:g_ui->game_st.forces[force-1].name)if(c>=32&&c!=127)expected+=char(c);
  check(fields[19]==expected,"slot faction does not match original map FORC/STR");++count;
 }
 check(count>0,"no original campaign score rows");
 game_load_functions fixture(g_ui->player.st());auto& force=fixture.game_st.forces[0];g_ui->st.players[0].force=1;g_ui->st.players[1].force=1;
 force.name="Shared Faction";check(g_campaign->score_faction_name(0)=="Shared Faction"&&g_campaign->score_faction_name(1)=="Shared Faction","shared-force slots differ");
 force.name="";check(g_campaign->score_faction_name(0).empty(),"empty name fallback");
 force.name="<null string>";check(g_campaign->score_faction_name(0).empty(),"invalid name fallback");
 force.name="Editor Force";g_campaign->melee_ai=true;check(g_campaign->score_faction_name(0).empty(),"melee leaked editor force names");g_campaign->melee_ai=false;
 g_ui->st.players[0].force=0;check(g_campaign->score_faction_name(0).empty(),"zero force indexed");g_ui->st.players[0].force=5;check(g_campaign->score_faction_name(0).empty(),"invalid force indexed");
 check(g_campaign->score_faction_name(-1).empty()&&g_campaign->score_faction_name(8).empty(),"invalid owner indexed");
 std::cout<<"PASS "<<checks<<" score metadata checks, campaign "<<argv[3]<<"\n";close_game();return 0;
}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
