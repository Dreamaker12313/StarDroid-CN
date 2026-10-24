"""Reproducible native corrections for the 0.29 feedback pass."""

def prepare(stage):
    def replace(file, old, new, count=1):
        p = stage / file
        s = p.read_text()
        if new in s:
            return
        if old not in s:
            raise RuntimeError('Unrecognized feedback source: ' + file + ': ' + old[:70])
        p.write_text(s.replace(old, new, count))

    # Traps are not buildings that can leave a visible last-seen silhouette.
    # The same predicate gates rendering, hit tests, selections and unit audio.
    replace('ui/ui.h', 'return ut_building(u) || unit_is_mineral_field(u)',
            'return (ut_building(u) && !unit_is_trap(u)) || unit_is_mineral_field(u)')
    replace('ui/ui.h', '''		if (u->owner == fog_player) return false;
		if (u->sprite->visibility_flags & (1 << fog_player)) return false;''', '''		if (u->owner == fog_player) return false;
        if (unit_is_trap(u) && unit_is_undetected(u, fog_player)) return true;
		if (u->sprite->visibility_flags & (1 << fog_player)) return false;''')
    replace('web/sandbox.h', '''		const auto* armor = get_upgrade_type(u->unit_type->armor_upgrade);
		int level = player_upgrade_level(u->owner,armor->id);
		details_text += format("\\narmor\\t%d\\t%d\\t%d\\t%d\\t1\\t%d",armor->icon,level,
			u->unit_type->armor,unit_armor(u).integer_part()-u->unit_type->armor,armor->label);''', '''        if (!unit_is_trap(u)) {
            const auto* armor = get_upgrade_type(u->unit_type->armor_upgrade);
            int level = player_upgrade_level(u->owner,armor->id);
            details_text += format("\\narmor\\t%d\\t%d\\t%d\\t%d\\t1\\t%d",armor->icon,level,
                u->unit_type->armor,unit_armor(u).integer_part()-u->unit_type->armor,armor->label);
        }''')

    # unit_can_use_tech already knows hero variants and mission restrictions.
    # Filtering first by the normal caster's exact ID hid those valid abilities.
    replace('web/sandbox.h', '\t\t\tif (sp[i].caster != id) continue;', '''            if (sp[i].tech == TechTypes::None && !unit_is_ghost(u)) continue;''')
    replace('web/sandbox.h', 'if (id == U::Terran_Marine || id == U::Terran_Firebat)',
            'if (unit_is_marine(u) || unit_is_firebat(u))')
    replace('web/sandbox.h', 'else if (id == U::Terran_Siege_Tank_Tank_Mode || id == U::Terran_Siege_Tank_Tank_Mode_Turret)',
            'else if (unit_is_unsieged_tank(u))')
    replace('web/sandbox.h', 'else if (id == U::Terran_Siege_Tank_Siege_Mode || id == U::Terran_Siege_Tank_Siege_Mode_Turret)',
            'else if (unit_is_sieged_tank(u))')
    replace('web/sandbox.h', 'ut_can_burrow(u) && (unit_is(u, U::Zerg_Lurker) || player_has_researched(my_player, TechTypes::Burrowing))',
            'ut_can_burrow(u) && unit_can_use_tech(u, get_tech_type(TechTypes::Burrowing), my_player)')
    replace('web/sandbox.h', '''bool cloakable = (id == U::Terran_Wraith && player_has_researched(my_player, TechTypes::Cloaking_Field)) ||
		                 (id == U::Terran_Ghost && player_has_researched(my_player, TechTypes::Personnel_Cloaking));''', '''bool cloakable = unit_can_use_tech(u, get_tech_type(TechTypes::Cloaking_Field), my_player)
            || unit_can_use_tech(u, get_tech_type(TechTypes::Personnel_Cloaking), my_player);''')
    replace('web/sandbox.h', 'c.enabled = player_has_researched(my_player, TechTypes::Stim_Packs);',
            'c.enabled = unit_can_use_tech(u, get_tech_type(TechTypes::Stim_Packs), my_player);')
    replace('web/sandbox.h', 'c.enabled = player_has_researched(my_player, TechTypes::Tank_Siege_Mode);',
            'c.enabled = unit_can_use_tech(u, get_tech_type(TechTypes::Tank_Siege_Mode), my_player);')
    replace('web/sandbox.h', 'else card.push_back({\'c\', "Cloak", C_CLOAK, U::None});', '''else {
                const auto* cloak = get_tech_type(unit_is_wraith(u)
                    ? TechTypes::Cloaking_Field : TechTypes::Personnel_Cloaking);
                card.push_back({'c', "Cloak", C_CLOAK, U::None,
                    u->energy >= fp8::integer(cloak->energy_cost)});
            }''')
    replace('web/sandbox.h', 'case C_UPGRADE: case C_RESEARCH: case C_SPELL: case C_LIFT: break;',
            'case C_UPGRADE: case C_RESEARCH: case C_SPELL: case C_CLOAK: case C_LIFT: break;')
    replace('web/sandbox.h', 'if (c.act == C_SPELL) raise_error(E_ENERGY);',
            'if (c.act == C_SPELL || c.act == C_CLOAK) raise_error(E_ENERGY);')
    replace('web/sandbox.h', 'unit_is(sel,UnitTypes::Terran_Ghost) ? TechTypes::Personnel_Cloaking : TechTypes::Cloaking_Field',
            'unit_is_wraith(sel) ? TechTypes::Cloaking_Field : TechTypes::Personnel_Cloaking', 2)
    replace('web/sandbox.h', '''{U::Terran_Ghost, T::Lockdown, O::CastLockdown, true, "Lockdown", 'l'},''', '''{U::Terran_Ghost, T::Lockdown, O::CastLockdown, true, "Lockdown", 'l'},
            {U::Terran_Vulture, T::Spider_Mines, O::PlaceMine, false, "Spider Mines", 'i'},''')
    replace('web/sandbox.h', '''    c.act == C_RESEARCH ? int(c.tech) : -1);''', '''    c.act == C_RESEARCH ? int(c.tech) : -1);
            int energy = c.act == C_SPELL && c.tech != TechTypes::None
                ? get_tech_type(c.tech)->energy_cost
                : c.act == C_CLOAK ? get_tech_type(unit_is_wraith(sel)
                    ? TechTypes::Cloaking_Field : TechTypes::Personnel_Cloaking)->energy_cost : 0;
            card_text += format("\\t%d", energy);''')
    # Infested Kerrigan has a personal cloak but is not a Ghost for Lockdown/nukes.
    replace('bwgame.h', '''case TechTypes::Personnel_Cloaking:
			if (!ut_hero(u) && !player_has_researched(owner, TechTypes::Personnel_Cloaking)) return false;
			if (!unit_is_ghost(u)) return false;''', '''case TechTypes::Personnel_Cloaking:
			if (!ut_hero(u) && !player_has_researched(owner, TechTypes::Personnel_Cloaking)) return false;
            if (!unit_is_ghost(u) && !unit_is(u, UnitTypes::Hero_Infested_Kerrigan)) return false;''')
    replace('actions.h', 'if (unit_is_ghost(u)) tech = get_tech_type(TechTypes::Personnel_Cloaking);',
            'if (unit_is_ghost(u) || unit_is(u, UnitTypes::Hero_Infested_Kerrigan)) tech = get_tech_type(TechTypes::Personnel_Cloaking);', 2)

    # Owned gas buildings must accept the contextual worker order before the
    # general "tap an owned unit to select it" rule takes precedence.
    replace('web/wasm_main.cpp', '''    if (target && !g_ui->unit_hidden_by_fog(target) && target->owner == g_ui->my_player) return 0;''', '''    if (target && g_ui->unit_hidden_by_fog(target)) target = nullptr;
    if (target && target->owner == g_ui->my_player) {
        if (g_ui->unit_is_refinery(target) && g_ui->u_completed(target))
            for (auto id : g_ui->current_selection) if (auto* worker = g_ui->get_unit(id))
                if (worker->owner == g_ui->my_player && g_ui->ut_worker(worker)
                    && g_ui->u_completed(worker)) return 1;
        return 0;
    }''')
    replace('web/sandbox.h', '''		if (!pending_land) play_sound(4 + int(unit_race(pending_build)),xy(),nullptr,false);
		if (auto* u = primary_selected()) play_unit_ack(u,u->unit_type->first_yes_sound,u->unit_type->last_yes_sound);''', '''		if (!pending_land) play_sound(4 + int(unit_race(pending_build)),xy(),nullptr,false);
        // Placement has its own acknowledgement. Do not also play worker speech.
        if (pending_land) if (auto* u = primary_selected())
            play_unit_ack(u,u->unit_type->first_yes_sound,u->unit_type->last_yes_sound);''')

    # Start the order before its iscript. Closing blocks immediately; opening
    # releases collision only when the animation raises its completion signal.
    replace('bwgame.h', '''			sprite_run_anim(u->sprite,enabled?iscript_anims::Enable:iscript_anims::Disable);
			set_unit_order(u,get_order_type(enabled?Orders::CloseDoor:Orders::OpenDoor));
			if(immediate){u_set_status_flag(u,unit_t::status_flag_no_collide,!enabled);u->sprite->elevation_level=enabled?u->unit_type->elevation_level:1;}''', '''            set_unit_order(u,get_order_type(enabled?Orders::CloseDoor:Orders::OpenDoor));
            if (enabled) {
                u_unset_status_flag(u,unit_t::status_flag_no_collide);
                u->sprite->elevation_level=u->unit_type->elevation_level;
            }
            auto unit_context = make_thingy_setter(iscript_unit, u);
            auto flingy_context = make_thingy_setter(iscript_flingy, u);
            sprite_run_anim(u->sprite,enabled?iscript_anims::Enable:iscript_anims::Disable);
            (void)immediate; // Initial doors also wait for their visible open frame.''')
