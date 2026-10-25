// Real imported campaign names; included by native_campaign79.cpp. The original
// map and DAT files, not a hard-coded hero substitution, select each identity.
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
 load(broodwar,307);step(240);
 auto aldaris=units(U::Hero_Tassadar,7);require(aldaris.size()==3,"Original Aldaris objective units missing");
 g_ui->current_selection_clear();g_ui->current_selection_add(aldaris[0]);g_ui->refresh_card();
 require(std::string(openbw_card()).rfind("Aldaris\t",0)==0,"Aldaris command-card title uses base hero name");
 auto snapshot=save_game();rebuild(snapshot,broodwar,307);
 require(std::string(g_ui->unit_name(U::Hero_Tassadar))=="Aldaris","Save/load lost map unit name");
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
 require(g_ui->get_unit_type(U::Hero_Alexei_Stukov)->id!=U::Hero_Samir_Duran,"Stukov substituted with Duran");
 require(std::string(g_ui->unit_name(U::Hero_Tassadar))==ordinary,"Aldaris name leaked into another mission");
 step(3500);auto stukov=units(U::Hero_Alexei_Stukov,7);
 require(stukov.size()==1,"Original Stukov unit missing");
 require(g_ui->unit_hidden_by_fog(stukov[0]),"Unrevealed Stukov visible through fog");
 std::cout<<"PASS dedicated Stukov identity/portrait and no cross-mission rename leakage\n";
}
