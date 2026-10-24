// Exercise the real engine renderers against an inaccessible page immediately
// after each image. No game data is bundled; supply the installed MPQs locally.
#include "../native/runtime.cpp"
#include <iostream>
#include <limits>
using namespace bwgame;

static size_t rectangle_cases = 0, ghost_cases = 0, rendered_frames = 0, scroll_frames = 0;
static void require(bool ok, const char* message) {
    if (!ok) throw std::runtime_error(message);
}

template<class Pixel> struct GuardedImage {
    static constexpr size_t prefix = 256;
    static constexpr Pixel untouched = Pixel(0x5a5a5a5a);
    size_t width, height, pitch, mapping_size;
    uint8_t* mapping;
    Pixel* data;
    GuardedImage(size_t w, size_t h, size_t padding) : width(w), height(h), pitch(w + padding) {
        const size_t page = size_t(sysconf(_SC_PAGESIZE));
        const size_t bytes = pitch * height * sizeof(Pixel);
        const size_t accessible = (bytes + prefix + page - 1) / page * page;
        mapping_size = accessible + 2 * page;
        mapping = static_cast<uint8_t*>(mmap(nullptr, mapping_size, PROT_NONE,
                                            MAP_PRIVATE | MAP_ANONYMOUS, -1, 0));
        require(mapping != MAP_FAILED, "mmap failed");
        require(mprotect(mapping + page, accessible, PROT_READ | PROT_WRITE) == 0, "mprotect failed");
        data = reinterpret_cast<Pixel*>(mapping + page + accessible - bytes);
        reset();
    }
    ~GuardedImage() { munmap(mapping, mapping_size); }
    GuardedImage(const GuardedImage&) = delete;
    void reset() {
        memset(reinterpret_cast<uint8_t*>(data) - prefix, 0x6b, prefix);
        std::fill(data, data + pitch * height, untouched);
    }
    void check_padding() const {
        const auto* before = reinterpret_cast<const uint8_t*>(data) - prefix;
        for (size_t i = 0; i < prefix; ++i) require(before[i] == 0x6b, "Write before image");
        for (size_t y = 0; y < height; ++y)
            for (size_t x = width; x < pitch; ++x)
                require(data[y * pitch + x] == untouched, "Write into row padding");
    }
};

template<class Pixel> static void rectangle_case(GuardedImage<Pixel>& image, rect area) {
    image.reset();
    const Pixel color = Pixel(0x12345678);
    if constexpr (sizeof(Pixel) == 1) g_ui->line_rectangle(image.data, image.pitch, area, color);
    else g_ui->line_rectangle_rgba(image.data, image.pitch, area, color);
    image.check_padding();
    // Pixel oracle for a one-pixel outline of the clipped half-open rectangle.
    const int left = std::max(0, area.from.x), top = std::max(0, area.from.y);
    const int right = std::min(int(image.width), area.to.x), bottom = std::min(int(image.height), area.to.y);
    for (int y = 0; y < int(image.height); ++y) for (int x = 0; x < int(image.width); ++x) {
        const bool inside = x >= left && x < right && y >= top && y < bottom;
        const bool edge = x == left || x == right - 1 || y == top || y == bottom - 1;
        require(image.data[y * image.pitch + x] == (inside && edge ? color : image.untouched),
                "Rectangle differs from clipped pixel bounds");
    }
    ++rectangle_cases;
}

template<class Pixel> static void rectangles() {
    // Exhaustive ordered, inverted, empty, one-pixel and offscreen rectangles.
    g_ui->screen_width = 7; g_ui->screen_height = 5;
    for (size_t padding : {size_t(0), size_t(3)}) {
        GuardedImage<Pixel> image(7, 5, padding);
        for (int x1 = -2; x1 <= 9; ++x1) for (int x2 = -2; x2 <= 9; ++x2)
            for (int y1 = -2; y1 <= 7; ++y1) for (int y2 = -2; y2 <= 7; ++y2)
                rectangle_case(image, {{x1, y1}, {x2, y2}});
    }
    for (auto size : {xy(1, 1), xy(640, 480), xy(457, 343), xy(1280, 720)}) {
        g_ui->screen_width = size.x; g_ui->screen_height = size.y;
        for (size_t padding : {size_t(0), size_t(7)}) {
            GuardedImage<Pixel> image(size.x, size.y, padding);
            const int w = size.x, h = size.y, low = std::numeric_limits<int>::min(), high = std::numeric_limits<int>::max();
            for (auto area : {rect{{0, 0}, {w, h}}, rect{{-32, -32}, {w + 32, h + 32}},
                              rect{{w - 1, h - 1}, {w, h}}, rect{{0, h - 1}, {w, h}},
                              rect{{w - 1, 0}, {w, h}}, rect{{-2, 0}, {0, h}},
                              rect{{w, 0}, {w + 32, h}}, rect{{0, h}, {w, h + 32}},
                              rect{{0, -32}, {w, 0}}, rect{{w, h}, {0, 0}},
                              rect{{low, low}, {high, high}}, rect{{high, high}, {low, low}}})
                rectangle_case(image, area);
        }
    }
    g_ui->screen_width = g_ui->screen_height = 0;
    // Empty render targets must return before forming any pixel pointer.
    if constexpr (sizeof(Pixel) == 1) g_ui->line_rectangle(nullptr, 0, {{-1, -1}, {1, 1}}, 1);
    else g_ui->line_rectangle_rgba(nullptr, 0, {{-1, -1}, {1, 1}}, 1);
    ++rectangle_cases;
}

static void reproduce(const std::string& mode) {
    g_ui->screen_pos = xy(0, 0);
    g_ui->screen_width = 640; g_ui->screen_height = 480;
    std::cerr << "Drawing bottom-edge " << mode << " into guarded image\n";
    if (mode == "rgba-repro") {
        GuardedImage<uint32_t> image(640, 480, 0);
        g_ui->line_rectangle_rgba(image.data, image.pitch, {{128, 416}, {224, 480}}, 0xff18fc10);
        image.check_padding();
    } else {
        GuardedImage<uint8_t> image(640, 480, 0);
        auto* type = g_ui->get_unit_type(UnitTypes::Terran_Supply_Depot);
        require(type->placement_size.y == 64, "Unexpected fixture footprint");
        g_ui->draw_placement_ghost(type, 4, 13, true, image.data, image.pitch);
        image.check_padding();
    }
}

static void ghosts() {
    // All standard racial building entries, including add-ons and morphs.
    std::vector<const unit_type_t*> buildings;
    for (int id = 106; id <= 172; ++id) {
        auto* type = g_ui->get_unit_type(UnitTypes(id));
        if (g_ui->ut_building(type) && type->placement_size.x && type->placement_size.y &&
            type->flingy && type->flingy->sprite && type->flingy->sprite->image)
            buildings.push_back(type);
    }
    require(buildings.size() >= 50, "Missing building coverage");
    for (auto display : {xy(640, 480), xy(1280, 720), xy(457, 343)}) for (double zoom : {.5, 1., 1.4, 3.}) {
        const int w = int(display.x / zoom), h = int(display.y / zoom);
        openbw_resize(w, h); openbw_set_view_scale(zoom);
        g_ui->screen_pos = xy(65, 97);
        for (size_t padding : {size_t(0), size_t(5)}) {
            GuardedImage<uint8_t> image(w, h, padding);
            for (const auto* type : buildings) {
                const int bw = type->placement_size.x, bh = type->placement_size.y;
                for (auto origin : {xy(96, 96), xy(-bw / 2, 32), xy(w - bw / 2, 32),
                                    xy(32, -bh / 2), xy(32, h - bh / 2), xy(w - bw, h - bh),
                                    xy(-bw * 4, -bh * 4), xy(w + bw * 4, h + bh * 4)}) {
                    // Choose a tile and pan so the requested pixel edge is exact.
                    const int tx = 20, ty = 20;
                    g_ui->screen_pos = xy(tx * 32 - origin.x, ty * 32 - origin.y);
                    for (bool valid : {false, true}) {
                        image.reset();
                        g_ui->draw_placement_ghost(type, tx, ty, valid, image.data, image.pitch);
                        image.check_padding();
                        if (origin.x == 96 && origin.y == 96 && w > 96 && h > 96)
                            require(image.data[96 * image.pitch + 96] == (valid ? g_ui->place_ok_color : g_ui->place_bad_color),
                                    "Visible placement footprint missing");
                        ++ghost_cases;
                    }
                }
            }
        }
        // Real frame path: normal placement, refinery snap and flying parent +
        // add-on; cursor at each corner and center, with drag selection enabled.
        g_ui->screen_pos = xy(128, 128);
        auto* worker = *ptr(g_ui->st.player_units[0]).begin();
        g_ui->current_selection_clear(); g_ui->current_selection_add(worker);
        for (auto type : {UnitTypes::Terran_Supply_Depot, UnitTypes::Terran_Refinery, UnitTypes::Terran_Factory,
                          UnitTypes::Zerg_Hatchery, UnitTypes::Protoss_Pylon}) {
            g_ui->pending_build = g_ui->get_unit_type(type);
            g_ui->pending_land = type == UnitTypes::Terran_Factory;
            g_ui->pending_addon = g_ui->pending_land ? g_ui->get_unit_type(UnitTypes::Terran_Machine_Shop) : nullptr;
            for (auto cursor : {xy(0, 0), xy(w - 1, 0), xy(0, h - 1), xy(w - 1, h - 1), xy(w / 2, h / 2)}) {
                openbw_mouse_move(cursor.x, cursor.y);
                g_ui->is_drag_selecting = true;
                g_ui->drag_select_from_x = 0; g_ui->drag_select_from_y = 0;
                g_ui->drag_select_to_x = w; g_ui->drag_select_to_y = h;
                openbw_render(double(++rendered_frames) * 42);
                require(openbw_framebuffer_width() == w && openbw_framebuffer_height() == h,
                        "Frame dimensions changed unexpectedly");
            }
        }
        g_ui->is_drag_selecting = false;
        g_ui->pending_build = g_ui->pending_addon = nullptr;
        g_ui->pending_land = false;
    }
    std::cout << "building_types=" << buildings.size() << " ";
}

static void scrolling() {
    for (double zoom : {.5, 1., 1.4, 3.}) {
        const int w = int(std::round(640 / zoom)), h = int(std::round(480 / zoom));
        openbw_resize(w, h); openbw_set_view_scale(zoom);
        command(21, int(std::round((480 - 376) / zoom)), 0, 0, 0);
        command(26, 1, 0, 0, 0);
        require(g_ui->host_controls_edge_scroll, "Host did not take ownership of edge scrolling");
        g_ui->pending_build = g_ui->get_unit_type(UnitTypes::Terran_Factory);
        g_ui->pending_addon = g_ui->get_unit_type(UnitTypes::Terran_Machine_Shop);
        g_ui->pending_land = true;
        for (auto direction : {xy(-1, 0), xy(1, 0), xy(0, -1), xy(0, 1), xy(-1, -1), xy(1, -1), xy(-1, 1), xy(1, 1)}) {
            g_ui->screen_pos = xy(400, 400); g_ui->clamp_viewport();
            // Put the cursor at a native image edge too, to catch double-panning
            // and exercise the retained border fix while the camera moves.
            command(0, direction.x < 0 ? 0 : direction.x > 0 ? w - 1 : w / 2,
                    direction.y < 0 ? 0 : direction.y > 0 ? h - 1 : h / 2, 0, 0);
            for (int frame = 0; frame < 12; ++frame) {
                const int step = frame == 10 ? 100000 : frame == 11 ? 0 : 4;
                command(3, direction.x * step, direction.y * step, 0, 0);
                const xy expected = g_ui->screen_pos;
                require(expected.x >= 0 && expected.y >= 0 &&
                        expected.x <= std::max(0, int(g_ui->game_st.map_width) - int(g_ui->view_width)) &&
                        expected.y <= std::max(0, int(g_ui->game_st.map_height) - int(g_ui->camera_height())),
                        "Host pan left map bounds");
                openbw_render(double(++rendered_frames) * 8.333333333);
                require(g_ui->screen_pos == expected, "Native edge logic added a second pan or moved a released target");
                require(g_ui->edge_dir == 0, "Native edge pan was still active");
                ++scroll_frames;
            }
        }
        g_ui->pending_build = g_ui->pending_addon = nullptr; g_ui->pending_land = false;
    }
}

int main(int argc, char** argv) { try {
    require(argc == 4, "Usage: native-placement DATA_DIR MAP [ghost-repro|rgba-repro|all]");
    std::string dir = argv[1], mode = argv[3];
    open_archive(0, dir + "/STARDAT.MPQ"); open_archive(1, dir + "/BROODAT.MPQ");
    open_archive(2, dir + "/patch_rt.mpq"); open_archive(3, argv[2]);
    int races[8] = {1, 0, 2, 1, 1, 1, 1, 1}, slots[8] = {1, 0, 0, 0, 0, 0, 0, 0};
    configured_init(640, 480, 0, races, slots, 2, true, false, false);
    openbw_render(0); g_ui->build_ghost_luts();
    g_ui->place_ok_color = g_ui->nearest_palette_color(40, 240, 40);
    g_ui->place_bad_color = g_ui->nearest_palette_color(240, 40, 40);
    if (mode == "all") {
        rectangles<uint8_t>(); rectangles<uint32_t>();
        reproduce("ghost-repro"); reproduce("rgba-repro"); ghosts(); scrolling();
    } else {
        require(mode == "ghost-repro" || mode == "rgba-repro", "Unknown case");
        reproduce(mode);
    }
    close_game();
    std::cout << "PASS mode=" << mode << " rectangle_cases=" << rectangle_cases
              << " ghost_cases=" << ghost_cases << " rendered_frames=" << rendered_frames
              << " scroll_frames=" << scroll_frames << "\n";
    return 0;
} catch (const std::exception& e) {
    std::cerr << "FAIL " << e.what() << "\n"; return 1;
} }
