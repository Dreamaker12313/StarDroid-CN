#include "data_loading.h"
#include <fstream>
#include <iostream>
int main(int argc,char** argv) {try {
 if(argc!=4)return 2;
 bwgame::data_loading::mpq_file<> archive(argv[1]);
 bwgame::a_vector<uint8_t> data;archive(data,argv[2]);
 std::ofstream out(argv[3],std::ios::binary);out.write((char*)data.data(),data.size());
 std::cout<<data.size()<<'\n';return out?0:1;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
