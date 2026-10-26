// Exercise the bounded parser used by replayScenario without opening a game.
#define main replay81_unused_main
#include "native_replay81.cpp"
#undef main
int main(int argc,char**argv){try{
 check(argc==2,"Expected embedded CHK fixture");
 std::ifstream in(argv[1],std::ios::binary);std::vector<uint8_t> chk((std::istreambuf_iterator<char>(in)),{});
 check(chk.size()>16,"Missing fixture");
 native_replay::Parsed p;p.header[0]=1;p.header[1]=24;p.header[60]=2;
 for(int slot=0;slot<12;slot++){p.header[161+slot*36+4]=slot;p.header[161+slot*36+8]=slot<2?player_t::controller_occupied:player_t::controller_closed;p.header[161+slot*36+9]=slot%3;}
 p.map.assign(chk.begin(),chk.end());
 auto file=classic(p);auto selectedBefore=native_replay::viewpoint;auto activeBefore=native_replay::active;
 native_replay::opened={7,8,9};native_replay::seek_target=123;
 for(int i=0;i<5;i++){
  auto decoded=native_replay::parse(file.data(),file.size());
  check(decoded.map.size()==chk.size()&&std::equal(decoded.map.begin(),decoded.map.end(),chk.begin()),"Embedded scenario bytes changed");
  check(!g_ui&&native_replay::viewpoint==selectedBefore&&native_replay::active==activeBefore&&native_replay::opened==std::vector<uint8_t>({7,8,9})&&native_replay::seek_target==123,"Preview parser changed game/replay state");
 }
 auto reject=[&](const std::vector<uint8_t>& b){rejected([&]{native_replay::parse(b.data(),b.size());},"Invalid preview replay admitted");};
 for(size_t length:{size_t(0),size_t(16),size_t(40),file.size()-1})reject(std::vector<uint8_t>(file.begin(),file.begin()+length));
 auto corrupted=file;corrupted[corrupted.size()-1]^=1;reject(corrupted);
 auto noMap=p;noMap.map.clear();reject(classic(noMap));
 auto badMap=p;badMap.map={68,73,77,32,4,0,0,0,1,1,64,0};reject(classic(badMap));
 rejected([&]{native_replay::parse(file.data(),native_replay::MAX_FILE+1);},"Oversized preview replay admitted");
 std::cout<<"PASS "<<checks<<" native embedded-map checks: exact CHK equality, repeated read-only extraction, malformed/truncated/oversized replay rejection\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
