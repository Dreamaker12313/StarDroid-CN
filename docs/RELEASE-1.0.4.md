# StarDroid 1.0.4

Android version code 74 · Android 8.0+ · ARM64 and x86-64

## Confirmed remaining failure

The tester's 1.0.3 report says the full StarCraft.mpq import installed all 31 maps, then failed with **Interface: The original font set is incomplete**. It confirms that StarDroid-Interface.zip was never installed, that the five menu fonts fell back to system text, and that the campaign used palnl because palcs/backgnd.pcx was unavailable.

The earlier image-size correction did not fix this separate validation rule. InterfaceData required all eight font entries before accepting any interface content. This could reject the campaign background and all five fonts actually used by these menus merely because another font was absent. The report does not reveal which font was missing; the font50 example is a synthetic reproduction, not a claim about the tester's files.

## Changes

- Normal **Import game files** accepts available interface entries even when some fonts are missing. Fonts and campaign artwork no longer depend on an eight-font completeness check.
- Installed content and import results list the missing menu font/background entries. Diagnostic reports also distinguish fonts not required by these menus.
- Reimports that would remove an existing menu font or campaign palette entry keep the previous bundle and explain why. Existing files are not silently downgraded.
- Invalid archive metadata, unexpected paths, missing packed payloads and size limits remain enforced. Complete imports still work.
- The diagnostic report button and its Copy, Share and Save actions remain available. There is no separate repair button.

## Install and reimport

Install **StarDroid-1.0.4.apk over the existing app**, without uninstalling or clearing data. Then use **App Options → Import game files** to reimport the same full classic **StarCraft.mpq** or original StarCraft **Install.exe** and return to the game menu.

The old rejected bundle cannot be recovered by updating the APK alone: the source archive must be selected again. If a font or background is genuinely absent from that archive, the app keeps its fallback and the report names the missing entry. Send a new diagnostic report after reopening the affected menu if the appearance is still wrong.

No StarCraft version mismatch is established by this report. The tester's archive fingerprints differ from the external core test files, and the tester's actual StarCraft.mpq has not been provided.

## Validation

Production import tests cover full-size PCX data, all 31 base maps, executable-contained MPQs, alternate font paths, partial imports, palette-only imports, replacement preservation and exact missing-file reporting. The 1.0.3 validator is run against the same partial fixture and reproduces the reported incomplete-font error.

The partial bundle is reconstructed with NativeData and decoded with the native archive reader. Both actual campaign menu classes then select its imported palette and all five menu fonts, without fallback. Menu recovery regression checks and signed release/lint/package checks are also run.

These are host tests and a release build, not a physical-device test. The tester's actual archive was not supplied. Native libraries and bundled game metadata are unchanged; no game assets or signing secrets are distributed. No GitHub release was published.
