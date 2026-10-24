/* Browser adapter for unmodified libsmacker (LGPL-2.1-or-later).
 * Kept in its own replaceable WASM module; see vendor/libsmacker/COPYING. */
#include "smacker.h"
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#define EXPORT(n) __attribute__((export_name(#n)))
static unsigned char *input;
static unsigned input_size;
static smk clip;
static unsigned long width, height, frames;
static double interval;
#ifdef OPENBW_MENU_DECODER
#define MAX_WIDTH 356
#define MAX_HEIGHT 304
#define MAX_FRAMES 180
#else
#define MAX_WIDTH 128
#define MAX_HEIGHT 128
#define MAX_FRAMES 600
#endif
static unsigned char pixels[MAX_WIDTH * MAX_HEIGHT * 4];
static uint32_t u32(unsigned p) {
    return input[p] | (uint32_t)input[p+1]<<8 | (uint32_t)input[p+2]<<16 | (uint32_t)input[p+3]<<24;
}
EXPORT(portrait_close) void portrait_close(void) {
    if (clip) smk_close(clip);
    clip = NULL; free(input); input = NULL; input_size = 0;
}
EXPORT(portrait_input) unsigned char *portrait_input(unsigned n) {
    portrait_close();
    if (n < 104 || n > 4 * 1024 * 1024) return NULL;
    input = malloc(n); if (input) input_size = n; return input;
}
EXPORT(portrait_open) int portrait_open(void) {
    if (!input || (memcmp(input,"SMK2",4) && memcmp(input,"SMK4",4))) return 0;
    unsigned w=u32(4), h=u32(8), f=u32(12), flags=u32(20);
    if (!w || !h || w>MAX_WIDTH || h>MAX_HEIGHT || (w&3) || (h&3) || !f || f>MAX_FRAMES || (flags&~7u)) return 0;
    if ((uint64_t)w*h*f*4 > 32*1024*1024 || 104+(uint64_t)(f+(flags&1))*5>input_size) return 0;
    if (u32(52)>input_size) return 0;
    for (unsigned p=56;p<72;p+=4) if (u32(p)>1024*1024) return 0;
    clip=smk_open_memory(input,input_size); if (!clip) return 0;
    unsigned char scale;
    smk_info_all(clip,NULL,&frames,&interval); smk_info_video(clip,&width,&height,&scale);
    if (width!=w || height!=h || frames!=f || scale!=SMK_FLAG_Y_NONE) { portrait_close(); return 0; }
    smk_enable_all(clip,SMK_VIDEO_TRACK); // speech is already played by the game audio bridge.
    return (signed char)smk_first(clip)>=0;
}
EXPORT(portrait_width) unsigned portrait_width(void) { return width; }
EXPORT(portrait_height) unsigned portrait_height(void) { return height; }
EXPORT(portrait_frames) unsigned portrait_frames(void) { return frames; }
EXPORT(portrait_interval) double portrait_interval(void) { return interval/1000.; }
EXPORT(portrait_rgba) const unsigned char *portrait_rgba(void) {
    if (!clip) return NULL;
    const unsigned char *indices=smk_get_video(clip),*palette=smk_get_palette(clip);
    for (unsigned i=0;i<width*height;++i) {
        unsigned c=indices[i]*3; memcpy(pixels+i*4,palette+c,3);
#ifdef OPENBW_MENU_DECODER
        pixels[i*4+3]=indices[i] ? 255 : 0;
#else
        pixels[i*4+3]=255;
#endif
    }
    return pixels;
}
EXPORT(portrait_next) int portrait_next(void) { return clip ? (signed char)smk_next(clip) : -1; }
