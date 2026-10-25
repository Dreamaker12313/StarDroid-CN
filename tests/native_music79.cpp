#include "data_loading.h"
#include "../native/audio.h"
#include <iostream>

static void require(bool value, const char* message) {
    if (!value) throw std::runtime_error(message);
}

static std::vector<double> envelope(const naudio::Clip& clip, size_t start) {
    std::vector<double> out(1500);
    for (size_t i = 0; i != out.size(); ++i) {
        double energy = 0;
        for (int n = 0; n != 220; ++n) {
            size_t p = (start + i * 220 + n) * clip.channels;
            double sample = (clip.pcm.at(p) + clip.pcm.at(p + clip.channels - 1)) / 2;
            energy += sample * sample;
        }
        out[i] = std::sqrt(energy / 220);
    }
    return out;
}

static double correlation(const std::vector<double>& a, const std::vector<double>& b) {
    double sa=0, sb=0, aa=0, bb=0, ab=0;
    for (size_t i=0; i!=a.size(); ++i) {sa+=a[i];sb+=b[i];aa+=a[i]*a[i];bb+=b[i]*b[i];ab+=a[i]*b[i];}
    return (ab-sa*sb/a.size()) / std::sqrt((aa-sa*sa/a.size())*(bb-sb*sb/a.size()));
}

// Private supplied music is decoded in memory only. No game audio is distributed.
int main(int argc, char** argv) {
    try {
        if (argc != 5) return 2;
        std::array<size_t,3> originalFrames{};
        std::array<std::vector<double>,3> originalEnvelope;
        for (int version = 0; version != 2; ++version) {
            bwgame::data_loading::mpq_file<> source(argv[version + 1]);
            bwgame::data_loading::mpq_file<> imported(argv[version + 3]);
            size_t raceIndex=0;
            for (const char* race : {"terran", "zerg", "protoss"}) {
                std::string name = std::string("music\\") + race + "1.wav";
                bwgame::a_vector<uint8_t> original, retained;
                source(original, name.c_str());
                imported(retained, name.c_str());
                require(original == retained, "Import truncated or altered the combined music file");
                auto clip = naudio::wav(retained.data(), retained.size());
                size_t frames = clip->pcm.size() / clip->channels;
                require(frames > size_t(clip->rate * (version ? 500 : 270)), "Unexpected shortened original music");
                require(clip->rate==22050, "Original music fixture has an unexpected sample rate");
                if (!version) {
                    originalFrames[raceIndex]=frames;
                    originalEnvelope[raceIndex]=envelope(*clip, 5*clip->rate);
                } else {
                    size_t offset=frames-originalFrames[raceIndex];
                    // MPQ sound compression is lossy. Compare short RMS windows
                    // around the expected appended-theme boundary, not PCM hashes.
                    double match=-1;
                    for (int shift=-220;shift<=220;shift+=22)
                        match=std::max(match,correlation(originalEnvelope[raceIndex],envelope(*clip,offset+5*clip->rate+shift)));
                    require(match>.8, "Original first theme was not found in the combined Brood War track");
                    std::cout << "PASS " << race << " original theme embedded after " << double(offset)/clip->rate
                              << " seconds; energy correlation=" << match << '\n';
                }
                naudio::play_clip(clip, 63);
                // Sample beyond both the expansion/original boundary and eight
                // minutes: the original portion must remain audible and active.
                for (int seconds : version ? std::vector<int>{270, 300, 480} : std::vector<int>{30, 240}) {
                    naudio::voices[63].position = size_t(seconds) * clip->rate;
                    int16_t out[4096];
                    naudio::mix(out, 2048, clip->rate);
                    require(naudio::playing(63), "Music stopped before the original theme finished");
                    require(std::any_of(out, out + 4096, [](int16_t value) { return value != 0; }), "Music tail was silent");
                }
                naudio::voices[63].position = frames - 1;
                int16_t tail[4];
                naudio::mix(tail, 1, clip->rate);
                require(naudio::playing(63), "Music discarded its final sample");
                naudio::mix(tail, 1, clip->rate);
                require(!naudio::playing(63), "Music failed to finish at the full WAV length");
                std::cout << "PASS " << (version ? "BroodWar " : "StarCraft ") << race
                          << "1 imported byte-identically; full native duration="
                          << double(frames) / clip->rate << " seconds; tail and end-of-track verified\n";
                ++raceIndex;
            }
        }
    } catch (const std::exception& e) {
        std::cerr << "FAIL " << e.what() << '\n';
        return 1;
    }
}
