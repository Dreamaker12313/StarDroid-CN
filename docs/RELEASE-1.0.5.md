# StarDroid 1.0.5

Android version code 75 · Android 8.0+ · ARM64 and x86-64

## Font recovery

The supplied 1.0.4 report confirms that campaign artwork was imported, but none of the eight expected font entries were found at either supported path in StarCraft.mpq. The report was taken before a menu loaded, so it does not establish the current decoder results for StarDat.mpq, BrooDat.mpq or patch_rt.mpq. The actual tester archive has not been supplied. A version mismatch is not established.

Fonts are now selected in this order:

1. The exact original font from the patch, BrooDat, StarDat or imported interface, preserving the existing archive precedence and both font paths.
2. The closest readable original size among 8, 10, 12, 14, 16, 16x, 32 and 50, scaled into the required line height. This includes fonts not normally used by these menus.
3. An installed Android sans-serif font, only when no supported original font can be read. Larger labels use bold lettering, menu buttons use wider lettering, and the imported menu palette supplies highlight, face and shadow colors. Small text stays regular for readability. Measurements, wrapping and drawing share the same cached glyph metrics.

Exact original fonts keep their original rendering. No fonts or game data are added to the APK. The styled Android font is an approximation; it cannot recreate missing original letterforms exactly and its appearance can vary with the device font.

Font-only substitution is recorded in diagnostics without covering working campaign artwork with a repair banner. Missing campaign artwork still has a visible recovery notice. The existing Diagnostic report button is retained, and its Font choices section identifies exact, substituted original, or styled system fonts and the selected archive.

## Update

Install **StarDroid-1.0.5.apk over the existing app**, then open the game menu. **No reimport is required for this font change.** Existing imports, saves and settings are preserved. Future imports through **Import game files** use the same font selection automatically when the menu reloads. There is no separate repair button.

If reporting the appearance, open the affected menu first and then use **Diagnostic report**, so the report includes the actual font choices rather than only the import inventory.

## Validation

- 3,686 font checks cover cached glyphs, proportional widths, control codes, colors, accents, wrapping and real menu label bounds using the production Java renderer with an AWT Canvas shim.
- 41 asset checks and 13 fallback action/label checks pass. Fixtures verify that a valid original font in another archive is preferred, that font12 can supply a missing menu size, and that an exact imported font takes precedence over a substitute.
- 33 production import checks pass. Palette-only normal import is reconstructed into a sparse MPQ, decoded by the native reader and loaded by both campaign menu classes: artwork is retained, styled fonts render, and there is no artwork repair warning. The complete/partial-original-font handoff also passes.
- Host previews inspected. Release build and lint pass with 0 errors and 10 existing warnings. Version, original release signing identity and 16 KiB APK alignment verified. All 76 native-library and bundled-asset entries are byte-identical to 1.0.4.

These checks are not an Android device test. Samsung rendering and touch interaction still need confirmation on the tester's phone. The host shim uses a desktop sans font in place of Android's font. No GitHub release was published.
