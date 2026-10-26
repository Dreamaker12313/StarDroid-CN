#include "../native/runtime.cpp"
#include <fstream>
#include <iostream>
#include <set>
using namespace bwgame;
static int checks=0;
static void check(bool v,const char*m){++checks;if(!v)throw std::runtime_error(m);}
static std::vector<uint8_t> pixels(unit_t* u,const grp_t& grp,int box){
 auto* p=g_ui->render_wireframe_unit(u,grp,box);check(p!=nullptr,"Wireframe frame missing");return {p,p+box*box*4};
}
static void write(const std::string& dir,const std::string& name,const std::vector<uint8_t>& p){std::ofstream f(dir+"/"+name+".rgba",std::ios::binary);f.write((const char*)p.data(),p.size());}
int main(int argc,char**argv){try{
 check(argc==4,"Usage: test CORE OUT baseline|fixed");std::string core=argv[1],out=argv[2];bool fixed=std::string(argv[3])=="fixed";
 open_archive(0,core+"/STARDAT.MPQ");open_archive(1,core+"/BROODAT.MPQ");open_archive(2,core+"/patch_rt.mpq");open_archive(3,"app/src/main/assets/native/weave.scx");
 int races[]={1,1,2,1,1,1,1,1},controllers[]={1,0,0,0,0,0,0,0};configured_init(640,480,0,races,controllers,0,true,false,false);
 check(g_ui->load_wire_grp(),"Original wireframe groups absent");
 a_vector<uint8_t> raw;g_ui->load_data_file(raw,"game\\twire.pcx");auto pcx=load_pcx_data(raw);check(pcx.width==24&&pcx.height==1,"Original twire palette dimensions changed");
 for(int mode=0;mode<3;mode++){
  const auto& grp=mode==0?g_ui->wire_big_grp:mode==1?g_ui->wire_grp:g_ui->wire_transport_grp;int box=mode==1?32:64;
  std::set<int> indices;
  for(size_t id=0;id<grp.frames.size()&&id<228;id++){
   const auto& f=grp.frames[id];check(f.offset.x>=0&&f.offset.y>=0&&f.offset.x+f.size.x<=box&&f.offset.y+f.size.y<=box,"Original frame exceeds its output box");
   unit_t u{};u.unit_type=g_ui->get_unit_type((UnitTypes)id);u.hp=u.unit_type->hitpoints;u.shield_points=fp8::integer(u.unit_type->shield_points);u.wireframe_randomizer=2;
   for(int hp:{100,70,40,15,1}){u.hp.raw_value=(int64_t)u.unit_type->hitpoints.raw_value*hp/100;auto p=pixels(&u,grp,box);for(auto c:g_ui->wire_index)if(c)indices.insert(c);
    if(fixed){for(size_t pos=0;pos<g_ui->wire_index.size();pos++){
      int c=g_ui->wire_index[pos];if(!c)continue;int palette=-1;
      if(c>=208&&c<=211&&(hp==100||hp==1))palette=pcx.data[hp==100?1:10];
      if(c>=216&&c<=219&&(hp==100||hp==1)){static const int healthy[]={0,1,18,10},critical[]={14,6,7,8};palette=pcx.data[(hp==100?healthy:critical)[c-216]];}
      if((c==192||c==193)&&u.unit_type->has_shield)palette=pcx.data[c==192?3:4];
      if(palette>=0){check(p[pos*4]==g_ui->tileset_img.wpe[palette*4]&&p[pos*4+1]==g_ui->tileset_img.wpe[palette*4+1]&&p[pos*4+2]==g_ui->tileset_img.wpe[palette*4+2]&&p[pos*4+3]==255,"Wireframe does not use original palette remap");}
    }}
   }
  }
  std::cout<<"GRP "<<mode<<" frames="<<grp.frames.size()<<" indices=";for(int c:indices)std::cout<<c<<',';std::cout<<'\n';
 }
 for(int id:{0,7,12,37,41,38,65,66,67,106,131,154})for(int mode=0;mode<3;mode++){
  const auto& grp=mode==0?g_ui->wire_big_grp:mode==1?g_ui->wire_grp:g_ui->wire_transport_grp;if(id>=int(grp.frames.size()))continue;int box=mode==1?32:64;
  unit_t u{};u.unit_type=g_ui->get_unit_type((UnitTypes)id);u.wireframe_randomizer=2;u.shield_points=fp8::integer(u.unit_type->shield_points);
  std::set<std::vector<uint8_t>> variants;
  for(int hp:{100,70,40,15,1}){u.hp.raw_value=(int64_t)u.unit_type->hitpoints.raw_value*hp/100;auto p=pixels(&u,grp,box);variants.insert(p);write(out,std::to_string(id)+"-"+std::to_string(mode)+"-"+std::to_string(hp),p);}
  if(fixed)check(variants.size()>=3,"Damage rendering does not progress through stages");
 }
 unit_t zealot{};zealot.unit_type=g_ui->get_unit_type(UnitTypes::Protoss_Zealot);zealot.hp=zealot.unit_type->hitpoints;
 std::set<std::vector<uint8_t>> shieldVariants;
 for(int shields:{100,70,40,15,1,0}){zealot.shield_points.raw_value=(int64_t)zealot.unit_type->shield_points*256*shields/100;auto p=pixels(&zealot,g_ui->wire_big_grp,64);write(out,"shield-"+std::to_string(shields),p);shieldVariants.insert(p);}
 if(fixed)check(shieldVariants.size()>=4,"Shields remain one fixed blue until zero");
 if(fixed){
  auto create=[](int type){auto* ut=g_ui->get_unit_type((UnitTypes)type);
   for(int y=320;y<1600;y+=96)for(int x=320;x<1600;x+=96){xy pos{x,y};if(!g_ui->unit_type_can_fit_at(ut,pos))continue;
    bool free=true;for(auto* other:g_ui->find_units(g_ui->square_at(pos,40)))if(!g_ui->unit_dying(other))free=false;
    if(free){auto* u=g_ui->create_initial_unit(ut,pos,0);if(u)return u;}}
   throw std::runtime_error("No fixture space");};
  std::vector<unit_t*> units;for(int type:{0,37,65})units.push_back(create(type));
  for(auto* u:units){g_ui->current_selection.clear();g_ui->current_selection.push_back(g_ui->get_unit_id(u));
   check(g_ui->wire_box()==64,"Single selection uses wrong frame dimensions");auto* p=g_ui->render_wireframe(0);check(p,"Selected unit has no wireframe");std::vector<uint8_t> selected(p,p+64*64*4);
   check(selected==pixels(u,g_ui->wire_big_grp,64),"Selected unit uses wrong original frame");
   auto state=std::string(g_ui->wires());u->hp.raw_value=u->unit_type->hitpoints.raw_value/4;
   check(state!=g_ui->wires(),"Damage did not invalidate redraw state");
  }
  auto* protoss=units.back();g_ui->current_selection.clear();g_ui->current_selection.push_back(g_ui->get_unit_id(protoss));
  auto state=std::string(g_ui->wires());protoss->shield_points.raw_value=int64_t(protoss->unit_type->shield_points)*256/2;
  check(state!=g_ui->wires(),"Partial shield damage did not invalidate redraw state");
  g_ui->current_selection.clear();for(auto* u:units)g_ui->current_selection.push_back(g_ui->get_unit_id(u));
  check(g_ui->wire_box()==32,"Group uses wrong frame dimensions");
  for(size_t i=0;i<units.size();i++){auto* p=g_ui->render_wireframe(i);check(p,"Group member has no wireframe");std::vector<uint8_t> selected(p,p+32*32*4);check(selected==pixels(units[i],g_ui->wire_grp,32),"Group member frame/damage differs");}
  auto* transport=create(11);for(auto* u:units){check(g_ui->unit_can_load_target(transport,u),"Cargo cannot board");g_ui->unit_load_target(transport,u);}
  g_ui->current_selection.clear();g_ui->current_selection.push_back(g_ui->get_unit_id(transport));size_t index=0;
  for(auto* u:g_ui->loaded_units(transport)){auto* p=g_ui->render_cargo_wireframe(index++);check(p,"Cargo member has no wireframe");std::vector<uint8_t> selected(p,p+64*64*4);check(selected==pixels(u,g_ui->wire_transport_grp,64),"Cargo member frame/damage differs");}
  check(index==3,"Cargo members missing");
 }
 close_game();std::cout<<"PASS "<<checks<<" wireframe checks: original GRPs for single/group/cargo, original palette endpoints and damage/shield transitions\n";return 0;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<'\n';return 1;}}
