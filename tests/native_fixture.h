#pragma once
// Minimal synthetic data shared by native logic tests, never game assets.
#include "../native/runtime.cpp"
#include <iostream>
#include <set>
using namespace bwgame;
static void require(bool ok, const char* why) {if (!ok) throw std::runtime_error(why);}

struct RecordingUI : campaign_ui {
  using campaign_ui::campaign_ui;
  using campaign_ui::play_sound;
  struct Sound {int id;xy position;const unit_t* source;};
  std::vector<Sound> sounds;
  void play_sound(int id,xy position,const unit_t* source,bool) override {sounds.push_back({id,position,source});}
};
struct Fixture {
  global_state global{};
  game_state game{};
  state st{};
  std::unique_ptr<RecordingUI> ui;
  grp_t grp{};
  sprite_type_t spriteType{};
  image_type_t imageType{};
  Fixture() {
    st.global = &global; st.game = &game;
    game.map_width = game.map_height = 1024;
    game.map_tile_width = game.map_tile_height = 32;
    game.max_unit_width = game.max_unit_height = 64;
    st.tiles.resize(32 * 32);
    global.order_types.vec.resize(size_t(Orders::None));
    for (size_t i=0;i<global.order_types.vec.size();i++) {
      auto& o=global.order_types.vec[i];o.id=Orders(i);o.can_be_interrupted=true;
    }
    game.unit_types.vec.resize(size_t(UnitTypes::None));
    for (size_t i=0;i<game.unit_types.vec.size();i++) {
      auto& t=game.unit_types.vec[i];t.id=UnitTypes(i);t.group_flags=GroupFlags::Zerg;
      t.armor_upgrade=UpgradeTypes::Zerg_Carapace;t.hitpoints=100_fp8;
      t.dimensions={{8,8},{8,8}};t.placement_size={32,32};
      t.return_to_idle=&global.order_types.vec[size_t(Orders::Nothing)];
    }
    game.tech_types.vec.resize(size_t(TechTypes::None));
    for(size_t i=0;i<game.tech_types.vec.size();i++) {auto& t=game.tech_types.vec[i];t.id=TechTypes(i);t.energy_cost=25;}
    game.upgrade_types.vec.resize(size_t(UpgradeTypes::None));
    for(size_t i=0;i<game.upgrade_types.vec.size();i++)game.upgrade_types.vec[i].id=UpgradeTypes(i);
    for(auto& a:game.tech_available)a.fill(true);
    st.players[0].controller=player_t::controller_occupied;st.players[0].initially_active=true;
    grp.width=grp.height=32;grp.frames.resize(1);grp.frames[0].size={32,32};
    game_player player;player.set_st(st);ui.reset(new RecordingUI(std::move(player),0,race_t::zerg));
    ui->stat_txt_names.resize(1);ui->stat_txt_names[0]="Fixture";
    ui->screen_pos={0,0};ui->view_scale=fp16::integer(1);
  }
  unit_t* unit(UnitTypes type, int owner=0, xy position={128,128}, int flags=0) {
    auto* u=st.units_container.top();st.units_container.pop();
    auto& t=game.unit_types.vec[size_t(type)];t.flags=unit_type_t::flags_t(flags);u->unit_type=&t;u->owner=owner;
    u->status_flags=unit_t::status_flag_completed;u->hp=100_fp8;u->energy=250_fp8;
    u->position=position;u->order_type=ui->get_order_type(Orders::Nothing);
    u->secondary_order_type=ui->get_order_type(Orders::Nothing);
    auto* s=st.sprites_container.top();st.sprites_container.pop();u->sprite=s;
    s->sprite_type=&spriteType;s->position=position;s->visibility_flags=255;s->owner=owner;
    auto* image=st.images_container.top();st.images_container.pop();
    image->sprite=s;image->image_type=&imageType;image->grp=&grp;image->flags=image_t::flag_clickable;
    image->iscript_state.animation=iscript_anims::Init;s->main_image=image;s->images.push_back(*image);
    ui->unit_finder_insert(u);
    return u;
  }
  void select(unit_t* u) {ui->current_selection.clear();ui->current_selection.push_back(ui->get_unit_id(u));}
  std::set<std::string> card(unit_t* u) {
    select(u);ui->card.clear();ui->card_for_unit(u,u->unit_type->id);
    std::set<std::string> result;for(auto& c:ui->card)result.insert(c.label);return result;
  }
};

