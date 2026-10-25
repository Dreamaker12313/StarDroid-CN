// Real imported campaign identities; included by native_campaign79.cpp. Portrait
// substitutions affect presentation only; combat types and DAT data stay intact.
static void portrait79_assets(int type, const char* expected, const char* label) {
 auto data=read_asset(-1,"arr/portdata.dat"),table=read_asset(-1,"arr/portdata.tbl");
 require(!data.empty()&&table.size()>2,"Imported portrait tables missing");
 size_t count=data.size()/12;int id=value_query(11,type);
 require(id>=0&&size_t(id)<count,"Portrait index outside imported table");
 for(bool talking:{false,true}) {
  unsigned index=naudio::u32(data.data()+(talking?count*4:0)+id*4);
  require(index>0&&index<=naudio::u16(table.data()),"Invalid portrait string index");
  unsigned off=naudio::u16(table.data()+index*2);
  require(off<table.size(),"Portrait string offset outside table");
  std::string base((const char*)table.data()+off);
  require(base.rfind(expected,0)==0,"Wrong character's portrait movie selected");
  // NativePortrait uses four weighted idle variants and three talking variants,
  // falling back to a lower variant when an archive omits an optional movie.
  for(int choice=0;choice<(talking?3:4);++choice) {
   a_vector<uint8_t> bytes;
   for(int v=choice;v>=0&&bytes.empty();--v)bytes=read_asset(-1,"portrait/"+base+std::to_string(v)+".smk");
   require(!bytes.empty(),"Character portrait movie missing");
   int slot=open_movie(bytes.data(),bytes.size());auto* movie=movie_frame(slot,0,false);
   require(movie&&movie->width==60&&movie->height==56&&movie->frames>1,"Character portrait movie did not decode");
   movie=movie_frame(slot,(movie->frames-1)*movie->us/1000.,false);
   require(movie&&movie->current+1==movie->frames,"Character portrait did not decode through final frame");
   require(std::any_of(movie->rgba.begin(),movie->rgba.end(),[](uint8_t v){return v!=0;}),"Character portrait frame empty");
   movies[slot].reset();
  }
 }
 std::cout<<"PASS "<<label<<" imported idle/talking portrait movie variants and full decode\n";
}
static void heroes79(const char* broodwar) {
 struct Rename {int mission, type;const char* name;};
 const Rename renamed[] = {
  {599,15,"Genetic Engineer"}, {303,79,"Aldaris"}, {307,79,"Aldaris"},
  {402,15,"Terran Pilot"}, {405,29,"Norad III"}, {415,29,"Norad III"},
  {408,29,"Admiral DuGalle"}, {505,29,"Edmund Duke"}, {505,51,"Kerrigan"},
  {506,0,"UED Security Guard"}, {506,15,"UED Scientist"},
  {506,32,"UED Pyrotechnic Engineer"}, {506,34,"UED Genetic Engineer"},
  {508,74,"Raszagal"}, {509,51,"Kerrigan"}, {509,74,"Raszagal"}
 };
 int previous=-1;
 for (auto c:renamed) {
  if(c.mission!=previous){load(broodwar,c.mission);previous=c.mission;}
  auto* ut=g_ui->get_unit_type(U(c.type));
  require(ut->unit_map_string_index>0,"Original mission rename not loaded");
  require(std::string(g_ui->unit_name(U(c.type)))==c.name,"Original mission unit name ignored");
 }
 std::cout<<"PASS all 16 custom unit names found in the 64 original campaign maps (11 missions)\n";
 struct Portrait {int mission;U surrogate,character;const char* base;const char* label;};
 const Portrait portraits[] = {
  {303,U::Hero_Tassadar,U::Hero_Aldaris,"PAdvisor\\","Aldaris / Legacy of the Xel'Naga"},
  {307,U::Hero_Tassadar,U::Hero_Aldaris,"PAdvisor\\","Aldaris / The Insurgent"},
  {408,U::Hero_Norad_II,U::Hero_Gerard_DuGalle,"TDugal\\","DuGalle / To Chain the Beast"},
  {508,U::Hero_Dark_Templar,U::Hero_Raszagal,"PRaz\\","Raszagal / To Slay the Beast"},
  {509,U::Hero_Dark_Templar,U::Hero_Raszagal,"PRaz\\","Raszagal / The Reckoning"}
 };
 for(auto p:portraits) {
  load(broodwar,p.mission);auto defaults=data_loading::load_units_dat(g_ui->global_st.units_dat);
  int expected=defaults.vec[size_t(p.character)].portrait,ordinary_portrait=defaults.vec[size_t(p.surrogate)].portrait;
  require(expected!=ordinary_portrait,"Portrait test needs distinct original characters");
  auto* surrogate=g_ui->get_unit_type(p.surrogate);
  require(surrogate->id==p.surrogate&&surrogate->portrait==defaults.vec[size_t(p.surrogate)].portrait,"Portrait routing modified simulation unit data");
  auto snapshot=save_game();
  require(value_query(11,int(p.surrogate))==expected,"Campaign surrogate uses wrong portrait");
  require(value_query(11,int(p.character))==expected,"Dedicated transmission character uses wrong portrait");
  require(save_game()==snapshot,"Portrait lookup changes simulation state");
  portrait79_assets(int(p.surrogate),p.base,p.label);
  rebuild(snapshot,broodwar,p.mission);
  require(value_query(11,int(p.surrogate))==expected,"Save reload loses campaign portrait");
  game_load_functions rules(g_ui->player.st());
  auto* mutable_type=rules.get_unit_type(p.surrogate);auto name=mutable_type->unit_map_string_index;
  rules.game_st.map_strings[name-1]="\xC0\xEB\xE4\xE0\xF0\xE8\xF1";
  require(value_query(11,int(p.surrogate))==expected,"Localized name loses campaign portrait");
  mutable_type->unit_map_string_index=0;
  require(value_query(11,int(p.surrogate))==ordinary_portrait,"Unrenamed unit unexpectedly receives campaign portrait");
  mutable_type->unit_map_string_index=rules.game_st.map_strings.size()+1;
  require(value_query(11,int(p.surrogate))==ordinary_portrait,"Invalid name unexpectedly receives campaign portrait");
  mutable_type->unit_map_string_index=name;g_campaign->presentation_mission=0;
  require(value_query(11,int(p.surrogate))==ordinary_portrait,"Custom scenario unexpectedly receives campaign portrait");
 }
 require(value_query(11,-1)==-1&&value_query(11,228)==-1,"Invalid portrait unit indices accepted");
 std::cout<<"PASS campaign portrait routes, dedicated transmissions, localized names, save/load, custom-map guards and unchanged simulation\n";
 load(broodwar,307);step(240);
 auto aldaris=units(U::Hero_Tassadar,7);require(aldaris.size()==3,"Original Aldaris objective units missing");
 g_ui->current_selection_clear();g_ui->current_selection_add(aldaris[0]);g_ui->refresh_card();
 require(std::string(openbw_card()).rfind("Aldaris\t",0)==0,"Aldaris command-card title uses base hero name");
 auto snapshot=save_game();rebuild(snapshot,broodwar,307);
 require(std::string(g_ui->unit_name(U::Hero_Tassadar))=="Aldaris","Save/load lost map unit name");
 require(value_query(11,int(U::Hero_Tassadar))==value_query(11,int(U::Hero_Aldaris)),"Selected Aldaris portrait differs from dialogue portrait");
 // The original map deliberately enables enemy P8 shared vision (+Vi7).
 // Preserve this story objective visibility instead of hiding its targets.
 require(g_ui->st.shared_vision[7]&(1<<g_ui->my_player),"Original Aldaris shared-vision script did not run");
 for(auto* u:units(U::Hero_Tassadar,7))require(!g_ui->unit_hidden_by_fog(u),"Original revealed Aldaris unexpectedly hidden");
 std::cout<<"PASS Aldaris card/save identity and original objective shared vision\n";
 // Fallbacks handle default, absent, malformed, and empty map-name entries.
 game_load_functions rules(g_ui->player.st());
 auto* ut=rules.get_unit_type(U::Hero_Tassadar);
 std::string ordinary=g_ui->stat_name(int(U::Hero_Tassadar));
 ut->unit_map_string_index=0;
 require(std::string(g_ui->unit_name(U::Hero_Tassadar))==ordinary,"Default hero name changed");
 ut->unit_map_string_index=rules.game_st.map_strings.size()+10;
 require(std::string(g_ui->unit_name(U::Hero_Tassadar))==ordinary,"Invalid map-name index failed fallback");
 rules.game_st.map_strings.push_back("");ut->unit_map_string_index=rules.game_st.map_strings.size();
 require(std::string(g_ui->unit_name(U::Hero_Tassadar))==ordinary,"Empty custom name failed fallback");
 // Preserve imported CP1251/other legacy bytes for the host's language decoder.
 rules.game_st.map_strings.back()="\xC0\xEB\xE4\xE0\xF0\xE8\xF1";
 require(std::string(g_ui->unit_name(U::Hero_Tassadar))=="\xC0\xEB\xE4\xE0\xF0\xE8\xF1","Localized custom name bytes changed");
 std::cout<<"PASS default/invalid/empty map-name fallback and localized byte preservation\n";
 load(broodwar,407);
 auto defaults=data_loading::load_units_dat(g_ui->global_st.units_dat);
 require(std::string(g_ui->unit_name(U::Hero_Alexei_Stukov))=="Alexei Stukov","Stukov default name incorrect");
 require(openbw_portrait_for_type(int(U::Hero_Alexei_Stukov))==defaults.vec[size_t(U::Hero_Alexei_Stukov)].portrait,"Stukov portrait differs from imported DAT");
 portrait79_assets(int(U::Hero_Alexei_Stukov),"Talex\\","Stukov / Patriot's Blood");
 for(auto p:portraits)require(value_query(11,int(p.surrogate))==defaults.vec[size_t(p.surrogate)].portrait,"Campaign portrait leaked into another mission");
 require(g_ui->get_unit_type(U::Hero_Alexei_Stukov)->id!=U::Hero_Samir_Duran,"Stukov substituted with Duran");
 require(std::string(g_ui->unit_name(U::Hero_Tassadar))==ordinary,"Aldaris name leaked into another mission");
 step(3500);auto stukov=units(U::Hero_Alexei_Stukov,7);
 require(stukov.size()==1,"Original Stukov unit missing");
 require(g_ui->unit_hidden_by_fog(stukov[0]),"Unrevealed Stukov visible through fog");
 std::cout<<"PASS dedicated Stukov identity/portrait and no cross-mission rename leakage\n";
}
