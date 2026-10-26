#include "data_loading.h"
#include "../native/audio.h"
#include <iostream>
#include <fstream>
#ifdef STARDROID_NEXT_TRACK_TEST
// These are the exact JNI entry points extracted from native/runtime.cpp.
#include "music-seek-jni.h"
#endif

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

#ifdef STARDROID_NEXT_TRACK_TEST
static void verify_seek(const std::shared_ptr<naudio::Clip>& clip, int milliseconds) {
    naudio::play_clip(clip, 63);
    Java_org_openbw_androidtest_NativeBridge_seekSound(nullptr, nullptr, 63, milliseconds);
    const double target=double(milliseconds)*clip->rate/1000.;
    require(std::abs(naudio::voices[63].position-target)<1e-7, "JNI seek overflowed or selected the wrong PCM offset");
    require(std::abs(Java_org_openbw_androidtest_NativeBridge_soundPosition(nullptr,nullptr,63)-milliseconds)<1e-7,
            "JNI seek position was not reported in milliseconds");
    Java_org_openbw_androidtest_NativeBridge_seekSound(nullptr,nullptr,63,-1);
    Java_org_openbw_androidtest_NativeBridge_seekSound(nullptr,nullptr,64,milliseconds);
    require(std::abs(naudio::voices[63].position-target)<1e-7,"Invalid seek changed playback");
    constexpr int count=2048;int16_t out[count*2];const float volume=naudio::music;
    naudio::mix(out,count,clip->rate);
    const size_t frames=clip->pcm.size()/clip->channels;
    for(int i=0;i<count;++i) {
        const double offset=target+i;size_t p=size_t(offset),q=std::min(p+1,frames-1);float f=float(offset-p);
        for(int channel=0;channel<2;++channel) {
            int ch=channel?clip->channels-1:0;
            float sample=(clip->pcm.at(p*clip->channels+ch)*(1-f)+clip->pcm.at(q*clip->channels+ch)*f)*volume;
            int16_t expected=int16_t(std::max(-1.f,std::min(.9999f,sample))*32767);
            require(out[i*2+channel]==expected,"PCM output after JNI seek differs from selected track offset");
        }
    }
    require(std::abs(naudio::voices[63].position-(target+count))<1e-7,"Seeked music failed to continue playing");
    Java_org_openbw_androidtest_NativeBridge_seekSound(nullptr,nullptr,63,2147483647);
    require(naudio::voices[63].position==double(frames),"Oversized seek did not clamp to EOF");
    naudio::mix(out,1,clip->rate);require(!naudio::playing(63),"Seek to EOF failed to complete");
}
#endif

// Private supplied music is decoded in memory only. No game audio is distributed.
int main(int argc, char** argv) {
    try {
        if (argc != 5 && argc != 6) return 2;
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
                if (argc == 6) {
                    std::ofstream out(std::string(argv[5]) + "/" + race + (version ? "-bw.wav" : "-sc.wav"), std::ios::binary);
                    out.write(reinterpret_cast<const char*>(retained.data()), retained.size());
                    require(bool(out), "Could not write private music test fixture");
                }
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
#ifdef STARDROID_NEXT_TRACK_TEST
                    int boundary=int((1000*offset+clip->rate-1)/clip->rate);
                    verify_seek(clip,boundary);verify_seek(clip,boundary+5000);
                    std::cout << "PASS " << race << " exact production JNI seekSound/soundPosition at " << boundary
                              << " ms; 8192 stereo PCM samples match the requested theme offsets; oversized/invalid seeks safe\n";
#endif
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
                // The other two complete files finish each four-theme BW loop.
                for (int track = 2; track <= 3; ++track) {
                    name = std::string("music\\") + race + std::to_string(track) + ".wav";
                    source(original, name.c_str()); imported(retained, name.c_str());
                    require(original == retained, "Import altered a later race theme");
                    auto later = naudio::wav(retained.data(), retained.size());
                    size_t total = later->pcm.size() / later->channels;
                    require(total > size_t(later->rate * 30), "Later race theme missing or shortened");
                    require(std::any_of(later->pcm.begin(), later->pcm.end(), [](float v) { return v != 0; }), "Later race theme is silent");
                    naudio::play_clip(later, 63); naudio::voices[63].position = total - 1;
                    naudio::mix(tail, 1, later->rate); require(naudio::playing(63), "Later theme final sample discarded");
                    naudio::mix(tail, 1, later->rate); require(!naudio::playing(63), "Later theme did not advance at EOF");
                    std::cout << "PASS " << (version ? "BroodWar " : "StarCraft ") << race << track
                              << " imported byte-identically, decoded and played through EOF; duration=" << double(total) / later->rate << " seconds\n";
                }
                ++raceIndex;
            }
        }
    } catch (const std::exception& e) {
        std::cerr << "FAIL " << e.what() << '\n';
        return 1;
    }
}
