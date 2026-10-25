# StarDroid 1.0.6

Android version code 76 · Android 8.0+ · ARM64 and x86-64

## Original installed fonts

The tester's supplied StarDat.mpq contains all eight original font files under their normal names. They have an extra encryption layer applied by the classic installer. Earlier builds extracted the MPQ entries but could not interpret the encrypted contents as FONT data, so they used substitute text. The supplied StarCraft.mpq has campaign artwork but no entries at either supported font location. The fonts were not renamed, and a game-version mismatch is not established.

This release decodes the installed fonts with their matching local installation metadata, checks the original envelope checksum, then uses the normal bitmap-font renderer. All eight decoded files match an independent reference decoding byte for byte. No font, installation metadata, key or other game data is bundled in the APK or source package. Plain original fonts still work; unavailable or invalid originals retain the existing readable fallback.

The added menu report button, font inventory, repair banners and saved menu reports are removed. **Show Credits still opens the original Diagnostics / credits screen**, including Copy, device/performance details and general failure information. Network diagnostics are retained. Installed content shows a simple campaign-artwork and music status.

## Update

Install **StarDroid-1.0.6.apk over the existing app without uninstalling**, then open the game menu. **No reimport is needed for the font fix** when the supplied StarDat.mpq is already installed. Existing game imports, saves and settings remain in place.

New files use the same decoding after the ordinary **Import game files** flow. StarCraft.mpq imports retain available campaign artwork even when that archive has no font copies. There is no separate repair button. Keep the original installed archive intact so its font metadata remains available.

## Validation

- Reproduced 1.0.5 falling back for all five menu font slots with the tester's actual core archives.
- Passed 1,717 encrypted-font checks covering all eight fonts, independent byte comparisons, exact menu font selection, glyph decoding, malformed envelopes/metadata, fallback recovery and unchanged source data.
- Imported the supplied StarCraft.mpq through the production importer: 31 maps and campaign artwork were retained, without a missing-font repair warning. Verified its sparse MPQ handoff to the native reader and Java menus.
- Passed 3,686 fallback/font checks, 41 asset checks, 13 fallback label/action checks and 33 synthetic import checks. Credits still invokes Diagnostics / credits.
- Inspected host renders using the original fonts. Host captures omit animated Smacker layers and do not verify Samsung display or touch behavior.
- Release assembly and lint pass (0 errors, 10 existing warnings). Version 1.0.6/code 76, the original release signing identity and 16 KiB APK alignment pass. All 76 native-library and bundled-asset entries are unchanged from 1.0.5.

No physical Android device test or GitHub publication was performed. The BroodWar.mpq upload did not transfer; it was not needed for this installed-font fix and was not inspected.
