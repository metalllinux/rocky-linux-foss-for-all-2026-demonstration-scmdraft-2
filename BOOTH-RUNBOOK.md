# BOOTH RUNBOOK

How to start the FOSS for All booth cycle with one command, what the cycle does, what it costs,
which maps it shows, and what the audience actually sees the editor do versus what a program
builds. Written by dispatch `D3` on 2026-11-22 from the runner as it stands after dispatch `S1b`
and from the measured cycle costs recorded in `planning/TASK-0042-foss-for-all-scmdraft2-demo.md`.
The measured numbers here come from `gate-reports/S1b300_cycle_report.json`,
`gate-reports/S1b150_cycle_report.json` and the step log `booth-loop/s1a-run-log.jsonl`.

## The cycle in one line

The operator's booth model, recorded 2026-11-21 22:05. The team builds all six maps on a loop,
each map is shown on the laptop panel for five minutes after it is built, then the next map is
built, and after the last map the loop returns to the first. One controller command starts it.

```
python3 /tmp/opencode/t0042/booth_loop.py \
  --maps foss-for-all,rocky-logo,rocky-with-heart,tux,republic-of-korea,i-love-korea \
  --loops 1 --display-seconds 300
```

The runner source is published in this repository at `code/booth_loop.py`. Variants the booth
operator uses, `--loops N` sustains the loop across the booth session, `--display-seconds 150`
is the recorded shorter-window fallback, `--paint-only` runs the visible painting segment alone,
`--stability` re-reads the six deliverable hashes on the target without touching them, and
`--summary --tag-prefix <phase>` writes the per-cycle cost report for a phase after it finishes.
Loop count and window are parameters, not a hardcoded schedule, because the booth duration is
recorded nowhere in this task and nothing in the runner presumes it.

## Where the cycle actually runs, stated honestly

The runner runs from `/tmp/opencode/t0042` on the controller machine, and it needs three things
that this repository does not carry. The build step invokes `code/build_ts.py` against
`ts-harvest/ref-era6.chk`, a harvested plaintext CHK extracted from a shipped Blizzard map, and
every `.chk` and `.scx` intermediate is withheld from this repository under the exclusion rules
recorded in `PUBLISH-STATUS.md`, because shipped game data is not this team's authorship. The
runner also authenticates to the target at `192.168.1.99` with `sshpass -f` against
`~/AI/secrets/scm_draft_pass.md`, a file mode 600 in the operator's secrets directory that is
never published. So this repository is the complete record of the cycle, every step of it
reproducible from published source, and the controller working directory is the runnable
environment. A reader who clones this repository can read exactly what runs and rebuild every
map's mask and container logic, and needs the reference CHK and the credentials locally to run
it end to end.

## What one cycle does, per map, in order

Each step below is timed in the run log and carries its own inverse at the moment it completes.
The seconds column is the measured mean from dispatch `S1b`, all six maps, 300 s window.

| step | what happens on the target | measured cost |
|---|---|---|
| `tmp_cleanup` | removes `C:\Maps\Scm*.tmp` editor backups left by earlier opens, naming every removed file with its byte size. A deletion has no byte inverse, so the log names it as permanent | 0.74 to 0.76 s |
| `disk_headroom before` | reads `df -B1 /` and `du -sb` of `C:\Maps\`, read-only | about 0.25 s |
| `build` | rebuilds the map deterministically from the committed mask code, `build_ts.py` with the era 6 reference CHK, glyph 192 on ground 64 | 0.04 to 0.56 s |
| `sha_verify_controller` | the rebuilt file must reproduce the recorded SHA-256 below or the map aborts before anything is transferred | under 0.01 s |
| `transfer` | copies the rebuilt file to `C:\Maps\<name>.scm` by absolute path (`scp` in SFTP mode does not expand a literal `$HOME`), then re-hashes the target copy against the same record | 0.50 to 0.53 s |
| `open` | launches SCMDraft 2 on the drive-qualified path `C:\Maps\<name>.scm`, dismisses the Scenario-properties dialog with Enter, captures the title bar, which carries the opened path | 25.5 s |
| `zoom walk` | walks the Zoom combo from 100 to 25 percent and verifies the resulting zoom from capture pixels, indicator 216 x 96 tiles at 7.931 x 7.854 px per tile. The combo's own readout is not trusted and is not a booth readout | 14.5 to 15.1 s |
| `display window` | holds the map on the panel for the requested seconds through scripted main-canvas frames planned from the committed mask geometry, frame counts 4, 6, 6, 6, 3 and 6 across the six maps, every frame captured and measured | requested seconds plus 3 to 6 percent per-frame capture overhead |
| `teardown` | kills SCMDraft 2, removes the loop copy from `C:\Maps\`, verifies `NO_SCM_RUNNING` and `REMOVED` | 2.9 s |

After the six maps, one scratch painting segment runs on `C:\Maps\live-demo-ice.scm` (12 recorded
steps, measured 72.96 s at the 300 s window and 73.01 s at 150 s), then the headroom read closes
the cycle. The scratch map is restored to its pre-cycle state at teardown, 12502 B at
`f00d1f60...`.

## The six maps and their SHA-256

Every map in the loop is verified against this table twice per cycle, once on the controller after
the rebuild and once on the target after the transfer. A map that does not match aborts before its
copy reaches the panel.

| map | SHA-256 | bytes | build mode |
|---|---|---|---|
| `foss-for-all` | `e856f0e1d62ec8f7ecfccf8f0d5f08aee0d5798ef972ea9fee996bbf3bfd3eb0` | 614561 | glyph |
| `rocky-logo` | `447360ce8077e54293bf37857402860fdb6b918eb335ca95426c7d2abc656e83` | 614559 | silhouette |
| `rocky-with-heart` | `b9b056c27a67851508dae01493ccd92ee4df4d70846f2ab8b9cb635fe141f0d8` | 614565 | silhouette |
| `tux` | `79002eacd5d673c531d6e2e417dddb6c00b02d9a9b9577fab7d43373f682bca4` | 614552 | silhouette |
| `republic-of-korea` | `c773a534a564d4b3bd13bb9eede10838daa1729784a693f28e6185e779c40976` | 614566 | silhouette |
| `i-love-korea` | `16fe455d46fd88671a98a79f3db65d934400ce0d4edd98f677313e6668d38ba9` | 614561 | silhouette |

The originals in `~/scmdraft-maps/` on the target are never written by the loop, and their hashes
and mtimes were re-verified unchanged after all three measured phases.

## What a cycle costs, measured

Costs measured end to end on the target by dispatch `S1b`, one full six-map cycle per window,
from `gate-reports/S1b300_cycle_report.json` and `gate-reports/S1b150_cycle_report.json`.

| display window | measured cycle cost | complete cycles that fit |
|---|---|---|
| 300 s, the operator's default | 2232.36 s, 37 min 12 s | 1 in one hour, 3 in two, 4 in three |
| 150 s, the recorded fallback | 1331.99 s, 22 min 12 s | 2 in one hour, 5 in two, 8 in three |

Non-display overhead holds at 43.86 to 44.46 s per map on all six maps at both windows, so halving
the display window cuts cycle time by 44.7 percent rather than 50, and a shorter window buys maps
rather than headroom. The 300 s default is the operator's stated booth model and stays. The 150 s
cycle is the fallback if the venue gives less time than expected. Disk residue is bounded by the
cycle-start cleanup at 4301926 B per cycle, the seven `Scm*.tmp` backups a full six-map cycle
writes, named in the run log.

## What the audience sees, honestly separated

**Programmatic, and nobody pretends otherwise.** The artwork of all six maps is written
into the map CHK by `code/build_ts.py` from committed bitmap masks, one tile per mask pixel, and
the rebuild finishes in well under a second. The audience does not watch these maps being drawn,
because drawing them by hand is out of reach by measured arithmetic. `i-love-korea` carries 20600
glyph tiles and `tux` 43968 tiles, the editor's own paint segment changes 13.8 to 19.1 percent of
a commanded stroke rectangle per placement at about 5.75 s per audience-safe step, so hand-painting
`tux` alone would be roughly six hours of clicking. Transfer, zoom walk, frame planning, cleanup
and teardown are scripted too.

**Editor-driven, and live on the panel.** The maps open and render in SCMDraft 2 in front of the
audience, title bar carrying the opened path. The display frames are the editor's own canvas being
moved, viewport jumps driven through overview-thumbnail clicks and the zoom combo walk, panning
across the main canvas at the measured 8.00 px per tile floor. And inside every cycle the scratch
map carries the proven visible-construction segment, Ctrl+T, Ctrl+U and Ctrl+D layer switches read
back out of the editor status bar, the terrain palette re-derived per cycle from a fresh capture
rather than hardcoded (`S1b` re-measured Rocky Snow at row 839 and High Outpost at row 968),
pointer clicks landing, and painted bands appearing on the canvas. The contrast is measured in the
run itself, 42581 changed pixels sampled per phase at median WCAG 6.267 against the 3.0 gate,
minimum pair 1.2 on stroke-edge pixels, identical figures in all three measured phases, recorded
with its low tail rather than only its median.

**Not shown, and recorded as not shown.** No editor save runs on any map in the cycle, deliverable
or scratch. An editor save rewrites the container and invalidates the gate hashes and coverage
numbers measured on the file (decision of 2026-11-21 08:40), so the loop never saves. The save
chain `Ctrl+S, Enter, Enter, Enter` is drivable on the scratch map, recorded in
`live-segment/commands/`, and a presenter may perform it by hand in front of the audience on the
scratch map, stating that the saved file is the scratch map and not one of the six deliverables.
Playability is the DoD fallback, no map has been loaded in StarCraft, and SCMDraft 2's own
map-validation dialog has never been run on any map.

## Limits a reader should know before 2026-11-28

The whole 256 x 256 map cannot be shown legibly on the 1920x1080 panel at any zoom, every
presentation is framed and panned, and the reachable zoom floor is 8.00 px per tile. The Zoom combo
display is not a booth readout, zoom is verified from pixels. Cycle costs come from one measured
cycle per window, `--loops 1` per phase, so loop-to-loop drift within a booth session is not
measured, and the cycles-that-fit figures are arithmetic on those measurements. The 3 to 6 percent
display-window overshoot is per-frame capture cost inside the hold loop, kept in the totals rather
than tuned away. The per-map legibility verdicts are the independent reads in the planning docs,
not this runbook's claims.
