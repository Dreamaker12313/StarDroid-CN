// Real-data campaign smoke/save continuation harness. Original game archives
// remain external. This deliberately does not call itself a full playthrough.
#include <execinfo.h>
#include "../native/runtime.cpp"
#include <fstream>
#include <iostream>
#include <chrono>
#include <csignal>
#include <execinfo.h>
static void require(bool ok,const char* message) {if(!ok)throw std::runtime_error(message);}
static std::string quote(const std::string& v) {
    std::string out="\"";for(unsigned char c:v){if(c=='\\'||c=='\"'){out+='\\';out+=c;}else if(c=='\n')out+="\\n";else if(c=='\r')out+="\\r";else if(c=='\t')out+="\\t";else if(c>=32)out+=c;}return out+'\"';
}
static std::set<unsigned> burrowed_lurkers;
static void advance(int frames) {for(int i=0;i<frames&&!g_ui->outcome;++i){native_step();for(int owner:{3,4})for(auto* u:ptr(g_ui->st.player_units[owner]))if(g_ui->unit_is(u,bwgame::UnitTypes::Zerg_Lurker)&&g_ui->u_burrowed(u))burrowed_lurkers.insert(g_ui->get_unit_id(u).raw_value);}}
static size_t live_units() {size_t n=0;for(auto& list:g_ui->st.player_units)for(auto* u:ptr(list))if(!g_ui->unit_dying(u)&&!g_ui->ut_turret(u))++n;return n;}
static size_t first_difference(const std::vector<uint8_t>& a,const std::vector<uint8_t>& b) {size_t i=0;while(i<a.size()&&i<b.size()&&a[i]==b[i])++i;return i;}
#include "native_objective_attempts.h"
#include "native_campaign_cases.h"
int main(int argc,char** argv) {
    std::cout.setf(std::ios::unitbuf);
    signal(SIGSEGV,[](int){void* trace[60];int n=backtrace(trace,60);backtrace_symbols_fd(trace,n,2);_exit(139);});
    std::string phase="arguments";
    try {
        require(argc>=5,"Usage: native-campaigns DATA_DIR MAP_MPQ MISSION_CODE FRAMES [REPORT] [SCREENSHOT_PPM]");
        std::string dir=argv[1],map=argv[2];int code=std::stoi(argv[3]),frames=std::stoi(argv[4]);
        auto start=std::chrono::steady_clock::now();
        open_archive(0,dir+"/STARDAT.MPQ");open_archive(1,dir+"/BROODAT.MPQ");open_archive(2,dir+"/patch_rt.mpq");open_archive(3,map);
        phase="initialization";openbw_init_campaign(640,480,code);openbw_set_external_cursor(1);
        size_t initial=live_units();phase="simulation";advance(frames);
        if(argc>7){phase=argv[7];if(phase=="objectives")attempt_mission_objectives(code);else campaign_case(phase);}
        openbw_render(openbw_frame()*42.);
        int frame=openbw_frame(),outcome=openbw_outcome();size_t alive=live_units();
        auto ai_error=g_campaign->ai_error;size_t ai_threads=g_campaign->threads.size();
        if(argc>6&&std::string(argv[6])!="-"){std::ofstream out(argv[6],std::ios::binary);out<<"P6\n640 480\n255\n";auto* f=openbw_framebuffer();for(int i=0;i<640*480;++i)out.write(reinterpret_cast<const char*>(f)+i*4,3);}
        native_save::HostState host;phase="save";auto saved=native_save::save(*g_ui,g_campaign,host);
        phase="uninterrupted continuation";advance(240);auto checksum=openbw_checksum();auto continued=native_save::save(*g_ui,g_campaign,host);
        phase="reload map";close_game();openbw_init_campaign(640,480,code);openbw_set_external_cursor(1);
        phase="restore";auto restored_host=native_save::restore(*g_ui,g_campaign,saved);
        auto restored=native_save::save(*g_ui,g_campaign,restored_host);
        phase="restored continuation";advance(240);auto resumed_checksum=openbw_checksum();auto resumed=native_save::save(*g_ui,g_campaign,restored_host);
        bool immediate=saved==restored,deterministic=continued==resumed;
        phase="restored render";openbw_render(openbw_frame()*42.);
        auto seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
        bool pass=ai_error.empty()&&g_campaign->ai_error.empty()&&immediate&&deterministic&&checksum==resumed_checksum;
        std::string report="{\"passed\":"+std::string(pass?"true":"false")+",\"missionCode\":"+std::to_string(code)+",\"requestedFrames\":"+std::to_string(frames)+",\"frame\":"+std::to_string(frame)+",\"outcome\":"+std::to_string(outcome)+",\"initialUnits\":"+std::to_string(initial)+",\"liveUnits\":"+std::to_string(alive)+",\"aiThreads\":"+std::to_string(ai_threads)+",\"aiError\":"+quote(ai_error.c_str())+",\"snapshotBytes\":"+std::to_string(saved.size())+",\"restoreIdentical\":"+(immediate?"true":"false")+",\"continuationIdentical\":"+(deterministic?"true":"false")+",\"checksumEqual\":"+(checksum==resumed_checksum?"true":"false")+",\"restoreFirstDifference\":"+std::to_string(first_difference(saved,restored))+",\"continuationFirstDifference\":"+std::to_string(first_difference(continued,resumed))+",\"seconds\":"+std::to_string(seconds)+",\"victoryAttempted\":"+std::string(victory_attempted?"true":"false")+",\"objectiveAssists\":"+std::to_string(objective_assists)+",\"fullPlaythrough\":false}\n";
        if(argc>5)std::ofstream(argv[5])<<report;std::cout<<"CAMPAIGN_RESULT "<<report;close_game();return pass?0:1;
    }catch(const std::exception& e){std::cerr<<"CAMPAIGN_ERROR phase="<<phase<<" "<<e.what()<<'\n';return 2;}
}
