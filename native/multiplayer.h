#pragma once
// Eight slots, fixed ordered input and bounded payloads. Runs on the render worker.
static int net_remaining=0;
static void net_validate(const uint8_t* data,size_t size) {
 if(size>16384)throw std::runtime_error("Multiplayer command batch is too large");
 for(size_t p=0;p<size;) {
  if(size-p<3)throw std::runtime_error("Truncated multiplayer command");
  size_t n=data[p]|(size_t(data[p+1])<<8);p+=2;
  if(n==0||n>size-p)throw std::runtime_error("Invalid multiplayer command length");
  unsigned op=data[p];size_t expected=0;
  switch(op) {
   case 9:if(n<2||data[p+1]>12)throw std::runtime_error("Invalid unit selection");expected=2+2*data[p+1];break;
   case 12:expected=8;break;case 20:expected=10;break;case 21:expected=11;break;
   case 24:case 25:case 39:case 42:case 46:case 49:case 51:case 52:case 54:case 90:expected=1;break;
   case 26:case 30:case 33:case 34:case 37:case 38:case 40:case 43:case 44:case 45:case 48:case 50:case 87:expected=2;break;
   case 31:case 32:case 35:case 41:case 53:expected=3;break;case 47:expected=5;break;
   default:throw std::runtime_error("Unsupported multiplayer command");
  }
  if(n!=expected)throw std::runtime_error("Malformed multiplayer command");
  p+=n;
 }
}
static void configured_init(int width,int height,int slot,const int* races,const int* controllers,int difficulty,bool expansion,bool ffa,bool network,const int* teams=nullptr,bool team_game=false,bool heroes=false) {
 if(slot<0||slot>7||difficulty<0||difficulty>2)throw std::runtime_error("Invalid game setup");
 bwgame::mp_slot slots[8];size_t n=0;unsigned ai=0;
 for(int i=0;i<8;++i) {
  if(races[i]<0||races[i]>2||controllers[i]<0||controllers[i]>2 ||
     (!network && (i==slot?controllers[i]!=1:controllers[i]==1)))throw std::runtime_error("Invalid game slot");
  if(controllers[i]){slots[n++]={i,bwgame::race_t(races[i])};if(controllers[i]==2)ai|=1u<<i;}
 }
 if(controllers[slot]!=1)throw std::runtime_error("Local slot is not a player");
 if(team_game&&(!teams||ffa))throw std::runtime_error("Invalid team settings");
 if(teams)for(int i=0;i<8;i++)if(teams[i]<1||teams[i]>8)throw std::runtime_error("Invalid team number");
 close_game();g_skirmish_expansion=expansion;custom_bot_slot=-1;g_terran_ai_level=difficulty;
 init_game(width,height,slot,slots,n,false,-1,ai,ffa);net_active=network;net_remaining=0;
 configure_hero_mode(heroes);
 bwgame::game_load_functions rules(g_ui->st);rules.game_st.team_game=team_game;
 if(team_game)for(int i=0;i<8;i++) {
  g_ui->st.shared_vision[i]=0;
  for(int j=0;j<8;j++) {
   bool allied=i==j||(controllers[i]&&controllers[j]&&teams[i]==teams[j]);
   g_ui->st.alliances[i][j]=allied?1:0;
   if(allied)g_ui->st.shared_vision[i]|=1u<<j;
  }
 }
 g_ui->test_instant=false;g_ui->rep.game_name=network?"OpenBW Local Multiplayer":"OpenBW Custom Game";
 openbw_set_external_cursor(1);openbw_mouse_move(-100,-100);
}
static void net_init(int width,int height,int slot,int first,int second,bool expansion) {
 int races[]={first,second,1,1,1,1,1,1},controllers[]={1,1,0,0,0,0,0,0};
 configured_init(width,height,slot,races,controllers,2,expansion,false,true);
}
static std::vector<uint8_t> net_save() {
 native_save::check(net_active&&g_ui&&net_remaining==0,"Wait for the current multiplayer turn before saving");
 native_save::HostState host;return native_save::save(*g_ui,g_campaign,host);
}
static void net_restore(std::vector<uint8_t>& bytes) {
 native_save::check(net_active&&g_ui,"No multiplayer game");
 int local=g_ui->my_player;auto race=g_ui->my_race;
 native_save::restore(*g_ui,g_campaign,bytes);
 native_save::check(g_ui->st.current_frame%4==0,"Saved multiplayer turn is incomplete");
 int saved_player=g_ui->my_player;
 g_ui->my_player=local;g_ui->my_race=race;g_ui->kit=bwgame::kit_for(race);g_ui->fog_player=local;
 // Simulation command selections belong to all players and are retained. UI state
 // and unsubmitted taps belong to one device and must never leak to its opponent.
 g_ui->current_selection_clear();g_ui->groups={};g_ui->outgoing.clear();g_ui->clear_pending();g_ui->targeting=false;
 g_ui->screen_pos=g_ui->game_st.start_locations[local]-bwgame::xy(320,240);g_ui->clamp_viewport();
 if(saved_player!=local){g_ui->fog_snapshots.assign(2500,{});for(int p=0;p<12;p++)for(auto* u:bwgame::ptr(g_ui->st.player_units[p]))if(u->sprite&&g_ui->unit_persists_in_fog(u)&&!g_ui->unit_hidden_by_fog(u))g_ui->snapshot_fog_sprite(u->sprite);}g_ui->events_seeded=false;g_ui->last_life.clear();g_ui->last_stim.clear();g_ui->announced.clear();g_ui->alerts.clear();g_ui->advisor_queue.clear();
 g_ui->outcome=0;g_ui->rep_on=false;g_ui->rep_out.clear();net_remaining=0;
 for(int ch=0;ch<57;ch++)naudio::stop(ch);
 naudio::stop(62); // Discard mission speech; preserve the lobby's own transition.
}
static uint64_t net_assets() {
 uint64_t h=14695981039346656037ull;
 for(int i=0;i<3;i++) {
  if(!archives[i].data)throw std::runtime_error("Missing multiplayer core data");
  h=native_save::hash_bytes(archives[i].data,archives[i].size,h);
 }
 return h;
}
static uint64_t net_hash() {
 if(!g_ui||!net_active)throw std::runtime_error("No multiplayer game");
 auto& st=g_ui->st;uint64_t h=14695981039346656037ull;
 auto mix=[&](uint64_t n){for(int i=0;i<8;i++){h^=uint8_t(n>>(8*i));h*=1099511628211ull;}};
 mix(bwgame::sim_checksum(st));mix(g_ui->game_st.hero_mode);mix(g_ui->game_st.team_game);
 for(auto vision:st.shared_vision)mix(vision);
 for(auto& row:st.alliances)for(auto alliance:row)mix(alliance);
 if(g_campaign) {
  mix(g_campaign->ai_clock);mix(g_campaign->ai_random);
  for(auto& t:g_campaign->threads){mix(t.owner);mix(t.pc);mix(t.wake);mix(t.file);mix(t.id);mix(t.done);for(auto v:t.calls)mix(v);}
  for(auto& t:g_campaign->towns){mix(t.active);mix(t.center.x);mix(t.center.y);mix(t.built);mix(t.trained);mix(t.attacks);mix(t.orders);for(auto& q:t.builds){mix(q.type);mix(q.amount);mix(q.priority);}}
 }

 for(int owner=0;owner<12;owner++) {
  mix(st.current_minerals[owner]);mix(st.current_gas[owner]);mix(st.players[owner].victory_state);
  for(auto n:st.upgrade_levels[owner])mix(n);
  for(auto n:st.tech_researched[owner])mix(n);
  for(auto n:st.supply_used[owner])mix(n.raw_value);
  for(auto* u:bwgame::ptr(st.player_units[owner])) {
   mix(u->index);mix(u->unit_id_generation);mix(int(u->unit_type->id));mix(u->status_flags);
   mix(u->energy.raw_value);mix(u->shield_points.raw_value);mix(u->remaining_build_time);
   mix(u->order_state);mix(u->main_order_timer);mix(u->order_target.pos.x);mix(u->order_target.pos.y);
   mix(g_ui->get_unit_id(u->order_target.unit).raw_value);
   for(auto* t:u->build_queue)mix(int(t->id));
  }
 }
 return h;
}
static void net_apply(const uint8_t* a,size_t an,const uint8_t* b,size_t bn) {
 if(!net_active||!g_ui||net_remaining!=0||g_ui->st.current_frame%4)throw std::runtime_error("Multiplayer frame order differs");
 net_validate(a,an);net_validate(b,bn); // Validate both before either can mutate the world.
 if(an)g_ui->apply_commands(0,a,an);if(bn)g_ui->apply_commands(1,b,bn);net_remaining=4;
}
static void net_apply_all(const std::array<std::vector<uint8_t>,8>& commands) {
 if(!net_active||!g_ui||net_remaining!=0||g_ui->st.current_frame%4)throw std::runtime_error("Multiplayer frame order differs");
 for(auto& c:commands)net_validate(c.data(),c.size());
 for(int i=0;i<8;i++)if(!commands[i].empty())g_ui->apply_commands(i,commands[i].data(),commands[i].size());
 net_remaining=4;
}
static void net_step() {
 if(!net_active||!g_ui||net_remaining<=0)throw std::runtime_error("Missing multiplayer input");
 openbw_step();--net_remaining;
}
static void net_peer_left() {
 if(!net_active||!g_ui)return;
 bwgame::a_vector<uint8_t> input;bwgame::bw_cmd cmd(input);cmd.player_leave(1);
 g_ui->apply_commands(1-g_ui->my_player,input.data(),input.size());
 for(int i=0;i<32&&!g_ui->outcome;i++){openbw_step();g_ui->poll_events();}
 g_ui->poll_events();net_active=false;net_remaining=0;
}
