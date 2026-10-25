// open_movie/movie_frame are extracted unchanged from native/runtime.cpp by the runner.
#include "movie-runtime80.h"
#include <fstream>
#include <iostream>
#include <cstdio>
static void require(bool value,const char* why){if(!value)throw std::runtime_error(why);}
static uint64_t hash_bytes(const void* data,size_t size) {
 const uint8_t* bytes=static_cast<const uint8_t*>(data);uint64_t h=14695981039346656037ull;
 for(size_t i=0;i<size;++i){h^=bytes[i];h*=1099511628211ull;}return h;
}
static uint64_t hash_image(const Movie* movie){return hash_bytes(movie->rgba.data(),movie->rgba.size());}
struct Playback {
 unsigned long frames,width,height;double duration;uint64_t first,middle,last,rewind,audio;size_t audioSamples;
 bool operator==(const Playback& b)const{return frames==b.frames&&width==b.width&&height==b.height&&duration==b.duration&&first==b.first&&middle==b.middle&&last==b.last&&rewind==b.rewind&&audio==b.audio&&audioSamples==b.audioSamples;}
};
static Playback play(int id) {
 auto* movie=movies[id].get();require(movie&&movie->frames>10,"Movie did not initialize");
 auto clip=naudio::voices[60].clip;require(clip&&!clip->pcm.empty(),"Cinematic audio missing");
 require(std::any_of(clip->pcm.begin(),clip->pcm.end(),[](float s){return s!=0;}),"Cinematic audio is silent");
 Playback result{};result.frames=movie->frames;result.width=movie->width;result.height=movie->height;
 result.audioSamples=clip->pcm.size();result.audio=hash_bytes(clip->pcm.data(),clip->pcm.size()*sizeof(float));
 result.first=hash_image(movie_frame(id,0,false));
 double end=(movie->frames-1)*movie->us/1000.;result.duration=end/1000.;
 result.middle=hash_image(movie_frame(id,end/2,false));result.last=hash_image(movie_frame(id,end+1,false));
 require(movie->current==movie->frames-1,"Movie did not reach its final video frame");
 require(result.first!=result.middle||result.middle!=result.last,"Cinematic video failed to advance");
 result.rewind=hash_image(movie_frame(id,0,false));
 if(result.rewind!=result.first)std::cerr<<"Decoder note: rewind first frame differs from initial frame (baseline behavior)\n";
 naudio::voices[60].position=clip->pcm.size()/clip->channels-1;int16_t tail[4];naudio::mix(tail,2,clip->rate);
 require(!naudio::playing(60),"Movie audio failed to finish normally");
 return result;
}
int main(int argc,char** argv) {
 try {
  if(argc!=4)return 2;
  int id=-1;Playback reference;
  {
   bwgame::data_loading::mpq_file<> source(argv[1]),temporary(argv[2]);
   bwgame::a_vector<uint8_t> original,requested;
   source(original,argv[3]);temporary(requested,argv[3]);
   require(original==requested,"Single-movie cache changed SMK bytes");
   std::cerr<<"CHECK_PHASE baseline\n";
   int baseline=open_movie(original.data(),original.size(),true);reference=play(baseline);movies[baseline].reset();
   std::cerr<<"CHECK_PHASE candidate\n";
   id=open_movie(requested.data(),requested.size(),true);
  } // Both MPQs and source byte buffers are gone before candidate playback begins.
  require(std::remove(argv[2])==0,"Could not remove temporary movie archive");
  require(!std::ifstream(argv[2]).good(),"Temporary archive still exists before playback");
  Playback result=play(id);require(result==reference,"Cinematic video/audio differs from original archive playback");
  movies[id].reset();require(!naudio::playing(60),"Closed cinematic left audio playing");
  require(!std::ifstream(argv[2]).good(),"Temporary archive reappeared during playback");
  std::cout<<"PASS "<<argv[3]<<": byte-identical; "<<result.duration<<"s video/audio survives archive deletion; original frame/PCM/rewind parity, audio end\n";
 }catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
}
