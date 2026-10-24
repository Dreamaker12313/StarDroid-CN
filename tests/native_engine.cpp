#include "../native/runtime.cpp"
#include <fstream>
#include <chrono>
int main(int argc,char** argv){
 try{
  std::string dir=argc>1?argv[1]:"/tmp/openbw-test-data";
  open_archive(0,dir+"/STARDAT.MPQ");open_archive(1,dir+"/BROODAT.MPQ");open_archive(2,dir+"/patch_rt.mpq");
  int code=argc>2?atoi(argv[2]):102,ticks=argc>3?atoi(argv[3]):2400;
  bool expansion=code>=300;open_archive(3,dir+(expansion?"/BroodWar.mpq":"/StarCraft.mpq"));
  auto start=std::chrono::steady_clock::now();openbw_init_campaign(640,480,code);openbw_set_external_cursor(1);
  for(int i=0;i<ticks;i++){openbw_step();if(i%24==0)openbw_render(i*42.);}
  openbw_render(ticks*42.);auto elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
  if(!g_campaign->ai_error.empty())throw std::runtime_error(g_campaign->ai_error.c_str());
  if(argc>4){std::ofstream out(argv[4],std::ios::binary);out<<"P6\n640 480\n255\n";auto* f=openbw_framebuffer();for(int i=0;i<640*480;i++)out.write((const char*)f+i*4,3);}
  std::vector<int16_t> samples(48000*2);naudio::mix(samples.data(),48000,48000);size_t nonzero=0;for(auto v:samples)if(v)++nonzero;
  printf("NATIVE_RESULT {\"mission\":%d,\"frames\":%d,\"outcome\":%d,\"seconds\":%.3f,\"audioSamples\":%zu,\"checksum\":%u}\n",code,openbw_frame(),openbw_outcome(),elapsed,nonzero,openbw_checksum());
  close_game();return 0;
 }catch(const std::exception& e){fprintf(stderr,"NATIVE_ERROR %s\n",e.what());return 1;}
}
