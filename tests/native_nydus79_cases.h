#pragma once
// Included after native_campaign79.cpp's shared helpers. All map/terrain data
// comes from the caller's external archives; only link mutations live here.
namespace nydus79 {
using Pairs = std::vector<std::pair<xy,xy>>;
static uint32_t get32(const a_vector<uint8_t>& b,size_t p) {
    return uint32_t(b[p]) | uint32_t(b[p+1])<<8 | uint32_t(b[p+2])<<16 | uint32_t(b[p+3])<<24;
}
static unsigned get16(const a_vector<uint8_t>& b,size_t p) {return b[p] | unsigned(b[p+1])<<8;}
static void put32(a_vector<uint8_t>& b,size_t p,uint32_t n) {for(int k=0;k<4;++k)b[p+k]=uint8_t(n>>(8*k));}
static void put16(a_vector<uint8_t>& b,size_t p,unsigned n) {b[p]=uint8_t(n);b[p+1]=uint8_t(n>>8);}
static std::vector<size_t> records(const a_vector<uint8_t>& b) {
    std::vector<size_t> result;
    for(size_t p=0;p+8<=b.size();) {
        size_t n=get32(b,p+4);require(n<=b.size()-p-8,"Invalid external CHK chunk");
        if(!memcmp(b.data()+p,"UNIT",4)) {
            require(n%36==0,"Invalid external UNIT records");
            for(size_t q=p+8;q<p+8+n;q+=36)if(get16(b,q+8)==unsigned(U::Zerg_Nydus_Canal))result.push_back(q);
        }
        p+=8+n;
    }
    return result;
}
static void check_exit(state_functions& f,unit_t* u,const Pairs& pairs) {
    xy expected{};bool linked=false;
    for(auto pair:pairs) {
        if(pair.first==u->position){expected=pair.second;linked=true;}
        if(pair.second==u->position){expected=pair.first;linked=true;}
    }
    auto* exit=u->building.nydus.exit;
    if(!linked)require(!exit,"Unexpected Nydus link on an unpaired/invalid endpoint");
    else require(exit && exit!=u && f.unit_is_nydus(exit) && exit->position==expected
                 && exit->owner==u->owner && exit->building.nydus.exit==u,
                 "Nydus link does not match the exact original map pairing");
}
static void check_loaded(int owner,size_t count,const Pairs& pairs) {
    auto canals=units(U::Zerg_Nydus_Canal,owner);require(canals.size()==count,"Original mission Nydus count changed");
    for(auto* u:canals)check_exit(*g_ui,u,pairs);
}
static void check_custom(a_vector<uint8_t> b,const Pairs& pairs) {
    // Use the shared UMS loader directly, with no campaign compatibility code.
    // A private state/game keeps the live UI's pointers out of these fixtures.
    auto game=std::make_unique<game_state>();auto st=std::make_unique<state>();
    st->global=g_ui->st.global;st->game=game.get();game_load_functions f(*st);
    std::array<int,12> owners{},races{};
    for(size_t p=0;p+8<=b.size();) {
        size_t n=get32(b,p+4);require(n<=b.size()-p-8,"Invalid custom CHK chunk");
        if(n>=12)for(size_t i=0;i<12;++i) {
            if(!memcmp(b.data()+p,"OWNR",4))owners[i]=b[p+8+i];
            if(!memcmp(b.data()+p,"SIDE",4))races[i]=b[p+8+i];
        }
        p+=8+n;
    }
    f.load_map_data(b.data(),b.size(),[&] {
        f.setup_info.victory_condition=0;f.setup_info.resource_type=0;
        for(size_t i=0;i<12;++i) {
            auto& p=st->players[i];p.controller=owners[i];p.race=race_t(races[i]);
            if(p.controller==player_t::controller_open)p.controller=player_t::controller_occupied;
            if(p.controller==player_t::controller_computer)p.controller=player_t::controller_computer_game;
        }
    },false);
    size_t count=0;
    for(auto& list:st->player_units)for(auto* u:ptr(list))if(f.unit_is_nydus(u)) {check_exit(f,u,pairs);++count;}
    require(count==records(b).size(),"UMS fixture failed to place every Nydus record");
}
static void cases(const char* broodwar,const char* starcraft) {
    load(broodwar,408);
    check_loaded(4,2,{{{4224,2080},{2944,2624}}});
    load(broodwar,501);
    check_loaded(1,8,{{{1440,3488},{480,3584}},{{1184,3552},{224,3648}},
                      {{1344,3616},{384,3712}},{{1440,3744},{480,3840}}});
    load(broodwar,301);check_loaded(-1,14,{});
    std::cout<<"PASS To Chain the Beast and Vile Disruption original Nydus pairs; Escape from Aiur unpaired canals remain unpaired\n";

    load(starcraft,108);auto original=g_ui->rep_map;auto r=records(original);
    require(r.size()==4,"Expected four Eye for an Eye map records");
    // Match offsets by exact position instead of assuming source record order.
    auto at=[&](xy pos) {for(size_t p:r)if(get16(original,p+4)==unsigned(pos.x)&&get16(original,p+6)==unsigned(pos.y))return p;
        throw std::runtime_error("Expected Nydus source position missing");};
    size_t a=at({800,384}),b=at({3264,512}),c=at({3424,576}),d=at({3808,3776});
    Pairs all={{{800,384},{3264,512}},{{3424,576},{3808,3776}}};
    Pairs second={{{3424,576},{3808,3776}}};
    check_custom(original,all);
    {auto x=original;for(size_t k=0;k<36;++k)std::swap(x[a+k],x[d+k]);check_custom(x,all);}
    // The exit need not repeat the entrance's declaration.
    {auto x=original;put16(x,b+10,0);put32(x,b+32,0);check_custom(x,all);}
    {auto x=original;put32(x,a+32,0x7ffffffe);put16(x,b+10,0);put32(x,b+32,0);check_custom(x,second);}
    {auto x=original;put32(x,a+32,get32(x,a));put32(x,b+32,get32(x,b));check_custom(x,second);}
    {auto x=original;x[b+16]=11;check_custom(x,second);}
    {auto x=original;put16(x,b+8,unsigned(U::Zerg_Hatchery));check_custom(x,second);}
    // A->B<-C has no unique pairing, even when B has no declaration.
    {auto x=original;put16(x,b+10,0);put32(x,b+32,0);put32(x,c+32,get32(x,b));
        put16(x,d+10,0);put32(x,d+32,0);check_custom(x,{});}
    // A->B->C<->D cannot be resolved by accepting whichever pair comes first.
    {auto x=original;put32(x,b+32,get32(x,c));check_custom(x,{});}
    {auto x=original;put32(x,d,get32(x,a));check_custom(x,{});}
    {auto x=original;put16(x,a+10,0x200);put16(x,b+10,0x200);check_custom(x,second);}
    {auto x=original;for(size_t p:r){put16(x,p+10,0);put32(x,p+32,0);}check_custom(x,{});}
    std::cout<<"PASS custom UMS Nydus links: exact/reordered/one-sided pairs, missing/self/cross-owner/non-Nydus targets, conflicting/duplicate serials and absent/wrong link flags\n";
}
} // namespace nydus79
