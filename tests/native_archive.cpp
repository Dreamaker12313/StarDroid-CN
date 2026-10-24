#include "data_loading.h"
#include <iostream>
using namespace bwgame;
using namespace bwgame::data_loading;
static void require(bool condition) {if(!condition)throw std::runtime_error("MPQ hash lookup regression");}
int main(int argc,char** argv) {try {
    // A valid empty archive lets the checks isolate the hash probing rules.
    uint8_t bytes[32]={0x4d,0x50,0x51,0x1a,32,0,0,0,32,0,0,0};
    mpq_data archive(bytes,sizeof(bytes));auto& m=archive.mpq;
    require(!m.file_exists("missing.wav"));
    a_string name="campaign/voice.wav";
    auto first=string_hash(name.c_str(),0,m.crypt_table)%4;
    auto h1=string_hash(name.c_str(),1,m.crypt_table),h2=string_hash(name.c_str(),2,m.crypt_table);
    m.hash_table.assign(4,{0,0,0xffffffff});m.hash_table[first]={h1,h2,0xfffffffe};
    require(!m.file_exists(name)); // Deleted entries retain the original hashes.
    auto next=(first+1)%4;m.hash_table[next]={h1,h2,0};
    require(m.find_hash_table_entry(name)==&m.hash_table[next]); // Probe past deletion.
    for(auto& e:m.hash_table)e={h1,h2,0xfffffffe};
    require(!m.file_exists(name)); // Full deleted table terminates after one lap.
    std::cout<<"PASS empty, deleted, colliding and fully deleted MPQ hash tables\n";
    for(bool crc:{false,true}) {
        a_vector<uint8_t> packed(crc?30:18);unsigned table=crc?16:12;
        for(unsigned i=0;i<(crc?4u:3u);i++) {
            unsigned offset=i==0?table:i==1?table+4:i==2?table+6:30;
            for(int b=0;b<4;b++)packed[i*4+b]=uint8_t(offset>>(8*b));
        }
        memcpy(packed.data()+table,"FONTxy",6);
        data_reader<> data(packed.data(),packed.data()+packed.size());
        block_table_entry block{0,uint32_t(packed.size()),6,0x80000200u|(crc?0x04000000u:0)};
        mpq_archive_file_reader<data_reader<>> file("fixture",data,4,block,0,m.crypt_table);
        uint8_t actual[6];file.get_bytes(actual,6);require(!memcmp(actual,"FONTxy",6));
        packed[4]=0;data_reader<> bad(packed.data(),packed.data()+packed.size());bool rejected=false;
        try{mpq_archive_file_reader<data_reader<>> broken("bad",bad,4,block,0,m.crypt_table);}catch(const std::exception&){rejected=true;}
        require(rejected);
    }
    std::cout<<"PASS ordinary/CRC sector tables, checksum-block exclusion and invalid offsets\n";
    if(argc>1){mpq_file<> core(argv[1]);for(auto name:{"font/font8.fnt","font/font10.fnt","font/font16.fnt"}){
        a_vector<uint8_t> font;core(font,name);
        auto* entry=core.mpq.find_hash_table_entry(name);auto& block=core.mpq.block_table[entry->block_index];
        size_t sectors=(block.size+core.mpq.sector_size-1)/core.mpq.sector_size,table=(sectors+2)*4;
        require((block.flags&0x04000000)&&block.compressed_size==table+block.size+sectors*4&&font.size()==block.size);
        a_vector<uint8_t> raw(block.size);core.paged.seek(block.data_offset+table);core.paged.get_bytes(raw.data(),raw.size());require(font==raw);
        std::cout<<"PASS original checksum-enabled payload "<<name<<" "<<font.size()<<" bytes (font readability checked by Android)\n";
    }}
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
