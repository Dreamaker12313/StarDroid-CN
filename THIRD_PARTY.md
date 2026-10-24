# Credits and third-party notices

**StarDroid was put together by ToadWarrior.**

StarDroid is an unofficial Android adaptation. StarCraft and Brood War are Blizzard Entertainment properties. The player supplies original game archives; Blizzard game data is not distributed with this repository or APK.

| Component | Origin and attribution | Notice |
| --- | --- | --- |
| OpenBW engine and web-host ancestry | [OpenBW](https://github.com/OpenBW/openbw), [heiner/openbw](https://github.com/heiner/openbw), and their contributors | Pinned commit `469d2037e2fd03085dac4729912f4188bc2a778b`; provenance and archive changes in [UPSTREAM.json](UPSTREAM.json). |
| libsmacker 1.2.0 | Greg Kennedy and contributors; pinned [JonnyH/libsmacker](https://github.com/JonnyH/libsmacker) commit `ae8d4c9ec07b24d43ccff184d6e512bae793dfd1` | LGPL 2.1 or later. Full license in [vendor/libsmacker/COPYING](vendor/libsmacker/COPYING). Source is included and the Android decoder is a separate shared library. |
| PyMS listfiles and format references | Zach Zahos / poiuyqwert, [PyMS](https://github.com/poiuyqwert/PyMS) | [MIT license](app/src/main/assets/missions/PyMS-LICENSE.txt) is preserved with the mission metadata. |
| Weave map | Alexandre Coderre-Chabot, [acodcha/sc](https://github.com/acodcha/sc) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); map attribution in [ATTRIBUTION.md](app/src/main/assets/game/maps/ATTRIBUTION.md). The native copy is the same map. |
| Asio in the upstream archive | Asio authors and contributors | Boost Software License 1.0; `deps/asio/LICENSE_1_0.txt` is retained inside the vendored source archive. |
| JSON-java test dependency | [stleary/JSON-java](https://github.com/stleary/JSON-java), version 20240303 | Used only by development test harnesses, not bundled as an APK dependency. Upstream source and licensing are maintained in the linked JSON-java repository. |

The pinned OpenBW archive does not contain a top-level engine license file. This repository does not assign a new license to that upstream code or claim that one blanket license covers every component. Existing notices and their scope are preserved. Upstream's license discussion is tracked in [OpenBW/openbw issue 17](https://github.com/OpenBW/openbw/issues/17).

See [REFERENCES.md](REFERENCES.md) for historical implementation references. References are not included game assets. See [docs/BUILDING.md](docs/BUILDING.md) for rebuilding the native app and replacing the decoder library.
