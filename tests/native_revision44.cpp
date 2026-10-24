// Real DAT/CHK/GRP regressions for command feedback and nuclear strikes.
#define OPENBW_REVISION43_EMBEDDED
#include "native_revision43.cpp"
#undef main
static void start44(int race=1){openbw_init(640,480,race,0);g_ui->competitive=false;advance(2);g_ui->st.current_minerals[0]=50000;g_ui->st.current_gas[0]=50000;}
static void sound44(){
 start44();
 for(auto e:{std::pair<int,const char*>{41,"ZDrErr00"},{7,"TSCErr01"},{64,"PPrErr00"}}){
  select(create(e.first));require(g_ui->placement_error_sound(855)==g_ui->find_sound(e.second),"Wrong race placement voice");
  require(g_ui->placement_error_sound(855)>=0,"Missing placement voice");
 }
 select(create(64));require(g_ui->placement_error_sound(860)==g_ui->find_sound("PPrErr01"),"Wrong pylon placement voice");
 auto* lander=create(106);select(lander);g_ui->pending_land=true;require(g_ui->placement_error_sound(855)==g_ui->find_sound("TAdErr04"),"Wrong landing voice");g_ui->pending_land=false;
 require(g_ui->landing_error_sound(true)==g_ui->find_sound("TAdErr03"),"Wrong interrupted landing voice");
 xy landingPos=lander->position;g_ui->set_unit_order(lander,g_ui->get_order_type(Orders::BuildingLiftoff),landingPos);advance(150);
 require(g_ui->u_flying(lander),"Landing fixture failed to lift off");
 int tile=(landingPos.y/32)*g_ui->game_st.map_tile_width+landingPos.x/32;auto flags=g_ui->st.tiles[tile].flags;g_ui->st.tiles[tile].flags|=tile_t::flag_unbuildable;
 int errorBefore=g_ui->error_seq;g_ui->set_unit_order(lander,g_ui->get_order_type(Orders::BuildingLand),landingPos);advance(250);
 require(g_ui->u_flying(lander)&&g_ui->error_seq==errorBefore+1&&g_ui->error_text==g_ui->stat_name(862),"Interrupted landing lacks error notification");g_ui->st.tiles[tile].flags=flags;
 for(auto e:{std::pair<int,const char*>{109,"TSCUpd00"},{120,"TAdUpd03"},{117,"TAdUpd03"},{118,"TAdUpd03"},{131,"ZChRdy00"}}){
  g_ui->poll_events();int before=g_ui->ready_notifications;auto* u=create(e.first);g_ui->poll_events();
  require(g_ui->ready_notifications==before+1&&g_ui->last_ready_sound==g_ui->find_sound(e.second),"Wrong building/addon completion voice");
  g_ui->poll_events();require(g_ui->ready_notifications==before+1,"Duplicate completion notification");
 }
 auto* tank=create(5);g_ui->poll_events();int before=g_ui->ready_notifications;
 g_ui->st.tech_researched[0][TechTypes::Tank_Siege_Mode]=true;
 action_state state;action_functions af(g_ui->st,state);af.action_select(0,tank);require(af.action_siege(0,false),"Siege command refused");
 for(int i=0;i<400;i++){advance(1);g_ui->poll_events();if(tank->order_type->id==Orders::Sieging)require(g_ui->ready_notifications==before,"Tank ready before siege animation finished");}
 require(g_ui->unit_is_sieged_tank(tank)&&g_ui->ready_notifications==before+1&&g_ui->last_ready_sound==g_ui->find_sound("TTaRdy00"),"Siege ready voice missing");
 before=g_ui->ready_notifications;require(af.action_unsiege(0,false),"Unsiege refused");
 for(int i=0;i<400;i++){advance(1);g_ui->poll_events();}
 require(g_ui->unit_is_unsieged_tank(tank)&&g_ui->ready_notifications==before+1&&g_ui->last_ready_sound==g_ui->find_sound("TTaRdy00"),"Unsiege ready voice missing");
 snapshot();std::cout<<"PASS race placement, landing, SCV/addon completion and both tank transitions\n";close_game();
}
static void alerts44(){
 start44();auto* cc=create(106);auto* marine=create(0);auto* enemy=create(0,{1600,1600});g_ui->set_unit_owner(enemy,1,false);
 g_ui->set_unit_hp(cc,100_fp8);g_ui->poll_events();g_ui->alerts.clear();
 for(int i=0;i<160;i++){advance(1);g_ui->poll_events();}
 require(cc->hp<100_fp8&&g_ui->alerts.empty(),"Burning building raises attack alert");
 g_ui->unit_deal_damage(marine,10_fp8,nullptr,~0);g_ui->poll_events();require(g_ui->alerts.empty(),"Self/trigger damage raises attack alert");
 g_ui->unit_deal_damage(marine,1_fp8,marine,0);require(g_ui->alerts.empty(),"Friendly fire raises attack alert");
 g_ui->st.alliances[0][1]=1;g_ui->unit_deal_damage(marine,1_fp8,enemy,1);require(g_ui->alerts.empty(),"Allied fire raises attack alert");g_ui->st.alliances[0][1]=0;
 g_ui->unit_deal_damage(marine,0_fp8,enemy,1);require(g_ui->alerts.empty(),"Zero damage raises alert");
 g_ui->unit_deal_damage(marine,1_fp8,enemy,1);require(g_ui->alerts.size()==1,"Enemy hit lacks attack ping");
 g_ui->poll_events();int ttl=g_ui->alerts[0].ttl;g_ui->unit_deal_damage(marine,1_fp8,enemy,1);
 require(g_ui->alerts.size()==1&&g_ui->alerts[0].ttl==ttl,"Repeated hit restarts existing ping");
 auto* near=create(0,marine->position);g_ui->unit_deal_damage(near,1_fp8,enemy,1);require(g_ui->alerts.size()==1,"Nearby hit spams overlapping ping");
 g_ui->poll_events();for(int i=0;i<play_ui::ALERT_TTL;i++)g_ui->poll_events();require(g_ui->alerts.empty(),"Attack ping never expires");
 g_ui->unit_deal_damage(marine,1_fp8,enemy,1);require(g_ui->alerts.size()==1,"New hit cannot ping after expiry");
 require(g_ui->attack_sound_for(marine)==g_ui->find_sound("TAdUpd01")&&g_ui->attack_sound_for(cc)==g_ui->find_sound("TAdUpd00"),"Base/forces alert voice mixed up");
 auto* zealot=create(65,{1800,1200});g_ui->alerts.clear();auto hp=zealot->hp;auto shields=zealot->shield_points;
 g_ui->weapon_deal_damage(g_ui->get_weapon_type(WeaponTypes::Gauss_Rifle),5_fp8,1,zealot,0_dir,nullptr,1);
 require(zealot->hp==hp&&zealot->shield_points<shields&&g_ui->alerts.size()==1,"Shield hit from dead projectile owner lacks alert");
 snapshot();std::cout<<"PASS burn/self/ally/zero damage, real shield hits and non-repeating attack pings\n";close_game();
}
static void ui44(){
 start44();auto* cc=create(106);auto* enemy=create(0,{1200,1000});g_ui->set_unit_owner(enemy,1,false);enemy->sprite->visibility_flags=1;
 g_ui->screen_pos=enemy->position-xy(320,160);select(cc);
 require(openbw_touch_action(320,160)==0,"Immobile selection sends rally instead of selecting");
 g_ui->start_target(play_ui::T_RALLY);require(openbw_touch_action(320,160)==2,"Explicit rally target no longer works");g_ui->clear_pending();g_ui->targeting=false;
 auto* mobile=create(0);select(mobile);require(openbw_touch_action(320,160)==3,"Mobile attack tapping broken");
 auto* cloaked=create(8);g_ui->set_unit_owner(cloaked,1,false);cloaked->sprite->visibility_flags=1;g_ui->u_set_status_flag(cloaked,unit_t::status_flag_cloaked);cloaked->detected_flags=2;
 openbw_reveal_map();require(g_ui->unit_hidden_by_fog(cloaked)&&!g_ui->unit_can_be_selected(cloaked),"Map cheat reveals/selects undetected cloak");
 require(!g_ui->unit_hidden_by_fog(enemy),"Map cheat does not reveal ordinary enemy");cloaked->detected_flags|=1;require(!g_ui->unit_hidden_by_fog(cloaked),"Detected cloak hidden with reveal cheat");
 for(auto e:{std::pair<int,int>{113,120},{114,115},{116,117},{116,118},{106,107},{106,108}}){
  auto* parent=create(e.first);auto* addon=create(e.second);select(parent);bool before=false;for(auto& c:g_ui->card)before|=int(c.ut)==e.second;require(before,"Addon missing before construction");
  parent->building.addon=addon;g_ui->refresh_card();for(auto& c:g_ui->card)require(c.ut==UnitTypes::None||!g_ui->ut_addon(g_ui->get_unit_type(c.ut)),"Built addon icon remains");
  parent->building.addon=nullptr;g_ui->refresh_card();bool after=false;for(auto& c:g_ui->card)after|=int(c.ut)==e.second;require(after,"Addon icon fails to return after detachment");
 }
 for(auto e:{std::pair<int,int>{111,1},{35,0},{154,2}}){select(create(e.first));require(g_ui->card_text.find(e.second==1?"\t0\t2\t1":e.second==0?"\t0\t2\t0":"\t0\t2\t2")!=a_string::npos,"Tooltip missing cost supply race");}
 snapshot();std::cout<<"PASS immobile taps, reveal/detection, addon availability and mixed-race supply metadata\n";close_game();
}
static void nuke44(){
 start44();auto* ghost=create(1,{1000,1500});select(ghost);require(find("Nuclear Strike")&&!find("Nuclear Strike")->enabled,"Empty nuke button missing/not grey");
 require(g_ui->card_text.find("\t311\t")!=a_string::npos,"Nuke mushroom icon missing");
 auto* silo=create(108,{800,900});auto* ops=create(117);(void)ops;create(109);
 action_state state;action_functions af(g_ui->st,state);af.action_select(0,silo);
 require(af.action_train(0,g_ui->get_unit_type(UnitTypes::Terran_Nuclear_Missile)),"Cannot train nuke");
 for(int i=0;i<2400&&!g_ui->has_ready_nuke(0);i++)advance(1);
 require(g_ui->has_ready_nuke(0),"Trained nuclear missile never ready");select(ghost);require(find("Nuclear Strike")->enabled,"Ready missile does not enable Ghost command");
 auto* victim=create(109,ghost->position+xy(0,-288));g_ui->set_unit_owner(victim,1,false);auto hp=victim->hp;xy target=victim->position;
 auto ghostId=g_ui->get_unit_id(ghost),victimId=g_ui->get_unit_id(victim);bool damaged=false;int damage=0;
 g_ui->run_command(find("Nuclear Strike")->key);require(g_ui->pending_spell_order==Orders::NukePaint,"Ghost uses internal missile order");g_ui->issue_target(target);
 bool launched=false;int launchFrame=-1;
 for(int i=0;i<1600;i++){
  advance(1);ghost=g_ui->get_unit(ghostId);victim=g_ui->get_unit(victimId);
  if(ghost&&ghost->connected_unit){launched=true;if(launchFrame<0){launchFrame=i;require(!g_ui->has_ready_nuke(0),"Launch did not consume silo missile");}}
  if(!victim||victim->hp<hp){damaged=true;damage=victim?(hp-victim->hp).integer_part():hp.integer_part();break;}
  if(i==200&&launched)snapshot();
 }
 require(launched&&damaged,"Nuclear strike failed to launch/damage target");
 std::cout<<"PASS original command-to-launch-to-explosion nuke damage="<<damage<<" launchFrame="<<launchFrame<<"\n";
 ghost=g_ui->get_unit(ghostId);require(ghost&&!g_ui->unit_dying(ghost),"Ghost at maximum targeting range died");select(ghost);require(find("Nuclear Strike")&&!find("Nuclear Strike")->enabled,"Spent nuke button not grey");
 snapshot();close_game();
}
static std::vector<uint8_t> capture44(const char* name){
 openbw_render(openbw_frame()*42.);int w=openbw_framebuffer_width(),h=openbw_framebuffer_height();auto* p=openbw_framebuffer();
 std::vector<uint8_t> bytes(p,p+w*h*4);std::ofstream f(std::string("build-native/")+name+".ppm",std::ios::binary);f<<"P6\n"<<w<<" "<<h<<"\n255\n";
 for(int i=0;i<w*h;i++){f.put(p[i*4]);f.put(p[i*4+1]);f.put(p[i*4+2]);}return bytes;
}
static void cloak44(){
 start44();auto* enemy=create(8);g_ui->set_unit_owner(enemy,1,false);g_ui->screen_pos=enemy->position-xy(320,200);g_ui->current_selection.clear();
 for(auto& t:g_ui->st.tiles){t.visible=0xfe;t.explored=0xfe;}enemy->sprite->visibility_flags=1;
 g_ui->u_set_status_flag(enemy,unit_t::status_flag_cloaked);g_ui->u_set_status_flag(enemy,unit_t::status_flag_requires_detector);enemy->detected_flags=2;
 g_ui->set_sprite_cloak_modifier(enemy->sprite,true,true,false,8,0);
 require(g_ui->unit_has_cloak_shimmer(enemy),"Visible undetected cloak lacks shimmer");require(g_ui->unit_hidden_by_fog(enemy),"Shimmer makes enemy targetable");
 std::vector<std::pair<image_t*,int>> images;for(auto* im:ptr(enemy->sprite->images)){images.push_back({im,im->flags});g_ui->hide_image(im);}
 auto bg=capture44("cloak44-background");for(auto e:images)e.first->flags=e.second;
 auto shimmer=capture44("cloak44-undetected");require(bg!=shimmer,"Undetected cloak draws no refraction pixels");
 g_ui->st.current_frame+=8;auto animated=capture44("cloak44-shimmer-next");require(animated!=shimmer,"Cloak shimmer is static");g_ui->st.current_frame-=8;
 enemy->detected_flags|=1;require(!g_ui->unit_has_cloak_shimmer(enemy)&&!g_ui->unit_hidden_by_fog(enemy),"Detection failed to restore unit visibility");auto detected=capture44("cloak44-detected");require(detected!=shimmer&&detected!=bg,"Detected cloak uses undetected shimmer");enemy->detected_flags=2;
 g_ui->u_set_status_flag(enemy,unit_t::status_flag_burrowed);require(!g_ui->unit_has_cloak_shimmer(enemy),"Burrowed unit leaks shimmer");g_ui->u_unset_status_flag(enemy,unit_t::status_flag_burrowed);
 openbw_reveal_map();require(g_ui->unit_has_cloak_shimmer(enemy)&&!g_ui->unit_can_be_selected(enemy),"Reveal changes cloak targeting rules");
 for(auto& t:g_ui->st.tiles)t.visible|=1;require(!g_ui->unit_has_cloak_shimmer(enemy),"Reveal leaks cloak outside actual vision");
 // Exercise sprite clipping and both horizontal orientations at all viewport edges.
 for(auto p:{xy(-4,200),xy(644,200),xy(320,-4),xy(320,484)}){
  for(auto& t:g_ui->st.tiles)t.visible&=~1;g_ui->screen_pos=enemy->position-p;
  capture44("cloak44-edge");enemy->sprite->main_image->flags^=image_t::flag_horizontally_flipped;capture44("cloak44-edge-flipped");
 }
 std::cout<<"PASS animated original-GRP cloak refraction, detection, fog, burrow and edge clipping\n";close_game();
}
static void web44(){
 openbw_init_campaign(640,480,507);int p=g_ui->my_player;require(p==3,"Wrong Drawing of the Web human");
 require(g_ui->game_st.unit_type_allowed[p][UnitTypes::Zerg_Queen],"Original mission disallows Queen");
 for(auto t:{UnitTypes::Zerg_Mutalisk,UnitTypes::Zerg_Guardian,UnitTypes::Zerg_Devourer,UnitTypes::Zerg_Spire,UnitTypes::Zerg_Greater_Spire})require(!g_ui->game_st.unit_type_allowed[p][t],"Offensive air incorrectly unlocked");
 require(g_ui->player_max_upgrade_level(p,UpgradeTypes::Ventral_Sacs)==0,"Mission allows transport upgrade");
 advance(2400);snapshot();std::cout<<"PASS original Drawing of the Web: Queen allowed, combat air/Spire/Ventral Sacs disabled\n";close_game();
}
#ifdef OPENBW_REVISION44_EMBEDDED
#define main revision44_main
#endif
int main(int argc,char**argv){
 if(argc<4)return revision43_main(argc,argv);std::string mode=argv[3];if(mode!="sounds44"&&mode!="alerts44"&&mode!="ui44"&&mode!="nuke44"&&mode!="web44"&&mode!="cloak44")return revision43_main(argc,argv);
 std::cout.setf(std::ios::unitbuf);try{std::string d=argv[1];open_archive(0,d+"/STARDAT.MPQ");open_archive(1,d+"/BROODAT.MPQ");open_archive(2,d+"/patch_rt.mpq");open_archive(3,argv[2]);
 if(mode=="sounds44")sound44();else if(mode=="alerts44")alerts44();else if(mode=="ui44")ui44();else if(mode=="nuke44")nuke44();else if(mode=="cloak44")cloak44();else web44();return 0;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}
}
