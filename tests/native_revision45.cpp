#define OPENBW_REVISION44_EMBEDDED
#include "native_revision44.cpp"
#undef main
static void difficulty45(){
 const uint32_t ids[3][3]={{0x784f4c5au,0x78454d5au,0x7849485au},{0x784f4c54u,0x78454d54u,0x78494854u},{0x784f4c50u,0x78454d50u,0x78494850u}};
 for(int race=0;race<3;race++)for(int level=0;level<3;level++){
  command(20,1,race,level,0);require(custom_ai_race==race&&g_terran_ai_level==level,"Native setup ignored race/difficulty");
  openbw_init_race_ai(640,480,1,custom_bot_slot,custom_ai_race);
  require(g_campaign&&g_campaign->melee_ai&&g_campaign->melee_ai_level==level,"Manager difficulty not applied");
  require(g_campaign->threads.size()==1&&g_campaign->threads.front().id==ids[race][level],"Wrong original difficulty script");
  advance(120);require(g_campaign->ai_error.empty(),g_campaign->ai_error.c_str());
  std::cout<<"PASS race="<<race<<" level="<<level<<" script="<<std::string((const char*)&ids[race][level],4)<<" opcodes="<<g_campaign->towns[1].opcodes<<"\n";snapshot();close_game();
 }
}
static void zerg45(int level,int frames){
 command(20,1,0,level,0);openbw_init_race_ai(640,480,1,1,custom_ai_race);g_ui->competitive=false;
 require(g_ui->st.players[1].race==race_t::zerg,"Opponent is not Zerg");
 require(g_ui->st.current_minerals[1]==50&&g_ui->st.current_gas[1]==0,"AI resources boosted");
 std::set<int> seen;int firstDamage=-1,firstLair=-1,firstHive=-1,firstExpansion=-1;bool burrow=false,lurkerContact=false;
 for(int f=0;f<frames;f++){
  native_step();require(g_campaign->ai_error.empty(),g_campaign->ai_error.c_str());
  for(auto* u:ptr(g_ui->st.player_units[0]))if(!g_ui->unit_dying(u)){if(u->hp<u->unit_type->hitpoints&&firstDamage<0)firstDamage=f;g_ui->set_unit_hp(u,u->unit_type->hitpoints);}
  for(auto* u:ptr(g_ui->st.player_units[1]))if(g_ui->u_completed(u)&&!g_ui->unit_dying(u)){
   seen.insert(int(u->unit_type->id));if(g_ui->unit_is(u,UnitTypes::Zerg_Lurker)) {
    if(g_ui->u_burrowed(u))burrow=true;
    if(f%12==0)for(auto* other:g_ui->find_units(g_ui->square_at(u->position,192)))
     if(!g_ui->unit_dying(other)&&!g_ui->u_flying(other)&&!g_ui->u_invincible(other)&&g_ui->unit_target_is_enemy(u,other)&&g_ui->unit_can_see_target(u,other))lurkerContact=true;
   }
  }
  if(firstLair<0&&g_campaign->ai_count(1,132,true))firstLair=f;
  if(firstHive<0&&g_campaign->ai_count(1,133,true))firstHive=f;
  if(firstExpansion<0&&f%240==0&&g_campaign->ai_zerg_bases(1)>1)firstExpansion=f;
  if(f%6000==0){std::cout<<"AI "<<f<<" "<<g_campaign->ai_status()<<" types:";for(int t:seen)std::cout<<t<<",";std::cout<<"\n";}
 }
 std::cout<<"FINAL types:";for(int t:seen)std::cout<<t<<",";std::cout<<"\n";
 for(auto* u:ptr(g_ui->st.player_units[1]))if(!g_ui->unit_dying(u))std::cout<<"U "<<int(u->unit_type->id)<<" pos="<<u->position.x<<","<<u->position.y<<" order="<<int(u->order_type->id)<<" completed="<<g_ui->u_completed(u)<<" queue="<<(u->build_queue.empty()?-1:int(u->build_queue.front()->id))<<"\n";
 std::cout<<"METRICS bases="<<g_campaign->ai_zerg_bases(1)<<" hatcheries="<<g_campaign->ai_count(1,131,true)<<" gas="<<g_campaign->ai_count(1,149,true)<<" attacks="<<g_campaign->towns[1].attacks<<" minerals="<<g_ui->st.total_minerals_gathered[1]<<" gasGathered="<<g_ui->st.total_gas_gathered[1]<<" firstDamage="<<firstDamage<<" firstLair="<<firstLair<<" firstHive="<<firstHive<<" firstExpansion="<<firstExpansion<<" lurkerResearch="<<g_ui->player_has_researched(1,TechTypes::Lurker_Aspect)<<" lurkerContact="<<lurkerContact<<" lurkerBurrow="<<burrow<<"\n";
 require(g_campaign->towns[1].attacks>=3&&firstDamage>=0,"Zerg failed to attack opponent");
 require(g_campaign->ai_zerg_bases(1)>=2&&g_campaign->ai_count(1,149,true)>=2,"Zerg failed to expand mining");
 require(g_ui->st.total_gas_gathered[1]>3000,"Zerg gas gathering stalled");
 for(int type:{37,38,41,42,43,103,133})require(seen.count(type),(std::string("Zerg missing core/tech unit ")+std::to_string(type)).c_str());
 if(level==2)for(int type:{39,44,45,46,47,62})require(seen.count(type),(std::string("Zerg missing advanced unit ")+std::to_string(type)).c_str());
 require(!lurkerContact||burrow,"Zerg Lurkers did not burrow in ground combat");
 openbw_render(openbw_frame()*42.);auto saved=save_game();advance(32);auto expected=save_game();close_game();
 openbw_init_race_ai(640,480,1,1,0);restore_game(saved);require(save_game()==saved,"Fresh-init Zerg save round trip differs");advance(32);require(save_game()==expected,"Fresh-init Zerg continuation differs");
 std::cout<<"PASS Zerg level="<<level<<" frames="<<frames<<" freshInitSave32=exact\n";close_game();
}
static void zergSupport45(){
 command(20,1,0,2,0);openbw_init_race_ai(640,480,1,1,0);g_ui->competitive=false;advance(2);
 g_campaign->threads.clear();g_campaign->towns[1].active=false;
 xy center=g_ui->game_st.start_locations[0]+xy(0,256);

 auto own=[&](int type,xy pos){auto* u=g_ui->create_initial_unit(g_ui->get_unit_type(UnitTypes(type)),pos,1);require(u,"Own fixture creation failed");g_ui->u_set_status_flag(u,unit_t::status_flag_invincible);return u;};
 auto* queen=own(45,center-xy(160,0));auto* defiler=own(46,center-xy(128,-96));
 auto* ling=own(37,center-xy(64,0));g_campaign->towns[1].attackers.push_back(g_ui->get_unit_id(ling));
 std::vector<unit_t*> marines;
 for(int y:{-16,16})for(int x:{-16,16}){auto* u=g_ui->create_initial_unit(g_ui->get_unit_type(UnitTypes::Terran_Marine),center+xy(x,y),0);require(u,"Marine fixture creation failed");marines.push_back(u);}
 g_ui->st.tech_researched[1][TechTypes::Ensnare]=true;queen->energy=fp8::integer(200);defiler->energy=fp8::integer(200);
 for(int f=0;f<48;f++){native_step();for(auto* u:marines)g_ui->set_unit_hp(u,u->unit_type->hitpoints);}
 for(auto* u:marines){g_ui->stop_unit(u);g_ui->set_unit_order(u,g_ui->get_order_type(Orders::Nothing));}
 g_ui->stop_unit(ling);g_ui->set_unit_order(ling,g_ui->get_order_type(Orders::Nothing));
 openbw_render(openbw_frame()*42.);g_campaign->ai_zerg_support(1);
 std::cout<<"SUPPORT queen="<<int(queen->order_type->id)<<" defiler="<<int(defiler->order_type->id)<<" positions="<<queen->position.x<<","<<queen->position.y<<" / "<<center.x<<","<<center.y<<"\n";
 require(queen->order_type->id==Orders::CastEnsnare,"Queen did not aim Ensnare");
 require(defiler->order_type->id==Orders::CastDarkSwarm,"Defiler did not aim Dark Swarm");
 bool ensnared=false,swarm=false;
 for(int f=0;f<240;f++){
  native_step();for(auto* u:marines)g_ui->set_unit_hp(u,u->unit_type->hitpoints);
  for(auto* enemy:ptr(g_ui->st.player_units[0]))if(enemy->ensnare_timer)ensnared=true;
  for(int p=0;p<12;p++)for(auto* u:ptr(g_ui->st.player_units[p]))if(g_ui->unit_is(u,UnitTypes::Spell_Dark_Swarm))swarm=true;
 }
 require(ensnared&&queen->energy<fp8::integer(140),"Ensnare did not apply or spend energy");
 require(swarm&&defiler->energy<fp8::integer(115),"Dark Swarm did not apply or spend energy");
 snapshot();std::cout<<"PASS Zerg researched Ensnare, Dark Swarm and spell energy/save behavior (controlled fixtures)\n";close_game();
}
#ifdef OPENBW_REVISION45_EMBEDDED
#define main revision45_main
#endif
int main(int argc,char**argv){
 if(argc<4)return revision44_main(argc,argv);std::string mode=argv[3];if(mode!="zerg45"&&mode!="difficulty45"&&mode!="zergSupport45")return revision44_main(argc,argv);
 std::cout.setf(std::ios::unitbuf);try{std::string d=argv[1];open_archive(0,d+"/STARDAT.MPQ");open_archive(1,d+"/BROODAT.MPQ");open_archive(2,d+"/patch_rt.mpq");open_archive(3,argv[2]);
 if(mode=="difficulty45")difficulty45();else if(mode=="zergSupport45")zergSupport45();else zerg45(argc>4?std::atoi(argv[4]):2,argc>5?std::atoi(argv[5]):60000);return 0;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}
}
