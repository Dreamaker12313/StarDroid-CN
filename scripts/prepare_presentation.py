"""Idempotent native presentation fixes applied to the pinned engine sources."""
from pathlib import Path

def prepare(stage):
    def replace(file, old, new):
        p = stage / file; s = p.read_text()
        if new in s: return
        if old not in s: raise RuntimeError('Unrecognized presentation source: ' + file + ': ' + old[:65])
        p.write_text(s.replace(old, new, 1))
    replace('web/sandbox.h', '\tvoid add_move_orders() {', '''\tbool command_can_attack(const unit_t* u) const {
        return unit_or_subunit_ground_weapon(u) || unit_air_weapon(u)
            || unit_is_carrier(u) || unit_is_reaver(u);
    }
    void add_move_orders() {''')
    replace('web/sandbox.h', '\t\tcard.push_back({\'a\', "Attack", C_ATTACK, UnitTypes::None});', '''        bool armed = false;
        for (auto id : current_selection) if (auto* u = get_unit(id))
            if (u->owner == my_player && command_can_attack(u)) armed = true;
        if (armed) card.push_back({'a', "Attack", C_ATTACK, UnitTypes::None});''')
    replace('web/wasm_main.cpp', '!g_ui->unit_is(u, UnitTypes::Zerg_Larva) && !g_ui->unit_is_egg(u)) return 3;', '!g_ui->unit_is(u, UnitTypes::Zerg_Larva) && !g_ui->unit_is_egg(u) && g_ui->command_can_attack(u)) return 3;')
    replace('web/sandbox.h', 'e.type == ev::type_key_down && e.scancode == 41', 'e.type == ev::type_key_down && (e.scancode == 41 || e.sym == 27)')
    # Morphing a colony or spire does not make it a unit producer. Conversely,
    # a Hatchery still rallies larvae when this mission forbids its Lair morph.
    replace('web/sandbox.h', '''\t\t\tbool produces = false;
\t\t\tfor (auto& c : card) if (c.act == C_TRAIN || c.act == C_MORPHBLDG) { produces = true; break; }
\t\t\tif (produces) card.push_back({pick_key("Rally"), "Set Rally Point", C_RALLY, U::None});''',
        '''            if (unit_is_factory(u)) card.push_back({pick_key("Rally"), "Set Rally Point", C_RALLY, U::None});''')
    # Rendering still covers the full backing surface. Camera bounds, centering
    # and the minimap rectangle use the part of the map visible above the HUD.
    replace('ui/ui.h', '\tsize_t view_height;', '''\tsize_t view_height;
    int hud_bottom_inset = 0;
    size_t camera_height() const { return std::max(1, int(view_height) - hud_bottom_inset); }''')
    replace('ui/ui.h', '(size_t)((view_height + 31) / 32u) * mh / th', '(size_t)((camera_height() + 31) / 32u) * mh / th')
    replace('ui/ui.h', 'screen_pos = xy(32 * x - view_width / 2, 32 * y - view_height / 2);', 'screen_pos = xy(32 * x - view_width / 2, 32 * y - camera_height() / 2);')
    replace('ui/ui.h', 'if (screen_pos.y + (int)view_height > (int)game_st.map_height) screen_pos.y = (int)game_st.map_height - (int)view_height;', 'if (screen_pos.y + (int)camera_height() > (int)game_st.map_height) screen_pos.y = (int)game_st.map_height - (int)camera_height();')
    replace('web/sandbox.h', 'void center_on(xy pos) { screen_pos = xy(pos.x - view_width / 2, pos.y - view_height / 2); }', 'void center_on(xy pos) { screen_pos = xy(pos.x - view_width / 2, pos.y - camera_height() / 2); clamp_viewport(); }')
    replace('web/sandbox.h', '(int)game_st.map_height - (int)view_height));', '(int)game_st.map_height - (int)camera_height()));')
    replace('web/campaign.h', 'screen_pos = (loc.area.from + loc.area.to) / 2 - xy(screen_width / 2, screen_height / 2);', 'center_on((loc.area.from + loc.area.to) / 2);')
    # Initial UNIT records contain explicit addon relationships. Resolve them
    # after all units exist; starting an addon in its idle animation omits its
    # connecting arm and also leaves its parent's technology disconnected.
    replace('bwgame.h', 'tag_funcs["UNIT"] = [&](data_reader_le r) {\n\t\t\twhile (r.left()) {', '''tag_funcs["UNIT"] = [&](data_reader_le r) {
            a_unordered_map<int, unit_t*> initial_units;
            a_vector<std::pair<int, int>> initial_links;
\t\t\twhile (r.left()) {''')
    replace('bwgame.h', 'unit_t* u = create_initial_unit(unit_type, {x, y}, owner);\n\n\t\t\t\tif (!u) continue;', '''unit_t* u = create_initial_unit(unit_type, {x, y}, owner);

                if (!u) continue;
                initial_units[id] = u;
                if ((link & 0x200) && related_unit_id) initial_links.emplace_back(id, related_unit_id);''')
    replace('bwgame.h', '''\t\t\tfor (unit_t* u : ptr(st.visible_units)) {
\t\t\t\tupdate_unit_sprite(u);
\t\t\t}
\t\t\tst.update_psionic_matrix = true;
\t\t};''', '''            for (auto ids : initial_links) {
                auto a = initial_units.find(ids.first), b = initial_units.find(ids.second);
                if (a == initial_units.end() || b == initial_units.end()) continue;
                auto* parent = a->second; auto* addon = b->second;
                if (ut_addon(parent)) std::swap(parent, addon);
                if (!u_grounded_building(parent) || !unit_can_attach_addon(parent, addon)
                    || parent->building.addon || (addon->owner != parent->owner && addon->owner != 11)) continue;
                xy expected = parent->sprite->position - parent->unit_type->placement_size / 2
                    + addon->unit_type->addon_position + addon->unit_type->placement_size / 2;
                if (expected != addon->sprite->position) continue;
                connect_addon(parent, addon);
            }
            // Older maps can omit serial links but still place owned addons at
            // the canonical socket. Do not attach arbitrary neutral neighbors.
            for (unit_t* parent : ptr(st.visible_units)) {
                if (!u_grounded_building(parent) || ut_addon(parent)
                    || unit_race(parent) != race_t::terran || parent->building.addon) continue;
                for (unit_t* addon : ptr(st.player_units[parent->owner])) {
                    if (!ut_addon(addon) || !unit_can_attach_addon(parent, addon)) continue;
                    xy expected = parent->sprite->position - parent->unit_type->placement_size / 2
                        + addon->unit_type->addon_position + addon->unit_type->placement_size / 2;
                    if (expected == addon->sprite->position) {connect_addon(parent, addon); break;}
                }
            }
\t\t\tfor (unit_t* u : ptr(st.visible_units)) {
\t\t\t\tupdate_unit_sprite(u);
\t\t\t}
\t\t\tst.update_psionic_matrix = true;
\t\t};''')
