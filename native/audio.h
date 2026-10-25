#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <memory>
#include <mutex>
#include <stdexcept>
#include <vector>
namespace naudio {
struct Clip { int rate=22050, channels=1; std::vector<float> pcm; };
struct Voice { std::shared_ptr<Clip> clip; double position=0; float left=1,right=1; bool loop=false; int effect_id=-1; };
static std::mutex mutex;
static std::vector<std::shared_ptr<Clip>> clips;
static std::array<Voice,64> voices;
static float effects=1,music=.65f;
static bool paused=false;
inline uint32_t u32(const uint8_t* p){return p[0]|uint32_t(p[1])<<8|uint32_t(p[2])<<16|uint32_t(p[3])<<24;}
inline unsigned u16(const uint8_t* p){return p[0]|unsigned(p[1])<<8;}
inline std::shared_ptr<Clip> wav(const uint8_t* b,size_t len){
 if(len<12||memcmp(b,"RIFF",4)||memcmp(b+8,"WAVE",4))throw std::runtime_error("Invalid WAV");
 unsigned format=0,channels=0,rate=0,bits=0,align=0;const uint8_t* data=nullptr;size_t size=0;
 for(size_t p=12;p+8<=len;){size_t n=u32(b+p+4);if(n>len-p-8)throw std::runtime_error("Truncated WAV");
  if(!memcmp(b+p,"fmt ",4)&&n>=16){format=u16(b+p+8);channels=u16(b+p+10);rate=u32(b+p+12);align=u16(b+p+20);bits=u16(b+p+22);}
  if(!memcmp(b+p,"data",4)){data=b+p+8;size=n;}p+=8+n+(n&1);
 }
 if(!data||channels<1||channels>2||rate<4000||rate>192000||size>128*1024*1024)throw std::runtime_error("Unsupported WAV parameters");
 auto c=std::make_shared<Clip>();c->rate=rate;c->channels=channels;
 if(format==1&&(bits==8||bits==16)){
  c->pcm.resize(size/(bits/8));for(size_t i=0;i<c->pcm.size();++i)c->pcm[i]=bits==8?(int(data[i])-128)/128.f:int16_t(u16(data+i*2))/32768.f;
 }else if(format==17&&bits==4&&align>=4*channels){
  static const int steps[89]={7,8,9,10,11,12,13,14,16,17,19,21,23,25,28,31,34,37,41,45,50,55,60,66,73,80,88,97,107,118,130,143,157,173,190,209,230,253,279,307,337,371,408,449,494,544,598,658,724,796,876,963,1060,1166,1282,1411,1552,1707,1878,2066,2272,2499,2749,3024,3327,3660,4026,4428,4871,5358,5894,6484,7132,7845,8630,9493,10442,11487,12635,13899,15289,16818,18500,20350,22385,24623,27086,29794,32767};
  static const int adjust[8]={-1,-1,-1,-1,2,4,6,8};
  for(size_t base=0;base+4*channels<=size;base+=align){size_t end=std::min(size,base+align);int pred[2],idx[2];std::vector<float> lane[2];
   for(unsigned k=0;k<channels;k++){pred[k]=int16_t(u16(data+base+k*4));idx[k]=std::min(88,int(data[base+k*4+2]));lane[k].push_back(pred[k]/32768.f);}
   unsigned ch=0;for(size_t p=base+4*channels;p<end;){for(unsigned j=0;j<4&&p<end;j++,p++)for(int h=0;h<2;h++){
    int n=(data[p]>>(h*4))&15,step=steps[idx[ch]],diff=step/8;if(n&1)diff+=step/4;if(n&2)diff+=step/2;if(n&4)diff+=step;
    pred[ch]=std::max(-32768,std::min(32767,pred[ch]+((n&8)?-diff:diff)));idx[ch]=std::max(0,std::min(88,idx[ch]+adjust[n&7]));lane[ch].push_back(pred[ch]/32768.f);
   }ch=(ch+1)%channels;}
   size_t frames=lane[0].size();if(channels==2)frames=std::min(frames,lane[1].size());for(size_t i=0;i<frames;i++)for(unsigned k=0;k<channels;k++)c->pcm.push_back(lane[k][i]);
  }
 }else throw std::runtime_error("Unsupported WAV codec "+std::to_string(format));
 if(c->pcm.empty())throw std::runtime_error("Empty WAV");return c;
}
inline int add(const void* b,size_t n){auto c=wav((const uint8_t*)b,n);std::lock_guard<std::mutex> l(mutex);clips.push_back(c);return int(clips.size()-1);}
inline void play(int id,int ch,int volume,int pan,bool loop=false){std::lock_guard<std::mutex> l(mutex);if(ch<0||ch>=64)return;auto& v=voices[ch];v={};if(id<0||size_t(id)>=clips.size())return;v.clip=clips[id];v.left=volume/128.f*(pan>0?1-pan/128.f:1);v.right=volume/128.f*(pan<0?1+pan/128.f:1);v.loop=loop;}
inline void stop(int ch){std::lock_guard<std::mutex> l(mutex);if(ch>=0&&ch<64)voices[ch]={};}
inline bool playing(int ch){std::lock_guard<std::mutex> l(mutex);return ch>=0&&ch<64&&bool(voices[ch].clip);}
inline void clear(){std::lock_guard<std::mutex> l(mutex);for(auto& v:voices)v={};clips.clear();}
// Channels 57..63 own menu/briefing clips independently of simulation handles.
// Lobby roster changes rebuild the world while its menu transition is playing.
inline void clear_game(){std::lock_guard<std::mutex> l(mutex);for(int i=0;i<57;i++)voices[i]={};clips.clear();}
inline void play_clip(std::shared_ptr<Clip> clip,int channel){std::lock_guard<std::mutex> l(mutex);voices[channel]={};voices[channel].clip=std::move(clip);}
// Trigger Play WAV effects have their own pool. They cannot replace dialogue,
// music, movies or ordinary unit speech; repeated active effects are coalesced.
inline bool effect_playing(int id){std::lock_guard<std::mutex> l(mutex);for(int i=48;i<56;i++)if(voices[i].clip&&voices[i].effect_id==id)return true;return false;}
inline void play_effect(std::shared_ptr<Clip> clip,int id){
 std::lock_guard<std::mutex> l(mutex);int chosen=48;
 for(int i=48;i<56;i++){
  if(voices[i].clip&&voices[i].effect_id==id)return;
  if(!voices[i].clip){chosen=i;break;}
  if(voices[i].position/voices[i].clip->rate>voices[chosen].position/voices[chosen].clip->rate)chosen=i;
 }
 voices[chosen]={};voices[chosen].clip=std::move(clip);voices[chosen].effect_id=id;
}
inline std::shared_ptr<Clip> score_clip(const Clip& fill,const Clip& end,int milliseconds){
 if(milliseconds<500||milliseconds>10000)throw std::runtime_error("Invalid score duration");
 auto out=std::make_shared<Clip>();out->rate=fill.rate;out->channels=fill.channels;
 size_t frames=size_t(milliseconds)*out->rate/1000;
 size_t tail=std::min(frames/2,size_t(double(end.pcm.size()/end.channels)*out->rate/end.rate));
 size_t start=frames-tail,fade=std::min(size_t(out->rate/100),start);
 out->pcm.resize(frames*out->channels);
 for(size_t i=0;i<frames;i++)for(int ch=0;ch<out->channels;ch++){
  float v;
  if(i<start){v=fill.pcm[(i%(fill.pcm.size()/fill.channels))*fill.channels+ch];if(i+fade>start)v*=float(start-i)/fade;}
  else{size_t p=std::min(end.pcm.size()/end.channels-1,size_t(double(i-start)*end.rate/out->rate));v=end.pcm[p*end.channels+std::min(ch,end.channels-1)];if(i-start<fade)v*=float(i-start)/fade;}
  if(i+fade>frames)v*=float(frames-i-1)/fade;
  out->pcm[i*out->channels+ch]=v;
 }
 return out;
}
inline double position_ms(int channel){std::lock_guard<std::mutex> l(mutex);auto& v=voices[channel];return v.clip?1000.*v.position/v.clip->rate:-1;}
inline void mix(int16_t* out,int frames,int sampleRate){
 std::lock_guard<std::mutex> l(mutex);std::fill(out,out+frames*2,0);if(paused)return;
 for(int i=0;i<frames;i++){float left=0,right=0;for(int channel=0;channel<64;channel++){auto& v=voices[channel];if(!v.clip)continue;auto& c=*v.clip;size_t count=c.pcm.size()/c.channels;
   if(v.position>=count){if(v.loop)v.position=fmod(v.position,double(count));else{v.clip.reset();continue;}}
   size_t p=size_t(v.position),q=std::min(p+1,count-1);float f=float(v.position-p),vol=channel==63?music:effects;
   float a=c.pcm[p*c.channels]*(1-f)+c.pcm[q*c.channels]*f,b=c.pcm[p*c.channels+c.channels-1]*(1-f)+c.pcm[q*c.channels+c.channels-1]*f;
   left+=a*v.left*vol;right+=b*v.right*vol;v.position+=double(c.rate)/sampleRate;
  }out[2*i]=int16_t(std::max(-1.f,std::min(.9999f,left))*32767);out[2*i+1]=int16_t(std::max(-1.f,std::min(.9999f,right))*32767);
 }
}
}
