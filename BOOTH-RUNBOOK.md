# BOOTH RUNBOOK

How to start the FOSS for All booth cycle with one command, what the cycle does, what it costs,
which maps it shows, and what the audience actually sees the editor do versus what a program
builds. Written by dispatch `D3` on 2026-11-22 from the runner as it stands after dispatch `S1b`
and from the measured cycle costs recorded in `planning/TASK-0042-foss-for-all-scmdraft2-demo.md`.
The measured numbers here come from `gate-reports/S1b300_cycle_report.json`,
`gate-reports/S1b150_cycle_report.json` and the step log `booth-loop/s1a-run-log.jsonl`.

## The cycle in one line, and which mode it runs in

The operator's booth model, recorded 2026-11-21 22:05. The team builds all six maps on a loop,
each map is shown on the laptop panel for five minutes after it is built, then the next map is
built, and after the last map the loop returns to the first. One controller command starts it.

The runner has two ways to obtain the map it shows, added by dispatch `S1c`, and they do not run
from the same place. This runbook documents both, and names which one a reader can actually start
from a clone of this repository.

**Published mode, `--source published`, the mode this repository can run.** It skips the rebuild
entirely. It takes each of the six maps from `maps/deliverable/` in a clone of this repository,
verifies each against the recorded SHA-256 below in a preflight that runs before any target contact,
verifies it again immediately before transfer and once more on the target after transfer, and then
drives the same open, display, painting-segment and teardown sequence described below with no save
on any map. It reads no `.chk` file at all.

```
git clone https://github.com/metalllinux/rocky-linux-foss-for-all-2026-demonstration-scmdraft-2 booth
python3 booth/code/booth_loop.py \
  --source published --clone "$PWD/booth" \
  --maps foss-for-all,rocky-logo,rocky-with-heart,tux,republic-of-korea,i-love-korea \
  --loops 1 --display-seconds 300 --tag-prefix S1c300
```

**Rebuild mode, `--source rebuild`, the default.** It rebuilds each map from the committed mask code
through `code/build_ts.py` against `ts-harvest/ref-era6.chk`, a harvested plaintext CHK extracted
from a shipped Blizzard map. That file is withheld from this repository for licence reasons and stays
withheld, so this mode runs only from a working tree that already holds it, which today is the
controller working tree `/tmp/opencode/t0042`. Every cycle whose cost is measured in this runbook
and every cycle `S1a` and `S1b` ran was a rebuild-mode cycle.

```
python3 /tmp/opencode/t0042/booth_loop.py \
  --maps foss-for-all,rocky-logo,rocky-with-heart,tux,republic-of-korea,i-love-korea \
  --loops 1 --display-seconds 300
```

Run the rebuild command against a clone and it refuses rather than half-running, logging `build`
`FAIL` with the reason naming the withheld reference CHK and pointing at `--source published`. The
map content the two modes put on the panel is the same file at the same SHA-256, because the rebuild
reproduces the published copy byte for byte, which is what the preflight and the transfer gates
measure each cycle.

The runner source is published in this repository at `code/booth_loop.py`. Variants the booth
operator uses, `--loops N` sustains the loop across the booth session, `--display-seconds 150`
is the recorded shorter-window fallback, `--paint-only` runs the visible painting segment alone,
`--stability` re-reads the six deliverable hashes on the target without touching them, and
`--summary --tag-prefix <phase>` writes the per-cycle cost report for a phase after it finishes.
Loop count and window are parameters, not a hardcoded schedule, because the booth duration is
recorded nowhere in this task and nothing in the runner presumes it.

## Where each mode actually runs, stated honestly

Neither mode runs from this repository alone, and the two need different things outside it.

Both modes need three machine-local things that this repository does not carry and will not. The
input injector `rdp-input` is a compiled binary, withheld under the compiled-binary exclusion rule
(source published at `code/rdp-input.c`). The file `rdp-args` that carries the target RDP credential
is withheld as a credential. The target password file `~/AI/secrets/scm_draft_pass.md` is a credential
in the operator's secrets directory, file mode 600 or stricter, never published. Both modes also need
Python 3 with Pillow and the `tesseract` OCR binary on the controller, and a writable scratch
directory for captures, crops, the run log and the cycle reports, defaulting to `/tmp/opencode/t0042`
and overridable with `CHAOTIX_T0042_WORK` so a published-mode run writes nothing into the clone it
runs from.

Rebuild mode additionally needs `ts-harvest/ref-era6.chk`, the harvested reference CHK named above.
That is the single thing that makes rebuild mode unrunnable from a clone, and it is withheld
correctly: it is an extract of a shipped Blizzard map, not this team's authorship.

Published mode needs nothing beyond those four things that is not already in this repository. The six
maps, the flat Ice World scratch seed at `live-segment/maps/live-demo-ice.scm`, the mask code the
display frames are planned from at `code/rocky.py` and `code/glyph.py`, and the target-side launch
script `code/t0042-run-dos.sh` are all published here. The runner's `preflight_published` step names
that list in the run log, and `preflight_target_run_script` compares the launch script already on the
target against the published copy, installs the published copy if the target has none, and refuses to
overwrite a target script that differs.

So this repository is the complete record of the cycle, and from a clone it is also a runnable cycle,
in published mode, on a controller that carries the injector, the credentials and the target.

## What one cycle does, per map, in order

Each step below is timed in the run log and carries its own inverse at the moment it completes.
The seconds column is the measured mean from dispatch `S1b`, all six maps, 300 s window.

| step | what happens on the target | measured cost |
|---|---|---|
| `tmp_cleanup` | removes `C:\Maps\Scm*.tmp` editor backups left by earlier opens, naming every removed file with its byte size. A deletion has no byte inverse, so the log names it as permanent | 0.74 to 0.76 s |
| `disk_headroom before` | reads `df -B1 /` and `du -sb` of `C:\Maps\`, read-only | about 0.25 s |
| `build` or `published_source` | rebuild mode, rebuilds the map from the committed mask code, `build_ts.py` with the era 6 reference CHK, glyph 192 on ground 64. Published mode, `published_source`, reads the clone's `maps/deliverable/<name>.scm` read-only and writes nothing | 0.04 to 0.56 s, published mode under 0.01 s |
| `sha_verify_controller` | the file about to be sent must reproduce the recorded SHA-256 below or the map aborts before anything is transferred. In published mode the same six files were already checked once more in `preflight_published`, before any target contact | under 0.01 s |
| `transfer` | copies the file to `C:\Maps\<name>.scm` by absolute path (`scp` in SFTP mode does not expand a literal `$HOME`), then re-hashes the target copy against the same record | 0.50 to 0.53 s |
| `open` | launches SCMDraft 2 on the drive-qualified path `C:\Maps\<name>.scm`, dismisses the Scenario-properties dialog with Enter, captures the title bar, which carries the opened path | 25.5 s |
| `zoom walk` | walks the Zoom combo from 100 to 25 percent and verifies the resulting zoom from capture pixels, indicator 216 x 96 tiles at 7.931 x 7.854 px per tile. The combo's own readout is not trusted and is not a booth readout | 14.5 to 15.1 s |
| `display window` | holds the map on the panel for the requested seconds through scripted main-canvas frames planned from the committed mask geometry, frame counts 4, 6, 6, 6, 3 and 6 across the six maps, every frame captured and measured | requested seconds plus 3 to 6 percent per-frame capture overhead |
| `teardown` | kills SCMDraft 2, removes the loop copy from `C:\Maps\`, verifies `NO_SCM_RUNNING` and `REMOVED` | 2.9 s |

After the six maps, one scratch painting segment runs on `C:\Maps\live-demo-ice.scm` (12 recorded
steps, measured 72.96 s at the 300 s window and 73.01 s at 150 s), then the headroom read closes
the cycle. The flat Ice World seed it paints on is the same file in both modes, 614562 B at
`8f338a3cea24...`, rebuilt from `code/build_ice_seed.py` in rebuild mode and read from this
repository at `live-segment/maps/live-demo-ice.scm` in published mode, verified against that SHA-256
before transfer either way. The scratch map is restored to its pre-cycle state at teardown, 12502 B
at `f00d1f60...`.

## The six maps and their SHA-256

Every map in the loop is verified against this table on the controller before it is sent and again on
the target after the transfer. In published mode the six files are verified a third time, in
`preflight_published`, before the runner makes any contact with the target. A map that does not match
aborts before its copy reaches the panel.

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
