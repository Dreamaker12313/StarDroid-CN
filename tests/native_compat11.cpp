// Reject replay rules from a different simulation before touching the live game.
#define main replay81_unused_main
#include "native_replay81.cpp"
#undef main
int main(int argc,char**argv){try{
 check(argc==2,"Expected CHK fixture");
 std::ifstream in(argv[1],std::ios::binary);std::vector<uint8_t> chk((std::istreambuf_iterator<char>(in)),{});
 check(chk.size()>16,"Missing map");native_replay::Parsed p;p.header[0]=1;p.header[1]=24;p.header[60]=2;
 for(int slot=0;slot<12;slot++){p.header[161+slot*36+4]=slot;p.header[161+slot*36+8]=slot<2?player_t::controller_occupied:player_t::controller_closed;p.header[161+slot*36+9]=slot%3;}
 p.map.assign(chk.begin(),chk.end());auto base=classic(p);
 auto recording=[&](unsigned version){auto b=base;b.reserve(b.size()+256);auto w=bwgame::data_loading::make_vector_writer(b);
  w.put<uint64_t>(native_replay::MAGIC);w.put<uint32_t>(version);w.put<uint64_t>(0);w.put<uint64_t>(0);w.put<uint32_t>(0);
  w.put<uint8_t>(2);w.put<uint8_t>(0);w.put<uint8_t>(0);w.put<uint8_t>(0);w.put<uint8_t>(1);
  for(int i=0;i<144;i++)w.put<uint8_t>(0);for(int i=0;i<12;i++)w.put<uint32_t>(0);
  auto hash=native_save::hash_bytes(b.data(),b.size());w.put<uint64_t>(hash);return b;};
 auto current=recording(84);check(native_replay::parse(current.data(),current.size()).rules.present,"Current rules rejected");
 native_replay::opened={7,8,9};native_replay::seek_target=123;
 for(unsigned version:{80u,81u,83u,85u}){auto bytes=recording(version);bool failed=false;
  try{native_replay::open(bytes.data(),bytes.size());}catch(const std::exception& e){failed=true;std::string message=e.what();check(message=="The selected replay was recorded with a different version of the app.","Unclear compatibility error");}
  check(failed,"Wrong simulation rules accepted");check(!g_ui&&native_replay::opened==std::vector<uint8_t>({7,8,9})&&native_replay::seek_target==123,"Rejected replay destroyed current state");}
 check(!native_replay::parse(base.data(),base.size()).rules.present,"Classic human replay metadata rejected");
 std::cout<<"PASS "<<checks<<" replay rules compatibility checks: current84 metadata, old81/future rejection, read-only failure, classic human metadata\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
