# StarDroid 1.0.7 · build 77

Install `StarDroid-1.0.7.apk` over the existing app. It uses the same application
ID and release signing certificate. Keep the existing app installed to retain
imports, saves and settings. Existing English imports need no repair or reimport.

## Campaign objects and sound

The psi emitter in Brood War Zerg's **Reign of Fire** could receive the neutral
controller's idle order, preventing its worker pickup logic from running. Pickup
now follows the object's type regardless of that idle order. This covers the
Young Chrysalis, Psi Emitter, Data Disk, Khaydarin, Uraj and Khalis crystals, with
SCVs, Drones and Probes. A worker already carrying resources or an object cannot
take a second object. Carried objects retain their carrier through saves, follow
the worker and drop on death.

Triggered effects previously shared the mission speech channel, allowing a
dropship sound to replace Raynor's line. Effects and dialogue now have separate
channels. Overlapping transmissions queue, subtitles remain while speech plays,
and briefings wait for recordings to finish. Saved presentation state includes
pending dialogue. Ordinary effects also cannot evict an active unit voice.

## Options

- **App Options → Interface language:** English, Deutsch, Español and Français;
  Русский appears when Russian core data is detected. The port's menus, options,
  common messages and interface labels are translated. Original campaign text,
  unit names and voice recordings still follow the imported data language.
- **Options → Video Options → Widescreen:** Off, On, or **+ over camera area**.
  The last choice includes the phone camera cutout in the game display. App
  Options keeps safe margins.
- **Touch Controls → Selection settings → Original larvae selection:** on by
  default. Select Larvae selects at most three larvae belonging to the selected
  Hatchery, Lair or Hive. Off retains selection of up to twelve across buildings.
  Timing controls are grouped under **Timing & accuracy**.

## Russian data and original fonts

Use the normal import action for the Russian MPQs. Duplicate filename suffixes
such as `(1)` are accepted. The supplied Russian installation uses Windows-1251
text and its original bitmap fonts. The renderer now maps Cyrillic characters
correctly and fixes transparent FONT runs that previously distorted letters.
Missing characters use the system font individually; readable imported glyphs
are retained. The installer-encrypted StarDat font support from 1.0.6 remains.

The Russian archives also exposed two native reader limitations: uncompressed
game assets and encrypted sectors padded to whole cipher words. Both are handled
without altering the imported archives. A strict end-marker check distinguishes
a padded compressed tail from raw data of the same size.

Menus remain clean: no repair button, font inventory or menu report banner.
**Show Credits → Diagnostics / credits** and **Copy** remain available.

## Compatibility and verification

Both ARM64 and x86-64 libraries are rebuilt. Local multiplayer requires build 77
on all devices because the simulation changed. Existing single-player save
format support is retained; object links and queued dialogue have regression
coverage.

The actual English Reign of Fire introduction and objective pickup pass the
native test. All 18 worker/object combinations, larvae filtering, voice channel
isolation, translation layout checks, original fonts and import regressions pass.
The supplied Russian StarCraft archive imports 31 maps; its first mission passes
1,200 simulated frames, rendering and an exact save/load round trip. Its corrected
orders table and affected image match the English originals byte for byte.

These are bounded host tests, not full campaign playthroughs. Physical Android
touch/audio/camera-cutout testing remains pending. The Russian BroodWar campaign
archive did not transfer, so its campaign content has not been verified. Russian
BrooDat core data was tested. See [validation](../VALIDATION.md) for reports.
