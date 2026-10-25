# StarDroid 1.0.8

Android version code **78** · Android **8.0+** · **ARM64 and x86-64**

This release includes the fixes and features developed since the public 1.0.1 release.

## AI transports across campaigns and custom games

- **Dropships, Shuttles, and Overlords with Ventral Sacs** can carry ground attack groups across disconnected terrain, including water, cliffs, and enclosed areas.
- A shared controller loads passengers within capacity, finds reachable landing areas, unloads attackers, and reuses surviving transports for additional trips.
- Scripted campaign attacks can use existing transports even without an active production town. Transport production, prerequisites, and upgrades respect normal costs and mission restrictions.
- Workers can be ferried to island expansions and resume construction after unloading.
- Transport assignments survive saves; destroyed ships release their assignments.

The fix applies across campaign missions and custom-game AI for all three races, including the original Zerg mission 4, **Agent of the Swarm**.

## Large map ZIP imports

- Import up to **10,000 maps** from a single ZIP, including `.scm` and `.scx` files in nested folders.
- Supports **8 GiB uncompressed per pack**, **64 MiB per map**, and **50,000 ZIP entries**. Keep enough free storage for unpacked content and working space.
- Files stream to disk; validation and installation run in the background with progress updates.
- Identical maps are deduplicated, invalid maps are rejected individually, and map labels and sorting are cached.
- Import validation is isolated from the running game engine. The separate nearby multiplayer map-transfer limit is unchanged.

## Larvae selection and morphing

Both options are under **Game Menu → Options → Touch Controls → Selection settings**.

- **Original larvae selection — on by default:** Select Larvae chooses up to three larvae belonging to the selected Hatchery, Lair, or Hive. Turn it off to select larvae across multiple buildings.
- **One larva morph per press — optional, off by default:** each command-button press or hotkey morphs one selected larva, including rapid presses. Remaining larvae keep their morph commands after the first becomes an egg. One larva still produces two Zerglings or two Scourge. Other unit and building morphs retain their normal behavior.

## Campaign objects and uninterrupted dialogue

- Fixed worker pickup of campaign objects, including the **Psi Emitter in Brood War Zerg's Reign of Fire**.
- Covers SCVs, Drones, and Probes carrying the Psi Emitter, Young Chrysalis, Data Disk, Khaydarin Crystal, Uraj Crystal, and Khalis Crystal. Carried objects survive save/load and drop when their carrier dies.
- Mission dialogue and effects use separate playback channels, preventing effects from replacing an active transmission.
- Overlapping transmissions queue, subtitles stay with their speech, and briefings wait for recordings to finish. Pending dialogue is retained in saves.
- Ordinary sound effects cannot evict an active unit voice.

## Languages, original menus, and widescreen

- Choose **English, Русский, Deutsch, Español, or Français** under **App Options → Interface language**. These choices translate the port's menus, settings, common messages, and interface labels. Original campaign text, unit names, and recorded speech follow the imported game data.
- Added Russian game-data and original bitmap-font support, including corrected Cyrillic decoding and font transparency.
- Corrected handling of installer-encrypted fonts in **StarDat.mpq**, plus compressed/encrypted archive entries used by supported classic installations.
- Normal game-file imports apply the menu/font fixes automatically. Duplicate download suffixes such as `(1)` are accepted. Missing glyphs fall back individually while readable original glyphs are retained.
- Menu artwork and labels recover more reliably. Menus stay clean, while **Show Credits → Diagnostics / credits** and **Copy** remain available.
- **Options → Video Options → Widescreen** offers **Off**, **On**, and **+ over camera area**. The last option extends the game display into the phone's camera-cutout area; App Options retains safe margins.

## Install and compatibility

Download **StarDroid-1.0.8.apk** below and install it **over the existing app without uninstalling**. It uses the same application ID and signing certificate as the previous distributed APK, preserving imported files, maps, saves, and settings. Existing imports need no repair action or reimport for this update.

- Use **build 78 on every nearby multiplayer device**, with matching game data.
- Existing save schemas 1–3 remain readable. New schema-4 saves require this version or newer. Previously retired external-bot saves remain unsupported.
- **Game data is not included.** Import your own classic StarCraft and Brood War files. The source ZIP is for development, not installation.
- **SHA256SUMS.txt** contains the hashes of the APK and source ZIP.

## Validation

Automated checks cover **2,501 distinct maps**, all three transport types in campaign and custom-game scenarios, repeated airlift trips, island-worker construction, transport save/load and loss handling, larvae command timing, campaign-object pickup, speech isolation, language/font layouts, save compatibility, and nearby protocol behavior.

All **64 campaign maps** passed load and short simulation checks, with **144 computer-owner restriction checks**. The original **Agent of the Swarm** scenario ran for **18,000 simulation frames**, recording **31 ground-unit load events and 21 unload events**. These are bounded regression tests, not full campaign playthroughs.

Release assembly and lint passed (**0 errors, 11 warnings**). Signing, both native architectures, and 16 KiB alignment were verified. Physical Android installation, touch, audio, camera-cutout, and multiplayer-radio testing remain pending. Detailed reports are included in the source ZIP.

Put together by **ToadWarrior**, using **OpenBW**. [Discord community](https://discord.gg/F2FnjUrtQ)
