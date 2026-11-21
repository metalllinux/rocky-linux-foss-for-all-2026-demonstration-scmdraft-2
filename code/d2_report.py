#!/usr/bin/env python3
"""TASK-0042 dispatch D2 report generator.

Writes PUBLISH-STATUS.md first, then MANIFEST.md, into the booth repo clone,
from the files actually present in that clone and from the withheld list
recorded by d2_stage.py in d2_stage_plan.tsv. Both documents are generated from
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
PLAN = "/tmp/opencode/t0042/d2_stage_plan.tsv"

sys.path.insert(0, "/tmp/opencode/t0042")
from d0_reasons import HOLD_REASONS  # noqa: E402  withheld reasons, identical to D0

TEAM_COMMIT = sys.argv[1] if len(sys.argv) > 1 else "unknown"

REPO_NAMES = (
    "This repository was renamed by the operator between dispatches `D0` and `D2`. It is "
    "`metalllinux/rocky-linux-foss-for-all-2026-demonstration-scmdraft-2`, and `metalllinux/"
    "foss-for-all-booth-demonstration-scmdraft-2` is the same repository under its former name, "
    "not a second repo. Evidence, both API paths carry repository id `1455994123`, and the old "
    "path answers `301 Moved Permanently` pointing at `https://api.github.com/repositories/1455994123` "
    "while the new path answers `200` with the repository JSON. This dispatch used the new name for "
    "every API call."
)

CATEGORY_NOTES = {
    "maps/deliverable": ("six deliverable maps", "The six booth maps, each re-verified against the SHA-256 value the task record carries before it was copied. `i-love-korea.scm` at `16fe455d46fd...` is the accepted two-line build as ruled by `M10`, replacing the superseded single-row `82589b4205f5...` build that `D0` published at this name."),
    "maps/superseded": ("superseded builds", "The four superseded builds kept at their ratified prefixed names, so a reader can open the file a `## Status` entry names. The two `i-love-korea` superseded files differ from each other in kind, see the named statement below this table."),
    "code": ("map and mask code and the letterform renderer", "This task's own Python, C and shell source, map writers, mask builders, the parameterized glyph renderer, measurement scripts, capture drivers, and the staging and report scripts that produced `D0` and `D2`."),
    "gate-reports": ("gate reports", "Machine-readable gate reports, one per map plus the live-segment, rebuild, and `F2` artifact-verification reports."),
    "booth-artifacts": ("booth artifacts", "Accepted-set overview-thumbnail map bodies and their 64 px and 32 px booth downscales, plus the mask renders named by the gate record."),
    "booth-artifacts/superseded": ("superseded booth artifacts", "The four `M7`-era `i-love-korea` artifacts, moved out of the accepted set in `D2` with their names unchanged because `F2` measured that they belong to the superseded single-row build, not the accepted two-line build."),
    "booth-artifacts/f2-recut": ("artifact provenance set", "The `F2` verification set, three re-cuts proven byte-identical to the accepted `i-love-korea` booth artifacts and two inpaint controls that quantify viewport-indicator overlay influence."),
    "captures": ("editor capture sets", "Editor captures, 100 percent and 25 percent zoom, minimap and title-bar crops, re-open pairs, jump frames, and the reading aids the independent reads produced."),
    "calibration": ("calibration renders", "Tileset tone calibration renders the terrain-pair choice was made from."),
    "live-segment/maps": ("live-segment maps", "The flat Ice World seed the live segment was painted on, its painted pair, and the editor-saved file that closed the era 6 save blocker in dispatch `L5`."),
    "live-segment/commands": ("replayable live-segment command lists", "The exact injected scancode and click lists the visible construction segment was driven with, in the order that reproduces it."),
    "live-segment/captures": ("live-segment captures", "Before and after pairs of the same view, status-bar crops for each layer switch, pan and re-open frames, and every capture from the recorded attempts `L1` to `L5`."),
    "montages": ("montages", "Before-and-after and step montages assembled by the review dispatches."),
    "notes": ("measurement transcripts", "Measurement transcripts named by the gate record."),
    "planning": ("planning docs", "The planning docs for TASK-0041, TASK-0042 and TASK-0043, copied verbatim from the team repository as of the commit named below."),
    ".": ("repository root documents", "The root documents as they stood when this table was generated, `DEMO-LOG.md` copied from the team repository, `LICENSE` and `README.md` from the initial commit, `PUBLISH-STATUS.md` and `MANIFEST.md` written by this same dispatch after the table is generated and both listed in `MANIFEST.md`."),
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
    ("booth-geometry-captures", "The single capture dispatch `B1` measured the booth panel geometry from, "
     "`b1-editor.png`, no longer exists on the controller because `B1`'s own brief required the exact "
     "inverse of every capture it created and `B1` removed it after measuring. `B1`'s measurements, panel "
     "identity, millimetres per pixel, pixels and millimetres per tile in both views, and the angular "
     "subtence table, are published in `planning/TASK-0042-foss-for-all-scmdraft2-demo.md`. `0` files "
     "withheld because none existed to withhold."),
    ("shadow-independent-read-scripts-and-reading-aids", "The independent reader's scripts and reading "
     "aids live under `/tmp/opencode/shadow-t0042`, outside the staging directory `/tmp/opencode/t0042` "
     "that `D0` classified and `D2` re-classified, so neither dispatch copied any file from that "
     "directory, including the `M10` reading aids and scripts named in the `## Review` verdict. Aids a "
     "dispatch placed inside `/tmp/opencode/t0042` itself, for example the `m7-read-` and `m5-read-` "
     "renders, landed with the capture sets. `0` files withheld from the staging directory."),
]


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


NAMING_STATEMENT = """## The `i-love-korea` naming, stated because the repo carries three files in this family

| file | sha256 | what it is |
|---|---|---|
| `maps/deliverable/i-love-korea.scm` | `16fe455d46fd88671a98a79f3db65d934400ce0d4edd98f677313e6668d38ba9` | The accepted booth build, two-line layout, 20600 glyph tiles. |
| `maps/superseded/superseded-i-love-korea.scm` | `82589b4205f5deb8ed123273f1c6b5262472806bb90373d6b267c8f27e2319a0` | The `M7` single-row build, 19666 glyph tiles, a different map from the accepted build. Superseded in content, `M8` found its `I`, `O` and `E` strokes fail the 64 px criterion, `M9` rebuilt it, `M10` accepted the rebuild. |
| `maps/superseded/superseded-i-love-korea-2line.scm` | `e7ad27b2f4e7c6d12771b410edd289821fe438d7e4f2bc62caacb40a0b63efab` | A name-superseded duplicate of the accepted build, not a third design. `F2` decoded the containers and found its `MTXM` identical cell for cell to the accepted build, 20600 glyph tiles at values 64 and 192, and the entire 6-byte size difference is the internal `STR` map-name field reading 19 characters for `i-love-korea-2line` against 13 for `i-love-korea`. |

So the two superseded `i-love-korea` files are superseded in different senses, the plain-prefixed one in
content and the `-2line` one in name only. A reader who opens all three is looking at two designs, not
three. The measurement is in `gate-reports/f2_artifact_check.json` and in `## Implementation` dispatch
`F2` of `planning/TASK-0042-foss-for-all-scmdraft2-demo.md`."""

ARTIFACT_STATEMENT = """## The `i-love-korea` booth artifacts, source capture named per the `F2` ruling

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
exact Lanczos 0.5 of it, so they belong to the superseded `M7` single-row build."""


def write_status(files, plan_landed, withheld):
    out = [
        "# PUBLISH STATUS",
        "",
        "What dispatch `D2` actually published into this repository on 2026-11-21, and what it did not "
        "publish. Written so the operator can check this repository against the task record without "
        "reading the planning docs first. `MANIFEST.md` lists every file here with its size and SHA-256. "
        "This is a re-publication, the repository previously held the interim record dispatch `D0` pushed "
        "at commit `3da0937`, and `D2` replaces the interim `i-love-korea` content with the accepted "
        "build set.",
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
        f"| DEMO-LOG.md | `DEMO-LOG.md` | {files['DEMO-LOG.md'][0]} | Copied from the team repository "
        f"`metalllinux/team-chaotix-MoE` at commit `{TEAM_COMMIT}`. It ends at the `D2` staging entry, "
        "because the entry describing this push cannot be written into a commit that has not happened yet. "
        "The team repository carries the push entry. |",
        f"| six deliverable maps | `maps/deliverable/` | {sum(s for r, (s, _) in files.items() if r.startswith('maps/deliverable'))} | "
        "Re-verified with `sha256sum` against the recorded values before the copy, all six byte-exact, "
        "`i-love-korea` at the accepted `16fe455d46fd...` value. |",
        f"| four superseded builds | `maps/superseded/` | {sum(s for r, (s, _) in files.items() if r.startswith('maps/superseded'))} | "
        "Re-verified with `sha256sum` against the recorded values before the copy. See the naming statement below. |",
        f"| three planning docs | `planning/` | {sum(s for r, (s, _) in files.items() if r.startswith('planning/'))} | "
        f"Copied verbatim from the team repository at commit `{TEAM_COMMIT}`. |",
        "| replayable live-segment command lists | `live-segment/commands/` | "
        f"{sum(s for r, (s, _) in files.items() if r.startswith('live-segment/commands/'))} | "
        "`live-demo-commands.txt`, `live-demo-commands-l3.txt`, `live-demo-commands-l4.txt`, "
        "`paint_cmds.txt`. The scancode lists the segment was driven with. |",
        "| existing repo content | `LICENSE`, `README.md` | 1192 | Untouched by `D0` and by `D2`. The "
        "`README.md` prose is `D1`'s to rewrite. Repository visibility was not changed. |",
        "",
        NAMING_STATEMENT,
        "",
        ARTIFACT_STATEMENT,
        "",
        "## Classification deltas this dispatch added, and the rules it re-applied unchanged",
        "",
        "`D2` re-ran `D0`'s staging over the controller working directory with `D0`'s classification rules "
        "imported unchanged, `d0_stage.py`, and five named deltas, recorded in `d2_stage.py`. 1, the two "
        "superseded `i-love-korea` builds land in `maps/superseded/`. 2, the four `M7`-era `i-love-korea` "
        "booth artifacts move to `booth-artifacts/superseded/`. 3, the `F2` re-cut and control images land "
        "as a set in `booth-artifacts/f2-recut/`. 4, `f2_artifact_check.json` and `f2_control.json` land in "
        "`gate-reports/`. 5, `i-love-korea-2line-thumbnail128.png` is classified with the booth artifacts "
        "rather than the captures. Every `D0` hard exclusion, shipped game data, harvested reference CHKs, "
        "all `.chk` and `.scx` intermediates including the team's own, upstream library and dataset copies, "
        "compiled binaries, ISOs and disk images, and the credential scratch file, is re-applied unchanged "
        "and no delta overrides one. New files that `D0` staged before they existed, the `M9` capture set, "
        "the accepted `i-love-korea` artifacts and report, the `M9` and `F2` scripts, land under the same "
        "rules that landed their `M7` counterparts.",
        "",
        "## Not copied",
        "",
        "Each row is a category that existed in the controller working directory `/tmp/opencode/t0042` "
        "and was not published. The last five rows are categories the brief excluded that had no "
        "representative in the staging directory, recorded so a reader does not assume a copy exists "
        "elsewhere. The reasons are AGENTS.md section 4 and section 9 and this task's own position that "
        "shipped game data is not this team's authorship. They are `D0`'s exclusion reasons, re-applied "
        "unchanged.",
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
        "imports, and the StarCraft data provenance question opened on 2026-11-13. Dispatch `D2` changed no "
        "visibility setting and made no licence ruling.",
        "",
        "Nothing in this repository was measured or re-verified by `D2` beyond file hashes and the container "
        "decodes carried in `gate-reports/`. The gate numbers are the numbers the dispatches that produced "
        "them recorded, and the legibility verdicts are `Shadow`'s in the `## Review` section of "
        "`planning/TASK-0042-foss-for-all-scmdraft2-demo.md`. As of this publish `i-love-korea` is "
        "booth-accepted in its two-line form, per the `M10` verdict of 2026-11-21 20:00, the accepted booth "
        "set is `foss-for-all`, `rocky-logo`, `rocky-with-heart`, `tux`, `republic-of-korea` and "
        "`i-love-korea`, and the `M8` rejection applies to the superseded single-row build. The zoom floor "
        "`M10` measured, 8.00 px per tile, supersedes the fit-to-line figures earlier `## Status` entries "
        "derived.",
        "",
        "No map in this repository has been validated by SCMDraft 2's own map-validation dialog, no map has "
        "been loaded in StarCraft, and no blind reader has identified any map. Those limits are recorded in "
        "the planning docs and are not closed by publishing their artifacts.",
        "",
        "Push result, the remote commit hash, and the categories `D2` did not copy are recorded in "
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
        "Every file in this repository as published by dispatch `D2` on 2026-11-21, with its size in bytes "
        "and its SHA-256, grouped by directory. Generated by `/tmp/opencode/t0042/d2_report.py` from the "
        "tree as written rather than transcribed, so a file listed here is a file in the repository. This "
        "manifest replaces the one `D0` published at commit `3da0937`.",
        "",
        REPO_NAMES,
        "",
        "`MANIFEST.md` is the only file not listed here, because a file cannot contain the hash of itself. "
        "Compare this list against `git ls-tree -r HEAD` to check it independently.",
        "",
        f"Totals, {total_files + 1} files in the repository once this manifest is written, {total_files} of "
        f"them listed here, {total_bytes} bytes listed, `PUBLISH-STATUS.md` included, on top of the `Initial commit` "
        "at `7e0d58d` and the `D0` commit `3da0937`, `LICENSE` and `README.md` byte-unchanged by both dispatches.",
        "",
        "The `i-love-korea` family and the booth-artifact provenance are explained in `PUBLISH-STATUS.md`, "
        "which is listed below like every other file.",
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
        "was not copied here. The classification was applied by `/tmp/opencode/t0042/d2_stage.py` before any "
        "copy, running the `D0` ruleset from `/tmp/opencode/t0042/d0_stage.py` unchanged plus the five "
        "deltas named in `PUBLISH-STATUS.md`, and the same run produced the list above. A category with zero "
        "files is recorded as zero rather than omitted.",
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
    landed, withheld = read_plan()
    files = tree()
    missing = set(landed) - set(files)
    extra = set(files) - set(landed) - {"DEMO-LOG.md", "LICENSE", "README.md", "PUBLISH-STATUS.md", "MANIFEST.md",
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
    write_status(files, landed, withheld)
    files2 = tree()
    write_manifest(files2, landed, withheld)
    print("wrote PUBLISH-STATUS.md and MANIFEST.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
