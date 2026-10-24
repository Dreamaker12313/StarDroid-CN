#define OPENBW_REVISION58_EMBEDDED
#include "native_revision58.cpp"
#undef main

static void loss_reuse59(){
 setup56(1,0);auto* u=create55(U::Terran_Marine,0,{1000,1000});auto id=g_ui->get_unit_id(u).raw_value;
 int before=g_ui->score_lost[0];g_ui->kill_unit(u);g_ui->kill_unit(u);
 require(g_ui->score_lost[0]==before+1,"Repeated kill counted more than once");
 require(g_ui->scored_losses.count(id)==1,"Dying unit lacks duplicate-loss guard");
 for(int i=0;i<1000&&g_ui->scored_losses.count(id);i++)steps56(1);
 require(!g_ui->scored_losses.count(id),"Recycled unit retained a stale loss guard");
 require(g_ui->score_lost[0]==before+1,"Recycling changed the recorded loss");
 std::cout<<"PASS duplicate death guarded until recycling, then stale ID released\n";close_game();
}
static void image_reuse59(){
 setup56(1,0);auto* u=create55(U::Terran_Marine,0,{1000,1000});
 auto* type=u->sprite->main_image->image_type;
 // A free slot may retain a construction overlay's old fields. The pool is
 // FIFO, so model that state on the next slot rather than the last freed one.
 auto* old=g_ui->st.images_container.top();old->flags|=image_t::flag_y_frozen;old->frozen_y_value=1234;
 auto* next=g_ui->create_image(type,u->sprite,{},g_ui->image_order_top);
 require(next==old,"Image reuse fixture did not recycle the slot");
 require(!(next->flags&image_t::flag_y_frozen)&&next->frozen_y_value==0,"Reused image retained frozen position");
 std::cout<<"PASS recycled image clears frozen position for identical save continuation\n";close_game();
}
static void times59(){
 for(bool bw:{false,true}) {
  setup56(1,0,1,true,bw);configure_hero_mode(true);
  for(const auto& h:hero_roster()) {
   auto* hero=g_ui->get_unit_type(U(h.id));auto* base=g_ui->get_unit_type(U(h.base));
   require(hero->build_time==base->build_time,"Hero build time differs from normal counterpart");
   std::cout<<"TIME expansion="<<bw<<" hero="<<h.id<<" frames="<<hero->build_time<<"\n";
  }
  require(g_ui->get_unit_type(U::Hero_Edmund_Duke_Siege_Mode)->build_time==g_ui->get_unit_type(U::Terran_Siege_Tank_Tank_Mode)->build_time,"Duke siege build time differs");
  close_game();
 }
 std::cout<<"PASS all 18 hero build times exactly match their counterparts in both expansions\n";
}
static void spire59(){
 for(bool bw:{false,true})for(auto producer:{U::Zerg_Spire,U::Zerg_Greater_Spire}) {
  setup56(0,0,1,true,bw);auto* spire=create55(producer,0,{1000,1000});
  for(auto type:{UpgradeTypes::Zerg_Flyer_Attacks,UpgradeTypes::Zerg_Flyer_Carapace}) {
   g_ui->st.upgrade_levels[0][type]=2;auto* up=g_ui->get_upgrade_type(type);
   require(!g_ui->unit_can_upgrade(spire,up),"Level 3 air upgrade accepted without Hive");
   auto* hive=create55(U::Zerg_Hive,0,{1600,1600});
   require(g_ui->unit_can_upgrade(spire,up),"Spire cannot research level 3 with a Hive");g_ui->kill_unit(hive);steps56(48);
  }
  close_game();
 }
 std::cout<<"PASS ordinary and Greater Spire both research level 3 air attack/armor with completed Hive, both expansions\n";
}
static void heroai59(int race,int level,bool bw,int frames){
 auto setup=[&](){int races[8]={1,race},slots[8]={1,2};configured_init(640,480,0,races,slots,level,bw,true,false,nullptr,false,true);g_ui->competitive=false;};
 setup();
 std::map<int,int> seen;int first=-1,peakProducers=0;bool parallel=false;
 for(int f=0;f<frames;f++) {
  steps56(1);require(g_campaign->ai_error.empty(),g_campaign->ai_error.c_str());
  for(auto* u:ptr(g_ui->st.player_units[0]))if(!g_ui->unit_dying(u))g_ui->set_unit_hp(u,u->unit_type->hitpoints);
  int producers=0,upgrading=0,training=0;
  for(auto* u:ptr(g_ui->st.player_units[1]))if(!g_ui->unit_dying(u)) {
   if(const auto* h=hero_definition(u->unit_type->id))if(!g_ui->ut_turret(u)&&g_ui->u_completed(u)) {
    if(seen.emplace(h->id,f).second)std::cout<<"HERO race="<<race<<" level="<<level<<" bw="<<bw<<" id="<<h->id<<" frame="<<f<<"\n"<<std::flush;
    if(first<0)first=f;
   }
   if(g_ui->unit_is(u,hero_producer(race))&&g_ui->u_completed(u)) {
    producers++;upgrading+=g_ui->unit_is_upgrading(u);
    training+=!u->build_queue.empty()&&hero_definition(u->build_queue.front()->id)!=nullptr;
   }
  }
  peakProducers=std::max(peakProducers,producers);parallel|=upgrading&&training;
  if(f%6000==0)std::cout<<"ECON "<<f<<" "<<g_campaign->ai_status()<<std::flush;
 }
 int upgrades=0;for(auto n:g_ui->st.upgrade_levels[1])upgrades+=n;
 int bases=race==0?g_campaign->ai_zerg_bases(1):int(g_campaign->ai_depots(1).size());
 std::cout<<"RESULT race="<<race<<" level="<<level<<" bw="<<bw<<" first="<<first<<" heroes="<<seen.size()<<" producers="<<peakProducers<<" parallel="<<parallel<<" bases="<<bases<<" upgrades="<<upgrades<<"\n";
 require(first>=0&&first<4500,"First hero not produced early");
 require(seen.size()==6,"AI never completed all six hero types");
 require(peakProducers>=2&&parallel,"AI did not train heroes while upgrading at another building");
 require(bases>=2&&upgrades>=5,"Hero production stalled expansion/upgrades");
 openbw_render(openbw_frame()*42.);auto saved=save_game();steps56(48);auto expected=save_game();
 setup();restore_game(saved);require(save_game()==saved,"Hero AI save round trip differs");steps56(48);require(save_game()==expected,"Hero AI saved continuation differs");
 std::cout<<"PASS early hero, all six types, parallel hero/upgrade buildings, economy and exact save continuation\n";close_game();
}
int main(int argc,char**argv){try{
 require(argc>=4,"data map mode");std::string d=argv[1];open_archive(0,d+"/STARDAT.MPQ");open_archive(1,d+"/BROODAT.MPQ");open_archive(2,d+"/patch_rt.mpq");open_archive(3,argv[2]);std::string mode=argv[3];
 if(mode=="loss-reuse")loss_reuse59();else if(mode=="image-reuse")image_reuse59();else if(mode=="times")times59();else if(mode=="spire")spire59();else if(mode=="hero-ai")heroai59(std::atoi(argv[4]),std::atoi(argv[5]),argc<7||std::atoi(argv[6]),argc<8?48000:std::atoi(argv[7]));
 else if(mode=="heroes")heroes58();else if(mode=="merge")merge58();else if(mode=="teams")teams58();else if(mode=="legacy")legacy58();else if(mode=="power")power58();else if(mode=="victory")victory56();else if(mode=="deplete")deplete58(std::atoi(argv[4]));else if(mode=="macro")macro56(std::atoi(argv[4]),60000,std::atoi(argv[5]),std::atoi(argv[6]));else if(mode=="sound")sound56();else if(mode=="addons")addon57();else if(mode=="cargo")cargo56();else if(mode=="detection")detection56();else throw std::runtime_error("Unknown test");return 0;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
