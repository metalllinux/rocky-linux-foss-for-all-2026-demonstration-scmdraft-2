# PUBLISH STATUS

What dispatch `D3` actually published into this repository on 2026-11-22, and what it did not publish. Written so the operator can check this repository against the task record without reading the planning docs first. `MANIFEST.md` lists every file here with its size and SHA-256. This is an addition on top of what dispatch `D2` pushed at commit `39f2119`, the booth runner, its measured run log and cycle reports, the booth-loop captures, and the runbook. No previously published map, artifact, capture, report or document was replaced or moved by `D3`.

This repository was renamed by the operator between dispatches `D0` and `D2`. It is `metalllinux/rocky-linux-foss-for-all-2026-demonstration-scmdraft-2`, and `metalllinux/foss-for-all-booth-demonstration-scmdraft-2` is the same repository under its former name, not a second repo. Evidence, both API paths carry repository id `1455994123`, and the old path answers `301 Moved Permanently` pointing at `https://api.github.com/repositories/1455994123` while the new path answers `200` with the repository JSON. Dispatch `D3` used the new name for every API call and for the clone remote.

## Copied

| category | repo path | files | bytes | what it is |
|---|---|---|---|---|
| repository root documents | `./` | 4 | 289124 | The root documents as they stood when this table was generated, `DEMO-LOG.md` copied from the team repository, `LICENSE` and `README.md` from the initial commit, `BOOTH-RUNBOOK.md` written by dispatch `D3`, and `PUBLISH-STATUS.md` and `MANIFEST.md` written by this same dispatch after the table is generated and both listed in `MANIFEST.md`. |
| booth artifacts | `booth-artifacts/` | 64 | 588258 | Accepted-set overview-thumbnail map bodies and their 64 px and 32 px booth downscales, plus the mask renders named by the gate record. |
| artifact provenance set | `booth-artifacts/f2-recut/` | 5 | 9706 | The `F2` verification set, three re-cuts proven byte-identical to the accepted `i-love-korea` booth artifacts and two inpaint controls that quantify viewport-indicator overlay influence. |
| superseded booth artifacts | `booth-artifacts/superseded/` | 4 | 16579 | The four `M7`-era `i-love-korea` artifacts, moved out of the accepted set in `D2` with their names unchanged because `F2` measured that they belong to the superseded single-row build. |
| the booth loop's measured step log | `booth-loop/` | 1 | 87906 | `s1a-run-log.jsonl`, one timed JSONL record per booth-cycle step as it completed, each carrying its own inverse or its teardown, covering dispatches `S1a` and `S1b`: the three-map partial cycle, the three-map phase, and both full six-map cycles at the 300 s and 150 s windows. Read together with `gate-reports/S1b300_cycle_report.json` and `gate-reports/S1b150_cycle_report.json`, which summarize it. |
| calibration renders | `calibration/` | 13 | 1146512 | Tileset tone calibration renders the terrain-pair choice was made from. |
| editor capture sets | `captures/` | 341 | 57222742 | Editor captures, 100 percent and 25 percent zoom, minimap and title-bar crops, re-open pairs, jump frames, the reading aids the independent reads produced, and from `D3` the booth-loop frame captures of dispatches `S1a` and `S1b`, named by their phase tag (`S1aL1-`, `S1bAL1-`, `S1b300L1-`, `S1b150L1-`), one open frame, one zoom-walk frame and every scripted display frame per map per phase. |
| map and mask code, the booth runner, and the tooling | `code/` | 94 | 542811 | This task's own Python, C and shell source, map writers, mask builders, the parameterized glyph renderer, measurement scripts, capture drivers, the staging and report scripts that produced `D0`, `D2` and `D3`, and the booth loop runner `booth_loop.py`. |
| gate reports | `gate-reports/` | 16 | 121612 | Machine-readable gate reports, one per map plus the live-segment, rebuild, `F2` artifact-verification, and the four booth-cycle cost reports `s1a_cycle_report.json`, `S1bA_cycle_report.json`, `S1b300_cycle_report.json` and `S1b150_cycle_report.json`. |
| live-segment captures | `live-segment/captures/` | 207 | 127499630 | Before and after pairs of the same view, status-bar crops for each layer switch, pan and re-open frames, and every capture from the recorded attempts `L1` to `L5`. |
| replayable live-segment command lists | `live-segment/commands/` | 4 | 7337 | The exact injected scancode and click lists the visible construction segment was driven with, in the order that reproduces it. |
| live-segment maps | `live-segment/maps/` | 3 | 1241626 | The flat Ice World seed the live segment was painted on, its painted pair, and the editor-saved file that closed the era 6 save blocker in dispatch `L5`. |
| six deliverable maps | `maps/deliverable/` | 6 | 3687364 | The six booth maps, each re-verified against the SHA-256 value the task record carries before it was copied. `i-love-korea.scm` at `16fe455d46fd...` is the accepted two-line build as ruled by `M10`. |
| superseded builds | `maps/superseded/` | 4 | 2458255 | The four superseded builds kept at their ratified prefixed names. The two `i-love-korea` superseded files differ from each other in kind, see the named statement below the table. |
| montages | `montages/` | 10 | 2533807 | Before-and-after and step montages assembled by the review dispatches. |
| measurement transcripts | `notes/` | 6 | 46793 | Measurement transcripts named by the gate record. |
| planning docs | `planning/` | 3 | 852944 | The planning docs for TASK-0041, TASK-0042 and TASK-0043, copied verbatim from the team repository as of the commit named below. |

Named items, because the brief names them.

| item | repo path | bytes | status |
|---|---|---|---|
| booth loop runner | `code/booth_loop.py` | 36458 | The runner as it stands after dispatch `S1b`, parameters `--maps`, `--loops`, `--display-seconds` defaulting to 300, `--tag-prefix`, `--paint-only`, `--stability`, `--summary`. Lands under the unchanged `D0` rule that places this task's Python in `code/`. |
| booth runbook | `BOOTH-RUNBOOK.md` | 10472 | The one command that starts a cycle, the per-step table, the per-map SHA-256 table, the measured cycle costs and cycles-that-fit table, and the editor-driven versus programmatic statement. |
| booth step log | `booth-loop/s1a-run-log.jsonl` | 87906 | 279 timed step records from dispatches `S1a` and `S1b`, each appended the moment its step completed, each carrying its inverse or teardown. |
| four cycle cost reports | `gate-reports/` | 6601 | `s1a_cycle_report.json`, `S1bA_cycle_report.json`, `S1b300_cycle_report.json`, `S1b150_cycle_report.json`, the per-map and per-cycle costs the measured figures are taken from. |
| booth-loop captures | `captures/` | 25316382 | 165 frames from the three measured phases and the `S1a` partial cycle, open, zoom-walk, scripted display and painting frames, named by phase tag. |
| DEMO-LOG.md | `DEMO-LOG.md` | 277460 | Copied from the team repository `metalllinux/team-chaotix-MoE` at commit `5f9947d`. It ends at the `D3` staging entry, because the entry describing this push cannot be written into a commit that has not happened yet. The team repository carries the push entry. |
| six deliverable maps | `maps/deliverable/` | 3687364 | Re-verified with `sha256sum` against the recorded values before this copy, all six byte-exact, `i-love-korea` at the accepted `16fe455d46fd...` value. Unchanged from `D2`. |
| four superseded builds | `maps/superseded/` | 2458255 | Re-verified with `sha256sum` against the recorded values. See the naming statement below. |
| three planning docs | `planning/` | 852944 | Copied verbatim from the team repository at commit `5f9947d`. |
| replayable live-segment command lists | `live-segment/commands/` | 7337 | `live-demo-commands.txt`, `live-demo-commands-l3.txt`, `live-demo-commands-l4.txt`, `paint_cmds.txt`. The scancode lists the segment was driven with. |
| existing repo content | `LICENSE`, `README.md` | 1192 | Untouched by `D0`, by `D2` and by `D3`. The `README.md` prose is `D1`'s to rewrite. Repository visibility was not changed. |

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

## The booth cycle, the measured cost, and what is editor-driven

Dispatch `D3` publishes the booth runner and its runbook. The one command that starts a cycle is
`python3 /tmp/opencode/t0042/booth_loop.py --maps
foss-for-all,rocky-logo,rocky-with-heart,tux,republic-of-korea,i-love-korea --loops 1
--display-seconds 300`, and the full runbook, the per-map SHA-256 table, the per-step costs, the
cycles-that-fit table, and the honest separation of what the audience sees the editor do from what
a program builds, are in `BOOTH-RUNBOOK.md` at the repository root.

Measured cycle cost, from dispatch `S1b`, one full six-map cycle per window on the target,
summarized in `gate-reports/S1b300_cycle_report.json` and `gate-reports/S1b150_cycle_report.json`
and reconstructible step by step from `booth-loop/s1a-run-log.jsonl`. At the 300 s display default
a cycle costs 2232.36 s, 37 min 12 s, fitting 1 complete cycle in one hour, 3 in two, 4 in three.
At the 150 s fallback a cycle costs 1331.99 s, 22 min 12 s, fitting 2, 5 and 8. Non-display
overhead holds at 43.86 to 44.46 s per map on all six maps at both windows. An earlier projection
of 2219.5 s is superseded by these measurements, 0.58 percent away.

## Classification deltas this dispatch added, and the rules it re-applied unchanged

`D3` re-ran the staging over the controller working directory with `D0`'s classification rules
imported unchanged from `d0_stage.py`, `D2`'s five deltas imported unchanged from `d2_stage.py`,
and three named `D3` deltas, recorded in `d3_stage.py`. 1, `s1a-run-log.jsonl`, the booth loop's
measured step log, lands in `booth-loop/`; under `D0` and `D2` rules its name fell to the
`transient-note` catch-all, the same catch-all class from which `D2` promoted the superseded
`i-love-korea` builds, and it is not a hard exclusion. 2, `BOOTH-RUNBOOK.md` lands at the repository
root, copied into the clone outside the classify walk exactly as `DEMO-LOG.md`, `LICENSE`,
`README.md` and the three planning docs are, and listed in `MANIFEST.md` like every other file. 3,
a walk-scope exclusion, the scratch directories `s1a-build/` and `s1a-rebuild/` are outside the
classified walk. Their `.chk` files were already held by the hard `chk-or-scx-intermediate` rule,
and their `.scm` files carry the deliverable basenames, so under the unchanged rule they would have
copied byte-identical duplicates of the six published maps into `maps/deliverable/`. Each rebuild
byte-matches its published map at the recorded SHA-256, re-verified before this staging, so the
exclusion loses no content and keeps one copy of each map in the tree. The clone exclusion list
grows by `booth-verify-d3`. A credential scan of every landing file, comparing file bytes against
the four values in `~/AI/secrets/` read at run time and printing nothing of them, ran before any
copy and found none.

Every `D0` hard exclusion is re-applied unchanged and no delta overrides one, shipped game data,
harvested reference CHKs, all `.chk` and `.scx` intermediates including the team's own, upstream
library and dataset copies, compiled binaries, ISOs and disk images, and the credential scratch
file. New files that earlier dispatches staged before they existed, the booth runner, the four
cycle reports, the 165 booth-loop captures, and the `D3` scripts, land under the same rules that
landed their earlier counterparts.

## Not copied

Each row is a category that existed in the classified walk of the controller working directory `/tmp/opencode/t0042` and was not published. The scratch rebuild directories `s1a-build/` and `s1a-rebuild/` are outside that walk by the named `D3` walk-scope delta above, so the 24 files inside them are not counted in any row. The last five rows are categories the brief excluded that had no representative in the staging directory, recorded so a reader does not assume a copy exists elsewhere. The reasons are AGENTS.md section 4 and section 9 and this task's own position that shipped game data is not this team's authorship. They are `D0`'s exclusion reasons, re-applied unchanged.

| category | files withheld | bytes withheld | reason |
|---|---|---|---|
| build-artifact | 20 | 328156 | `__pycache__` bytecode caches. |
| build-log-or-probe | 66 | 5533392 | Build, launch and error logs, and the bulk per-row tileset probe captures from the calibration stage, superseded by the calibration renders that landed. |
| chk-or-scx-intermediate | 68 | 18517724 | CHK and SCX intermediates. Every `.scm` that landed is the MPQ container holding the same map data, and each `.chk` here is either an extract of a shipped Blizzard map or a decompressed copy of a `.scm` that landed. |
| compiled-binary | 4 | 1342056 | ELF binaries the team built on the controller from the C sources that landed, `chkdump`, `mkmpq`, `rdp-input`, `rdp-shot`. Build artifacts, machine-specific, reproducible from the sources in `code/`. |
| credential | 1 | 79 | A scratch argument file for the team's own RDP input injector holding a live target credential in plaintext. Never published. Reported to the operator for rotation. Its value appears in no commit, no landed file, and no document in either repository. |
| harvested-reference-chks | 170 | 43258081 | Reference CHK sections harvested from Blizzard-published maps under `ts-harvest/`. Extracts of a Blizzard map, not this team's authorship. |
| probe-map | 38 | 2787866 | Throwaway calibration, tileset-probe and save-path-probe maps. Superseded by the calibration renders and gate reports that landed, and several of them are seeded from a shipped StarCraft map. |
| raw-desktop-capture | 1 | 6220817 | Uncompressed PPM desktop sanity captures from the earliest control stage, superseded by the PNG capture sets that landed. |
| shipped-starcraft-data | 4 | 352574 | Copy of shipped StarCraft map data. `base-map.scx` is Blizzard's stock Brood War map, `maps/rc.scm` is the shipped map `(2)River Crossing.scm`, and `live-seed.scm` is byte-identical to `maps/rc.scm` by `sha256sum`, so it is a copy of a shipped map rather than this team's authorship. |
| transient-note | 9 | 600914 | One-off scratch notes and partial hash lists superseded by `DEMO-LOG.md` and `MANIFEST.md`. |
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

The captures and booth artifacts that landed are downscaled renders of Blizzard tileset tones, and
the `.scm` maps name game data they do not contain. This repository is private today, so publishing
them is not distribution to the public. Making it public is the operator's action, and the recorded
position in `## Status` is that it should wait for the licence rulings `R4` and `R5`, `Charmy`'s and
`Flicky`'s reads on the Natural Earth derived Korea mask, the StormLib and richchk imports, and the
StarCraft data provenance question opened on 2026-11-13. Dispatch `D3` changed no visibility setting
and made no licence ruling.

The published runner is a record of what runs on the controller, not a standalone program. Its
build step invokes `code/build_ts.py` against `ts-harvest/ref-era6.chk`, a harvested plaintext CHK
extracted from a shipped Blizzard map, and every `.chk` and `.scx` intermediate is withheld from
this repository by the exclusion rules above. The runner also authenticates to the target with a
secrets-directory password that is never published. Every mask, writer and measurement input except
those two is published here, so the cycle is fully readable and its logic fully rebuildable from
this repository, and running it end to end needs the withheld reference CHK and the credentials
locally.

Nothing in this repository was measured or re-verified by `D3` beyond file hashes and the six
deliverable re-hash against the task record. The gate numbers and cycle costs are the numbers the
dispatches that produced them recorded, and the legibility verdicts are `Shadow`'s in the `## Review`
section of `planning/TASK-0042-foss-for-all-scmdraft2-demo.md`. `D3` made no target contact, so the
target-side map hashes remain `S1b`'s claim as recorded at `DEMO-LOG.md` 2026-11-22 09:05. The
booth-loop captures published here are timed cycle frames, and no independent reader has read them;
that belongs to the review chain.

No map in this repository has been validated by SCMDraft 2's own map-validation dialog, no map has
been loaded in StarCraft, and no blind reader has identified any map. Those limits are recorded in
the planning docs and are not closed by publishing their artifacts.

Push result, the remote commit hash, and the categories `D3` did not copy are recorded in
`DEMO-LOG.md` and `## Implementation` of `planning/docs/TASK-0042-foss-for-all-scmdraft2-demo.md`
in the team repository, because they cannot be written into a commit that has not happened yet.
