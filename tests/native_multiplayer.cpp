#include "../native/runtime.cpp"
#include <iostream>
#include <fstream>
using namespace bwgame;
static void require(bool b,const char* s){if(!b)throw std::runtime_error(s);}
static a_vector<uint8_t> input(int owner,int frame) {
 a_vector<uint8_t> out;bw_cmd cmd(out);a_vector<unit_t*> workers;
 for(auto* u:ptr(g_ui->st.player_units[owner]))if(g_ui->ut_worker(u)&&!g_ui->unit_dying(u))workers.push_back(u);
 if(frame==0 || frame==2400)for(auto* worker:workers) {
  unit_t* mineral=nullptr;int best=100000;
  for(auto* resource:ptr(g_ui->st.player_units[11]))if(int(resource->unit_type->id)>=176&&int(resource->unit_type->id)<=178) {
   int distance=std::abs(resource->position.x-worker->position.x)+std::abs(resource->position.y-worker->position.y);
   if(distance<best){best=distance;mineral=resource;}
  }
  if(mineral){uint16_t id=g_ui->get_unit_id(worker).raw_value;cmd.select(&id,1);cmd.default_order(mineral->position,g_ui->get_unit_id(mineral).raw_value,false);}
 }
 if(frame%240==0) {
  int race=int(g_ui->st.players[owner].race);
  for(auto* u:ptr(g_ui->st.player_units[owner]))if(!g_ui->unit_dying(u) && g_ui->u_completed(u) &&
     ((race==1&&g_ui->unit_is(u,UnitTypes::Terran_Command_Center)) || (race==2&&g_ui->unit_is(u,UnitTypes::Protoss_Nexus)) || (race==0&&g_ui->unit_is(u,UnitTypes::Zerg_Larva)))) {
    uint16_t id=g_ui->get_unit_id(u).raw_value;cmd.select(&id,1);cmd.type(race==0?35:31,race==0?UnitTypes::Zerg_Drone:race==1?UnitTypes::Terran_SCV:UnitTypes::Protoss_Probe);break;
  }
 }
 if(frame==3600) {
  uint16_t ids[12];size_t n=0;for(auto* u:workers)if(n<12)ids[n++]=g_ui->get_unit_id(u).raw_value;
  cmd.select(ids,n);cmd.order(Orders::AttackMove,g_ui->game_st.start_locations[1-owner],0xffff,false);
 }
 return out;
}
int main(int argc,char** argv) {try {
 if(argc<8)throw std::runtime_error("data map slot race0 race1 expansion output");
 std::string data=argv[1];int slot=std::atoi(argv[3]),first=std::atoi(argv[4]),second=std::atoi(argv[5]);bool expansion=std::atoi(argv[6]);
 open_archive(0,data+"/STARDAT.MPQ");open_archive(1,data+"/BROODAT.MPQ");open_archive(2,data+"/patch_rt.mpq");open_archive(3,argv[2]);
 auto scenario=read_asset(3,"staredit/scenario.chk");std::ofstream chk("build-native/nearby-weave.chk",std::ios::binary);chk.write((const char*)scenario.data(),scenario.size());chk.close();
 net_init(640,480,slot,first,second,expansion);
 require(!g_campaign&&count_units(g_ui->st,0)>=5&&count_units(g_ui->st,1)>=5,"Missing multiplayer starting army");
 auto before=net_hash();native_step();require(net_hash()==before,"Single-player tick advanced multiplayer");
 bool denied=false;try{save_game();}catch(...){denied=true;}require(denied,"Multiplayer save was allowed");
 int minerals=g_ui->st.current_minerals[slot];command(9,0,0,0,0);command(10,1,0,0,0);command(13,1,0,0,0);
 require(g_ui->st.current_minerals[slot]==minerals&&!g_ui->test_instant&&!g_ui->outcome,"Testing cheats changed multiplayer");
 uint8_t bad[]={1,0,255};denied=false;try{net_apply(nullptr,0,bad,sizeof(bad));}catch(...){denied=true;}
 require(denied&&net_remaining==0&&net_hash()==before,"Malformed turn modified the world");
 std::ofstream trace(argv[7]);trace<<net_assets()<<"\n";
 for(int f=0;f<7200;f+=4) {
  trace<<f<<" "<<net_hash()<<"\n";
  auto a=input(0,f),b=input(1,f);net_apply(a.data(),a.size(),b.data(),b.size());
  for(int k=0;k<4;k++) {
   net_step();
   // Different camera, refresh rate, selection and UI acknowledgement on each peer.
   if(slot==0 || (f+k)%3==0) {
    if((f+k)%120==0){for(auto* u:ptr(g_ui->st.player_units[slot]))if(!g_ui->unit_dying(u)){g_ui->current_selection_clear();g_ui->current_selection_add(u);g_ui->on_selection(false);break;}}
    if(slot==1)g_ui->screen_pos=xy(700,500);
    openbw_render((f+k)*(slot==0?42.:18.));
   }
  }
 }
 trace<<7200<<" "<<net_hash()<<"\n";trace.close();
 require(g_ui->st.total_minerals_gathered[0]>0&&g_ui->st.total_minerals_gathered[1]>0,"Players did not gather resources");
 net_peer_left();require(g_ui->outcome==1,"Opponent surrender did not produce victory");close_game();
 // Starting a solo game after multiplayer must restore ordinary stepping and saves.
 openbw_init(640,480,1,0);int f=g_ui->st.current_frame;native_step();require(g_ui->st.current_frame==f+1,"Multiplayer leaked into solo game");
 auto snapshot=save_game();restore_game(snapshot);close_game();
 std::cout<<"PASS multiplayer 7200 frames slot="<<slot<<" races="<<first<<","<<second<<" expansion="<<expansion<<"\n";
 return 0;
 }catch(const std::exception& e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
