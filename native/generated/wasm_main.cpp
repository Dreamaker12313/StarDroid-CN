// web/wasm_main.cpp — browser (wasm) entry point for the single-player sandbox.
//
// Reactor-model module: JS calls _initialize() once, then openbw_init() after
// the MPQ bytes are available, then openbw_step() (timer) + openbw_render()
// (animation frame). File
// bytes come from JS through the js_read_data / js_file_size imports (the same
// pattern the old Emscripten build used); rendering goes to the framebuffer in
// web/wasm_backend.cpp, which JS blits to a <canvas>.

#include "sandbox.h"
#include "campaign.h"

#include <cstdio>
#include <cstdlib>
#include <cctype>

using namespace bwgame;
static int g_terran_ai_level = 2;

// --- imports provided by the JS host ------------------------------------
extern "C" {

void js_read_data(int index, void* dst, unsigned offset, unsigned n);

unsigned js_file_size(int index);
}

// --- logging sinks required by ui/common.h ------------------------------
namespace bwgame {
namespace ui {
void log_str(a_string str) { fwrite(str.data(), str.size(), 1, stdout); fflush(stdout); }
void fatal_error_str(a_string str) { throw std::runtime_error(str.c_str()); }
}
}

// --- file reader bridged to JS ------------------------------------------
// Archive index mapping (JS must provide matching bytes):
//   0 StarDat.mpq   1 BrooDat.mpq   2 Patch_rt.mpq   3 the map (.scx/.scm)
namespace bwgame {
namespace data_loading {

template<bool default_little_endian = true>
struct js_file_reader {
	size_t index = 3;
	size_t file_pointer = 0;
	js_file_reader() = default;
	explicit js_file_reader(a_string filename) { open(std::move(filename)); }
	void open(a_string filename) {
		a_string low;
		for (char c : filename) low += (char)std::tolower((unsigned char)c);
		auto has = [&](const char* s) { return low.find(s) != a_string::npos; };
		if (has("stardat")) index = 0;
		else if (has("brood")) index = 1;
		else if (has("patch")) index = 2;
		else index = 3;   // the map archive
	}
	void get_bytes(uint8_t* dst, size_t n) {
		js_read_data((int)index, dst, (unsigned)file_pointer, (unsigned)n);
		file_pointer += n;
	}
	void seek(size_t offset) { file_pointer = offset; }
	size_t tell() const { return file_pointer; }
	size_t size() { return js_file_size((int)index); }
};

}
}

// --- game globals -------------------------------------------------------
namespace {
using loader_t = data_loading::data_files_loader<data_loading::mpq_file<data_loading::js_file_reader<>>>;
loader_t* g_loader = nullptr;
play_ui* g_ui = nullptr;
campaign_ui* g_campaign = nullptr;
data_loading::mpq_file<data_loading::js_file_reader<>>* g_mission = nullptr;
#include "campaign_catalog.h"
bool g_campaign_expansion = false;
bool g_skirmish_expansion = true; // Legacy callers/saves used Brood War melee rules.
a_unordered_map<int, a_vector<uint8_t>> g_mission_sounds;
a_vector<uint8_t> g_empty_sound;
a_string g_campaign_prefix = "campaign/terran/terran01/";
const a_vector<uint8_t>& mission_sound(int index) {
	if (!g_campaign || !g_mission || index < 1 || size_t(index) > g_ui->game_st.map_strings.size()) return g_empty_sound;
	auto found = g_mission_sounds.find(index);
	if (found != g_mission_sounds.end()) return found->second;
	a_string filename = g_campaign_prefix + g_ui->game_st.map_strings[index - 1];
	a_vector<uint8_t>& out = g_mission_sounds[index];
	if (g_mission->mpq.file_exists(filename)) (*g_mission)(out, filename);
	return out;
}
}

#define OPENBW_EXPORT(name) extern "C"

// Build the game with `n` occupied slots. Every peer must pass an identical slot list (and
// the same map) or their initial states differ and lockstep is broken from frame 0.
static void init_game(int width, int height, int my_slot, const mp_slot* slots, size_t n, bool campaign = false, int original_ai_slot = -1, unsigned ai_mask = 0, bool free_for_all = false) {
    if(original_ai_slot>=0)ai_mask|=1u<<original_ai_slot;
	g_loader = new loader_t(data_loading::data_files_directory<loader_t>(""));

	race_t my_race = race_t::terran;
	for (size_t k = 0; k != n; ++k) if (slots[k].slot == my_slot) my_race = slots[k].race;

	game_player player(*g_loader);
	if (campaign || ai_mask) {
		g_campaign = new campaign_ui(std::move(player), my_slot, my_race);
		g_ui = g_campaign;
		g_campaign->sound_file = mission_sound;
	} else g_ui = new play_ui(std::move(player), my_slot, my_race);
	g_ui->exit_on_close = false;
	g_ui->competitive = campaign || n > 1;   // victory/defeat only matters with an opponent
	g_ui->load_data_file = [](a_vector<uint8_t>& data, a_string filename) {
		(*g_loader)(data, std::move(filename));
	};
	g_ui->init();

	uint32_t rep_seed0 = 0;   // filled in at the map's setup point (see setup_melee_slots)
	data_loading::mpq_file<data_loading::js_file_reader<>> map_loader("openbw.map");
	// Tee the map's CHK out of the loader: a .rep embeds it verbatim, and it's the only
	// part of the replay we can't reconstruct from the sim afterwards.
	if (campaign) {
		g_mission = new data_loading::mpq_file<data_loading::js_file_reader<>>("openbw.map");
		(*g_mission)(g_ui->rep_map, g_campaign_prefix + "staredit/scenario.chk");
		game_load_functions load(g_ui->player.st());
		// Preserve every original owner and race, before the melee loader's
		// default random-race setup. Mission 1's human is player 2 (slot 1).
		std::array<int, 12> owners{}, races{};
		auto& data = g_ui->rep_map;
		for (size_t p = 0; p + 8 <= data.size();) {
			unsigned len = campaign_ui::u32(&data[p + 4]);
			if (len > data.size() - p - 8) error("Invalid campaign CHK");
			if (!memcmp(&data[p], "UPRP", 4)) g_campaign->properties.assign(data.begin()+p+8,data.begin()+p+8+len);
			if (len >= 12) for (size_t i = 0; i < 12; ++i) {
				if (!memcmp(&data[p], "OWNR", 4)) owners[i] = data[p + 8 + i];
				if (!memcmp(&data[p], "SIDE", 4)) races[i] = data[p + 8 + i];
			}
			p += 8 + len;
		}
		load.load_map_data(data.data(), data.size(), [&]() {
			load.setup_info.victory_condition = 0;
			load.setup_info.resource_type = 0;
			for (size_t i = 0; i < 12; ++i) {
				auto& p = g_ui->st.players[i];
				p.controller = (decltype(p.controller))owners[i];
				p.race = (race_t)races[i];
				if (p.controller == player_t::controller_open) p.controller = player_t::controller_occupied;
				if (p.controller == player_t::controller_computer) p.controller = player_t::controller_computer_game;
			}
		});

	} else {
	setup_melee_slots(g_ui->player.st(), [&](a_vector<uint8_t>& out, a_string fn) {
		map_loader(out, fn);
		a_string low;
		for (char c : fn) low += (char)std::tolower((unsigned char)c);
		if (low.find("scenario.chk") != a_string::npos) g_ui->rep_map = out;
	}, slots, n, &rep_seed0);
	}

    // Classic restrictions apply to every owner, including the AI and practice
    // games, regardless of whether the terrain was imported from an SCM or SCX.
    if (!(campaign ? g_campaign_expansion : g_skirmish_expansion)) {
      game_load_functions rules(g_ui->player.st());
      for (int p=0;p<12;++p) {
        for (const auto& type : g_ui->game_st.unit_types.vec)
            if (type.is_broodwar) rules.game_st.unit_type_allowed[p][type.id]=false;
        for (const auto& type : g_ui->game_st.upgrade_types.vec)
            if (type.is_broodwar) {rules.game_st.max_upgrade_levels[p][type.id]=0;g_ui->st.upgrade_levels[p][type.id]=0;}
        for (int i=24;i<44;++i) {
            rules.game_st.tech_available[p][(TechTypes)i]=false;
            g_ui->st.tech_researched[p][(TechTypes)i]=false;
        }
      }
    }

	if (g_campaign) {
		const char* names[]={"scripts/aiscript.bin","scripts/bwscript.bin"};
		for(int i=0;i<2;++i) for(auto& archive:g_loader->mpqs) if(archive.mpq.file_exists(names[i])) { archive(g_campaign->scripts[i],names[i]); break; }
	}

    for(int original_ai_slot=0;original_ai_slot<8;++original_ai_slot) if(ai_mask & (1u<<original_ai_slot)) {
        g_campaign->melee_ai=true;
        g_campaign->melee_ai_level=std::max(0,std::min(2,g_terran_ai_level));
        g_ui->st.players[original_ai_slot].controller=player_t::controller_computer_game;
        const uint32_t terran[]={0x784f4c54u,0x78454d54u,0x78494854u}; // TLOx / TMEx / THIx
        const uint32_t protoss[]={0x784f4c50u,0x78454d50u,0x78494850u}; // PLOx / PMEx / PHIx
        const uint32_t zerg[]={0x784f4c5au,0x78454d5au,0x7849485au}; // ZLOx / ZMEx / ZHIx
        const auto race=g_ui->st.players[original_ai_slot].race;
        const auto* scripts=race==race_t::zerg?zerg:race==race_t::protoss?protoss:terran;
        uint32_t script=scripts[std::max(0,std::min(2,g_terran_ai_level))];
        // The original archives contain separate Classic and expansion scripts.
        if(!g_skirmish_expansion) script=(script&0x00ffffffu)|((g_terran_ai_level==1?uint32_t('D'):uint32_t('f'))<<24);
        g_campaign->ai_start(original_ai_slot,script,0);
        if(!g_campaign->ai_error.empty())error("Skirmish AI: %s",g_campaign->ai_error.c_str());
    }

    if(!campaign) {
        // Melee computers form a team; FFA gives every occupied slot its own side.
        for(int i=0;i<8;++i) for(int j=0;j<8;++j)
            g_ui->st.alliances[i][j] = i==j || (!free_for_all && (ai_mask&(1u<<i)) && (ai_mask&(1u<<j))) ? 1 : 0;
    }

	g_ui->wnd.create("OpenBW Web", 0, 0, width, height);
	g_ui->resize(width, height);
	g_ui->set_image_data();
	if (campaign) g_ui->seed_explored_structures();
	xy start = g_ui->game_st.start_locations[my_slot];
	g_ui->screen_pos = start - xy(width / 2, height / 2);

	// Seed the replay header from the loaded game. Everything here is fixed at start, so
	// the recording only has to accumulate actions from now on.
	{
		state& st = g_ui->player.st();
		replay_saver_state& r = g_ui->rep;
		r.map_data = g_ui->rep_map.data();
		r.map_data_size = g_ui->rep_map.size();
		r.map_tile_width = g_ui->game_st.map_tile_width;
		r.map_tile_height = g_ui->game_st.map_tile_height;
		r.tileset = (int)g_ui->game_st.tileset_index;
		r.active_player_count = (int)n;
		r.slot_count = (int)n;
		r.game_speed = 6;                 // "fastest", matching our default step rate
		r.game_type = free_for_all ? 3 : 2;                  // melee
		r.random_seed = rep_seed0;
		r.game_name = "OpenBW Web";
		r.map_name = g_ui->game_st.scenario_name;
		r.player_name = "Player";
		// Must mirror setup_melee_slots, or a replayer rebuilds a different game.
		r.setup_info.victory_condition = 1;
		r.setup_info.tournament_mode = 0;
		r.setup_info.starting_units = 0;
		r.setup_info.resource_type = 1;
		r.setup_info.starting_minerals = 50;
		for (size_t i = 0; i != 12; ++i) {
			r.players[i] = st.players[i];
			r.setup_info.create_melee_units_for_player[i] = st.players[i].controller == player_t::controller_occupied || st.players[i].controller == player_t::controller_computer_game;
		}
		for (size_t k = 0; k != n; ++k)
			r.player_names[slots[k].slot] = (int)k == my_slot ? "You" : "Opponent";
		g_ui->rep_on = !campaign && g_ui->rep_map.size() != 0;
	}

	ui::log("openbw_init: map '%s' %dx%d, slot %d of %d, units=%d, fog_player=%d\n",
		g_ui->game_st.scenario_name, (int)g_ui->game_st.map_width,
		(int)g_ui->game_st.map_height, my_slot, (int)n,
		count_units(g_ui->player.st(), my_slot), g_ui->fog_player);
}

// Single-player. Call after all four archives' bytes are available in JS.
OPENBW_EXPORT(openbw_init) void openbw_init(int width, int height, int race, int slot) {
	mp_slot s{slot, (race_t)race};
	init_game(width, height, slot, &s, 1);
}

// Catalog IDs keep existing Terran routes stable while retaining each CHK's
// original human player slot and race.
OPENBW_EXPORT(openbw_init_campaign) void openbw_init_campaign(int width, int height, int mission) {
    for (const auto& entry : web_campaigns) if (entry.code == mission) {
        g_campaign_prefix = entry.prefix;
        g_campaign_expansion = entry.expansion;
        mp_slot slot{entry.player,race_t(entry.race)};
        init_game(width,height,entry.player,&slot,1,true);
        g_campaign->apply_campaign_compatibility(mission);
        return;
    }
    error("Unknown campaign mission");
}
OPENBW_EXPORT(openbw_campaign_chk) const uint8_t* openbw_campaign_chk() { return g_campaign ? g_ui->rep_map.data() : nullptr; }
OPENBW_EXPORT(openbw_campaign_chk_len) int openbw_campaign_chk_len() { return g_campaign ? (int)g_ui->rep_map.size() : 0; }
OPENBW_EXPORT(openbw_campaign_sound) const uint8_t* openbw_campaign_sound(int index) { return mission_sound(index).data(); }
OPENBW_EXPORT(openbw_campaign_sound_len) int openbw_campaign_sound_len(int index) { return (int)mission_sound(index).size(); }
OPENBW_EXPORT(openbw_campaign_events) const char* openbw_campaign_events() {
	static a_string out;
	out.clear(); if (g_campaign) out.swap(g_campaign->events);
	return out.c_str();
}
OPENBW_EXPORT(openbw_campaign_status) const char* openbw_campaign_status() {
	static a_string out;
	if (!g_campaign) return "";
	char buf[160];
	int alive = count_units_of_type(g_ui->st, 1, UnitTypes::Hero_Jim_Raynor_Vulture) + count_units_of_type(g_ui->st, 2, UnitTypes::Hero_Jim_Raynor_Vulture);
	snprintf(buf, sizeof(buf), "%d\t%d\t%d\t%d\t%d\t%d", g_campaign->objectives,
		g_ui->st.completed_unit_counts[1][UnitTypes::Terran_Marine],
		g_ui->st.completed_unit_counts[1][UnitTypes::Terran_Barracks],
		count_units_of_type(g_ui->st, 1, UnitTypes::Hero_Jim_Raynor_Vulture), alive,
		g_campaign->campaign_control_lock || g_campaign->units_paused);
	out = buf; return out.c_str();
}

OPENBW_EXPORT(openbw_campaign_timer) const char* openbw_campaign_timer() { static char out[24];int sec=g_campaign?(g_campaign->countdown_ms+999)/1000:0;snprintf(out,sizeof(out),"%d:%02d",sec/60,sec%60);return out; }
OPENBW_EXPORT(openbw_campaign_ai) const char* openbw_campaign_ai() { static a_string out; out=g_campaign?g_campaign->ai_status():"";return out.c_str(); }
OPENBW_EXPORT(openbw_campaign_ai_error) const char* openbw_campaign_ai_error() { return g_campaign?g_campaign->ai_error.c_str():""; }
OPENBW_EXPORT(openbw_campaign_ai_trace) const char* openbw_campaign_ai_trace() { return g_campaign?g_campaign->ai_trace.c_str():""; }

// Resize the render target (e.g. when the browser window changes). Recreates
// the framebuffer at the new size; ui.resize() rebuilds the surfaces.
OPENBW_EXPORT(openbw_resize) void openbw_resize(int width, int height) {
	if (!g_ui) return;
	g_ui->wnd.destroy();
	if (g_campaign) {
		const char* names[]={"scripts/aiscript.bin","scripts/bwscript.bin"};
		for(int i=0;i<2;++i) for(auto& archive:g_loader->mpqs) if(archive.mpq.file_exists(names[i])) { archive(g_campaign->scripts[i],names[i]); break; }
	}

	g_ui->wnd.create("OpenBW Web", 0, 0, width, height);
	g_ui->resize(width, height);
}

// Nudge the camera by (dx, dy) map pixels (e.g. from a trackpad/wheel scroll).
// Clamp immediately with signed coordinates, including gestures past an edge.
OPENBW_EXPORT(openbw_pan) void openbw_pan(int dx, int dy) {
	if (g_ui) { g_ui->screen_pos += xy(dx, dy); g_ui->clamp_viewport(); }
}

// One simulation frame. JS drives this from a fixed-interval timer, so it keeps
// ticking (throttled) while the tab is backgrounded and never fast-forwards a
// backlog on return — unlike advancing by elapsed wall-clock time.
OPENBW_EXPORT(openbw_step) void openbw_step() {
	if (g_ui) { g_ui->apply_testing_cheats(); if(g_campaign) g_campaign->campaign_tick(); g_ui->state_functions::next_frame(); }
}

// Render the current state into the framebuffer and process input. JS drives
// this from requestAnimationFrame, passing performance.now() so time-based UI
// effects (the target-ring blink, the click marker) are refresh-rate-independent
// — a frame counter would run twice as fast on a 120 Hz display.
OPENBW_EXPORT(openbw_render) void openbw_render(double now_ms) {
	if (g_ui) { g_ui->ui_now = now_ms; g_ui->update(); }
}

// The current command card as "title\nKEY\tLabel\tEN\n…" — the JS host renders it.
OPENBW_EXPORT(openbw_card) const char* openbw_card() {
	return g_ui ? g_ui->card_text.c_str() : "";
}

// Producer status "<progress%>\t<name>…" (empty if not training) — rebuilt per call.
OPENBW_EXPORT(openbw_status) const char* openbw_status() {
	return g_ui ? g_ui->build_status() : "";
}
OPENBW_EXPORT(openbw_production_icon) int openbw_production_icon() {
    auto* u = g_ui ? g_ui->primary_selected() : nullptr;
    if (!u) return -1;
    if (!u->build_queue.empty()) return (int)u->build_queue.front()->id;
    if (g_ui->unit_is_researching(u)) return u->building.researching_type->icon;
    if (g_ui->unit_is_upgrading(u)) return u->building.upgrading_type->icon;
    return -1;
}
OPENBW_EXPORT(openbw_production_kind) int openbw_production_kind() {
    auto* u = g_ui ? g_ui->primary_selected() : nullptr;
    if (!u || g_ui->current_selection.size() != 1) return 0;
    if (g_ui->ut_worker(u)) return 0;
    if (g_ui->archon_merging(u)) return 5;
    if (!g_ui->u_completed(u)) return 4;
    if (!u->build_queue.empty()) return 1;
    if (g_ui->unit_is_researching(u)) return 2;
    if (g_ui->unit_is_upgrading(u)) return 3;
    return 0;
}
OPENBW_EXPORT(openbw_production_queue_type) int openbw_production_queue_type(int slot) {
    auto* u = g_ui ? g_ui->primary_selected() : nullptr;
    return u && slot >= 0 && size_t(slot) < u->build_queue.size() ? int(u->build_queue[slot]->id) : -1;
}
OPENBW_EXPORT(openbw_selected_race) int openbw_selected_race() {
    auto* u = g_ui ? g_ui->primary_selected() : nullptr;
    return u ? int(g_ui->unit_race(u)) : -1;
}

// "minerals\tgas\tsupply_used\tsupply_max" for the resource HUD.
OPENBW_EXPORT(openbw_resources) const char* openbw_resources() {
	return g_ui ? g_ui->resources() : "";
}

// Pointer mode so JS can pick a cursor: 0 normal, 1 targeting, 2 placing.
OPENBW_EXPORT(openbw_cursor) int openbw_cursor() {
	return g_ui ? g_ui->cursor() : 0;
}

// Render a command-button icon (frame == unit id) to RGBA; returns a pointer into
// wasm memory valid until the next call, with the size in openbw_icon_w/h.
OPENBW_EXPORT(openbw_icon) const uint8_t* openbw_icon(int frame) {
	return g_ui ? g_ui->render_icon(frame) : nullptr;
}
OPENBW_EXPORT(openbw_icon_w) int openbw_icon_w() { return g_ui ? g_ui->icon_w : 0; }
OPENBW_EXPORT(openbw_icon_h) int openbw_icon_h() { return g_ui ? g_ui->icon_h : 0; }

// Resource-HUD icon (0 = minerals, 1 = gas) to RGBA; same size convention as openbw_icon.
OPENBW_EXPORT(openbw_res_icon) const uint8_t* openbw_res_icon(int which) {
	return g_ui ? g_ui->render_res_icon(which) : nullptr;
}

// Production progress bar (percent, target width) rendered like the in-world health bar,
// as RGBA; actual size in openbw_progress_bar_w/h.
OPENBW_EXPORT(openbw_progress_bar) const uint8_t* openbw_progress_bar(int percent, int width) {
	return g_ui ? g_ui->render_progress_bar(percent, width) : nullptr;
}
OPENBW_EXPORT(openbw_progress_bar_w) int openbw_progress_bar_w() { return g_ui ? g_ui->pbar_w : 0; }
OPENBW_EXPORT(openbw_progress_bar_h) int openbw_progress_bar_h() { return g_ui ? g_ui->pbar_h : 0; }

// Edge-scroll direction for the cursor: 0 none, 1 N, 2 NE, 3 E, 4 SE, 5 S, 6 SW, 7 W, 8 NW.
OPENBW_EXPORT(openbw_edge) int openbw_edge() { return g_ui ? g_ui->edge_dir : 0; }

// Last blocked-command reason as "seq\tmessage" — the host shows a toast when seq changes.
OPENBW_EXPORT(openbw_error) const char* openbw_error() { return g_ui ? g_ui->error_status() : ""; }

// System message log (eliminations…), newline-separated. Empty when there's nothing to show.
OPENBW_EXPORT(openbw_messages) const char* openbw_messages() { return g_ui ? g_ui->game_messages() : ""; }

// Read-only debug dump of the primary selected unit (window.__bw.x.openbw_debug_dump).
OPENBW_EXPORT(openbw_debug_dump) const char* openbw_debug_dump() { return g_ui ? g_ui->debug_dump() : ""; }

// Vision tripwire: nonzero = abnormal fog/shared-vision/cheat state (see sandbox.h).
OPENBW_EXPORT(openbw_vision_anomaly) int openbw_vision_anomaly() { return g_ui ? g_ui->vision_anomaly() : 0; }

// Selection wireframes: one line per selected unit; per-unit RGBA in a wire_box() square
// (64 for a single selection's big console wireframe, 32 for group tiles).
OPENBW_EXPORT(openbw_wires) const char* openbw_wires() { return g_ui ? g_ui->wires() : ""; }
OPENBW_EXPORT(openbw_wire_rgba) const uint8_t* openbw_wire_rgba(int i) { return g_ui ? g_ui->render_wireframe((size_t)i) : nullptr; }
OPENBW_EXPORT(openbw_wire_box) int openbw_wire_box() { return g_ui ? g_ui->wire_box() : 32; }
OPENBW_EXPORT(openbw_selected_type) int openbw_selected_type() {
    auto* u = g_ui ? g_ui->primary_selected() : nullptr;
    if (!u && g_ui && !g_ui->current_selection.empty()) u = g_ui->get_unit(g_ui->current_selection.front());
    return u ? (int)u->unit_type->id : -1;
}
OPENBW_EXPORT(openbw_placement_valid) int openbw_placement_valid(int x, int y) {
    return g_ui && g_ui->placement_valid(x,y);
}
OPENBW_EXPORT(openbw_unit_details) const char* openbw_unit_details() {
    return g_ui ? g_ui->unit_details() : "";
}
// A read-only, fog-aware hit test for the touch UI. No commands on touch-down.
// 0 = select/inspect; 1 = contextual worker/rally order; 2 = explicit target;
// 3 = attack/attack-move for owned mobile non-workers.
OPENBW_EXPORT(openbw_touch_action) int openbw_touch_action(int x, int y) {
    if (!g_ui || g_ui->paused || g_ui->campaign_control_lock) return 0;
    if (g_ui->pending_build || g_ui->targeting) return 2;
    auto* target = g_ui->select_get_unit_at(g_ui->screen_to_map(x,y));
    if (target && g_ui->unit_hidden_by_fog(target)) target = nullptr;
    // A tap selects when the selected card has no Move command. Rally points
    // still work through the explicit Set Rally Point button/targeting mode.
    g_ui->refresh_card();
    bool mobile = false;
    for (const auto& c : g_ui->card) if (c.act == play_ui::C_MOVE) mobile = true;
    if (target && !mobile) return 0;
    if (target && target->owner == g_ui->my_player) {
        for(auto id:g_ui->current_selection)if(auto* passenger=g_ui->get_unit(id))
            if(passenger!=target && passenger->owner==g_ui->my_player && !g_ui->ut_building(passenger)
                && !g_ui->u_flying(passenger) && !g_ui->u_loaded(passenger) && g_ui->u_completed(passenger)
                && ((g_ui->unit_provides_space(target) && passenger->unit_type->space_required>0
                     && g_ui->unit_can_load_target(target,passenger)) || g_ui->unit_can_enter_nydus(passenger,target)))return 1;
        if (g_ui->unit_is_refinery(target) && g_ui->u_completed(target))
            for (auto id : g_ui->current_selection) if (auto* worker = g_ui->get_unit(id))
                if (worker->owner == g_ui->my_player && g_ui->ut_worker(worker)
                    && g_ui->u_completed(worker)) return 1;
        return 0;
    }
    bool owned = false;
    for (auto id : g_ui->current_selection) if (auto* u = g_ui->get_unit(id)) {
        if (u->owner != g_ui->my_player) continue;
        owned = true;
        if (g_ui->u_completed(u) && !g_ui->ut_building(u) && !g_ui->ut_worker(u) &&
            !g_ui->unit_is(u, UnitTypes::Zerg_Larva) && !g_ui->unit_is_egg(u) && g_ui->command_can_attack(u)) return 3;
    }
    return owned ? 1 : 0;
}
OPENBW_EXPORT(openbw_touch_attack) void openbw_touch_attack() {
    if (g_ui && !g_ui->paused && !g_ui->campaign_control_lock) g_ui->start_target(g_ui->T_ATTACK);
}
OPENBW_EXPORT(openbw_touch_cancel) void openbw_touch_cancel() {
    if (!g_ui) return;
    // Cancel the local selection gesture without committing it or an order.
    extern void openbw_discard_pointer_events();
    openbw_discard_pointer_events();
    g_ui->is_drag_selecting = false;
    g_ui->is_dragging_screen = false;
    g_ui->is_moving_minimap = false;
}
OPENBW_EXPORT(openbw_portrait_for_type) int openbw_portrait_for_type(int type) {
    return g_ui && type >= 0 && type < 228 ? g_ui->unit_portrait((UnitTypes)type) : -1;
}
OPENBW_EXPORT(openbw_portrait_talking) int openbw_portrait_talking() {
    if (!g_ui) return 0;
    auto* u = g_ui->primary_selected();
    if (!u) return 0;
    for (size_t i = 0; i < g_ui->sound_channels.size(); ++i) {
        auto& c = g_ui->sound_channels[i];
        if (c.playing && (c.flags & 2) && c.unit_type == u->unit_type && native_sound::is_playing(i)) return 1;
    }
    return 0;
}
// Local test controls. Never grant resources or production bonuses to enemy players.
OPENBW_EXPORT(openbw_test_instant) void openbw_test_instant(int enabled) {
    if (g_ui) { g_ui->test_instant = enabled != 0; if (enabled) g_ui->rep_on = false; }
}
OPENBW_EXPORT(openbw_test_money) void openbw_test_money() {
    if (!g_ui) return;
    int p = g_ui->my_player;
    g_ui->st.current_minerals[p] = std::min(999999, g_ui->st.current_minerals[p] + 10000);
    g_ui->st.current_gas[p] = std::min(999999, g_ui->st.current_gas[p] + 10000);
    g_ui->rep_on = false;
}

// External cursor + view zoom support: the host renders the frame at window/zoom
// and upscales; the cursor is drawn in a native-resolution host overlay and the
// engine draws the minimap at 1/scale so both keep a constant on-screen size.
OPENBW_EXPORT(openbw_cursor_rgba) const uint8_t* openbw_cursor_rgba() { return g_ui ? g_ui->cursor_rgba() : nullptr; }
OPENBW_EXPORT(openbw_cursor_box) int openbw_cursor_box() { return g_ui ? (int)g_ui->cursor_box() : 128; }
OPENBW_EXPORT(openbw_set_external_cursor) void openbw_set_external_cursor(int on) { if (g_ui) g_ui->external_cursor = on != 0; }
OPENBW_EXPORT(openbw_set_view_scale) void openbw_set_view_scale(double s) { if (g_ui) g_ui->minimap_scale = s >= .5 ? s : .5; }

// Debug JS API for console/automation testing: list units, select by id (see sandbox.h).
OPENBW_EXPORT(openbw_debug_units) const char* openbw_debug_units() { return g_ui ? g_ui->debug_units() : ""; }
OPENBW_EXPORT(openbw_debug_select) void openbw_debug_select(int id, int add) { if (g_ui) g_ui->debug_select(id, add); }
// Diagnostic fault injection: exercise campaign replacement requests without
// modifying the mission or its original AI bytecode. Never called by game UI.
OPENBW_EXPORT(openbw_debug_kill) void openbw_debug_kill(int raw_id) { if(g_ui) { auto* u=g_ui->get_unit(unit_id(uint16_t(raw_id))); if(u&&!g_ui->unit_dying(u))g_ui->kill_unit(u); } }
OPENBW_EXPORT(openbw_debug_set_life) void openbw_debug_set_life(int id, int hp, int shields) { if (g_ui) g_ui->debug_set_life(id, hp, shields); }

// Deterministic scenario diagnostics, not exposed as player controls.
OPENBW_EXPORT(openbw_debug_warp) void openbw_debug_warp(int raw_id,int x,int y) {
    if(!g_ui)return;auto* u=g_ui->get_unit(unit_id(uint16_t(raw_id)));if(!u||g_ui->unit_dying(u))return;
    auto pos=g_ui->find_unit_placement(u,{x,y},true,false);if(!pos.first)return;
    g_ui->reset_movement_state(u);g_ui->move_unit(u,pos.second);g_ui->refresh_unit_vision(u);if(u->subunit)g_ui->move_unit(u->subunit,pos.second);
    g_ui->set_unit_order(u,u->unit_type->return_to_idle);
}
OPENBW_EXPORT(openbw_debug_doodads) const char* openbw_debug_doodads() {
    static a_string out;out.clear();if(!g_ui)return out.c_str();
    for(int p=0;p<12;++p)for(auto* u:ptr(g_ui->st.player_units[p]))if(g_ui->unit_is_door(u)||g_ui->unit_is_trap(u))
        out+=format("%d\t%d\t%d\t%d\t%d\t%d\t%d\n",int(g_ui->get_unit_id(u).raw_value),int(u->unit_type->id),u->sprite->position.x,u->sprite->position.y,int(g_ui->u_disabled(u)),int(g_ui->u_no_collide(u)),int(u->order_type->id));
    return out.c_str();
}

// Cancel the build-queue slot a status chip was clicked on (0 = the one in progress).
OPENBW_EXPORT(openbw_cancel) void openbw_cancel(int slot) { if (g_ui) g_ui->cancel_queue_slot(slot); }

// Toggle the selected-unit order/rally line overlay (off by default).
OPENBW_EXPORT(openbw_set_order_lines) void openbw_set_order_lines(int on) {
	if (g_ui) g_ui->show_order_lines = on != 0;
}

// Freeze game input (selection/orders/hotkeys and their sounds/markers) while paused.
OPENBW_EXPORT(openbw_set_paused) void openbw_set_paused(int on) {
	if (g_ui) g_ui->paused = on != 0;
}

// --- deterministic command stream (lockstep multiplayer) --------------------
// Local input is serialised to BW command bytes rather than applied directly. The host
// drains them each frame, schedules them for a later frame, ships them to peers, and every
// peer applies the identical stream via openbw_apply — keeping all sims bit-identical.
// The buffer holds framed records: [u16 len][opcode][payload].

OPENBW_EXPORT(openbw_out_ptr) const uint8_t* openbw_out_ptr() {
	return g_ui && !g_ui->outgoing.empty() ? g_ui->outgoing.data() : nullptr;
}
OPENBW_EXPORT(openbw_out_len) int openbw_out_len() { return g_ui ? (int)g_ui->outgoing.size() : 0; }
OPENBW_EXPORT(openbw_out_clear) void openbw_out_clear() { if (g_ui) g_ui->outgoing.clear(); }

// Scratch buffer the host writes a peer's batch into before calling openbw_apply.
namespace { a_vector<uint8_t> g_inbuf; }
OPENBW_EXPORT(openbw_in_ptr) uint8_t* openbw_in_ptr(int len) {
	if (len < 0) len = 0;
	g_inbuf.resize((size_t)len);
	return g_inbuf.empty() ? nullptr : g_inbuf.data();
}

// Post a chat/system line (bytes in the openbw_in_ptr scratch buffer) to the message log.
OPENBW_EXPORT(openbw_post_message) void openbw_post_message(int len) {
	if (g_ui && len > 0 && (size_t)len <= g_inbuf.size())
		g_ui->post_message(a_string((const char*)g_inbuf.data(), (size_t)len));
}
// Apply `len` bytes of framed commands as `owner`. Must be called on every peer for every
// player, in the same order, on the same frame.
OPENBW_EXPORT(openbw_apply) void openbw_apply(int owner, int len) {
	if (g_ui && len > 0 && (size_t)len <= g_inbuf.size())
		g_ui->apply_commands(owner, g_inbuf.data(), (size_t)len);
}

// Local skirmish using original-script runtime and portable snapshots.
OPENBW_EXPORT(openbw_init_race_ai) void openbw_init_race_ai(int width,int height,int race,int opponent,int ai_race) {
    if(opponent<1||opponent>=8||(ai_race<0||ai_race>2))error("Invalid computer opponent");
    mp_slot slots[]={{0,race_t(race)},{opponent,race_t(ai_race)}};
    init_game(width,height,0,slots,2,false,opponent);
}
// Preserve this entry point for existing Terran regression harnesses.
OPENBW_EXPORT(openbw_init_terran_ai) void openbw_init_terran_ai(int width,int height,int race,int opponent) {
    openbw_init_race_ai(width,height,race,opponent,1);
}

// Multiplayer init: the host writes the slot list into the openbw_in_ptr scratch buffer as
// int32 pairs [slot, race, slot, race, …] first, then calls this. Every peer must pass an
// identical list and load the same map, or the initial states differ and lockstep breaks
// at frame 0. (int is 32-bit on wasm32, so the pairs read back directly.)
OPENBW_EXPORT(openbw_init_mp) void openbw_init_mp(int width, int height, int my_slot, int n) {
	if (n <= 0 || g_inbuf.size() < (size_t)n * 2 * sizeof(int)) return;
	a_vector<mp_slot> slots;
	const int* p = (const int*)g_inbuf.data();
	for (int i = 0; i != n; ++i) slots.push_back(mp_slot{p[2 * i], (race_t)p[2 * i + 1]});
	init_game(width, height, my_slot, slots.data(), slots.size());
}


// 0 undecided, 1 victory, 2 defeat. Both peers derive this from the shared deterministic
// sim, so they agree without exchanging anything.
OPENBW_EXPORT(openbw_outcome) int openbw_outcome() { return g_ui ? g_ui->outcome : 0; }

// Number of start locations on the loaded map. The host picks starting slots before the
// map is parsed (start locations aren't known that early), so it works from a table; this
// lets the host verify that table at runtime instead of trusting it silently.
OPENBW_EXPORT(openbw_start_locations) int openbw_start_locations() {
	if (!g_ui) return 0;
	int n = 0;
	for (size_t i = 0; i != 8; ++i) if (g_ui->game_st.start_locations[i] != xy()) ++n;
	return n;
}

// Loaded-map metadata for the lobby info line + a runtime cross-check of the host's
// table (like openbw_start_locations). Tileset index: 0 Badlands, 1 Space, 2
// Installation, 3 Ashworld, 4 Jungle, 5 Desert, 6 Ice, 7 Twilight.
OPENBW_EXPORT(openbw_map_w) int openbw_map_w() { return g_ui ? (int)g_ui->game_st.map_tile_width : 0; }
OPENBW_EXPORT(openbw_map_h) int openbw_map_h() { return g_ui ? (int)g_ui->game_st.map_tile_height : 0; }
OPENBW_EXPORT(openbw_minimap_terrain) int openbw_minimap_terrain() { return g_ui && g_ui->minimap_terrain; }
OPENBW_EXPORT(openbw_set_minimap_terrain) void openbw_set_minimap_terrain(int on) { if (g_ui) g_ui->minimap_terrain = on != 0; }
OPENBW_EXPORT(openbw_map_tileset) int openbw_map_tileset() { return g_ui ? (int)g_ui->game_st.tileset_index : 0; }

// Serialise the recorded game as a BW .rep and hand back the bytes. Returns 0 if nothing
// was recorded. The result stays valid until the next call.
OPENBW_EXPORT(openbw_save_replay) const uint8_t* openbw_save_replay() {
	if (!g_ui || !g_ui->rep_on) return nullptr;
	g_ui->rep_out.clear();
	// vector_writer only writes into already-reserved capacity (its left() is
	// capacity - size) and throws otherwise, so size the buffer up front.
	size_t hist = 0;
	for (auto& v : g_ui->rep.history) hist += v.size();
	g_ui->rep_out.reserve(g_ui->rep.map_data_size + hist + (size_t)(1 << 20));
	auto w = data_loading::make_vector_writer(g_ui->rep_out);
	replay_saver_functions(g_ui->rep).save_replay(g_ui->player.st().current_frame, w, g_skirmish_expansion);
	return g_ui->rep_out.data();
}
OPENBW_EXPORT(openbw_replay_len) int openbw_replay_len() { return g_ui ? (int)g_ui->rep_out.size() : 0; }

// Resign: concede the game. Routed through the command stream so a 1v1 stays in lockstep.
OPENBW_EXPORT(openbw_resign) void openbw_resign() { if (g_ui) g_ui->resign(); }

// End-game score for the game-over screen (see play_ui::stats_text for the format).
OPENBW_EXPORT(openbw_stats) const char* openbw_stats() { return g_ui ? g_ui->stats_text() : ""; }

// Reveal the whole map (fog_player < 0 turns off fog rendering). Render-only, no sim
// effect — used by the game-over "Look at map" so you can review the final board.
OPENBW_EXPORT(openbw_reveal_map) void openbw_reveal_map() { if (g_ui) g_ui->fog_player = -1; }

// Spectator mode (bot-vs-bot): no unit-ack voices, and the resource HUD follows the
// selected unit's owner. Render/UI only — no sim effect.
OPENBW_EXPORT(openbw_set_spectator) void openbw_set_spectator(int on) { if (g_ui) g_ui->spectator = on != 0; }

// Debug: force the outcome (1 victory, 2 defeat) to exercise the game-over screen without
// playing to elimination. Bypasses the competitive gate, so it works in single-player too.
OPENBW_EXPORT(openbw_debug_outcome) void openbw_debug_outcome(int v) { if (g_ui) g_ui->outcome = v; }

OPENBW_EXPORT(openbw_debug_resources) void openbw_debug_resources(int minerals, int gas) {
	if (!g_ui) return;
	g_ui->st.current_minerals[g_ui->my_player] = minerals;
	g_ui->st.current_gas[g_ui->my_player] = gas;
}

OPENBW_EXPORT(openbw_frame) int openbw_frame() { return g_ui ? (int)g_ui->st.current_frame : 0; }

// Desync probe (shared implementation in sandbox.h, so native and wasm can't disagree).
// Peers compare it periodically; any divergence means the sims have drifted.
OPENBW_EXPORT(openbw_checksum) unsigned openbw_checksum() {
	return g_ui ? sim_checksum(g_ui->st) : 0;
}
