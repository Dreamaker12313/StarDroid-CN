// Regression checks against original campaign scripts and placed units.
#include "../native/runtime.cpp"
#include <iostream>
#include <set>
using namespace bwgame;
static double now = 0;
static void draw() {openbw_render(now += 42);}
static void require(bool ok, const char* why) {if (!ok) throw std::runtime_error(why);}
static unit_t* find(UnitTypes type) {
  for (auto* u : ptr(g_ui->st.player_units[g_ui->my_player])) if (u->unit_type->id == type) return u;
  return nullptr;
}
int main(int argc, char** argv) {try {
  require(argc > 1, "DATA_DIR required"); std::string dir = argv[1];
  open_archive(0, dir + "/STARDAT.MPQ"); open_archive(1, dir + "/BROODAT.MPQ");
  open_archive(2, dir + "/patch_rt.mpq"); open_archive(3, dir + "/StarCraft.mpq");
  openbw_init_campaign(640,480,3); command(21,160,0,0,0);
  std::set<std::pair<int,int>> pingPositions; bool centered = false, vulture = false, marine = false;
  for (int frame = 0; frame < 2100; frame++) {
    native_step();
    std::string events = openbw_campaign_events();
    if (events.find("10\t") != std::string::npos) {
      auto loc = g_ui->st.locations[13].area; xy p = (loc.from + loc.to) / 2;
      require(g_ui->screen_pos == xy(p.x-320,p.y-160), "T3 camera did not center on speaker in visible map area"); centered = true;
    }
    if (events.find("7\t") != std::string::npos) {
      if (!vulture) vulture = true; else marine = true;
    }
    for (const auto& a : g_ui->alerts) if (a.kind == 0) pingPositions.emplace(a.pos.x,a.pos.y);
    if (frame % 12 == 0) draw();
  }
  for (int id : {2,3}) {auto a = g_ui->st.locations[id].area; auto p = (a.from+a.to)/2;
    require(pingPositions.count({p.x,p.y}), "T3 original bunker ping missing");}
  require(centered && vulture && marine, "T3 opening script missing");
  std::cout << "PASS T3 original camera, speaker sequence, both bunker pings\n";
  for (auto size : {xy(640,480),xy(1280,960),xy(427,320),xy(960,480)}) {
    openbw_resize(size.x,size.y); command(21,size.y/3,0,0,0); openbw_pan(65536,65536); draw();
    require(g_ui->screen_pos.y + int(g_ui->camera_height()) == int(g_ui->game_st.map_height), "Bottom map edge hidden by HUD");
    require(g_ui->screen_pos.x + int(g_ui->view_width) == int(g_ui->game_st.map_width), "Right map edge out of bounds");
  }
  std::cout << "PASS bottom edge and camera bounds at four viewport/zoom sizes\n";
  close_game(); open_archive(3,dir + "/BroodWar.mpq"); openbw_init_campaign(640,480,502); draw();
  int connected = 0;
  for (auto* u : ptr(g_ui->st.visible_units)) if (u->unit_type->id == UnitTypes::Terran_Factory) {
    for (auto* a : ptr(g_ui->st.player_units[u->owner])) if (a->unit_type->id == UnitTypes::Terran_Machine_Shop) {
      xy expected = u->position-u->unit_type->placement_size/2+a->unit_type->addon_position+a->unit_type->placement_size/2;
      if (expected == a->position) {require(u->building.addon == a, "BW Z2 Machine Shop disconnected"); connected++;}
    }
  }
  require(connected > 0, "BW Z2 addon fixture absent");
  std::cout << "PASS BW Z2 connected Machine Shops: " << connected << "\n";
  close_game(); open_archive(3,dir + "/StarCraft.mpq"); openbw_init_campaign(640,480,102); draw();
  const std::pair<UnitTypes,bool> rallyCases[] = {
    {UnitTypes::Zerg_Creep_Colony,false}, {UnitTypes::Zerg_Spire,false},
    {UnitTypes::Zerg_Hatchery,true}, {UnitTypes::Zerg_Lair,true}, {UnitTypes::Zerg_Hive,true},
    {UnitTypes::Terran_Science_Facility,false}, {UnitTypes::Terran_Nuclear_Silo,false},
    {UnitTypes::Terran_Command_Center,true}, {UnitTypes::Terran_Factory,true},
    {UnitTypes::Protoss_Gateway,true}};
  for (auto test : rallyCases) {
    auto type = test.first;
    auto* u = g_ui->create_initial_unit(g_ui->get_unit_type(type), {1024,1024}, g_ui->my_player);
    require(u, "Missing rally fixture");
    // Keep the card independent of this mission's technology limits.
    g_ui->card.clear(); g_ui->card_for_unit(u,type);
    bool rally = false; for (const auto& c : g_ui->card) if (c.act == g_ui->C_RALLY) rally = true;
    require(rally == test.second, "Rally offered to non-producer or hidden by mission restrictions");
    g_ui->kill_unit(u);
  }
  std::cout << "PASS rally only for producers, including mission-restricted Hatcheries\n";
  for (auto type : {UnitTypes::Zerg_Overlord,UnitTypes::Zerg_Drone}) {
    auto* u = find(type); require(u, "Missing command fixture"); openbw_debug_select(g_ui->get_unit_id(u).raw_value,0); draw();
    bool attack = std::string(openbw_card()).find("\tAttack\t") != std::string::npos;
    require(attack == (type == UnitTypes::Zerg_Drone), "Wrong armed/unarmed Attack button");
  }
  command(2,'b',0,0,0); draw(); command(2,27,0,0,0); draw();
  require(g_ui->menu == 0 && !g_ui->targeting, "Touch Escape did not leave build menu");
  std::cout << "PASS unarmed commands and Escape without scan code\n";
  auto title = read_asset(3,"music/title.wav"); int id = naudio::add(title.data(),title.size()); naudio::play(id,63,128,0);
  std::vector<int16_t> sample(96000); naudio::mix(sample.data(),48000,48000); double position = naudio::position_ms(63);
  close_game(); require(naudio::playing(63) && naudio::position_ms(63) == position, "Menu cleanup restarted/stopped title music");
  naudio::stop(63); open_archive(10,dir + "/BroodWar.mpq");
  auto intro = read_asset(10,"smk/starxintr.smk"); require(intro.size() > 64*1024*1024, "Large movie fixture absent");
  int movie = open_movie(intro.data(),intro.size(),true); auto* picture = movie_frame(movie,1200,false);
  require(picture && picture->current > 0 && naudio::playing(60), "Large BW movie failed video/audio playback");
  movies[movie].reset();
  std::cout << "PASS preserved title music and >64 MB Brood War native cinematic\nPRESENTATION_RESULT PASS\n";
  return 0;
} catch (const std::exception& e) {std::cerr << "PRESENTATION_ERROR " << e.what() << '\n'; return 1;}}
