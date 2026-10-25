# Cache and save transfer changes (build 80)

## Why Android could show almost 4 GB of cache

`NativeData.prepare` previously reconstructed every imported content ZIP with the original CD archive's offsets and total length. Seven interface/music/story/movie MPQs therefore had roughly 3.52 GB of apparent file length, even though each contained only its selected files. The active campaign map added another approximately 500 MB logical archive. These files were sparse on supporting filesystems: their apparent length was not necessarily their physically allocated storage.

The new preparation writes selected packed blocks consecutively and rebuilds the MPQ header/tables. Offset-based (`FIX_KEY`) encryption is rekeyed per sector; compression and decoded asset bytes remain unchanged. The `compact80` stamp rebuilds existing caches automatically when starting the menu. New imports use the same path. The original imported bundles and save slots are untouched.

Compaction alone would bring those seven caches to approximately 838 MB. The final implementation also stops retaining duplicate cinematic archives. Movies are listed from their imported ZIP and prepared one at a time only when played. Once the decoder opens a movie, it owns its frame/audio data; the native archive slot is closed and the temporary MPQ and stamp are deleted immediately. Old full-movie caches are removed after their archive slots are closed when the menu opens.

With the supplied original archives, the **five retained content caches total 235,474,238 bytes (about 235 MB / 225 MiB)**. An active mission and the bounded nearby-map cache are additional. The largest tested temporary movie is 78,663,684 bytes (about 79 MB), present only while the decoder opens it; no persistent movie cache remains. Exact size depends on imported content. Imported game/movie bundles and save files remain intact.

This moves a little disk preparation from app startup to the moment a cinematic begins. Music remains cached to avoid adding ZIP extraction work during in-game track changes. Movie compression, video quality, sound, and the decoder's memory use are unchanged; no media is deleted from the import or transcoded.

| Content | Previous logical bytes | Retained cache bytes |
| --- | ---: | ---: |
| StarCraft music | 506,995,955 | 103,769,783 |
| StarCraft story | 506,995,955 | 1,252,032 |
| StarCraft movies | 506,995,955 | 0 |
| StarCraft campaign interface | 506,995,955 | 74,411 |
| Brood War music | 495,683,706 | 127,678,871 |
| Brood War story | 495,683,706 | 2,699,141 |
| Brood War movies | 495,683,706 | 0 |

Brood War's alternative campaign interface was separately checked (94,827 compact bytes). Only one interface bundle slot is opened by the app; the two interface entries are not both counted in the seven-slot total.

At the first Activity start in a process, `NativeCache.beginSession` removes only recognized abandoned map/save import/export files and unfinished MPQ preparations and an abandoned single-movie staging file in the private cache. It runs once per process to avoid deleting live work during an Activity recreation. It does not touch imported MPQs, installed map packs, settings, or save slots. Missing source bundles also remove their obsolete prepared slot/stamp when archives are reopened.

## Save transfer

App Options can import/export a single-player StarDroid `.obwsave` through Android's document picker, including a backup copied from a PC. Import validates the ZIP entries, manifest, state/map SHA-256, native state magic/schema, native checksum, and reconstructed MPQ bounds before atomically replacing the chosen slot. Corrupt or unsupported input leaves that slot unchanged. Legacy sparse-map saves remain supported.

This is portable StarDroid save transfer, not a converter for original Blizzard PC `.sng` / `.snx` saves. Those formats are rejected with a specific explanation. See [PC-SAVE-COMPATIBILITY.md](PC-SAVE-COMPATIBILITY.md).

## Validation

`python3 tests/run_storage80.py --data-dir /path/to/owned/archives`

`python3 tests/run_cinematic_cache80.py --data-dir /path/to/owned/archives`

- Java production-method tests cover cache migration and rollback, save export/import, legacy sparse maps, damaged state/map data, unsupported versions/engines, original-PC-save rejection, slot preservation, and temporary-file cleanup.
- An independent native MPQ reader compares 269 original music/story/movie/interface/font and mission assets byte-for-byte after compaction, including the full Wasteland and Reign of Fire import lists. Those two mission caches shrink to 1,172,744 and 3,367,966 bytes respectively.
- Synthetic raw, encrypted, offset-encrypted, sector-table, checksum-table, padded-tail, and whole-file cases verify the rekeying path, including a cipher stream longer than its 64 KiB buffer.
- The cinematic test exercises the production archive-loading/playback lifecycle and compares all 17 supplied movies against original-archive playback after the temporary MPQ has been closed and deleted, including decoded audio, representative video frames, rewind, and end of playback. See `validation/cinematic-cache80.json` for results and any baseline decoder warnings.
- Baseline limitations remain visible in the report: the original StarCraft introduction logs one libsmacker palette-overflow warning; rewinding the UED and Zerg Brood War endings produces a different initial palette/frame than their first opening. Both baseline and new cache path have identical results. This change does not claim to fix those existing decoder behaviors.
- Original data is used locally and is not included in the repository or APK. These are host checks, not a physical Android storage measurement.
