# Mission export in 0.31

Install the APK over the existing app. Open App Options, tap **Export missions**,
choose Downloads (or another folder), and tap **Save**. Attach the resulting
**OpenBW-Missions.zip** to the project chat. If the button is disabled, import
the campaign archives first. No additional storage permission is required.

The ZIP contains all currently installed catalogued missions, an index of their
titles and SHA-256 values, and a list of missions that are not installed. It
preserves original scenario bytes and MPQ metadata. The scenario includes map
terrain, unit placements, alliances, briefing text and triggers. Voice payloads,
movies, core game archives, saves and settings are excluded. The app performs
no network upload and does not modify the installed mission bundles.

Each `missions/OpenBW-*.zip` uses the existing `openbw-mission-bundle-v1` format
with just the `scenario.chk` entry. These are inspection bundles; keep the full
installed bundles for gameplay. Reconstruct a bundle using
`python scripts/rebuild_mission_mpq.py bundle.zip mission.mpq`, then read the
scenario path in its manifest with an MPQ reader. The reconstructed archive is
sparse and retains original offsets for encrypted entries.

Export builds a complete private temporary ZIP before opening the user's chosen
destination. Corrupt installed missions stop the export with the mission title
in the error. Temporary files are removed on completion or a handled failure.
Cancelling the Android Save dialog leaves installed files untouched. If a storage
provider fails during the final copy, its destination may contain an incomplete
file; the app reports failure and the user can retry.

Validation uses synthetic MPQs and Android instrumentation: all 64 catalog IDs,
original map/table bytes, sparse MPQ reconstruction, omission of voice and
unrelated files, unchanged sources, partial installations, corrupt inputs,
temporary-file cleanup, Save-dialog launch/cancellation, and the activity's
selected-destination write. The destination write fixture uses an app-owned file
URI; individual cloud storage providers and physical devices are not covered.
The native libraries are unchanged from 0.30. Original mission playthroughs
remain pending receipt of the user's exported maps.
