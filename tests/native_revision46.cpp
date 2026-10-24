#define OPENBW_REVISION45_EMBEDDED
#include "native_revision45.cpp"
#undef main
static uint32_t classicScript46(int race,int level){
 const char* ids[3][3]={{"ZLOf","ZMED","ZHIf"},{"TLOf","TMED","THIf"},{"PLOf","PMED","PHIf"}};
 uint32_t v;std::memcpy(&v,ids[race][level],4);return v;
}
static void restrictions46(bool expansion){
 for(int p=0;p<12;p++){
  for(const auto& t:g_ui->game_st.unit_types.vec)if(t.is_broodwar)
   require(g_ui->game_st.unit_type_allowed[p][t.id]==expansion,"Wrong unit ruleset");
  if(!expansion){
   for(const auto& t:g_ui->game_st.upgrade_types.vec)if(t.is_broodwar)require(!g_ui->game_st.max_upgrade_levels[p][t.id],"Expansion upgrade allowed");
   for(int t=24;t<44;t++)require(!g_ui->game_st.tech_available[p][TechTypes(t)]&&!g_ui->st.tech_researched[p][TechTypes(t)],"Expansion technology allowed");
  }
 }
}
static void rules46(){
 for(bool expansion:{false,true})for(int race=0;race<3;race++)for(int level=0;level<3;level++){
  command(20,1,race,level,expansion?2:1);openbw_init_race_ai(640,480,race,1,race);g_ui->competitive=false;advance(2);
  restrictions46(expansion);
  if(!expansion)require(g_campaign->threads.front().id==classicScript46(race,level),"Classic game uses expansion script");
  for(int type:{111,114,160,167,169,35,135,165}){
   select(create(type));for(const auto& c:g_ui->card)if(c.ut!=UnitTypes::None&&!expansion)require(!g_ui->get_unit_type(c.ut)->is_broodwar,"Brood War type leaked into Classic command card");
  }
  if(!expansion)for(int type:{34,58,60,61,63,62,103})require(!g_campaign->ai_produce(1,type),"AI bypasses Classic unit restriction");
  openbw_render(0);auto bytes=save_game();advance(32);auto expected=save_game();close_game();
  openbw_init_race_ai(640,480,race,1,race);restore_game(bytes);require(save_game()==bytes,"Ruleset save reload differs");advance(32);require(save_game()==expected,"Ruleset save continuation differs");
  std::cout<<"PASS rules expansion="<<expansion<<" race="<<race<<" difficulty="<<level<<" save32=exact\n";close_game();
 }
 command(20,-1,1,2,1);openbw_init(640,480,1,0);restrictions46(false);close_game();
 command(20,1,1,2,0);require(g_skirmish_expansion,"Legacy setup must stay Brood War");
}
static void classic46(int race,int level,int frames){
 command(20,1,race,level,1);openbw_init_race_ai(640,480,1,1,race);g_ui->competitive=false;
 require(g_campaign->threads.front().id==classicScript46(race,level),"Wrong Classic AI script");
 int firstDamage=-1;std::set<int> seen;
 for(int f=0;f<frames;f++){
  native_step();require(g_campaign->ai_error.empty(),g_campaign->ai_error.c_str());
  for(auto* u:ptr(g_ui->st.player_units[0]))if(!g_ui->unit_dying(u)){
   if(u->hp<u->unit_type->hitpoints&&firstDamage<0)firstDamage=f;g_ui->set_unit_hp(u,u->unit_type->hitpoints);
  }
  for(auto* u:ptr(g_ui->st.player_units[1]))if(!g_ui->unit_dying(u)){
   require(!u->unit_type->is_broodwar,"Classic AI produced expansion unit");
   for(auto* t:u->build_queue)require(!t->is_broodwar,"Classic AI queued expansion unit");
   if(g_ui->u_completed(u))seen.insert(int(u->unit_type->id));
  }
  if(f%12000==0)std::cout<<"AI "<<f<<" "<<g_campaign->ai_status()<<"\n";
 }
 require(firstDamage>=0&&g_campaign->towns[1].attacks>=3,"Classic AI fails to attack");
 require(g_ui->st.total_minerals_gathered[1]>5000&&g_ui->st.total_gas_gathered[1]>2000,"Classic economy stalled");
 std::cout<<"METRICS race="<<race<<" difficulty="<<level<<" firstDamage="<<firstDamage<<" attacks="<<g_campaign->towns[1].attacks<<" minerals="<<g_ui->st.total_minerals_gathered[1]<<" gas="<<g_ui->st.total_gas_gathered[1]<<"\nTYPES ";for(int t:seen)std::cout<<t<<",";std::cout<<"\n";
 openbw_render(openbw_frame()*42.);auto b=save_game();advance(32);auto e=save_game();close_game();
 openbw_init_race_ai(640,480,1,1,race);restore_game(b);advance(32);require(save_game()==e,"Classic AI save continuation differs");close_game();
 std::cout<<"PASS Classic original-script AI\n";
}
int main(int argc,char**argv){
 if(argc<4)return revision45_main(argc,argv);std::string mode=argv[3];if(mode!="rules46"&&mode!="classic46")return revision45_main(argc,argv);
 std::cout.setf(std::ios::unitbuf);try{std::string d=argv[1];open_archive(0,d+"/STARDAT.MPQ");open_archive(1,d+"/BROODAT.MPQ");open_archive(2,d+"/patch_rt.mpq");open_archive(3,argv[2]);
 if(mode=="rules46")rules46();else classic46(std::atoi(argv[4]),std::atoi(argv[5]),60000);return 0;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}
}
