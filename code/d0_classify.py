#!/usr/bin/env python3
"""TASK-0042 dispatch D0: classify the controller working directory into publish
categories and withheld categories. Reads only, writes a plan file. No file is
copied by this script.
"""
import os
import re
import sys

SRC = "/tmp/opencode/t0042"

# Category rules, evaluated in order. First match wins.
# (category, regex on relative path) or explicit sets.
DELIVERABLE_MAPS = {
    "foss-for-all.scm",
    "rocky-logo.scm",
    "rocky-with-heart.scm",
    "tux.scm",
    "republic-of-korea.scm",
    "i-love-korea.scm",
}
SUPERSEDED_MAPS = {
    "superseded-foss-for-all-jungle.scm",
    "superseded-republic-of-korea-110m.scm",
}
LIVE_MAPS = {"live-demo-ice.scm", "live-demo-ice-after.scm", "l5c-saved.scm"}
SHIPPED_MAPS = {"live-seed.scm", "maps/rc.scm", "maps/bn.scm"}
PROBE_MAPS = {
    "item5.scm", "stripes.scm", "slA.scm", "slB.scm", "slC.scm", "slD.scm", "slE.scm",
} | {f"calib-{n}.scm" for n in (0, 16, 32, 48, 96, 192, 288, 2880, 2240)}
CAL_MAPS = {f"ts{n}-{k}.scm" for n in (0, 1, 2, 3, 5, 6, 7) for k in ("cal", "pair", "rows")}

TEAM_CODE = {
    "analyze_sl.py", "build_ice_after.py", "build_ice_seed.py", "build_map.py",
    "build_map1.py", "build_map2.py", "build_map.py", "build_shapes.py", "build_ts.py",
    "chk_analyze.py", "chk_read.py", "drive_construct.py", "drive_l3.py", "drive_l4.py",
    "glyph.py", "grid_crop.py", "harvest_inventory.py", "harvest_probe.py",
    "hash_brute.py", "hash_probe.py", "key_recovery.py", "korea.py", "korea_10m.py",
    "l1_run2.py", "l5_a.py", "l5_b.py", "l5_c.py", "m5_measure.py", "m5_raster.py",
    "m5_source_probe.py", "m5_target.py", "m7_mask_diag.py", "m7_measure.py",
    "m7_target.py", "make_artifacts.py", "make_montage.py", "make_panels.py",
    "mask_png.py", "measure_contrast.py", "measure_pair.py", "measure_rebuild.py",
    "measure_silhouette.py", "measure_tux.py", "mk_probe_montage.py", "mk_slDE.py",
    "mk_variants.py", "mk_verdict.py", "paint_text.py", "parse2.py", "parse3.py",
    "parse_map.py", "probe_stage1.py", "probe_stage2a.py", "reader.py", "rocky.py",
    "rocky_svg.py", "scan.py", "shot.py", "tux.py",
}
UPSTREAM_CODE = {"starcraft_mpq_io.py", "richchk_pyproject.toml", "richchk_README.md"}

GATE_REPORTS = {
    "i-love-korea_report.json", "l3_report.json", "l4_report.json",
    "live_construct_report.json", "m5_raster_report.json", "maps23_rebuild_report.json",
    "republic-of-korea_report.json", "superseded-maps23_report.json", "tux_report.json",
}

BOOTH_RE = re.compile(
    r"(booth32|booth64|booth4x|maskrender|-mm(-2x)?\.png$|calibration-render|map-body)"
)

LIVE_RE = re.compile(r"^(live|l1_|l3v|l3_|l5|paint_cmds|live-demo-commands)")
CALIB_RE = re.compile(r"^(calibshot-|calib\d+\.png|strip-calib|ice25-)")
PROBE_RE = re.compile(r"^(probe/|rows\d|bar6-|harv|-shot\.png$|sl[A-E]-shot|slrc-shot)")


def classify(rel: str) -> str:
    name = os.path.basename(rel)
    top = rel.split("/")[0] if "/" in rel else ""

    # Hard exclusions first, they win over everything.
    if top == "ts-harvest":
        return "HOLD:harvested-reference-chks"
    if top == "StormLib":
        return "HOLD:upstream-library"
    if top == "m5-upstream":
        return "HOLD:upstream-dataset"
    if top == "__pycache__":
        return "HOLD:build-artifact"
    if rel in SHIPPED_MAPS:
        return "HOLD:shipped-starcraft-data"
    if name.endswith((".chk", ".scx")):
        return "HOLD:chk-or-scx-intermediate"
    if rel in PROBE_MAPS or rel in CAL_MAPS:
        return "HOLD:probe-map"
    if name in UPSTREAM_CODE:
        return "HOLD:upstream-code"
    if name == "chkdump":
        return "HOLD:compiled-binary"
    if name.endswith((".log", ".ppm")) or top == "probe":
        return "HOLD:build-log-or-probe"
    if name in ("sl.sha256", "ev_dirty_save.txt", ".output"):
        return "HOLD:transient-note"

    # Inclusions.
    if rel in DELIVERABLE_MAPS:
        return "maps/deliverable"
    if rel in SUPERSEDED_MAPS:
        return "maps/superseded"
    if rel in LIVE_MAPS:
        return "live-segment/maps"
    if rel in TEAM_CODE:
        return "code"
    if name.startswith("run_") and name.endswith(".sh"):
        return "code"
    if rel in ("l1_run1.sh", "l1_setup.sh", "shot.sh", "shot2.sh"):
        return "code"
    if rel in GATE_REPORTS:
        return "gate-reports"
    if name.endswith("-commands.txt") or name == "paint_cmds.txt":
        return "live-segment/commands"
    if LIVE_RE.match(name):
        return "live-segment/captures"
    if top == "montage":
        return "montages"
    if CALIB_RE.match(name):
        return "calibration"
    if BOOTH_RE.search(name):
        return "booth-artifacts"
    if name.endswith(".png"):
        return "captures/unsorted"
    if name.endswith(".txt"):
        return "notes"
    return "UNCLASSIFIED"


def main() -> None:
    out = {}
    for root, dirs, files in os.walk(SRC):
        dirs[:] = [d for d in dirs if d not in (".git",)]
        for f in files:
            full = os.path.join(root, f)
            if not os.path.isfile(full) or os.path.islink(full):
                continue
            rel = os.path.relpath(full, SRC)
            cat = classify(rel)
            out.setdefault(cat, []).append((rel, os.path.getsize(full)))
    total = 0
    for cat in sorted(out):
        files = sorted(out[cat])
        size = sum(s for _, s in files)
        total += size
        print(f"{cat}\t{len(files)}\t{size}")
    print(f"TOTAL\t{sum(len(v) for v in out.values())}\t{total}")
    detail = sys.argv[1] if len(sys.argv) > 1 else None
    if detail:
        for rel, size in sorted(out.get(detail, [])):
            print(f"{detail}\t{rel}\t{size}")


if __name__ == "__main__":
    main()
