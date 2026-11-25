# FOSS for All 2026 booth, StarCraft 1 maps built live by Team Chaotix

Repository, `metalllinux/rocky-linux-foss-for-all-2026-demonstration-scmdraft-2`.
Event, FOSS for All Conference 2026, 2026-11-28. Demonstration target, a Rocky Linux 10.2 GNOME 49
Wayland laptop at `192.168.1.99`, driven from a Rocky Linux 10.2 controller over SSH and RDP input.
Editor, SCMDraft 2 Beta 0.9.10 running under Wine on the target.

This file tells an agentic session what to run to reproduce the booth loop, and it tells a visitor what
the audience actually sees. The two are stated separately on purpose, because parts of the booth are
driven by the editor and parts of it are programmatic, and a reader should be able to tell which is
which.

## 1. What the audience sees on the panel

The screen shows the SCMDraft 2 editor on the target laptop. A six-map cycle runs on a loop, and each
map on the loop is produced by the pipeline while the audience watches.

1. The controller rebuilds a deliverable map from committed mask code, deterministically, and verifies
   the rebuilt file against its recorded SHA-256 before anything is sent.
2. The rebuilt file is transferred to the target Wine prefix `C:\Maps\` by absolute path.
3. The editor opens it by its drive-qualified path, and the map body is framed on the main canvas.
4. The map is held on the panel for a configured display window, 300 seconds by default.
5. The map is torn down. No deliverable map is ever saved by the editor during the booth.
6. A proven painting segment runs on a scratch map, `C:\Maps\live-demo-ice.scm`, inside the same cycle,
   so the audience sees terrain actually laid down by injected input, at about 5.75 seconds per
   audience-safe step.
7. The next map is built, and the cycle repeats.

Measured cost, one six-map cycle at the 300 second window, 2232.36 seconds in rebuild mode and 2232.13
seconds in published mode, 1331.99 seconds at the 150 second window, with 43.35 to 44.64 seconds of
non-display overhead per map. A three hour booth fits four six-map cycles at 300 seconds. The loop count
and the display window are parameters, not a hardcoded schedule.

One visual fact belongs in the same paragraph as the timings. Every open frame that was measured, fourteen
of them across two cycles, holds 6 distinct colours and 0.02 to 0.06 percent glyph tone. In other words
the field reads as blank for a moment after the editor opens a map, and the picture resolves as the map
body is framed and the canvas is stepped. The framing frames are scripted and their coordinates come from
the committed mask code at the 8.00 pixels per tile floor.

## 2. Who built this, and how the team works

The booth was built by Team Chaotix, an eleven-agent autonomous team running on opencode, source of truth
at `metalllinux/team-chaotix-MoE`. The agents are `Robotnik` as project manager plus ten workers, `Amy`
for planning, `Tails` for implementation, `Shadow` for quality, `Omega` for security, `Big` for testing,
`Charmy` for licence, `Vector` for documentation, `Knuckles` for release, `Espio` for record hygiene, and
`Sonic` for issue intake.

How the team operates, stated because a visitor watching the booth sees the team work as well as the maps.

- `Robotnik` is the only agent that delegates. One model endpoint slot is available, `--parallel 1`, so
  dispatch is strictly sequential. One agent works at a time.
- Every task has one planning document with a fixed section contract, `## Status`, `## Definition of Done`,
  `## Next Actions`, `## Plan`, `## Implementation`, `## Review`, `## Security`, `## License (Charmy)`,
  `## Test Results`, `## Docs`, `## Release`, `## Archive`. Each agent writes only in its own section, and
  the document is the bus between agents rather than the project manager carrying findings.
- Review runs as a four-stage chain, `Shadow` then `Omega` then `Big` then `Charmy`.
- A builder never certifies its own artifacts. A map or a segment is not accepted until an agent other
  than the builder has read its captures and stated whether the picture is identifiable, with colour and
  coverage numbers attached.
- Every step that changes the target gets a dated entry in `DEMO-LOG.md` in the team repository, with the
  command that produced each claim and the exact inverse of the change written at the time the step
  completes.
- Credentials are read from `~/AI/secrets/` at run time only. They never appear in a commit, a log, a
  planning document, a command line, or this repository.
- Timestamps in the record are UTC with the JST equivalent in parentheses. The host clock is JST +0900.

## 3. The two run modes, and which one the booth uses

`--source rebuild` is the default and it is the mode the booth runs, because it is the only mode in which
a map is built during the cycle. It rebuilds each map from the committed mask code in `code/` plus a
reference CHK harvested from a shipped Blizzard map. That reference file is withheld from this repository
for licence reasons, so rebuild mode can only run from a working tree that holds it.

`--source published` skips the rebuild. It takes each deliverable `.scm` from a clone of this repository,
verifies it against the recorded SHA-256 before transfer and again on the target, and then drives the same
open, display, painting and teardown sequence. The frame planner still reads the committed mask code. In
this mode the maps are transferred, opened and rendered, not built, and any write-up of a published-mode
run has to say that plainly rather than claim live building.

## 4. The demonstration setup

Controller, Rocky Linux 10.2, `192.168.1.102`. Present, `ssh`, `scp`, `sshpass`, `rsync`, Python 3, gcc,
pkg-config with `freerdp-client3` from the `freerdp-devel` package, verified as
`freerdp-devel-3.32.2-1.el10_2.x86_64`. Absent, `xdotool`, `ydotool`, `grim`, `tesseract`, `gh`.

Target, `192.168.1.99`, hostname `scmdraft2-map-creator`, Rocky Linux 10.2, GNOME Shell 49.4,
`gnome-remote-desktop-49.3-4.el10_2` serving RDP on 3389, enabled repositories baseos, appstream, extras,
crb plus the copr `forecastwolf157/Wine-test`, Wine installed from that copr for SCMDraft 2, and the maps
directory at `/home/howard/.wine-scmdraft/drive_c/Maps`, which SCMDraft 2 sees as `C:\Maps\`. Era 6 Ice
World maps open and save only from inside the Wine prefix, which is why the runner passes drive-qualified
paths.

Control path, the target's own session is the only display used. Capture runs `/usr/bin/gnome-screenshot-tool
-f <file>` on the target, because a raw `gdbus` call to `org.gnome.Shell.Screenshot` returns `AccessDenied`
from any caller while gnome-shell 49 accepts the recognised screenshot client. Keyboard and pointer events
reach the live Wayland session through `rdp-input`, a self-authored tool that links `libfreerdp3` and
`libfreerdp-client3` and injects at the mutter compositor level, and through a `/dev/uinput` helper for
kernel-level injection, which needs a 1500 to 2000 ms settle after `UI_DEV_CREATE` because events emitted
in the same millisecond are dropped.

## 5. Running the loop on booth day

Prerequisites, in order. Each one is checkable.

1. Clone this repository.
   `git clone https://github.com/metalllinux/rocky-linux-foss-for-all-2026-demonstration-scmdraft-2`
2. Build the input injector, either from the copy published here or through the packaged team tooling.
   `gcc -O2 -Wall -o rdp-input code/rdp-input.c $(pkg-config --cflags --libs freerdp-client3)`
   The packaged equivalent is `scripts/remote/rt-build` in `metalllinux/team-chaotix-MoE`.
3. Place the injector binary where the runner looks for it. The runner reads `CHAOTIX_T0042_INJECTOR`,
   defaulting to the durable controller working tree `/home/howard/AI/booth-2026/t0042`, and expects
   `rdp-input` executable there. There is no `rdp-args` file. The runner assembles the injector's FreeRDP
   arguments at run time from `~/AI/secrets/scm_draft_rdp_pass.md` and hands them to `rdp-input` on its
   standard input, so the target RDP credential is stored nowhere by the runner and never appears in a
   command line, a log or this repository.
4. Confirm both target password files exist, `~/AI/secrets/scm_draft_pass.md` for the `sshpass -f` path and
   `~/AI/secrets/scm_draft_rdp_pass.md` for the injector, mode 600, each read at run time only.
5. Confirm the target is reachable and idle, `NO_SCM_RUNNING`, `NO_STARCRAFT_RUNNING`, `NO_WINESERVER`. The
   target-side launch script no longer has to survive cleaning of the target's own `/tmp`. In both modes
   `preflight_target_run_script` compares the target copy against the controller copy, `code/t0042-run-dos.sh`
   from a clone or `t0042-run-dos.sh` in the working tree, both reading `a85bba3c89f1`, installs it when the
   target has none, names `rm -f /tmp/t0042-run-dos.sh` as the inverse, and refuses to overwrite a target
   script that differs.
6. For rebuild mode only, `preflight_rebuild` checks four things a clone does not carry before any target
   contact and aborts with exit code 4 if any is missing: the reference CHK `ts-harvest/ref-era6.chk`, the map
   writer `mkmpq`, the mask code `rocky.py` and `glyph.py`, and the two secret files named above. On the team
   controller the durable working tree is `/home/howard/AI/booth-2026/t0042/`, created 2026-11-24 and completed
   2026-11-25 with `booth_loop.py`, `build_ts.py`, `build_map.py`, `mask_png.py`, the six mask modules,
   `t0042-run-dos.sh`, `ts-harvest/`, `mkmpq` beside `mkmpq.c` and the `stormlib/` headers and `libstorm.a` it
   builds against, `rdp-input`, and `work/` as the default scratch directory. The reference CHK there reads
   `d7afd6a53cd3664a822485cffc21f8502e584e7738e35b9835840782c621057b`. That directory is not a git repository
   and it is not pushed anywhere, which is why no credential and no withheld artifact sits in a git-tracked
   path.
7. `mkmpq` is the prerequisite this README omitted until 2026-11-25. Rebuild mode cannot produce a map without
   it, because `build_ts.py` calls `<working tree>/mkmpq` to wrap the built CHK into the map MPQ, and the path
   it uses is relative to the script itself. The durable copy on this controller was rebuilt in place from the
   recipe `gcc -O2 -Wall -I stormlib/include -o mkmpq mkmpq.c stormlib/lib/libstorm.a -lstdc++ -lm`, against
   StormLib at the commit named in section 7 with its MIT `LICENSE` carried beside the library, and it
   reproduces the recorded `tux` SHA-256 `79002eacd5d6` from a cold start on 2026-11-25. Without it the run
   fails at the `build` step of the first map.

Commands, as run and measured.

```
# health, controller-side only, no target contact
python3 code/booth_loop.py --stability

# rebuild mode, the booth mode, from a working tree that carries ts-harvest/ref-era6.chk
python3 /home/howard/AI/booth-2026/t0042/booth_loop.py \
  --maps foss-for-all,rocky-logo,rocky-with-heart,tux,republic-of-korea,i-love-korea \
  --loops 4 --display-seconds 300 --tag-prefix BOOTH

# published mode, from a bare clone of this repository, transfers and renders rather than builds
python3 code/booth_loop.py --source published --clone . \
  --maps foss-for-all,rocky-logo,rocky-with-heart,tux,republic-of-korea,i-love-korea \
  --loops 4 --display-seconds 300 --tag-prefix BOOTH

# measured cost report for a tag prefix
python3 code/booth_loop.py --summary --tag-prefix BOOTH

# painting segment alone, on the scratch map
python3 code/booth_loop.py --paint-only
```

Flags, `--maps` comma-separated names from the registry, `--loops` integer, `--display-seconds` default
300, `--no-paint` skips the painting segment, `--paint-only` runs only the painting segment, `--tag-prefix`
separates phases in the run log, `--source rebuild|published`, `--clone` required by published mode,
`--stability` and `--summary` are read-only reports.

Exit codes, `0` success, `2` unknown map name or published mode without `--clone`, `3` a map run failed
mid-cycle, `4` published-mode preflight rejected the clone or the controller working set, `5` the target
run script preflight failed. Preflight runs before any target contact, so a missing dependency aborts the
whole invocation instead of failing mid-cycle in front of an audience.

If an agent is pointed at this repository on booth day, the order is, read this file, read
`BOOTH-RUNBOOK.md`, run `--stability`, run the published-mode command with one map and a 60 second window
as a smoke test, confirm a capture shows the map rendered, then start the full loop. Do not start the full
loop without the smoke test.

## 6. The six deliverable maps and their recorded SHA-256 values

All six are built at the full 256 by 256 extent on Ice World era 6, glyph tiles on terrain value 192 over
ground value 64. Each cycle verifies the file against these values before transfer and again on the target.

| Map | SHA-256 |
|---|---|
| `foss-for-all` | `e856f0e1d62ec8f7ecfccf8f0d5f08aee0d5798ef972ea9fee996bbf3bfd3eb0` |
| `rocky-logo` | `447360ce8077e54293bf37857402860fdb6b918eb335ca95426c7d2abc656e83` |
| `rocky-with-heart` | `b9b056c27a67851508dae01493ccd92ee4df4d70846f2ab8b9cb635fe141f0d8` |
| `tux` | `79002eacd5d673c531d6e2e417dddb6c00b02d9a9b9577fab7d43373f682bca4` |
| `republic-of-korea` | `c773a534a564d4b3bd13bb9eede10838daa1729784a693f28e6185e779c40976` |
| `i-love-korea` | `16fe455d46fd88671a98a79f3db65d934400ce0d4edd98f677313e6668d38ba9` |

`i-love-korea` carries 20600 glyph tiles and `tux` carries 43968. Painting a deliverable map by hand at
that density takes far longer than a display window, which is why a deliverable map is programmatic and
the hand-painted segment runs on the scratch map. The two superseded `i-love-korea` builds sit under
ratified `superseded` prefixes in the manifest, and they are two designs rather than three.

## 7. What this repository does not contain, and why

No StarCraft game file from the StarCraft Anthology ISO, no SCMDraft 2 executable from
`http://www.stormcoast-fortress.net/cntt/software/scmdraft`, no third-party binary, no harvested reference
CHK, and no credential in any form. That is the operator's standing rule of 2026-11-22 22:10 UTC, and the
manifest names each withheld category with its reason. The sweep that proves it against the published tree
is recorded as owed to the licence review, and an unreadable sweep counts as a failure.

Licence posture in short form, with full detail in the root `NOTICE` in this repository, in
`PUBLISH-STATUS.md`, and in the team repository's licence section. Maps are the team's own work. Terrain
tones are renders of Blizzard tileset values. The shipped `republic-of-korea` mask derives from the Natural
Earth 10 m admin-0 dataset at `github.com/nvkelso/natural-earth-vector` tag `v5.1.2`, declared public
domain upstream. The map writer uses StormLib at commit `d60b7e6d3501474f4d92c7b9c752a37e78385f67`, MIT.
`code/rdp-input.c`, `code/rdp-shot.c` and `code/rdp-shot-probe.c` link FreeRDP dynamically. Upstream
FreeRDP is dual-licensed Apache-2.0 or GPL-2.0+, the distro package `freerdp-libs-3.32.2` carries
Apache-2.0 with HPND and LGPL-2.1-or-later terms, and the team takes the Apache-2.0 option for the library
it links while its own sources stay MIT. The Rocky logo art shipped in the booth artifacts comes from the
`rocky-logos-100.5-3.el10` package, which grants use only during normal operation of the software that
calls upon it and grants no trademark licence.

The licence review `R4` returned FAIL on this repository as published at commit `7c4fa16`, on two findings
reserved to the operator and both still open, `C2`, the Rocky Linux mark carried in the booth artifacts and
maps, and `C3`, the renders of Blizzard tileset tones the audience sees. Booth `main` now reads `b56d1df`
and that does not change the verdict. This repository is private and stays private, nothing clears a public
flip, and it must not be read as publishable. The visibility decision is the operator's to make.

## 8. Honest limits

- The editor is SCMDraft 2 Beta 0.9.10 and it performs no map validation of its own. That was established
  on all six accepted maps with two negative controls, a byte-corrupted map that opened silently and
  rendered normally, and a map with its `VER ` section name renamed that was refused silently in favour of
  a blank untitled map. The integrity gate the booth actually runs is therefore the per-cycle SHA-256
  verification, not a validator inside the editor.
- In-game playability is blocked. Flatpak Wine 11.0 launches on 2026-11-22 exited before any window
  existed, so there was no game surface for injected input to reach. The rendering of the intro and the
  main menu captured on 2026-11-14 is dated evidence about that day, and it is not presented here as
  present-tense capability. The booth demonstrates the editor, not the game.
- Delphi dialog buttons in SCMDraft 2 do not respond to injected clicks, so no step in the loop depends on
  one. Menu titles do respond, one injected click arms the menu bar and arrow keys walk it. Keyboard
  injection covers scancodes and Unicode code points, modifier chords are handled through the RDP keyboard
  pipe rather than as chords.
- The loop never saves a deliverable map. The only map touched on the target outside `C:\Maps\` is the
  scratch map, and even it is not saved.
- Target residue is named rather than hidden. Seventeen `Scm*.tmp` editor backups totalling 9845475 bytes
  are left deliberately so the operator can inspect them, `live-demo-ice.scm` at 12502 bytes,
  `(2)River Crossing.scm` at 90426 bytes, a 1152 byte game error file, and about 7195615 bytes per cycle of
  capture PNGs in the target's `/tmp`. The runner cleans `C:\Maps\Scm*.tmp` at cycle start and reads target
  disk headroom before and after every cycle.

## 9. Where the rest of the record lives

`BOOTH-RUNBOOK.md` in this repository is the step-by-step runbook with timings and inverses. `MANIFEST.md`
lists every published file with its size and SHA-256 and every withheld category with its reason,
cross-checked against the tree rather than against intent. `PUBLISH-STATUS.md` states which categories were
copied and which were withheld. `captures/`, `live-segment/`, `booth-artifacts/`, `calibration/`,
`montages/` and `gate-reports/` hold the evidence, including the editor captures an independent reader
scored for colour and coverage. `DEMO-LOG.md` and the planning documents for the four tasks that built the
booth live in `metalllinux/team-chaotix-MoE`, where the tooling under `scripts/remote/` and the
`remote-desktop` skill page also live.
