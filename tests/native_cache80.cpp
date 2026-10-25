#include "data_loading.h"
#include <fstream>
#include <iostream>
int main(int argc, char** argv) {
  try {
    if (argc != 4) return 2;
    bwgame::data_loading::mpq_file<> original(argv[1]), compact(argv[2]);
    std::ifstream paths(argv[3]); std::string path; int count = 0;
    while (std::getline(paths, path)) {
      if (path.empty()) continue;
      bwgame::a_vector<uint8_t> a,b; original(a,path.c_str()); compact(b,path.c_str());
      if (a != b) throw std::runtime_error("Changed decoded asset: " + path);
      ++count;
    }
    std::cout << "PASS " << count << " native decoded assets byte-identical after compaction\n";
  } catch (const std::exception& e) {std::cerr << e.what() << '\n';return 1;}
}
