// Real-data command identity and grid dispatch integration. Imported assets stay local.
#include "../native/runtime.cpp"
#include <iostream>
#include <fstream>
#include <sstream>
#include <map>
#include <filesystem>
using namespace bwgame;using U=UnitTypes;using A=play_ui::cmd_act;
static int checks;static double ms=100;
static void check(bool ok,const std::string& why){++checks;if(!ok)throw std::runtime_error(why);}
static void flush(){openbw_render(ms+=20);}
static void select(unit_t* u){g_ui->clear_pending();g_ui->targeting=false;g_ui->menu=0;g_ui->current_selection_clear();if(u)g_ui->current_selection_add(u);g_ui->on_selection(false);g_ui->refresh_card();g_ui->outgoing.clear();}
static int find(A act,U type=U::None,int special=-1){for(int i=0;i<int(g_ui->card.size());++i){auto&c=g_ui->card[i];if(c.act==act&&(type==U::None||c.ut==type)&&(special<0||int(c.tech)==special||int(c.upg)==special))return i;}throw std::runtime_error("Missing command "+std::to_string(act)+" / "+std::to_string(int(type)));}
static void press(int index){check(index>=0&&index<int(g_ui->card.size()),"Invalid fixture command");command(35,index,g_ui->command_token(g_ui->card[index]),0,0);}
static int u16(const uint8_t*p){return p[0]|p[1]<<8;}
static std::vector<int> orders(){std::vector<int>v;auto&raw=g_ui->outgoing;net_validate(raw.data(),raw.size());for(size_t p=0;p<raw.size();){int n=u16(raw.data()+p);p+=2;if(raw[p]!=9)v.push_back(raw[p]);p+=n;}return v;}
static void expect(int opcode){auto o=orders();check(o.size()==1&&o[0]==opcode,"Wrong exact-command opcode "+std::to_string(opcode));g_ui->outgoing.clear();}
static std::vector<std::string> split(const std::string&s,char delim){std::vector<std::string>out;std::stringstream f(s);std::string v;while(std::getline(f,v,delim))out.push_back(v);return out;}
static std::string normalized(const std::string&s){std::string out;for(unsigned char c:s)if((c>='a'&&c<='z')||(c>='0'&&c<='9'))out+=c;else if(c>='A'&&c<='Z')out+=c+32;return out;}
static std::vector<std::string> strings(){auto b=read_asset(-1,"rez/stat_txt.tbl");check(b.size()>2,"No original text table");std::vector<std::string>out;int n=u16(b.data());for(int i=0;i<n;++i){int off=u16(b.data()+2+i*2);check(off>=2+n*2&&off<int(b.size()),"Invalid original text offset");out.emplace_back(reinterpret_cast<const char*>(b.data()+off));}return out;}
static std::map<int,unit_t*> units;
static unit_t* unit(int id){
 auto found=units.find(id);if(found!=units.end())return found->second;
 // Cards and command emission are independent of pathfinding/placement. Keep
 // synthetic completed producers at a stable point; physical input is covered
 // separately in native_desktop11 with normally placed, simulated units.
 auto*u=g_ui->create_completed_unit(g_ui->get_unit_type(U(id)),{1024,1024},0);
 check(u!=nullptr,"Cannot create card fixture type "+std::to_string(id));
 g_ui->u_unset_status_flag(u,unit_t::status_flag_disabled);
 units[id]=u;return u;
}
static void corpus(const std::filesystem::path& root){std::filesystem::create_directories(root);auto manifestFile=root.parent_path()/"cards.json";auto temporary=manifestFile;temporary+=".tmp";std::ofstream manifest(temporary);manifest<<"[";bool first=true;int rows=0,cards=0;
 int types[]={0,1,2,3,5,7,8,9,11,12,32,34,35,37,38,39,40,41,42,43,44,45,46,47,60,61,62,63,64,65,66,67,68,69,70,71,72,83,84,103,106,107,108,109,110,111,112,113,114,115,116,117,118,120,122,123,124,125,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,146,149,154,155,156,157,159,160,162,163,164,165,166,167,169,170,171,172,48,51,53,54,55,104,16,19,20,23,28,99,75,77,78,79,82,88};
 for(bool heroes:{false,true}){const_cast<game_state&>(g_ui->game_st).hero_mode=heroes;for(int id:types){auto*u=unit(id);select(u);for(int menu=0;menu<=(g_ui->ut_worker(u)?2:0);++menu){g_ui->menu=menu;g_ui->refresh_card();auto text=std::string(g_ui->card_text.c_str());std::string name="type"+std::to_string(id)+"-menu"+std::to_string(menu)+"-hero"+std::to_string(heroes?1:0)+".txt";std::ofstream(root/name)<<text;
   if(!first)manifest<<",";first=false;manifest<<"{\"type\":"<<id<<",\"race\":"<<int(g_ui->unit_race(u))<<",\"menu\":"<<menu<<",\"hero\":"<<(heroes?"true":"false")<<",\"file\":\""<<name<<"\"}";++cards;
   auto lines=split(text,'\n');check(lines.size()==g_ui->card.size()+1,"Native command rows lost metadata");for(int i=0;i<int(g_ui->card.size());++i){auto f=split(lines[i+1],'\t');check(f.size()==18,"Exact command metadata not appended");check(std::stoi(f[16])==i&&std::stoi(f[17])==g_ui->command_token(g_ui->card[i]),"Host/native command identity mismatch");++rows;}
  }} }
 manifest<<"]\n";manifest.close();std::filesystem::rename(temporary,manifestFile);const_cast<game_state&>(g_ui->game_st).hero_mode=false;std::cout<<"PASS "<<cards<<" actual all-race unit/build/research/morph/hero cards; "<<rows<<" exact command identities\n";
}
static void original_audit(){auto table=strings();struct Pair{int type,index;};Pair train[]={{0,585},{1,586},{2,588},{3,589},{5,590},{7,591},{8,592},{9,593},{11,594},{12,595},{32,587},{34,1289},{37,574},{38,575},{39,576},{41,577},{42,578},{43,579},{44,580},{45,581},{46,582},{47,583},{60,1291},{61,1292},{62,1287},{64,598},{65,599},{66,600},{67,601},{69,602},{70,603},{71,604},{72,605},{83,607},{84,597},{103,1288},{58,1290}};
 for(auto p:train)check(play_ui::bw_train_key(U(p.type))==table.at(p.index)[0],"Original train hotkey mismatch type "+std::to_string(p.type));
 Pair build[]={{131,612},{143,613},{149,614},{142,615},{139,616},{135,617},{134,618},{141,619},{138,620},{140,621},{136,622},{132,623},{133,624},{137,625},{144,626},{146,627},{154,629},{156,630},{157,631},{160,632},{166,633},{162,634},{164,635},{172,636},{155,637},{159,638},{163,639},{165,640},{167,641},{169,642},{170,643},{171,644},{106,645},{109,646},{110,647},{111,648},{122,649},{124,650},{112,651},{125,652},{113,653},{114,654},{116,655},{123,656},{107,657},{108,658},{115,659},{117,660},{118,661},{120,662}};
 for(auto p:build)check(play_ui::bw_build_key(U(p.type))==table.at(p.index)[0],"Original build hotkey mismatch type "+std::to_string(p.type));
 Pair upgradeBindings[]={{0,455}, {1,456}, {2,457}, {3,458}, {4,459}, {5,460}, {6,461}, {7,462}, {8,463}, {9,464}, {10,465}, {11,466}, {12,467}, {13,468}, {14,469}, {15,470}, {16,471}, {17,472}, {19,474}, {20,475}, {21,476}, {22,477}, {23,478}, {24,479}, {25,480}, {26,481}, {27,482}, {28,483}, {29,484}, {30,485}, {31,486}, {32,487}, {33,488}, {34,489}, {35,490}, {36,491}, {37,492}, {38,493}, {39,494}, {40,495}, {41,496}, {42,497}, {43,498}, {44,499}, {47,1284}, {49,1285}, {51,1280}, {52,1283}, {53,1282}, {54,1281}};
 for(auto p:upgradeBindings)check(play_ui::bw_upgrade_key(UpgradeTypes(p.type))==table.at(p.index)[0],"Original upgrade hotkey mismatch type "+std::to_string(p.type));
 Pair researchBindings[]={{0,323}, {1,324}, {2,325}, {3,326}, {5,327}, {7,329}, {8,330}, {9,331}, {10,332}, {11,363}, {13,365}, {15,368}, {16,370}, {17,369}, {19,394}, {20,395}, {21,396}, {22,397}, {24,1244}, {25,1259}, {27,1260}, {30,1245}, {31,1262}, {32,1252}};
 for(auto p:researchBindings)check(play_ui::bw_research_key(TechTypes(p.type))==table.at(p.index)[0],"Original research hotkey mismatch type "+std::to_string(p.type));
 int upgrades=std::size(upgradeBindings),researches=std::size(researchBindings);
 int nativeUpgrades=0,nativeResearches=0;
 for(int i=0;i<int(UpgradeTypes::None);++i)if(play_ui::bw_upgrade_key(UpgradeTypes(i)))++nativeUpgrades;
 for(int i=0;i<int(TechTypes::None);++i)if(play_ui::bw_research_key(TechTypes(i)))++nativeResearches;
 check(nativeUpgrades==upgrades&&nativeResearches==researches,"Audit omitted a canonical upgrade or research binding");
 for(auto p:std::vector<std::pair<int,int>>{{130,584},{72,606},{83,608}}){select(unit(p.first));int index=find((p.first==130||p.first==108)?play_ui::C_TRAIN:play_ui::C_FIGHTER);check(g_ui->card[index].key==table[p.second][0],"Original specialist train key mismatch");}
 select(unit(172));int recharge=find(play_ui::C_RECHARGE);check(g_ui->card[recharge].key==table[672][0],"Recharge Shields differs from original data");
 std::cout<<"PASS original archive hotkeys: "<<std::size(train)<<" train/morph, "<<std::size(build)<<" build, "<<upgrades<<" upgrade, "<<researches<<" research, Shield Battery R\n";
}
int main(int argc,char**argv){try{
 check(argc==3,"Usage: hotkeys11 CORE OUTPUT");std::string core=argv[1];open_archive(0,core+"/STARDAT.MPQ");open_archive(1,core+"/BROODAT.MPQ");open_archive(2,core+"/patch_rt.mpq");open_archive(3,"app/src/main/assets/native/weave.scx");int races[]={1,0,2,1,1,1,1,1},slots[]={1,0,0,0,0,0,0,0};configured_init(640,480,0,races,slots,0,true,false,false);g_ui->fog_player=-1;g_ui->host_controls_edge_scroll=true;g_ui->set_test_unlimited_supply(true);g_ui->st.current_minerals[0]=100000;g_ui->st.current_gas[0]=100000;
 // Powered producers and completed prerequisites for card/action coverage.
 for(int id:{106,109,111,112,113,114,116,122,123,131,132,133,135,136,137,138,139,140,141,142,154,155,156,159,160,163,164,165,166,167,169,170,171})unit(id);
 corpus(std::filesystem::path(argv[2])/"cards");original_audit();
 auto*marine=unit(0);select(marine);int stop=find(play_ui::C_STOP),token=g_ui->command_token(g_ui->card[stop]);command(35,stop,token+2,0,0);command(35,-1,token,0,0);command(35,999,token,0,0);flush();check(g_ui->outgoing.empty(),"Stale or invalid exact command executed");
 command(32,1,0,225,0);press(stop);command(32,0,0,225,0);flush();auto raw=g_ui->outgoing;bool queued=false;for(size_t p=0;p<raw.size();){int n=u16(raw.data()+p);p+=2;if(raw[p]==26)queued=raw[p+n-1]==1;p+=n;}check(queued&&!g_ui->key_shift(),"Exact-command queue lost same-frame Shift");expect(26);
 for(int mode=0;mode<4;++mode){select(marine);stop=find(play_ui::C_STOP);if(mode==0)g_ui->paused=true;if(mode==1)g_ui->campaign_control_lock=true;if(mode==2)g_ui->spectator=true;if(mode==3)native_replay::active=true;press(stop);flush();check(g_ui->outgoing.empty(),"Exact command crossed pause/cutscene/spectator/replay guard");g_ui->paused=g_ui->campaign_control_lock=g_ui->spectator=false;native_replay::active=false;}
 select(marine);int attack=find(play_ui::C_ATTACK);press(attack);flush();check(g_ui->targeting&&g_ui->pending_targ==play_ui::T_ATTACK,"Exact attack did not target");command(2,27,41,0,0);flush();check(!g_ui->targeting,"Escape did not cancel exact target");
 select(unit(7));g_ui->paused=true;command(6,0,0,0,0);flush();int build=find(play_ui::C_BUILDMENU);press(build);command(6,0,0,0,0);flush();check(g_ui->menu==1,"Grid Build submenu failed");int depot=find(play_ui::C_BUILD,U::Terran_Supply_Depot);press(depot);flush();check(g_ui->pending_build&&g_ui->pending_build->id==U::Terran_Supply_Depot,"Grid submenu target wrong");command(2,27,41,0,0);flush();check(!g_ui->pending_build&&g_ui->menu==0,"Grid placement Escape failed");
 select(unit(7));build=find(play_ui::C_BUILDMENU);int stale=g_ui->command_token(g_ui->card[build]);press(build);flush();command(35,build,stale,0,0);flush();check(!g_ui->pending_build&&g_ui->menu==1,"Old card token activated replacement command");
 select(unit(111));int train=find(play_ui::C_TRAIN,U::Terran_Marine);press(train);flush();expect(31);
 select(unit(160));train=find(play_ui::C_TRAIN,U::Protoss_Zealot);check(g_ui->card[train].enabled,"Fixture Gateway unpowered");press(train);flush();expect(31);
 select(unit(35));train=find(play_ui::C_MORPH,U::Zerg_Drone);press(train);flush();expect(35);
 select(unit(122));int upgrade=find(play_ui::C_UPGRADE);check(g_ui->card[upgrade].enabled,"Fixture upgrade disabled");press(upgrade);flush();expect(50);
 select(unit(112));int research=find(play_ui::C_RESEARCH);press(research);flush();expect(48);
 select(unit(172));int recharge=find(play_ui::C_RECHARGE);unit(172)->energy=50_fp8;press(recharge);flush();check(g_ui->targeting&&g_ui->pending_spell_order==Orders::RechargeShieldsBattery,"Exact Recharge Shields failed");select(marine);
 // Native validation uses live eligibility, not the old enabled/affordable display.
 select(unit(111));train=find(play_ui::C_TRAIN,U::Terran_Marine);g_ui->st.current_minerals[0]=0;int errors=g_ui->error_seq;press(train);flush();check(g_ui->outgoing.empty()&&g_ui->error_seq>errors,"Grid bypassed resource requirements");g_ui->st.current_minerals[0]=100000;
 select(unit(113));int vessel=find(play_ui::C_TRAIN,U::Terran_Siege_Tank_Tank_Mode);check(!g_ui->card[vessel].enabled,"Fixture expected missing attached addon");press(vessel);flush();check(g_ui->outgoing.empty(),"Grid bypassed disabled command");
 select(marine);net_active=true;auto hash=net_hash();press(find(play_ui::C_STOP));flush();check(net_hash()==hash,"Grid bypassed multiplayer lockstep");expect(26);net_active=false;
 select(marine);press(find(play_ui::C_STOP));command(34,0,0,0,0);flush();check(g_ui->outgoing.empty(),"Reset did not discard queued grid command");
 check(native_replay::ENGINE==84,"Local grid changed simulation compatibility");std::cout<<"PASS native exact-command routing: stale identities, all-race training, submenu placement, research/upgrades, disabled/resources, Shift, locks, replay, multiplayer and cleanup\nPASS "<<checks<<" native hotkey checks\n";close_game();return 0;
}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
