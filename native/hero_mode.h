#pragma once
// Applied once after melee map initialization, identically on every device.
static void configure_hero_mode(bool enabled) {
 bwgame::game_load_functions rules(g_ui->st);
 rules.game_st.hero_mode=enabled;
 if(!enabled)return;
 using namespace bwgame;
 for(const auto& h:hero_roster()) {
  auto& type=rules.game_st.unit_types.vec[int(UnitTypes(h.id))];
  const auto& base=rules.game_st.unit_types.vec[int(UnitTypes(h.base))];
  type.mineral_cost=h.minerals;type.gas_cost=h.gas;
  type.supply_required.raw_value=h.supply2;
  type.build_time=base.build_time;
  for(int p=0;p<12;p++)rules.game_st.unit_type_allowed[p][type.id]=true;
 }
 auto& tank=rules.game_st.unit_types.vec[int(UnitTypes::Hero_Edmund_Duke_Tank_Mode)];
 auto& siege=rules.game_st.unit_types.vec[int(UnitTypes::Hero_Edmund_Duke_Siege_Mode)];
 siege.mineral_cost=tank.mineral_cost;siege.gas_cost=tank.gas_cost;
 siege.supply_required=tank.supply_required;siege.build_time=tank.build_time;
 auto& archon=rules.game_st.unit_types.vec[int(UnitTypes::Hero_Tassadar_Zeratul_Archon)];
 archon.supply_required=fp1::integer(4);
 archon.build_time=rules.game_st.unit_types.vec[int(UnitTypes::Protoss_Archon)].build_time;
}
