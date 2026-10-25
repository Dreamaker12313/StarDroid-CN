# OpenSnowstorm comparison

Reviewed 26 October 2026 against StarDroid 1.0.9, commit `8c2328dc55b732133751a1b86f0491bfbccc93a4`.

The requested [lofcz/OpenSnowstorm---Brood-War](https://github.com/lofcz/OpenSnowstorm---Brood-War) fork was inspected at commit [`d67171711a063b28602c4dfdc3e3a7389c1c7f4d`](https://github.com/lofcz/OpenSnowstorm---Brood-War/tree/d67171711a063b28602c4dfdc3e3a7389c1c7f4d). This is a source review, not a playthrough or certification of its README's feature claims. No OpenSnowstorm implementation was copied into StarDroid by this review.

## Most useful candidates

| Candidate | What is actually implemented there | Value for StarDroid | Integration approach |
| --- | --- | --- | --- |
| Replay viewing and seeking | The launcher finds `.rep` files; replay mode loads them and uses saved simulation snapshots to seek backwards or forwards. | A player-facing replay viewer would help inspect battles and reproduce bug reports. StarDroid already has replay recording/export code, so the gap is playback and its UI. | Adapt the session and seek design to StarDroid's existing engine, native save state, and Android file picker; do not replace its renderer or input layer. Bound snapshot memory and test version compatibility. |
| Reusable replay regression commands | `--validate-replay`, `--record-hashes`, and `--verify-hashes` validate command streams and compare simulation checkpoints. A Python runner pairs replays with hash files. | StarDroid already tests deterministic saves and multiplayer hashes, but a common replay-based regression runner would make user reproductions easier to retain and rerun. | Build on StarDroid's existing hashes and simulation tests. Reject an empty fixture suite instead of reporting success; regenerate baselines only for intentional simulation changes. |
| Frame-time percentiles | `perf_metrics.h` maintains a rolling timing window and computes percentiles. | StarDroid reports average and worst frame times. A p95/p99 measurement would distinguish frequent stutters from a single slow frame. | Use a small bounded window around actual simulation/render work, leaving simulation state unchanged. No SDL dependency is needed. |
| Configurable physical-key hotkeys | `client_settings.h` persists action hotkeys; `ui.h` applies them to keyboard commands. | Useful for players with Bluetooth keyboards, in addition to the gamepad settings requested separately. | Reuse the idea of action-to-binding preferences through Android `KeyEvent` handling. The SDL event handler itself is not reusable directly. |

Source locations:

- [Replay launcher, snapshot seeking, and validation/hash commands](https://github.com/lofcz/OpenSnowstorm---Brood-War/blob/d67171711a063b28602c4dfdc3e3a7389c1c7f4d/ui/gfxtest.cpp): `load_replay_session`, `save_replay_state_if_missing`, `compute_replay_checkpoint_hash`, `run_validate_replay`, `run_record_hashes`, and `run_verify_hashes`.
- [Regression runner](https://github.com/lofcz/OpenSnowstorm---Brood-War/blob/d67171711a063b28602c4dfdc3e3a7389c1c7f4d/scripts/regression_check.py): it exits successfully when there are no replays and skips replays without hash files. Those cases should not count as validation in a port.
- [Timing helper](https://github.com/lofcz/OpenSnowstorm---Brood-War/blob/d67171711a063b28602c4dfdc3e3a7389c1c7f4d/perf_metrics.h): `basic_frame_timer` and `percentile_us`.
- [Persisted hotkeys](https://github.com/lofcz/OpenSnowstorm---Brood-War/blob/d67171711a063b28602c4dfdc3e3a7389c1c7f4d/ui/client_settings.h) and [keyboard dispatch](https://github.com/lofcz/OpenSnowstorm---Brood-War/blob/d67171711a063b28602c4dfdc3e3a7389c1c7f4d/ui/ui.h).

## It does not solve these current reports

**Original PC saves:** its implemented persistent save format is `.osv`, identified by its own `OSV_MAGIC` and version 10. [The serializer](https://github.com/lofcz/OpenSnowstorm---Brood-War/blob/d67171711a063b28602c4dfdc3e3a7389c1c7f4d/serialization.h) writes native struct representations and translates selected pointers to indices. It does not decode classic StarCraft `.sng` or Brood War `.snx` files, and is not compatible with StarDroid's portable save schema. Its README still says saves are in-memory only, which does not match the inspected implementation.

**Carrier, Interceptor, and Scarab AI:** its [AI interpreter](https://github.com/lofcz/OpenSnowstorm---Brood-War/blob/d67171711a063b28602c4dfdc3e3a7389c1c7f4d/ai.h) skips the operands of build, tech, upgrade, and several attack-planning operations without implementing them. The train callback delegates to selected-unit action handling. No complete production planner or ammunition replenishment policy was found. Replacing StarDroid's AI with this would lose functionality.

**Gamepad controls:** no gamepad/joystick input dispatch was found in its application sources. Vendored SDL support for controllers is not an implemented game-control scheme.

**Invincibility:** the [damage hook](https://github.com/lofcz/OpenSnowstorm---Brood-War/blob/d67171711a063b28602c4dfdc3e3a7389c1c7f4d/bwgame_combat.h) checks `owner < 8`, which includes ordinary computer opponents as well as the player. It also runs after shield/matrix damage in the weapon path. This is not a suitable implementation to copy for a player-only invincibility option.

## Maintainability and reuse

The split into state, combat, triggers, creep, and other headers is a useful organization example. StarDroid's engine is reconstructed from a pinned upstream archive and an ordered patch stack, however, so replacing those files wholesale would discard Android fixes, campaign compatibility, save handling, and multiplayer changes. Small reviewed adaptations are preferable to changing engine forks.

The fork includes an [LGPL version 3 license](https://github.com/lofcz/OpenSnowstorm---Brood-War/blob/d67171711a063b28602c4dfdc3e3a7389c1c7f4d/LICENSE). Any future copied code needs its exact provenance, notices, and applicable source/relinking requirements retained. That file should not be treated as resolving the licensing history of all inherited OpenBW code; StarDroid records that history separately in [THIRD_PARTY.md](../THIRD_PARTY.md).

The highest-value follow-up is a bounded replay viewer plus a replay regression runner. Frame-time percentiles are a smaller diagnostic improvement. None of these requires replacing StarDroid's engine or importing another project's desktop UI.
