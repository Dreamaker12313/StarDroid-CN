/* Bounded, frame-at-a-time adapter for libsmacker (LGPL-2.1-or-later).
 * Movie bytes stay on the user's device. This module contains no game data. */
#include "smacker.h"
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#define EXPORT(n) __attribute__((export_name(#n)))
static unsigned char *input, pixels[640*480*4];
static unsigned input_size, track=7;
static smk clip;
static unsigned long width,height,frames,rates[7];
static unsigned char channels[7],bits[7];
static double interval;
static uint32_t u32(unsigned p){return input[p]|(uint32_t)input[p+1]<<8|(uint32_t)input[p+2]<<16|(uint32_t)input[p+3]<<24;}
EXPORT(movie_close) void movie_close(void){if(clip)smk_close(clip);clip=NULL;free(input);input=NULL;input_size=0;track=7;}
EXPORT(movie_input) unsigned char *movie_input(unsigned n){movie_close();if(n<104||n>64*1024*1024)return NULL;input=malloc(n);if(input)input_size=n;return input;}
EXPORT(movie_open) int movie_open(void){
 if(!input||(memcmp(input,"SMK2",4)&&memcmp(input,"SMK4",4)))return 0;
 unsigned w=u32(4),h=u32(8),f=u32(12),flags=u32(20);
 if(!w||!h||w>640||h>480||(w&3)||(h&3)||!f||f>18000||(flags&~7u)||104+(uint64_t)(f+(flags&1))*5>input_size||u32(52)>input_size)return 0;
 for(unsigned p=56;p<72;p+=4)if(u32(p)>1024*1024)return 0;
 for(unsigned p=24;p<52;p+=4)if(u32(p)>4*1024*1024)return 0;
 clip=smk_open_memory(input,input_size);if(!clip)return 0;
 /* libsmacker now owns copies of compressed chunks; free the input copy. */
 free(input);input=NULL;input_size=0;
 unsigned char scale,mask;smk_info_all(clip,NULL,&frames,&interval);smk_info_video(clip,&width,&height,&scale);
 if(width!=w||height!=h||frames!=f||scale!=SMK_FLAG_Y_NONE||interval<10000||interval>1000000){movie_close();return 0;}
 smk_info_audio(clip,&mask,channels,bits,rates);
 for(unsigned i=0;i<7;i++)if(mask&(1<<i)){if(channels[i]<1||channels[i]>2||(bits[i]!=8&&bits[i]!=16)||rates[i]<8000||rates[i]>48000){movie_close();return 0;}track=i;break;}
 smk_enable_all(clip,SMK_VIDEO_TRACK|(track<7?(1<<track):0));return (signed char)smk_first(clip)>=0;
}
EXPORT(movie_width) unsigned movie_width(void){return width;}
EXPORT(movie_height) unsigned movie_height(void){return height;}
EXPORT(movie_frames) unsigned movie_frames(void){return frames;}
EXPORT(movie_interval) double movie_interval(void){return interval/1000.;}
EXPORT(movie_channels) unsigned movie_channels(void){return track<7?channels[track]:0;}
EXPORT(movie_bits) unsigned movie_bits(void){return track<7?bits[track]:0;}
EXPORT(movie_rate) unsigned movie_rate(void){return track<7?rates[track]:0;}
EXPORT(movie_audio) const unsigned char *movie_audio(void){return clip&&track<7?smk_get_audio(clip,track):NULL;}
EXPORT(movie_audio_size) unsigned movie_audio_size(void){return clip&&track<7?smk_get_audio_size(clip,track):0;}
EXPORT(movie_rgba) const unsigned char *movie_rgba(void){if(!clip)return NULL;const unsigned char *ix=smk_get_video(clip),*pal=smk_get_palette(clip);for(unsigned i=0;i<width*height;i++){memcpy(pixels+i*4,pal+ix[i]*3,3);pixels[i*4+3]=255;}return pixels;}
EXPORT(movie_next) int movie_next(void){return clip?(signed char)smk_next(clip):-1;}
