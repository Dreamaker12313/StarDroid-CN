// No proprietary data. Build with -Ibuild-engine and run after applying the patch.
#include "data_loading.h"
#include <cassert>
#include <iostream>
using namespace bwgame::data_loading;
int main() {
    uint8_t mono[] = {0, 4, 0xe8, 3, 0x80, 0x80}; // repeated 1000 samples
    uint8_t stereo[] = {0, 4, 0xe8, 3, 0x18, 0xfc, 0x80, 0x80};
    uint8_t out[16];
    memset(out, 0x5a, sizeof out);
    assert(decompress_adpcm(mono, sizeof mono, out, 6, 1) == 6);
    for (int i=0;i<6;i+=2) assert((value_at<int16_t,true>(out+i) == 1000));
    assert(out[6] == 0x5a);
    assert(decompress_adpcm(stereo, sizeof stereo, out, 8, 2) == 8);
    for (int i=0;i<8;i+=2) assert((value_at<int16_t,true>(out+i) == (i%4 ? -1000 : 1000)));
    bool rejected = false;
    memset(out, 0x5a, sizeof out);
    try { decompress_adpcm(mono, sizeof mono, out, 5, 1); } catch (const bwgame::exception&) { rejected = true; }
    assert(rejected && out[4] == 0x5a && out[5] == 0x5a);
    // End of a stereo stream can follow a control byte without another sample.
    uint8_t tail[] = {0, 4, 0, 0, 0, 0, 0x81};
    assert(decompress_adpcm(tail, sizeof tail, out, 4, 2) == 4);
    std::cout << "PASS: mono/stereo sample values, exact boundaries, rejected short output and control-byte tail\n";
}
