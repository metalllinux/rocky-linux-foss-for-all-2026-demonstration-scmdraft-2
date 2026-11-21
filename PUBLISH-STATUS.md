# PUBLISH STATUS

What dispatch `D2` actually published into this repository on 2026-11-21, and what it did not publish. Written so the operator can check this repository against the task record without reading the planning docs first. `MANIFEST.md` lists every file here with its size and SHA-256. This is a re-publication, the repository previously held the interim record dispatch `D0` pushed at commit `3da0937`, and `D2` replaces the interim `i-love-korea` content with the accepted build set.

This repository was renamed by the operator between dispatches `D0` and `D2`. It is `metalllinux/rocky-linux-foss-for-all-2026-demonstration-scmdraft-2`, and `metalllinux/foss-for-all-booth-demonstration-scmdraft-2` is the same repository under its former name, not a second repo. Evidence, both API paths carry repository id `1455994123`, and the old path answers `301 Moved Permanently` pointing at `https://api.github.com/repositories/1455994123` while the new path answers `200` with the repository JSON. This dispatch used the new name for every API call.

## Copied

| category | repo path | files | bytes | what it is |
|---|---|---|---|---|
| repository root documents | `./` | 3 | 251154 | The root documents as they stood when this table was generated, `DEMO-LOG.md` copied from the team repository, `LICENSE` and `README.md` from the initial commit, `PUBLISH-STATUS.md` and `MANIFEST.md` written by this same dispatch after the table is generated and both listed in `MANIFEST.md`. |
| booth artifacts | `booth-artifacts/` | 64 | 588258 | Accepted-set overview-thumbnail map bodies and their 64 px and 32 px booth downscales, plus the mask renders named by the gate record. |
| artifact provenance set | `booth-artifacts/f2-recut/` | 5 | 9706 | The `F2` verification set, three re-cuts proven byte-identical to the accepted `i-love-korea` booth artifacts and two inpaint controls that quantify viewport-indicator overlay influence. |
| superseded booth artifacts | `booth-artifacts/superseded/` | 4 | 16579 | The four `M7`-era `i-love-korea` artifacts, moved out of the accepted set in `D2` with their names unchanged because `F2` measured that they belong to the superseded single-row build, not the accepted two-line build. |
| calibration renders | `calibration/` | 13 | 1146512 | Tileset tone calibration renders the terrain-pair choice was made from. |
| editor capture sets | `captures/` | 170 | 31529155 | Editor captures, 100 percent and 25 percent zoom, minimap and title-bar crops, re-open pairs, jump frames, and the reading aids the independent reads produced. |
| map and mask code and the letterform renderer | `code/` | 90 | 474549 | This task's own Python, C and shell source, map writers, mask builders, the parameterized glyph renderer, measurement scripts, capture drivers, and the staging and report scripts that produced `D0` and `D2`. |
| gate reports | `gate-reports/` | 12 | 115011 | Machine-readable gate reports, one per map plus the live-segment, rebuild, and `F2` artifact-verification reports. |
| live-segment captures | `live-segment/captures/` | 207 | 127499630 | Before and after pairs of the same view, status-bar crops for each layer switch, pan and re-open frames, and every capture from the recorded attempts `L1` to `L5`. |
| replayable live-segment command lists | `live-segment/commands/` | 4 | 7337 | The exact injected scancode and click lists the visible construction segment was driven with, in the order that reproduces it. |
| live-segment maps | `live-segment/maps/` | 3 | 1241626 | The flat Ice World seed the live segment was painted on, its painted pair, and the editor-saved file that closed the era 6 save blocker in dispatch `L5`. |
| six deliverable maps | `maps/deliverable/` | 6 | 3687364 | The six booth maps, each re-verified against the SHA-256 value the task record carries before it was copied. `i-love-korea.scm` at `16fe455d46fd...` is the accepted two-line build as ruled by `M10`, replacing the superseded single-row `82589b4205f5...` build that `D0` published at this name. |
| superseded builds | `maps/superseded/` | 4 | 2458255 | The four superseded builds kept at their ratified prefixed names, so a reader can open the file a `## Status` entry names. The two `i-love-korea` superseded files differ from each other in kind, see the named statement below this table. |
| montages | `montages/` | 10 | 2533807 | Before-and-after and step montages assembled by the review dispatches. |
| measurement transcripts | `notes/` | 6 | 46793 | Measurement transcripts named by the gate record. |
| planning docs | `planning/` | 3 | 803927 | The planning docs for TASK-0041, TASK-0042 and TASK-0043, copied verbatim from the team repository as of the commit named below. |

Named items, because the brief names them.

| item | repo path | bytes | status |
|---|---|---|---|
| DEMO-LOG.md | `DEMO-LOG.md` | 249962 | Copied from the team repository `metalllinux/team-chaotix-MoE` at commit `ba5af6b`. It ends at the `D2` staging entry, because the entry describing this push cannot be written into a commit that has not happened yet. The team repository carries the push entry. |
| six deliverable maps | `maps/deliverable/` | 3687364 | Re-verified with `sha256sum` against the recorded values before the copy, all six byte-exact, `i-love-korea` at the accepted `16fe455d46fd...` value. |
| four superseded builds | `maps/superseded/` | 2458255 | Re-verified with `sha256sum` against the recorded values before the copy. See the naming statement below. |
| three planning docs | `planning/` | 803927 | Copied verbatim from the team repository at commit `ba5af6b`. |
| replayable live-segment command lists | `live-segment/commands/` | 7337 | `live-demo-commands.txt`, `live-demo-commands-l3.txt`, `live-demo-commands-l4.txt`, `paint_cmds.txt`. The scancode lists the segment was driven with. |
| existing repo content | `LICENSE`, `README.md` | 1192 | Untouched by `D0` and by `D2`. The `README.md` prose is `D1`'s to rewrite. Repository visibility was not changed. |

## The `i-love-korea` naming, stated because the repo carries three files in this family

| file | sha256 | what it is |
|---|---|---|
| `maps/deliverable/i-love-korea.scm` | `16fe455d46fd88671a98a79f3db65d934400ce0d4edd98f677313e6668d38ba9` | The accepted booth build, two-line layout, 20600 glyph tiles. |
| `maps/superseded/superseded-i-love-korea.scm` | `82589b4205f5deb8ed123273f1c6b5262472806bb90373d6b267c8f27e2319a0` | The `M7` single-row build, 19666 glyph tiles, a different map from the accepted build. Superseded in content, `M8` found its `I`, `O` and `E` strokes fail the 64 px criterion, `M9` rebuilt it, `M10` accepted the rebuild. |
| `maps/superseded/superseded-i-love-korea-2line.scm` | `e7ad27b2f4e7c6d12771b410edd289821fe438d7e4f2bc62caacb40a0b63efab` | A name-superseded duplicate of the accepted build, not a third design. `F2` decoded the containers and found its `MTXM` identical cell for cell to the accepted build, 20600 glyph tiles at values 64 and 192, and the entire 6-byte size difference is the internal `STR` map-name field reading 19 characters for `i-love-korea-2line` against 13 for `i-love-korea`. |

So the two superseded `i-love-korea` files are superseded in different senses, the plain-prefixed one in
content and the `-2line` one in name only. A reader who opens all three is looking at two designs, not
three. The measurement is in `gate-reports/f2_artifact_check.json` and in `## Implementation` dispatch
`F2` of `planning/TASK-0042-foss-for-all-scmdraft2-demo.md`.

## The `i-love-korea` booth artifacts, source capture named per the `F2` ruling

The accepted booth artifacts are `booth-artifacts/i-love-korea-2line-thumbnail128.png`,
`i-love-korea-2line-booth64.png` and `i-love-korea-2line-booth32.png`. `F2` re-cut them independently
from the body crop (18,112)-(146,240) of `m9-open.png`, the 100 percent capture, at single-step Lanczos
0.5 and 0.25 and found its re-cuts byte-identical to the published files, 0 px differing and 0 maximum
channel delta. The re-cuts and the inpaint controls land together in `booth-artifacts/f2-recut/` as that
verification run. The source-capture ruling is `F2`'s, artifacts are cut from the 100 percent captures
only, because the viewport-indicator overlay census in `gate-reports/f2_artifact_check.json` counts 33
overlay pixels on glyph cells in `captures/m9-zoom25.png` and 102 in `captures/m9-jump.png` against 0 in
`captures/m9-open.png` and `captures/m9-reopen.png`. The four files in `booth-artifacts/superseded/`
(`i-love-korea-mm.png`, `i-love-korea-mm-2x.png`, `i-love-korea-booth32.png`, `i-love-korea-booth64.png`)
were published in the accepted `booth-artifacts/` directory by `D0` and move here in `D2`. `F2` measured
`i-love-korea-mm.png` byte-identical to the same crop of `m7-open.png` and `i-love-korea-booth64.png` an
exact Lanczos 0.5 of it, so they belong to the superseded `M7` single-row build.

## Classification deltas this dispatch added, and the rules it re-applied unchanged

`D2` re-ran `D0`'s staging over the controller working directory with `D0`'s classification rules imported unchanged, `d0_stage.py`, and five named deltas, recorded in `d2_stage.py`. 1, the two superseded `i-love-korea` builds land in `maps/superseded/`. 2, the four `M7`-era `i-love-korea` booth artifacts move to `booth-artifacts/superseded/`. 3, the `F2` re-cut and control images land as a set in `booth-artifacts/f2-recut/`. 4, `f2_artifact_check.json` and `f2_control.json` land in `gate-reports/`. 5, `i-love-korea-2line-thumbnail128.png` is classified with the booth artifacts rather than the captures. Every `D0` hard exclusion, shipped game data, harvested reference CHKs, all `.chk` and `.scx` intermediates including the team's own, upstream library and dataset copies, compiled binaries, ISOs and disk images, and the credential scratch file, is re-applied unchanged and no delta overrides one. New files that `D0` staged before they existed, the `M9` capture set, the accepted `i-love-korea` artifacts and report, the `M9` and `F2` scripts, land under the same rules that landed their `M7` counterparts.

## Not copied

Each row is a category that existed in the controller working directory `/tmp/opencode/t0042` and was not published. The last five rows are categories the brief excluded that had no representative in the staging directory, recorded so a reader does not assume a copy exists elsewhere. The reasons are AGENTS.md section 4 and section 9 and this task's own position that shipped game data is not this team's authorship. They are `D0`'s exclusion reasons, re-applied unchanged.

| category | files withheld | bytes withheld | reason |
|---|---|---|---|
| build-artifact | 17 | 255717 | `__pycache__` bytecode caches. |
| build-log-or-probe | 66 | 5533392 | Build, launch and error logs, and the bulk per-row tileset probe captures from the calibration stage, superseded by the calibration renders that landed. |
| chk-or-scx-intermediate | 68 | 18517724 | CHK and SCX intermediates. Every `.scm` that landed is the MPQ container holding the same map data, and each `.chk` here is either an extract of a shipped Blizzard map or a decompressed copy of a `.scm` that landed. |
| compiled-binary | 4 | 1342056 | ELF binaries the team built on the controller from the C sources that landed, `chkdump`, `mkmpq`, `rdp-input`, `rdp-shot`. Build artifacts, machine-specific, reproducible from the sources in `code/`. |
| credential | 1 | 79 | A scratch argument file for the team's own RDP input injector holding a live target credential in plaintext. Never published. Reported to the operator for rotation. Its value appears in no commit, no landed file, and no document in either repository. |
| harvested-reference-chks | 170 | 43258081 | Reference CHK sections harvested from Blizzard-published maps under `ts-harvest/`. Extracts of a Blizzard map, not this team's authorship. |
| probe-map | 38 | 2787866 | Throwaway calibration, tileset-probe and save-path-probe maps. Superseded by the calibration renders and gate reports that landed, and several of them are seeded from a shipped StarCraft map. |
| raw-desktop-capture | 1 | 6220817 | Uncompressed PPM desktop sanity captures from the earliest control stage, superseded by the PNG capture sets that landed. |
| shipped-starcraft-data | 4 | 352574 | Copy of shipped StarCraft map data. `base-map.scx` is Blizzard's stock Brood War map, `maps/rc.scm` is the shipped map `(2)River Crossing.scm`, and `live-seed.scm` is byte-identical to `maps/rc.scm` by `sha256sum`, so it is a copy of a shipped map rather than this team's authorship. |
| transient-note | 4 | 174819 | One-off scratch notes and partial hash lists superseded by `DEMO-LOG.md` and `MANIFEST.md`. |
| undocumented-binary | 1 | 3855 | `colorbase.bin`, an opaque intermediate whose generating script no longer exists on the controller, so its provenance cannot be stated honestly. |
| upstream-code | 3 | 21924 | `starcraft_mpq_io.py` and the `richchk` fragments, imported from upstream projects. Not this team's authorship, licence not yet ruled by `Charmy` and `Flicky`. |
| upstream-dataset | 5 | 17214092 | Natural Earth GeoJSON downloaded from `nvkelso/natural-earth-vector` at tag `v5.1.2`. Upstream data declared public domain upstream. Re-publishing 17 MB of it verbatim is outside this dispatch's include list; the landed record names the repo, tag, commit `f1890d9f`, and the git blob SHA-1 of each file, which is enough to fetch and verify the same bytes. |
| upstream-library | 905 | 8130862 | StormLib checkout, an upstream third-party library (MIT). Not this team's authorship and not in this dispatch's include list; its licence is ruled by `R4` and `R5`, and the build command that produces the tool this task used is recorded in `DEMO-LOG.md`. |
| iso-or-image | 0 | 0 | Excluded by the brief and absent from the controller. `find /tmp/opencode/t0042 -maxdepth 2 \( -iname '*.iso' -o -iname '*.img' \)` returns nothing, so the category is empty rather than removed. The StarCraft installer ISO the 2026-11-13 provenance question refers to is on the target, not here. |
| scmdraft-or-wine-binary-or-prefix | 0 | 0 | Excluded by the brief and absent from the controller. SCMDraft 2 lives at `~/scmdraft2` on the target and its Wine prefix at `~/.wine-scmdraft` on the target, never under `/tmp/opencode/t0042`, so no copy of either existed to publish. |
| game-data-mpq-unit-sprite-assets | 0 | 0 | Not present in the staging directory and not this team's authorship. The `.scm` maps that landed store terrain identifiers and contain no tile, unit or sprite graphics. |
| booth-geometry-captures | 0 | 0 | The single capture dispatch `B1` measured the booth panel geometry from, `b1-editor.png`, no longer exists on the controller because `B1`'s own brief required the exact inverse of every capture it created and `B1` removed it after measuring. `B1`'s measurements, panel identity, millimetres per pixel, pixels and millimetres per tile in both views, and the angular subtence table, are published in `planning/TASK-0042-foss-for-all-scmdraft2-demo.md`. `0` files withheld because none existed to withhold. |
| shadow-independent-read-scripts-and-reading-aids | 0 | 0 | The independent reader's scripts and reading aids live under `/tmp/opencode/shadow-t0042`, outside the staging directory `/tmp/opencode/t0042` that `D0` classified and `D2` re-classified, so neither dispatch copied any file from that directory, including the `M10` reading aids and scripts named in the `## Review` verdict. Aids a dispatch placed inside `/tmp/opencode/t0042` itself, for example the `m7-read-` and `m5-read-` renders, landed with the capture sets. `0` files withheld from the staging directory. |

## What this publish does not claim

The captures and booth artifacts that landed are downscaled renders of Blizzard tileset tones, and the `.scm` maps name game data they do not contain. This repository is private today, so publishing them is not distribution to the public. Making it public is the operator's action, and the recorded position in `## Status` is that it should wait for the licence rulings `R4` and `R5`, `Charmy`'s and `Flicky`'s reads on the Natural Earth derived Korea mask, the StormLib and richchk imports, and the StarCraft data provenance question opened on 2026-11-13. Dispatch `D2` changed no visibility setting and made no licence ruling.

Nothing in this repository was measured or re-verified by `D2` beyond file hashes and the container decodes carried in `gate-reports/`. The gate numbers are the numbers the dispatches that produced them recorded, and the legibility verdicts are `Shadow`'s in the `## Review` section of `planning/TASK-0042-foss-for-all-scmdraft2-demo.md`. As of this publish `i-love-korea` is booth-accepted in its two-line form, per the `M10` verdict of 2026-11-21 20:00, the accepted booth set is `foss-for-all`, `rocky-logo`, `rocky-with-heart`, `tux`, `republic-of-korea` and `i-love-korea`, and the `M8` rejection applies to the superseded single-row build. The zoom floor `M10` measured, 8.00 px per tile, supersedes the fit-to-line figures earlier `## Status` entries derived.

No map in this repository has been validated by SCMDraft 2's own map-validation dialog, no map has been loaded in StarCraft, and no blind reader has identified any map. Those limits are recorded in the planning docs and are not closed by publishing their artifacts.

Push result, the remote commit hash, and the categories `D2` did not copy are recorded in `DEMO-LOG.md` and `## Implementation` of `planning/docs/TASK-0042-foss-for-all-scmdraft2-demo.md` in the team repository, because they cannot be written into a commit that has not happened yet.
