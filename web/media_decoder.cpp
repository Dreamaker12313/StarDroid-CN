// Bounded, standalone MPQ decoder. Reuses OpenBW's original Storm codecs.
// The JS host supplies a sparse archive, so a CD-sized MPQ is never allocated.
#include "data_loading.h"
using namespace bwgame;
extern "C" {
__attribute__((import_module("env"), import_name("read_archive")))
void read_archive(void*, unsigned, unsigned);
__attribute__((import_module("env"), import_name("archive_size")))
unsigned archive_size();
}
struct archive_reader {
    size_t position = 0;
    explicit archive_reader(a_string) {}
    void get_bytes(uint8_t* dst, size_t n) { read_archive(dst, position, n); position += n; }
    void seek(size_t p) { position = p; }
    size_t tell() { return position; }
    size_t size() { return archive_size(); }
};
using archive_t = data_loading::mpq_file<archive_reader>;
static archive_t* archive = nullptr;
static a_vector<uint8_t> bytes;
static char name[256];
#define EXPORT(n) __attribute__((export_name(#n))) extern "C"
EXPORT(asset_name) char* asset_name() { return name; }
EXPORT(asset_reset) void asset_reset() { delete archive; archive = nullptr; bytes.clear(); }
EXPORT(asset_read) const uint8_t* asset_read() {
    bytes.clear(); name[255] = 0;
    if (!archive) archive = new archive_t("");
    auto& mpq = archive->mpq;
    auto* hash = mpq.find_hash_table_entry(name);
    if (!hash || hash->block_index >= mpq.block_table.size()) return nullptr;
    const auto& block = mpq.block_table[hash->block_index];
    if (block.size > 64 * 1024 * 1024) return nullptr;
    // OpenBW's game reader expects sector-compressed files. CD music may also
    // be stored verbatim. Handle that form without inventing a sector table.
    if (!(block.flags & 0x300)) {
        if (block.compressed_size != block.size) return nullptr;
        bytes.resize(block.size); read_archive(bytes.data(), block.data_offset, block.size);
        if (block.flags & 0x10000) {
            const char* base = name;
            for (const char* p=name;*p;++p) if (*p=='/' || *p=='\\') base=p+1;
            uint32_t key = data_loading::string_hash(base,3,mpq.crypt_table);
            if (block.flags & 0x20000) key=(key+block.data_offset)^block.size;
            size_t sector = block.flags & 0x1000000 ? block.size : mpq.sector_size;
            for(size_t start=0,i=0;start<bytes.size();start+=sector,++i) {
                uint32_t k=key+(uint32_t)i,seed=0xeeeeeeee;
                size_t end=std::min(start+sector,bytes.size());
                for(size_t p=start;p+4<=end;p+=4) {
                    seed+=mpq.crypt_table[1024+(k&255)];
                    uint32_t plain=data_loading::value_at<uint32_t,true>(bytes.data()+p)^(k+seed);
                    data_loading::set_value_at<true>(bytes.data()+p,plain);
                    k=((~k<<21)+0x11111111)|(k>>11);seed=plain+seed+(seed<<5)+3;
                }
            }
        }
        return bytes.data();
    }
    auto file = archive->mpq.open(name);
    if (file.size() > 64 * 1024 * 1024) return nullptr;
    bytes.resize(file.size()); file.get_bytes(bytes.data(), bytes.size());
    return bytes.data();
}
EXPORT(asset_size) unsigned asset_size() { return bytes.size(); }
