#pragma once
// Real imported GRP/palette rendering; simulation state and visibility are held
// fixed while comparing the target-feedback pixels. Included by the host suite.
static void fog_target79(const char* broodwar) {
 load(broodwar,502);step(4);openbw_render(0);
 unit_t* building=nullptr;for(auto* u:units(U::Terran_Bunker,7))if(u->position.x>512&&u->position.y>512){building=u;break;}
 auto marines=units(U::Terran_Marine,7);
 require(building&&!marines.empty(),"Fog target original units missing");auto* marine=marines.front();
 g_ui->set_unit_owner(marine,g_ui->my_player,false);
 g_ui->current_selection.clear();g_ui->screen_pos=building->position-xy(320,200);
 g_ui->clamp_viewport();
 int viewer=g_ui->fog_player;unsigned mask=1u<<viewer;
 for(auto& t:g_ui->st.tiles){t.explored&=~mask;t.visible|=mask;}
 building->sprite->visibility_flags=mask;
 g_ui->snapshot_fog_sprite(building->sprite);
 building->sprite->visibility_flags=0;
 require(g_ui->unit_frozen_by_fog(building),"Fixture building is not in explored fog");
 size_t width=g_ui->screen_width,height=g_ui->screen_height;
 auto scene=[&](bool flash,double elapsed=0){
  g_ui->ui_now=1000+elapsed;g_ui->flash_unit=g_ui->get_unit_id(building);g_ui->flash_start=flash?1000:-1;
  std::vector<uint8_t> pixels(width*height,1);g_ui->draw_sprites(pixels.data(),width);return pixels;
 };
 // Issue the actual attack-target input against the remembered building.
 g_ui->current_selection_add(marine);g_ui->ui_now=1000;g_ui->pending_targ=g_ui->T_ATTACK;
 g_ui->issue_target(building->position);
 require(g_ui->get_unit(g_ui->flash_unit)==building,"Attack command did not target remembered building");
 // Right-click/touch default orders use the same target cue.
 g_ui->campaign_control_lock=false;g_ui->paused=false;g_ui->targeting=false;g_ui->menu=0;g_ui->flash_start=-1;
 native_window::event_t click{};click.type=native_window::event_t::type_mouse_button_down;click.button=3;
 click.mouse_x=building->position.x-g_ui->screen_pos.x;click.mouse_y=building->position.y-g_ui->screen_pos.y;
 require(g_ui->handle_game_input(click)&&g_ui->flash_start==1000&&g_ui->get_unit(g_ui->flash_unit)==building,
         "Default order did not flash the remembered building");
 g_ui->current_selection.clear();
 auto checksum=openbw_checksum();auto plain=scene(false),targeted=scene(true);
 require(openbw_checksum()==checksum,"Target-circle rendering altered simulation state");
 require(plain!=targeted,"Fogged enemy building does not show a targeting circle");
 int red=g_ui->line_atk_color;require(red>=0,"Targeting did not resolve red palette entry");
 size_t redPixels=0;for(size_t i=0;i<plain.size();++i)if(plain[i]!=targeted[i]&&targeted[i]==red)++redPixels;
 require(redPixels>10,"Fogged enemy targeting circle is not red");
 require(scene(true,1000)==plain&&scene(true,2000)==targeted&&scene(true,3000)==plain,
         "Fogged target blink timing/lifetime differs from visible targets");
 // Compare the actual snapshot body and ring pixels to prove the body occludes
 // the back of the ring, rather than displaying feedback on top of the building.
 g_ui->ui_now=1000;g_ui->flash_start=-1;
 std::vector<uint8_t> body(width*height,1),ring(width*height,1),combined(width*height,1);
 g_ui->draw_fog_snapshot(building->sprite,body.data(),width);
 g_ui->draw_selection_ring(building,uint8_t(red),ring.data(),width);
 g_ui->flash_start=1000;g_ui->draw_fog_snapshot(building->sprite,combined.data(),width);
 size_t covered=0,exposed=0;
 for(size_t i=0;i<body.size();++i)if(ring[i]==red){
  if(body[i]!=1&&body[i]!=red&&combined[i]==body[i])++covered;
  if(body[i]==1&&combined[i]==red)++exposed;
 }
 require(covered>0&&exposed>0,"Target ring is not both exposed below and occluded by the remembered body");
 // An explored tile without a remembered image must not disclose a structure.
 auto snapshot=g_ui->fog_snapshots[building->sprite->index];
 g_ui->fog_snapshots[building->sprite->index].valid=false;
 require(scene(false)==scene(true),"Target feedback reveals a never-seen building");
 g_ui->fog_snapshots[building->sprite->index]=snapshot;
 for(auto& t:g_ui->st.tiles)t.explored|=mask;
 require(scene(false)==scene(true),"Target feedback reveals an unexplored building");
 for(auto& t:g_ui->st.tiles)t.explored&=~mask;
 // Ordinary selection also retains its red circle, independent of flash expiry.
 auto unselected=scene(false);g_ui->current_selection_add(building);auto selected=scene(false);
 require(selected!=unselected&&scene(false,5000)==selected,"Selected remembered building lacks a persistent circle");
 size_t selectedRed=0;
 for(size_t i=0;i<selected.size();++i)if(selected[i]!=unselected[i])
  for(int n=0;n<8;++n)if(selected[i]==g_ui->img.selection_colors[16+n]){++selectedRed;break;}
 require(selectedRed>10,"Selected remembered enemy building circle is not red");
 g_ui->fog_snapshots[building->sprite->index].valid=false;auto unseenSelected=scene(false);
 g_ui->current_selection.clear();require(scene(false)==unseenSelected,"Selecting a never-seen building discloses a circle");
 g_ui->fog_snapshots[building->sprite->index]=snapshot;
 // Live enemies retain the same target feedback.
 building->sprite->visibility_flags=mask;
 require(scene(false)!=scene(true),"Visible enemy target circle regressed");
 // Enemy mobile units disappear in fog even if a previous click still flashes.
 g_ui->set_unit_owner(marine,1,false);warp(marine,building->position+xy(160,0));marine->sprite->visibility_flags=mask;
 g_ui->flash_unit=g_ui->get_unit_id(marine);g_ui->ui_now=1000;
 auto mobile=[&](bool flash){g_ui->flash_start=flash?1000:-1;std::vector<uint8_t> p(width*height,1);g_ui->draw_sprites(p.data(),width);return p;};
 require(mobile(false)!=mobile(true),"Mobile fixture does not display a visible on-screen target circle");
 marine->sprite->visibility_flags=0;
 require(mobile(false)==mobile(true),"Target circle discloses an enemy mobile unit through fog");
 std::cout<<"PASS fogged enemy target: attack/default-order input, red pixels below remembered building, blink/expiry and persistent selection, visible targets and no unseen/mobile information leak\n";
 close_game();
}
