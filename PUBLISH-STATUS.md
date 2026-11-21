# PUBLISH STATUS

What dispatch `D0` actually published into this repository on 2026-11-21, and what it did not publish. Written so the operator can check this repository against the task record without reading the planning docs first. `MANIFEST.md` lists every file here with its size and SHA-256.

## Copied

| category | repo path | files | bytes | what it is |
|---|---|---|---|---|
| repository root documents | `./` | 3 | 221739 | The three root files that existed when this table was generated, `DEMO-LOG.md` copied from the team repository, `LICENSE` and `README.md` from the initial commit. `PUBLISH-STATUS.md` and `MANIFEST.md` are written by this same dispatch after the table is generated, and both are listed in `MANIFEST.md`. |
| booth artifacts | `booth-artifacts/` | 65 | 599518 | Overview-thumbnail map bodies and their 64 px and 32 px booth downscales, plus the mask renders named by the gate record. |
| calibration renders | `calibration/` | 13 | 1146512 | Tileset tone calibration renders the terrain-pair choice was made from. |
| editor capture sets for the six maps | `captures/` | 166 | 31205572 | Editor captures, 100 percent and 25 percent zoom, minimap and title-bar crops, re-open pairs, jump frames, and the reading aids the independent reads produced. |
| map and mask code and the letterform renderer | `code/` | 81 | 385716 | This task's own Python, C and shell source, map writers, mask builders, the parameterized glyph renderer, measurement scripts, capture drivers. |
| gate reports | `gate-reports/` | 9 | 80872 | Machine-readable gate reports, one per map plus the live-segment and rebuild reports. |
| live-segment captures | `live-segment/captures/` | 207 | 127499630 | Before and after pairs of the same view, status-bar crops for each layer switch, pan and re-open frames, and every capture from the recorded attempts `L1` to `L5`. |
| replayable live-segment command lists | `live-segment/commands/` | 4 | 7337 | The exact injected scancode and click lists the visible construction segment was driven with, in the order that reproduces it. |
| live-segment maps | `live-segment/maps/` | 3 | 1241626 | The flat Ice World seed the live segment was painted on, its painted pair, and the editor-saved file that closed the era 6 save blocker in dispatch `L5`. |
| six deliverable maps | `maps/deliverable/` | 6 | 3687364 | The six booth maps, each re-verified against the SHA-256 value the task record carries before it was copied. |
| superseded builds | `maps/superseded/` | 2 | 1229127 | The two superseded builds kept at their ratified prefixed names, so a reader can open the file a `## Status` entry names. |
| montages | `montages/` | 10 | 2533807 | Before-and-after and step montages assembled by the review dispatches. |
| measurement transcripts | `notes/` | 6 | 46793 | Measurement transcripts named by the gate record. |
| planning docs | `planning/` | 3 | 705067 | The planning docs for TASK-0041, TASK-0042 and TASK-0043, copied verbatim. |

Named items, because the brief names them.

| item | repo path | bytes | status |
|---|---|---|---|
| DEMO-LOG.md | `DEMO-LOG.md` | 220547 | Copied from the team repository `metalllinux/team-chaotix-MoE` at commit `2b29d7e`. It ends at the `D0` staging entry dated 2026-11-21 17:50, because the entry describing this push cannot be written into a commit that has not happened yet. The team repository carries the push entry. |
| six deliverable maps | `maps/deliverable/` | 3687364 | Re-verified with `sha256sum` against the recorded values before the copy, all six byte-exact. |
| three planning docs | `planning/` | 705067 | Copied verbatim from the team repository at commit `2b29d7e`. |
| replayable live-segment command lists | `live-segment/commands/` | 7337 | `live-demo-commands.txt`, `live-demo-commands-l3.txt`, `live-demo-commands-l4.txt`, `paint_cmds.txt`. The scancode lists the segment was driven with. |
| existing repo content | `LICENSE`, `README.md` | 1192 | Untouched. The `README.md` prose is `D1`'s to rewrite. Repository visibility was not changed. |

## Not copied

Each row is a category that existed in the controller working directory `/tmp/opencode/t0042` and was not published. The last three rows are categories the brief excluded that had no representative on the controller, recorded so a reader does not assume a copy exists elsewhere. The reasons are AGENTS.md section 4 and section 9 and this task's own position that shipped game data is not this team's authorship.

| category | files withheld | bytes withheld | reason |
|---|---|---|---|
| build-artifact | 15 | 239923 | `__pycache__` bytecode caches. |
| build-log-or-probe | 66 | 5533392 | Build, launch and error logs, and the bulk per-row tileset probe captures from the calibration stage, superseded by the calibration renders that landed. |
| chk-or-scx-intermediate | 62 | 14832452 | CHK and SCX intermediates. Every `.scm` that landed is the MPQ container holding the same map data, and each `.chk` here is either an extract of a shipped Blizzard map or a decompressed copy of a `.scm` that landed. |
| compiled-binary | 4 | 1342056 | ELF binaries the team built on the controller from the C sources that landed, `chkdump`, `mkmpq`, `rdp-input`, `rdp-shot`. Build artifacts, machine-specific, reproducible from the sources in `code/`. |
| credential | 1 | 79 | A scratch argument file for the team's own RDP input injector holding a live target credential in plaintext. Never published. Reported to the operator for rotation. Its value appears in no commit, no landed file, and no document in either repository. |
| harvested-reference-chks | 170 | 43258081 | Reference CHK sections harvested from Blizzard-published maps under `ts-harvest/`. Extracts of a Blizzard map, not this team's authorship. |
| probe-map | 38 | 2787866 | Throwaway calibration, tileset-probe and save-path-probe maps. Superseded by the calibration renders and gate reports that landed, and several of them are seeded from a shipped StarCraft map. |
| raw-desktop-capture | 1 | 6220817 | Uncompressed PPM desktop sanity captures from the earliest control stage, superseded by the PNG capture sets that landed. |
| shipped-starcraft-data | 4 | 352574 | Copy of shipped StarCraft map data. `base-map.scx` is Blizzard's stock Brood War map, `maps/rc.scm` is the shipped map `(2)River Crossing.scm`, and `live-seed.scm` is byte-identical to `maps/rc.scm` by `sha256sum`, so it is a copy of a shipped map rather than this team's authorship. |
| transient-note | 4 | 174769 | One-off scratch notes and partial hash lists superseded by `DEMO-LOG.md` and `MANIFEST.md`. |
| undocumented-binary | 1 | 3855 | `colorbase.bin`, an opaque intermediate whose generating script no longer exists on the controller, so its provenance cannot be stated honestly. |
| upstream-code | 3 | 21924 | `starcraft_mpq_io.py` and the `richchk` fragments, imported from upstream projects. Not this team's authorship, licence not yet ruled by `Charmy` and `Flicky`. |
| upstream-dataset | 5 | 17214092 | Natural Earth GeoJSON downloaded from `nvkelso/natural-earth-vector` at tag `v5.1.2`. Upstream data declared public domain upstream. Re-publishing 17 MB of it verbatim is outside this dispatch's include list; the landed record names the repo, tag, commit `f1890d9f`, and the git blob SHA-1 of each file, which is enough to fetch and verify the same bytes. |
| upstream-library | 905 | 8130862 | StormLib checkout, an upstream third-party library (MIT). Not this team's authorship and not in this dispatch's include list; its licence is ruled by `R4` and `R5`, and the build command that produces the tool this task used is recorded in `DEMO-LOG.md`. |
| iso-or-image | 0 | 0 | Excluded by the brief and absent from the controller. `find /tmp/opencode/t0042 -maxdepth 2 \( -iname '*.iso' -o -iname '*.img' \)` returns nothing, so the category is empty rather than removed. The StarCraft installer ISO the 2026-11-13 provenance question refers to is on the target, not here. |
| scmdraft-or-wine-binary-or-prefix | 0 | 0 | Excluded by the brief and absent from the controller. SCMDraft 2 lives at `~/scmdraft2` on the target and its Wine prefix at `~/.wine-scmdraft` on the target, never under `/tmp/opencode/t0042`, so no copy of either existed to publish. |
| game-data-mpq-unit-sprite-assets | 0 | 0 | Not present in the staging directory and not this team's authorship. The `.scm` maps that landed store terrain identifiers and contain no tile, unit or sprite graphics. |

## What this publish does not claim

The captures and booth artifacts that landed are downscaled renders of Blizzard tileset tones, and the `.scm` maps name game data they do not contain. This repository is private today, so publishing them is not distribution to the public. Making it public is the operator's action, and the recorded position in `## Status` is that it should wait for the licence rulings `R4` and `R5`, `Charmy`'s and `Flicky`'s reads on the Natural Earth derived Korea mask, the StormLib and richchk imports, and the StarCraft data provenance question opened on 2026-11-13. Dispatch `D0` changed no visibility setting and made no licence ruling.

Nothing in this repository was measured or re-verified by `D0` beyond file hashes. The gate numbers in `gate-reports/` are the numbers the dispatches that produced them recorded, the legibility verdicts are `Shadow`'s in the `## Review` section of `planning/TASK-0042-foss-for-all-scmdraft2-demo.md`, and `i-love-korea` is **not booth-accepted as shipped**, per the `M8` verdict of 2026-11-21 15:20. The booth set accepted as of this publish is `foss-for-all`, `rocky-logo`, `rocky-with-heart`, `tux` and `republic-of-korea`.

No map in this repository has been validated by SCMDraft 2's own map-validation dialog, no map has been loaded in StarCraft, and no blind reader has identified any map. Those limits are recorded in the planning docs and are not closed by publishing their artifacts.

Push result, the remote commit hash, and the categories `D0` did not copy are recorded in `DEMO-LOG.md` and `## Implementation` of `planning/docs/TASK-0042-foss-for-all-scmdraft2-demo.md` in the team repository, because they cannot be written into a commit that has not happened yet.
