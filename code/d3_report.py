#!/usr/bin/env python3
"""TASK-0042 dispatch D3 report generator.

Writes PUBLISH-STATUS.md first, then MANIFEST.md, into the booth repo clone,
from the files actually present in that clone and from the withheld list recorded
by d3_stage.py in d3_stage_plan.tsv. Both documents are generated from the tree
as written, so a file that did not land cannot appear in either. Carries the D2
naming and artifact-provenance statements unchanged.

Order matters. PUBLISH-STATUS.md is written before the manifest walk so that the
manifest lists it. MANIFEST.md lists every file in the repository except itself.
"""
import hashlib
import os
import sys
from collections import defaultdict

REPO = "/tmp/opencode/t0042/booth-repo"
PLAN = "/tmp/opencode/t0042/d3_stage_plan.tsv"

sys.path.insert(0, "/tmp/opencode/t0042")
from d0_reasons import HOLD_REASONS  # noqa: E402  withheld reasons, identical to D0
from d2_report import NAMING_STATEMENT, ARTIFACT_STATEMENT, EXTRA_EMPTY  # noqa: E402  unchanged D2 statements

TEAM_COMMIT = sys.argv[1] if len(sys.argv) > 1 else "unknown"

REPO_NAMES = (
    "This repository was renamed by the operator between dispatches `D0` and `D2`. It is "
    "`metalllinux/rocky-linux-foss-for-all-2026-demonstration-scmdraft-2`, and `metalllinux/"
    "foss-for-all-booth-demonstration-scmdraft-2` is the same repository under its former name, "
    "not a second repo. Evidence, both API paths carry repository id `1455994123`, and the old "
    "path answers `301 Moved Permanently` pointing at `https://api.github.com/repositories/1455994123` "
    "while the new path answers `200` with the repository JSON. Dispatch `D3` used the new name for "
    "every API call and for the clone remote."
)

CATEGORY_NOTES = {
    "maps/deliverable": ("six deliverable maps", "The six booth maps, each re-verified against the SHA-256 value the task record carries before it was copied. `i-love-korea.scm` at `16fe455d46fd...` is the accepted two-line build as ruled by `M10`."),
    "maps/superseded": ("superseded builds", "The four superseded builds kept at their ratified prefixed names. The two `i-love-korea` superseded files differ from each other in kind, see the named statement below the table."),
    "code": ("map and mask code, the booth runner, and the tooling", "This task's own Python, C and shell source, map writers, mask builders, the parameterized glyph renderer, measurement scripts, capture drivers, the staging and report scripts that produced `D0`, `D2` and `D3`, and the booth loop runner `booth_loop.py`."),
    "booth-loop": ("the booth loop's measured step log", "`s1a-run-log.jsonl`, one timed JSONL record per booth-cycle step as it completed, each carrying its own inverse or its teardown, covering dispatches `S1a` and `S1b`: the three-map partial cycle, the three-map phase, and both full six-map cycles at the 300 s and 150 s windows. Read together with `gate-reports/S1b300_cycle_report.json` and `gate-reports/S1b150_cycle_report.json`, which summarize it."),
    "gate-reports": ("gate reports", "Machine-readable gate reports, one per map plus the live-segment, rebuild, `F2` artifact-verification, and the four booth-cycle cost reports `s1a_cycle_report.json`, `S1bA_cycle_report.json`, `S1b300_cycle_report.json` and `S1b150_cycle_report.json`."),
    "booth-artifacts": ("booth artifacts", "Accepted-set overview-thumbnail map bodies and their 64 px and 32 px booth downscales, plus the mask renders named by the gate record."),
    "booth-artifacts/superseded": ("superseded booth artifacts", "The four `M7`-era `i-love-korea` artifacts, moved out of the accepted set in `D2` with their names unchanged because `F2` measured that they belong to the superseded single-row build."),
    "booth-artifacts/f2-recut": ("artifact provenance set", "The `F2` verification set, three re-cuts proven byte-identical to the accepted `i-love-korea` booth artifacts and two inpaint controls that quantify viewport-indicator overlay influence."),
    "captures": ("editor capture sets", "Editor captures, 100 percent and 25 percent zoom, minimap and title-bar crops, re-open pairs, jump frames, the reading aids the independent reads produced, and from `D3` the booth-loop frame captures of dispatches `S1a` and `S1b`, named by their phase tag (`S1aL1-`, `S1bAL1-`, `S1b300L1-`, `S1b150L1-`), one open frame, one zoom-walk frame and every scripted display frame per map per phase."),
    "calibration": ("calibration renders", "Tileset tone calibration renders the terrain-pair choice was made from."),
    "live-segment/maps": ("live-segment maps", "The flat Ice World seed the live segment was painted on, its painted pair, and the editor-saved file that closed the era 6 save blocker in dispatch `L5`."),
    "live-segment/commands": ("replayable live-segment command lists", "The exact injected scancode and click lists the visible construction segment was driven with, in the order that reproduces it."),
    "live-segment/captures": ("live-segment captures", "Before and after pairs of the same view, status-bar crops for each layer switch, pan and re-open frames, and every capture from the recorded attempts `L1` to `L5`."),
    "montages": ("montages", "Before-and-after and step montages assembled by the review dispatches."),
    "notes": ("measurement transcripts", "Measurement transcripts named by the gate record."),
    "planning": ("planning docs", "The planning docs for TASK-0041, TASK-0042 and TASK-0043, copied verbatim from the team repository as of the commit named below."),
    ".": ("repository root documents", "The root documents as they stood when this table was generated, `DEMO-LOG.md` copied from the team repository, `LICENSE` and `README.md` from the initial commit, `BOOTH-RUNBOOK.md` written by dispatch `D3`, and `PUBLISH-STATUS.md` and `MANIFEST.md` written by this same dispatch after the table is generated and both listed in `MANIFEST.md`."),
}

MEASURED_STATEMENT = """## The booth cycle, the measured cost, and what is editor-driven

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
of 2219.5 s is superseded by these measurements, 0.58 percent away."""

D3_DELTAS = """## Classification deltas this dispatch added, and the rules it re-applied unchanged

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
landed their earlier counterparts."""

NOT_CLAIM = """## What this publish does not claim

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
in the team repository, because they cannot be written into a commit that has not happened yet."""


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_plan():
    landed = {}
    withheld = defaultdict(list)
    roots = {}
    for line in open(PLAN):
        parts = line.rstrip("\n").split("\t")
        if parts[0] == "LAND" and len(parts) == 5 and parts[3] != "size":
            landed[parts[2]] = (int(parts[3]), parts[4])
        elif parts[0] == "HOLD" and len(parts) == 4 and parts[3] != "size":
            withheld[parts[1]].append((parts[2], int(parts[3])))
        elif parts[0] == "ROOT" and len(parts) == 4:
            roots[parts[1]] = (int(parts[2]), parts[3])
    return landed, withheld, roots


def tree():
    files = {}
    for root, dirs, names in os.walk(REPO):
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in names:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, REPO)
            files[rel] = (os.path.getsize(full), sha256(full))
    return files


def write_status(files, plan_landed, withheld):
    out = [
        "# PUBLISH STATUS",
        "",
        "What dispatch `D3` actually published into this repository on 2026-11-22, and what it did "
        "not publish. Written so the operator can check this repository against the task record "
        "without reading the planning docs first. `MANIFEST.md` lists every file here with its size "
        "and SHA-256. This is an addition on top of what dispatch `D2` pushed at commit `39f2119`, "
        "the booth runner, its measured run log and cycle reports, the booth-loop captures, and the "
        "runbook. No previously published map, artifact, capture, report or document was replaced or "
        "moved by `D3`.",
        "",
        REPO_NAMES,
        "",
        "## Copied",
        "",
        "| category | repo path | files | bytes | what it is |",
        "|---|---|---|---|---|",
    ]
    groups = defaultdict(list)
    for rel, (size, dg) in files.items():
        groups[os.path.dirname(rel) or "."].append((rel, size, dg))
    for group in sorted(groups):
        label, note = CATEGORY_NOTES.get(group, (group, ""))
        fs = groups[group]
        out.append(
            f"| {label} | `{group}/` | {len(fs)} | {sum(s for _, s, _ in fs)} | {note} |"
        )
    out += [
        "",
        "Named items, because the brief names them.",
        "",
        "| item | repo path | bytes | status |",
        "|---|---|---|---|",
        f"| booth loop runner | `code/booth_loop.py` | {files['code/booth_loop.py'][0]} | The runner "
        "as it stands after dispatch `S1b`, parameters `--maps`, `--loops`, `--display-seconds` "
        "defaulting to 300, `--tag-prefix`, `--paint-only`, `--stability`, `--summary`. Lands under "
        "the unchanged `D0` rule that places this task's Python in `code/`. |",
        f"| booth runbook | `BOOTH-RUNBOOK.md` | {files['BOOTH-RUNBOOK.md'][0]} | The one command "
        "that starts a cycle, the per-step table, the per-map SHA-256 table, the measured cycle "
        "costs and cycles-that-fit table, and the editor-driven versus programmatic statement. |",
        f"| booth step log | `booth-loop/s1a-run-log.jsonl` | {files['booth-loop/s1a-run-log.jsonl'][0]} | "
        "279 timed step records from dispatches `S1a` and `S1b`, each appended the moment its step "
        "completed, each carrying its inverse or teardown. |",
        f"| four cycle cost reports | `gate-reports/` | "
        f"{sum(s for r, (s, _) in files.items() if r.startswith('gate-reports/') and r.endswith('_cycle_report.json'))} | "
        "`s1a_cycle_report.json`, `S1bA_cycle_report.json`, `S1b300_cycle_report.json`, "
        "`S1b150_cycle_report.json`, the per-map and per-cycle costs the measured figures are taken from. |",
        f"| booth-loop captures | `captures/` | "
        f"{sum(s for r, (s, _) in files.items() if os.path.basename(r).startswith(('S1aL1-', 'S1bAL1-', 'S1b300L1-', 'S1b150L1-')))} | "
        "165 frames from the three measured phases and the `S1a` partial cycle, open, zoom-walk, "
        "scripted display and painting frames, named by phase tag. |",
        f"| DEMO-LOG.md | `DEMO-LOG.md` | {files['DEMO-LOG.md'][0]} | Copied from the team repository "
        f"`metalllinux/team-chaotix-MoE` at commit `{TEAM_COMMIT}`. It ends at the `D3` staging entry, "
        "because the entry describing this push cannot be written into a commit that has not happened "
        "yet. The team repository carries the push entry. |",
        f"| six deliverable maps | `maps/deliverable/` | {sum(s for r, (s, _) in files.items() if r.startswith('maps/deliverable'))} | "
        "Re-verified with `sha256sum` against the recorded values before this copy, all six byte-exact, "
        "`i-love-korea` at the accepted `16fe455d46fd...` value. Unchanged from `D2`. |",
        f"| four superseded builds | `maps/superseded/` | {sum(s for r, (s, _) in files.items() if r.startswith('maps/superseded'))} | "
        "Re-verified with `sha256sum` against the recorded values. See the naming statement below. |",
        f"| three planning docs | `planning/` | {sum(s for r, (s, _) in files.items() if r.startswith('planning/'))} | "
        f"Copied verbatim from the team repository at commit `{TEAM_COMMIT}`. |",
        "| replayable live-segment command lists | `live-segment/commands/` | "
        f"{sum(s for r, (s, _) in files.items() if r.startswith('live-segment/commands/'))} | "
        "`live-demo-commands.txt`, `live-demo-commands-l3.txt`, `live-demo-commands-l4.txt`, "
        "`paint_cmds.txt`. The scancode lists the segment was driven with. |",
        "| existing repo content | `LICENSE`, `README.md` | 1192 | Untouched by `D0`, by `D2` and by "
        "`D3`. The `README.md` prose is `D1`'s to rewrite. Repository visibility was not changed. |",
        "",
        NAMING_STATEMENT,
        "",
        ARTIFACT_STATEMENT,
        "",
        MEASURED_STATEMENT,
        "",
        D3_DELTAS,
        "",
        "## Not copied",
        "",
        "Each row is a category that existed in the classified walk of the controller working "
        "directory `/tmp/opencode/t0042` and was not published. The scratch rebuild directories "
        "`s1a-build/` and `s1a-rebuild/` are outside that walk by the named `D3` walk-scope delta "
        "above, so the 24 files inside them are not counted in any row. The last five rows are "
        "categories the brief excluded that had no representative in the staging directory, recorded "
        "so a reader does not assume a copy exists elsewhere. The reasons are AGENTS.md section 4 and "
        "section 9 and this task's own position that shipped game data is not this team's authorship. "
        "They are `D0`'s exclusion reasons, re-applied unchanged.",
        "",
        "| category | files withheld | bytes withheld | reason |",
        "|---|---|---|---|",
    ]
    for cat in sorted(withheld):
        fs = withheld[cat]
        out.append(
            f"| {cat} | {len(fs)} | {sum(s for _, s in fs)} | {HOLD_REASONS[cat]} |"
        )
    for cat, reason in EXTRA_EMPTY:
        out.append(f"| {cat} | 0 | 0 | {reason} |")
    out += [
        "",
        NOT_CLAIM,
        "",
    ]
    with open(os.path.join(REPO, "PUBLISH-STATUS.md"), "w") as fh:
        fh.write("\n".join(out))


def write_manifest(files, plan_landed, withheld):
    total_files = len(files)
    total_bytes = sum(v[0] for v in files.values())
    lines = [
        "# MANIFEST",
        "",
        "Every file in this repository as published by dispatch `D3` on 2026-11-22, with its size in "
        "bytes and its SHA-256, grouped by directory. Generated by `/tmp/opencode/t0042/d3_report.py` "
        "from the tree as written rather than transcribed, so a file listed here is a file in the "
        "repository. This manifest replaces the one `D2` published at commit `39f2119`.",
        "",
        REPO_NAMES,
        "",
        "`MANIFEST.md` is the only file not listed here, because a file cannot contain the hash of "
        "itself. Compare this list against `git ls-tree -r HEAD` to check it independently.",
        "",
        f"Totals, {total_files + 1} files in the repository once this manifest is written, {total_files} of "
        f"them listed here, {total_bytes} bytes listed, `PUBLISH-STATUS.md` included, on top of the `Initial commit` "
        "at `7e0d58d`, the `D0` commit `3da0937` and the `D2` commit `39f2119`. `LICENSE` and `README.md` "
        "are byte-unchanged by all three dispatches.",
        "",
        "The `i-love-korea` family, the booth-artifact provenance, the measured booth cycle cost, and "
        "the one command that starts a cycle are explained in `PUBLISH-STATUS.md` and `BOOTH-RUNBOOK.md`, "
        "both listed below like every other file.",
        "",
    ]
    groups = defaultdict(list)
    for rel, (size, dg) in files.items():
        if rel == "MANIFEST.md":
            continue
        groups[os.path.dirname(rel) or "."].append((rel, size, dg))
    for group in sorted(groups):
        fs = sorted(groups[group])
        label = group if group != "." else "(repository root)"
        lines.append(f"## `{label}`, {len(fs)} files, {sum(s for _, s, _ in fs)} bytes")
        lines.append("")
        lines.append("| file | bytes | sha256 |")
        lines.append("|---|---|---|")
        for rel, size, dg in fs:
            lines.append(f"| `{rel}` | {size} | `{dg}` |")
        lines.append("")
    lines += [
        "## Categories withheld, and the reason for each",
        "",
        "Withheld means the file was present in the classified walk of the controller working "
        "directory `/tmp/opencode/t0042` and was not copied here. The classification was applied by "
        "`/tmp/opencode/t0042/d3_stage.py` before any copy, running the `D0` ruleset from "
        "`/tmp/opencode/t0042/d0_stage.py` unchanged, the five `D2` deltas from "
        "`/tmp/opencode/t0042/d2_stage.py` unchanged, plus the three `D3` deltas named in "
        "`PUBLISH-STATUS.md`, and the same run produced the list above. A category with zero files is "
        "recorded as zero rather than omitted.",
        "",
        "| category | files | bytes | reason |",
        "|---|---|---|---|",
    ]
    for cat in sorted(withheld):
        fs = withheld[cat]
        lines.append(
            f"| {cat} | {len(fs)} | {sum(s for _, s in fs)} | {HOLD_REASONS[cat]} |"
        )
    for cat, reason in EXTRA_EMPTY:
        lines.append(f"| {cat} | 0 | 0 | {reason} |")
    lines.append("")
    with open(os.path.join(REPO, "MANIFEST.md"), "w") as fh:
        fh.write("\n".join(lines))


def main() -> int:
    landed, withheld, roots = read_plan()
    files = tree()
    missing = set(landed) - set(files)
    extra = set(files) - set(landed) - set(roots) - {
        "DEMO-LOG.md", "LICENSE", "README.md", "PUBLISH-STATUS.md", "MANIFEST.md",
        "planning/TASK-0041-remote-visual-control.md",
        "planning/TASK-0042-foss-for-all-scmdraft2-demo.md",
        "planning/TASK-0043-dispatch-gate.md"}
    if missing or extra:
        print(f"tree does not match the staging plan, missing {sorted(missing)} extra {sorted(extra)}")
        return 1
    for rel, (size, dg) in files.items():
        if rel in landed and landed[rel] != (size, dg):
            print(f"hash or size mismatch in the repository copy: {rel}")
            return 1
        if rel in roots and roots[rel] != (size, dg):
            print(f"hash or size mismatch in the root document: {rel}")
            return 1
    write_status(files, landed, withheld)
    files2 = tree()
    write_manifest(files2, landed, withheld)
    print("wrote PUBLISH-STATUS.md and MANIFEST.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
