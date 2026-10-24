#define main retained_multiplayer_main
#include "native_multiplayer.cpp"
#undef main
static unit_t* create55(UnitTypes type,int owner,xy around) {
 auto* ut=g_ui->get_unit_type(type);
 for(int r=0;r<20;r++)for(int y=-r;y<=r;y++)for(int x=-r;x<=r;x++){
  xy p=around+xy(x*32,y*32);if(!g_ui->unit_type_can_fit_at(ut,p))continue;bool free=true;for(auto* u:g_ui->find_units(g_ui->square_at(p,40)))if(!g_ui->unit_dying(u))free=false;
  if(free){auto* u=g_ui->create_initial_unit(ut,p,owner);if(u)return u;}
 }throw std::runtime_error("No room for fixture unit");
}
static void select55(unit_t* u){g_ui->current_selection_clear();g_ui->current_selection_add(u);g_ui->on_selection(false);}
static void native_feedback55(const char* map) {
 close_game();open_archive(3,map);custom_bot_slot=-1;openbw_init(640,480,0,0);g_ui->competitive=false;
 auto* ultra=create55(UnitTypes::Zerg_Ultralisk,0,{1300,1300});g_ui->fog_player=-1;select55(ultra);
 bool normal=false;for(auto& c:g_ui->sound_channels)if(c.playing&&c.sound_type){auto& file=g_ui->sound_filenames[int(c.sound_type->id)];if(file.find("ZUlWht")!=a_string::npos)normal=true;}
 require(normal,"Ultralisk selected an annoyed/incorrect voice");
 std::cout<<"PASS Ultralisk original descending range plays normal ZUlWht WAV\n";
 for(int kind=0;kind<3;kind++){
  g_ui->current_selection_clear();a_vector<unit_t*> larvae;
  for(int i=0;i<3;i++){auto* u=create55(UnitTypes::Zerg_Larva,0,{1400+i*96,1400});larvae.push_back(u);g_ui->current_selection_add(u);}
  auto* type=g_ui->get_unit_type(kind==1?UnitTypes::Zerg_Hydralisk:UnitTypes::Zerg_Drone);
  if(kind==1)create55(UnitTypes::Zerg_Hydralisk_Den,0,{1600,1600});
  g_ui->st.current_minerals[0]=kind==0?50:10000;g_ui->st.current_gas[0]=kind==1?25:10000;
  g_ui->st.supply_available[0][0].raw_value=400;g_ui->st.supply_used[0][0].raw_value=kind==2?398:0;
  auto ids=g_ui->current_selection;g_ui->action_select(0,larvae);int before=g_ui->error_seq;
  g_ui->action_morph(0,type);int queued=0;for(auto* u:larvae)if(!u->build_queue.empty())queued++;
  require(queued==1,"Affordable larvae were not partially queued");require(g_ui->error_seq==before+1,"Mass morph shortage is not reported exactly once");
  auto expected=kind==0?play_ui::E_MINERALS:kind==1?play_ui::E_GAS:play_ui::E_SUPPLY;
  require(g_ui->error_text==g_ui->err_message(expected),"Wrong mass morph resource error");
  for(auto* u:larvae)g_ui->kill_unit(u);
  std::cout<<"PASS mass larvae partial morph shortage="<<kind<<"\n";
 }
 // Advanced flying morphs replace existing supply; a full army can still morph them.
 create55(UnitTypes::Zerg_Greater_Spire,0,{1100,1600});a_vector<unit_t*> mutas;
 for(int i=0;i<3;i++)mutas.push_back(create55(UnitTypes::Zerg_Mutalisk,0,{1200+i*96,1700}));
 g_ui->st.current_minerals[0]=g_ui->st.current_gas[0]=10000;g_ui->st.supply_available[0][0].raw_value=g_ui->st.supply_used[0][0].raw_value=400;
 g_ui->action_select(0,mutas);int prior=g_ui->error_seq;g_ui->action_morph(0,g_ui->get_unit_type(UnitTypes::Zerg_Guardian));
 for(auto* u:mutas)require(!u->build_queue.empty(),"Supply-neutral Guardian morph blocked at full supply");require(prior==g_ui->error_seq,"Supply-neutral morph raised shortage");
 std::cout<<"PASS Guardian replacement morph at 200 supply\n";
 close_game();
}
static void duran55(const char* mission){
 open_archive(3,mission);openbw_init_campaign(640,480,401);openbw_set_external_cursor(1);
 unit_t* duran=nullptr;for(auto* u:ptr(g_ui->st.player_units[2]))if(g_ui->unit_is(u,UnitTypes::Hero_Samir_Duran))duran=u;
 require(duran,"Original Duran missing");
 for(int i=0;i<240;i++)native_step();
 auto* visitor=create55(UnitTypes::Terran_Marine,g_ui->my_player,{2336,1568});xy original=visitor->sprite->position;
 for(int i=0;i<800&&!g_campaign->units_paused;i++)native_step();require(g_campaign->units_paused,"Duran introduction did not trigger");
 for(int i=0;i<2;i++)native_step();openbw_render(0);
 require(!g_ui->unit_hidden_by_fog(duran),"Duran invisible during paused introduction");
 unit_t* center=nullptr;for(auto* u:ptr(g_ui->st.player_units[1]))if(g_ui->unit_is(u,UnitTypes::Terran_Command_Center))center=u;
 require(center&&!g_ui->unit_hidden_by_fog(center),"Duran base invisible during paused introduction");
 require(duran->owner==2,"Duran acquired before agreement");
 for(int i=0;i<100;i++)native_step();require(visitor->sprite->position==original,"Dialogue advanced unit movement");
 for(int i=0;i<4000&&duran->owner!=g_ui->my_player;i++)native_step();
 require(duran->owner==g_ui->my_player,"Duran not rescued by newly granted base");require(center->owner==g_ui->my_player,"Duran base was not given");
 require(visitor->sprite->position==original,"Visitor had to move closer to Duran");require(!g_ui->outcome,"Duran sequence ended mission");
 std::cout<<"PASS original First Strike triggers: reveal while paused; base and Duran automatically join without approaching again\n";close_game();
}
#ifdef OPENBW_REVISION55_EMBEDDED
#define main retained_revision55_main
#endif
int main(int argc,char** argv){try{
 require(argc>=5,"data map mode arguments");std::string data=argv[1];open_archive(0,data+"/STARDAT.MPQ");open_archive(1,data+"/BROODAT.MPQ");open_archive(2,data+"/patch_rt.mpq");
 std::string mode=argv[3];if(mode=="feedback"){native_feedback55(argv[2]);duran55(argv[4]);return 0;}
 int slot=std::atoi(argv[4]),humans=std::atoi(argv[5]),ffa=std::atoi(argv[6]);open_archive(3,argv[2]);
 int races[8],controllers[8];for(int i=0;i<8;i++){races[i]=i%3;controllers[i]=i<humans?1:2;}
 configured_init(640,480,slot,races,controllers,2,true,ffa,true);for(int i=0;i<8;i++)require(count_units(g_ui->st,i)>=5,"Missing eight-player start");
 xy starts[]={{512,512},{2048,512},{3584,512},{512,2048},{3584,2048},{512,3584},{2048,3584},{3584,3584}};
 for(int i=0;i<8;i++)require(g_ui->game_st.start_locations[i]==starts[i],"Lobby slot does not map to original start location");
 std::ofstream out(argv[7]);auto run=[&](int frames,bool trace){for(int n=0;n<frames;n+=4){int f=g_ui->st.current_frame;if(trace)out<<f<<" "<<net_hash()<<"\n";
  std::array<std::vector<uint8_t>,8> commands;for(int i=0;i<humans;i++){auto c=input(i,f);commands[i].assign(c.begin(),c.end());}net_apply_all(commands);
  for(int k=0;k<4;k++){net_step();if((f+k+slot)%3==0){g_ui->screen_pos=g_ui->game_st.start_locations[slot]-xy(320,240);openbw_render((f+k)*42.);}}
 }};
 run(1200,true);for(int i=humans;i<8;i++)require(g_ui->st.total_minerals_gathered[i]>0,"Computer did not gather resources");auto saved=net_save();auto at=net_hash();run(240,true);auto expected=net_hash();
 configured_init(640,480,slot,races,controllers,2,true,ffa,true);net_restore(saved);require(net_hash()==at,"Eight-slot saved restore hash differs");run(240,false);require(net_hash()==expected,"Eight-slot resumed continuation differs");
 std::array<std::vector<uint8_t>,8> invalid;invalid[7]={1,0,255};bool rejected=false;auto before=net_hash();try{net_apply_all(invalid);}catch(...){rejected=true;}require(rejected&&before==net_hash(),"Invalid last slot mutated world");
 // Save from a different player's perspective, preserving this device's slot and fog.
 configured_init(640,480,(slot+1)%humans,races,controllers,2,true,ffa,true);net_restore(saved);require(net_hash()==at,"Cross-slot restore differs");
 std::array<std::vector<uint8_t>,8> departure;departure[humans-1]={2,0,87,1};net_apply_all(departure);for(int i=0;i<4;i++)net_step();auto departed=net_save();auto departedHash=net_hash();controllers[humans-1]=0;
 configured_init(640,480,0,races,controllers,2,true,ffa,true);net_restore(departed);require(net_hash()==departedHash,"Departed player save did not restore with closed slot");
 std::cout<<"PASS eight native slots local="<<slot<<" humans="<<humans<<" ffa="<<ffa<<" save/restore240=cross-slot\n";close_game();return 0;
 }catch(const std::exception& e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
