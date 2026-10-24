// Original-data regressions for map edges, casualties, control groups and beacons.
static unit_t* polish_unit(U type,int owner,xy p) {
  auto* t=g_ui->get_unit_type(type);
  auto free=[&](xy pos) {
    if(!g_ui->unit_type_can_fit_at(t,pos))return false;
    for(auto* other:g_ui->find_units_noexpand({pos-t->dimensions.from-xy(32,32),pos+t->dimensions.to+xy(32,32)}))
      if(!g_ui->unit_dying(other)&&!g_ui->unit_is_special_beacon(other))return false;
    return true;
  };
  if(!free(p)) {
    bool found=false;
    for(int y=96;y<int(g_ui->game_st.map_height)-96&&!found;y+=64)for(int x=96;x<int(g_ui->game_st.map_width)-96&&!found;x+=64)
      if(free({x,y})){p={x,y};found=true;}
    require(found,"No open terrain for polish fixture");
  }
  auto* u=g_ui->create_initial_unit(t,p,owner);
  require(u,"Polish fixture creation failed: "+name(type));
  // Exercise flag pads as stationary mission markers. Capture-the-flag mode's
  // CTFCOPInit order is not implemented and none of the 64 supplied maps uses it.
  if(type>=U::Special_Zerg_Flag_Beacon&&type<=U::Special_Protoss_Flag_Beacon)
    g_ui->set_unit_order(u,g_ui->get_order_type(Orders::Nothing));
  return u;
}
static void polish39() {
  check("Map canvas clears off-map pixels at four viewport sizes",[]{
    for(auto size:{xy(640,480),xy(1280,960),xy(427,320),xy(960,480)}) {
      openbw_resize(size.x,size.y);command(21,size.y/3,0,0,0);openbw_pan(65536,65536);draw();
      require(g_ui->screen_pos.y+int(g_ui->camera_height())==int(g_ui->game_st.map_height),"Bottom camera does not end at map boundary");
      auto& surface=*g_ui->indexed_surface;
      auto* p=(uint8_t*)surface.lock();memset(p,127,surface.pitch*surface.h);surface.unlock();draw();
      p=(uint8_t*)surface.lock();
      for(size_t y=size.y-8;y<size_t(size.y);++y)for(size_t x=size_t(g_ui->get_minimap_area().to.x+2);x<size_t(size.x-8);++x)
        require(p[y*surface.pitch+x]==0,"Last frame persists beyond map");
      surface.unlock();
    }
    openbw_resize(640,480);command(21,160,0,0,0);draw();
  });
  check("Casualty returns survivor to 64px wireframe and control group",[]{
    auto* a=polish_unit(U::Terran_Marine,0,{300,300});auto* b=polish_unit(U::Terran_Marine,0,{350,300});
    select(a);openbw_debug_select(g_ui->get_unit_id(b).raw_value,1);draw();require(openbw_wire_box()==32,"Two units should use group tiles");
    command(25,1,1,0,0);require(value_query(21,1)==2,"Group assignment failed");
    g_ui->kill_unit(a);draw();require(g_ui->current_selection.size()==1&&openbw_wire_box()==64&&g_ui->selected_nth(0)==b,"Dying ID keeps survivor wireframe small");
    step(120);require(openbw_wire_box()==64,"Removed ID keeps survivor wireframe small");
    g_ui->current_selection_clear();command(25,1,0,0,0);draw();require(g_ui->primary_selected()==b&&value_query(21,1)==1,"Group recalls dead units");
    g_ui->screen_pos={500,500};g_ui->ui_now+=100;command(25,1,0,0,0);draw();
    require(g_ui->screen_pos.x<=b->position.x&&g_ui->screen_pos.y<=b->position.y,"Double recall does not center on survivor");
    g_ui->paused=true;command(25,2,1,0,0);require(value_query(21,2)==0,"Paused group input not blocked");g_ui->paused=false;
    auto snapshot=save_game();g_ui->groups[1].clear();restore_game(snapshot);require(value_query(21,1)==1,"Control group not restored with save");
  });
  for(U type:{U::Special_Zerg_Beacon,U::Special_Terran_Beacon,U::Special_Protoss_Beacon,U::Special_Zerg_Flag_Beacon,U::Special_Terran_Flag_Beacon,U::Special_Protoss_Flag_Beacon})
    check("Beacon immune to combat but removable by scripts: "+name(type),[=]{
      auto* target=polish_unit(type,1,{900,900});auto id=g_ui->get_unit_id(target);
      auto hp=target->hp;auto shield=target->shield_points;
      for(U attacker:{U::Terran_Marine,U::Protoss_Zealot,U::Zerg_Zergling,U::Hero_Infested_Kerrigan}) {
        auto* u=polish_unit(attacker,0,{800,900});
        require(!g_ui->unit_can_attack_target(u,target),"Beacon accepted as attack target");
        for(auto weapon:{WeaponTypes::Gauss_Rifle,WeaponTypes::Psionic_Storm}) {
          auto* w=g_ui->get_weapon_type(weapon);require(!g_ui->weapon_can_target_unit(w,target),"Beacon accepted as weapon target");
          g_ui->weapon_deal_damage(w,10000_fp8,1,target,u->heading,u,0);
          require(target->hp==hp&&target->shield_points==shield,"Combat or spell damage changed beacon");
        }
        select(u);press("Attack");click(target->position);step(24);
        require(u->order_target.unit!=target&&target->hp==hp,"Explicit attack retained beacon target");
        g_ui->kill_unit(u);step(60);
      }
      require(g_ui->trigger_give_unit_to(target,0),"Beacon rescue/ownership transfer blocked");
      g_ui->kill_unit(target);step(120);require(!g_ui->get_unit(id)||g_ui->unit_dying(g_ui->get_unit(id)),"Scripted beacon removal blocked");
    });
  check("Fleet Beacon remains a destructible Protoss building",[]{
    auto* target=polish_unit(U::Protoss_Fleet_Beacon,1,{1100,1000});auto* u=polish_unit(U::Terran_Marine,0,{1000,1000});
    require(!g_ui->u_invincible(target)&&g_ui->unit_can_attack_target(u,target),"Fleet Beacon accidentally protected");
    auto hp=target->hp;g_ui->set_unit_shield_points(target,0_fp8);
    g_ui->weapon_deal_damage(g_ui->get_weapon_type(WeaponTypes::Gauss_Rifle),10000_fp8,1,target,u->heading,u,0);
    require(target->hp<hp||g_ui->unit_dying(target),"Fleet Beacon cannot be damaged");
  });
}
