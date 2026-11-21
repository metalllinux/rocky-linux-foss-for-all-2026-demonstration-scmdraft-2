#!/usr/bin/env python3
"""TASK-0042 dispatch D0 report generator.

Writes PUBLISH-STATUS.md first, then MANIFEST.md, into the booth repo clone,
from the files actually present in that clone and from the withheld list
recorded by d0_stage.py in d0_stage_plan.tsv. Both documents are generated from
the tree as written, so a file that did not land cannot appear in either.

Order matters. PUBLISH-STATUS.md is written before the manifest walk so that the
manifest lists it. MANIFEST.md lists every file in the repository except itself,
because a file cannot contain its own SHA-256.
"""
import hashlib
import os
import sys
from collections import defaultdict

REPO = "/tmp/opencode/t0042/booth-repo"
PLAN = "/tmp/opencode/t0042/d0_stage_plan.tsv"
TEAM_COMMIT = "2b29d7e"

from d0_reasons import HOLD_REASONS  # noqa: E402


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_plan():
    landed = {}
    withheld = defaultdict(list)
    for line in open(PLAN):
        parts = line.rstrip("\n").split("\t")
        if parts[0] == "LAND" and len(parts) == 5 and parts[3] != "size":
            landed[parts[2]] = (int(parts[3]), parts[4])
        elif parts[0] == "HOLD" and len(parts) == 4 and parts[3] != "size":
            withheld[parts[1]].append((parts[2], int(parts[3])))
    return landed, withheld


def tree():
    files = {}
    for root, dirs, names in os.walk(REPO):
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in names:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, REPO)
            files[rel] = (os.path.getsize(full), sha256(full))
    return files


CATEGORY_NOTES = {
    "maps/deliverable": ("six deliverable maps", "The six booth maps, each re-verified against the SHA-256 value the task record carries before it was copied."),
    "maps/superseded": ("superseded builds", "The two superseded builds kept at their ratified prefixed names, so a reader can open the file a `## Status` entry names."),
    "code": ("map and mask code and the letterform renderer", "This task's own Python, C and shell source, map writers, mask builders, the parameterized glyph renderer, measurement scripts, capture drivers."),
    "gate-reports": ("gate reports", "Machine-readable gate reports, one per map plus the live-segment and rebuild reports."),
    "booth-artifacts": ("booth artifacts", "Overview-thumbnail map bodies and their 64 px and 32 px booth downscales, plus the mask renders named by the gate record."),
    "captures": ("editor capture sets for the six maps", "Editor captures, 100 percent and 25 percent zoom, minimap and title-bar crops, re-open pairs, jump frames, and the reading aids the independent reads produced."),
    "calibration": ("calibration renders", "Tileset tone calibration renders the terrain-pair choice was made from."),
    "live-segment/maps": ("live-segment maps", "The flat Ice World seed the live segment was painted on, its painted pair, and the editor-saved file that closed the era 6 save blocker in dispatch `L5`."),
    "live-segment/commands": ("replayable live-segment command lists", "The exact injected scancode and click lists the visible construction segment was driven with, in the order that reproduces it."),
    "live-segment/captures": ("live-segment captures", "Before and after pairs of the same view, status-bar crops for each layer switch, pan and re-open frames, and every capture from the recorded attempts `L1` to `L5`."),
    "montages": ("montages", "Before-and-after and step montages assembled by the review dispatches."),
    "notes": ("measurement transcripts", "Measurement transcripts named by the gate record."),
    "planning": ("planning docs", "The planning docs for TASK-0041, TASK-0042 and TASK-0043, copied verbatim."),
    ".": ("repository root documents", "The three root files that existed when this table was generated, `DEMO-LOG.md` copied from the team repository, `LICENSE` and `README.md` from the initial commit. `PUBLISH-STATUS.md` and `MANIFEST.md` are written by this same dispatch after the table is generated, and both are listed in `MANIFEST.md`."),
}

EXTRA_EMPTY = [
    ("iso-or-image", "Excluded by the brief and absent from the controller. `find /tmp/opencode/t0042 "
     "-maxdepth 2 \\( -iname '*.iso' -o -iname '*.img' \\)` returns nothing, so the category is empty "
     "rather than removed. The StarCraft installer ISO the 2026-11-13 provenance question refers to is on "
     "the target, not here."),
    ("scmdraft-or-wine-binary-or-prefix", "Excluded by the brief and absent from the controller. SCMDraft 2 "
     "lives at `~/scmdraft2` on the target and its Wine prefix at `~/.wine-scmdraft` on the target, never "
     "under `/tmp/opencode/t0042`, so no copy of either existed to publish."),
    ("game-data-mpq-unit-sprite-assets", "Not present in the staging directory and not this team's "
     "authorship. The `.scm` maps that landed store terrain identifiers and contain no tile, unit or "
     "sprite graphics."),
]


def write_status(files, plan_landed, withheld):
    out = [
        "# PUBLISH STATUS",
        "",
        "What dispatch `D0` actually published into this repository on 2026-11-21, and what it did not "
        "publish. Written so the operator can check this repository against the task record without "
        "reading the planning docs first. `MANIFEST.md` lists every file here with its size and SHA-256.",
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
        f"| DEMO-LOG.md | `DEMO-LOG.md` | {files['DEMO-LOG.md'][0]} | Copied from the team repository "
        f"`metalllinux/team-chaotix-MoE` at commit `{TEAM_COMMIT}`. It ends at the `D0` staging entry "
        "dated 2026-11-21 17:50, because the entry describing this push cannot be written into a commit "
        "that has not happened yet. The team repository carries the push entry. |",
        f"| six deliverable maps | `maps/deliverable/` | {sum(s for r, (s, _) in files.items() if r.startswith('maps/deliverable'))} | "
        "Re-verified with `sha256sum` against the recorded values before the copy, all six byte-exact. |",
        f"| three planning docs | `planning/` | {sum(s for r, (s, _) in files.items() if r.startswith('planning/'))} | "
        f"Copied verbatim from the team repository at commit `{TEAM_COMMIT}`. |",
        "| replayable live-segment command lists | `live-segment/commands/` | "
        f"{sum(s for r, (s, _) in files.items() if r.startswith('live-segment/commands/'))} | "
        "`live-demo-commands.txt`, `live-demo-commands-l3.txt`, `live-demo-commands-l4.txt`, "
        "`paint_cmds.txt`. The scancode lists the segment was driven with. |",
        "| existing repo content | `LICENSE`, `README.md` | 1192 | Untouched. The `README.md` prose is "
        "`D1`'s to rewrite. Repository visibility was not changed. |",
        "",
        "## Not copied",
        "",
        "Each row is a category that existed in the controller working directory `/tmp/opencode/t0042` "
        "and was not published. The last three rows are categories the brief excluded that had no "
        "representative on the controller, recorded so a reader does not assume a copy exists elsewhere. "
        "The reasons are AGENTS.md section 4 and section 9 and this task's own position that shipped game "
        "data is not this team's authorship.",
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
        "## What this publish does not claim",
        "",
        "The captures and booth artifacts that landed are downscaled renders of Blizzard tileset tones, "
        "and the `.scm` maps name game data they do not contain. This repository is private today, so "
        "publishing them is not distribution to the public. Making it public is the operator's action, and "
        "the recorded position in `## Status` is that it should wait for the licence rulings `R4` and `R5`, "
        "`Charmy`'s and `Flicky`'s reads on the Natural Earth derived Korea mask, the StormLib and richchk "
        "imports, and the StarCraft data provenance question opened on 2026-11-13. Dispatch `D0` changed no "
        "visibility setting and made no licence ruling.",
        "",
        "Nothing in this repository was measured or re-verified by `D0` beyond file hashes. The gate numbers "
        "in `gate-reports/` are the numbers the dispatches that produced them recorded, the legibility "
        "verdicts are `Shadow`'s in the `## Review` section of `planning/TASK-0042-foss-for-all-scmdraft2-demo.md`, "
        "and `i-love-korea` is **not booth-accepted as shipped**, per the `M8` verdict of 2026-11-21 15:20. "
        "The booth set accepted as of this publish is `foss-for-all`, `rocky-logo`, `rocky-with-heart`, "
        "`tux` and `republic-of-korea`.",
        "",
        "No map in this repository has been validated by SCMDraft 2's own map-validation dialog, no map has "
        "been loaded in StarCraft, and no blind reader has identified any map. Those limits are recorded in "
        "the planning docs and are not closed by publishing their artifacts.",
        "",
        "Push result, the remote commit hash, and the categories `D0` did not copy are recorded in "
        "`DEMO-LOG.md` and `## Implementation` of `planning/docs/TASK-0042-foss-for-all-scmdraft2-demo.md` "
        "in the team repository, because they cannot be written into a commit that has not happened yet.",
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
        "Every file in this repository as published by dispatch `D0` on 2026-11-21, with its size in bytes "
        "and its SHA-256, grouped by directory. Generated by `/tmp/opencode/t0042/d0_report.py` from the "
        "tree as written rather than transcribed, so a file listed here is a file in the repository.",
        "",
        "`MANIFEST.md` is the only file not listed here, because a file cannot contain the hash of itself. "
        "Compare this list against `git ls-tree -r HEAD` to check it independently.",
        "",
        f"Totals, {total_files + 1} files in the repository once this manifest is written, {total_files} of "
        f"them listed here, {total_bytes} bytes listed, `PUBLISH-STATUS.md` included, on top of the `Initial commit` "
        "at `7e0d58d`, which contributed `LICENSE` at 1063 bytes and `README.md` at 129 bytes and is unchanged by this dispatch.",
        "bytes and is unchanged by this dispatch.",
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
        "Withheld means the file was present in the controller working directory `/tmp/opencode/t0042` and "
        "was not copied here. The classification was applied by `/tmp/opencode/t0042/d0_stage.py` before any "
        "copy, and the same run produced the list above. A category with zero files is recorded as zero "
        "rather than omitted.",
        "",
        "| category | files | bytes | reason |",
        "|---|---|---|---|",
    ]
    for cat in sorted(withheld):
        fs = withheld[cat]
        lines.append(f"| {cat} | {len(fs)} | {sum(s for _, s in fs)} | {HOLD_REASONS[cat]} |")
    for cat, reason in EXTRA_EMPTY:
        lines.append(f"| {cat} | 0 | 0 | {reason} |")
    lines.append("")
    with open(os.path.join(REPO, "MANIFEST.md"), "w") as fh:
        fh.write("\n".join(lines))


def main() -> int:
    for stale in ("MANIFEST.md", "PUBLISH-STATUS.md"):
        p = os.path.join(REPO, stale)
        if os.path.exists(p):
            os.remove(p)  # a stale report from a previous run must not be counted as landed
    files = tree()
    plan_landed, withheld = read_plan()
    missing = sorted(set(plan_landed) - set(files))
    if missing:
        print(f"FATAL, planned but not on disk: {missing}", file=sys.stderr)
        return 1
    write_status(files, plan_landed, withheld)
    files = tree()
    write_manifest(files, plan_landed, withheld)
    extra = sorted(set(files) - set(plan_landed) - {"LICENSE", "README.md", "PUBLISH-STATUS.md", "MANIFEST.md"})
    print(f"wrote PUBLISH-STATUS.md then MANIFEST.md; manifest lists {len(files)} files, "
          f"{sum(v[0] for v in files.values())} bytes, repository total {len(files) + 1} files once MANIFEST.md exists")
    if extra:
        print(f"note, on disk and not in the staging plan: {extra}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
