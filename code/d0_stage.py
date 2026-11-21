#!/usr/bin/env python3
"""TASK-0042 dispatch D0 staging.

Classifies the controller working directory at /tmp/opencode/t0042, copies the
included categories into /tmp/opencode/t0042/publish/<category>/, and writes a
machine-readable plan at /tmp/opencode/t0042/d0_stage_plan.tsv listing every
file landed (path, destination, size, sha256) and every file withheld
(category, path, size). Nothing is copied into a git-tracked path of the team
repo by this script.

Hard rules enforced here:
  - no .scx / .chk / shipped StarCraft map / harvested reference CHK
  - no ISO, no container image, no SCMDraft or Wine binary or prefix
  - no credential file, no file whose bytes contain a credential value
  - no upstream library or upstream dataset copy
"""
import hashlib
import os
import re
import shutil
import sys

SRC = "/tmp/opencode/t0042"
PUB = "/tmp/opencode/t0042/publish"
PLAN = "/tmp/opencode/t0042/d0_stage_plan.tsv"

TEAM_REPO = "/home/howard/AI/projects/team-chaotix-moe"

DELIVERABLE_MAPS = [
    "foss-for-all.scm", "rocky-logo.scm", "rocky-with-heart.scm",
    "tux.scm", "republic-of-korea.scm", "i-love-korea.scm",
]
SUPERSEDED_MAPS = [
    "superseded-foss-for-all-jungle.scm", "superseded-republic-of-korea-110m.scm",
]
LIVE_MAPS = ["live-demo-ice.scm", "live-demo-ice-after.scm", "l5c-saved.scm"]

# Categories withheld, with the reason that lands in MANIFEST.md and
# PUBLISH-STATUS.md. Reason keys are stable strings used by the report writers.
HOLD_REASONS = {
    "shipped-starcraft-data":
        "Copy of shipped StarCraft map data. base-map.scx is Blizzard's stock "
        "Brood War map, maps/rc.scm is the shipped map (2)River Crossing.scm, and "
        "live-seed.scm is byte-identical to maps/rc.scm. Not this team's authorship.",
    "harvested-reference-chks":
        "Harvested reference CHK sections extracted from Blizzard-published maps "
        "under ts-harvest/. Extracts of a Blizzard map, not this team's authorship.",
    "chk-or-scx-intermediate":
        "CHK/SCX intermediates. The .scm containers that landed hold the same map "
        "data, and every .chk here is either an extract of a shipped Blizzard map "
        "or a decompressed copy of a .scm that landed.",
    "probe-map":
        "Throwaway calibration and probe maps from the tileset and save-path "
        "probing stages. Superseded by the calibration renders and gate reports "
        "that landed, and several are seeded from shipped StarCraft maps.",
    "upstream-library":
        "StormLib checkout, an upstream third-party library. Not this team's "
        "authorship, licence not yet ruled by Charmy and Flicky (R4 and R5).",
    "upstream-dataset":
        "Natural Earth GeoJSON downloaded from nvkelso/natural-earth-vector at "
        "tag v5.1.2. Upstream data, re-publishing it verbatim is outside this "
        "dispatch's include list; the landed record cites the repo, tag, commit, "
        "and per-file git blob SHAs instead.",
    "upstream-code":
        "richchk source fragments and starcraft_mpq_io.py imported from upstream "
        "projects. Not this team's authorship, licence not yet ruled (R4 and R5).",
    "compiled-binary":
        "ELF binaries built on the controller from the C sources that landed "
        "(chkdump, mkmpq, rdp-input, rdp-shot). Build artifacts, machine-specific.",
    "build-artifact":
        "__pycache__ bytecode caches.",
    "build-log-or-probe":
        "Build and launch logs and the bulk per-row tileset probe captures from "
        "the calibration stage, superseded by the calibration renders that landed.",
    "credential":
        "Scratch file holding a live target RDP credential in plaintext. Never "
        "published. Flagged to the operator for rotation.",
    "transient-note":
        "One-off scratch notes superseded by DEMO-LOG.md and MANIFEST.md.",
    "undocumented-binary":
        "Opaque intermediate binary with no generating script left on the "
        "controller, so its provenance cannot be stated honestly.",
    "raw-desktop-capture":
        "Uncompressed PPM desktop sanity captures from the earliest control "
        "stage, superseded by the PNG capture sets that landed.",
}

C_SRC_RE = re.compile(r"\.c$")
SH_RE = re.compile(r"^(run_|mkargs|read_|t0042-run|l1_run|l1_setup|shot)")
BOOTH_RE = re.compile(r"(booth32|booth64|booth4x|maskrender|-mm(-2x)?\.png$|calibration-render|map-body)")
LIVE_RE = re.compile(r"^(live|l1_|l3v|l3_|l5|paint_cmds)")
CALIB_RE = re.compile(r"^(calibshot-|calib\d+\.png|strip-calib|ice25-)")
PROBE_PNG_RE = re.compile(r"^(rows\d|bar6-|harv|sl[A-E]-shot|slrc-shot)")

ELF_MAGIC = b"\x7fELF"


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def classify(rel: str):
    """Return (destination_or_None, hold_category_or_None)."""
    name = os.path.basename(rel)
    top = rel.split("/")[0] if "/" in rel else ""

    if rel == "rdp-args":
        return None, "credential"
    if top == "ts-harvest":
        return None, "harvested-reference-chks"
    if top == "StormLib":
        return None, "upstream-library"
    if top == "m5-upstream":
        return None, "upstream-dataset"
    if top == "__pycache__":
        return None, "build-artifact"
    if name.endswith((".iso", ".img", ".qcow2")):
        return None, "iso-or-image"
    if name in ("base-map.scx",) or rel in ("maps/rc.scm", "maps/bn.scm", "live-seed.scm"):
        return None, "shipped-starcraft-data"
    if name.endswith((".chk", ".scx")):
        return None, "chk-or-scx-intermediate"
    if re.match(r"^(calib-|ts\d+-|item5\.scm$|stripes\.scm$|sl[A-E]\.scm$)", name):
        return None, "probe-map"
    if name in ("starcraft_mpq_io.py", "richchk_pyproject.toml", "richchk_README.md"):
        return None, "upstream-code"
    if name in ("sl.sha256", "maps.sha256", "ev_dirty_save.txt", ".output"):
        return None, "transient-note"
    if name == "colorbase.bin":
        return None, "undocumented-binary"
    if name.endswith(".ppm"):
        return None, "raw-desktop-capture"
    try:
        with open(os.path.join(SRC, rel), "rb") as fh:
            if fh.read(4) == ELF_MAGIC:
                return None, "compiled-binary"
    except OSError:
        pass
    if name.endswith(".log") or top == "probe":
        return None, "build-log-or-probe"

    if name in DELIVERABLE_MAPS:
        return "maps/deliverable", None
    if name in SUPERSEDED_MAPS:
        return "maps/superseded", None
    if name in LIVE_MAPS:
        return "live-segment/maps", None
    if name.endswith(".py") or C_SRC_RE.search(name) or SH_RE.match(name):
        return "code", None
    if name.endswith("_report.json"):
        return "gate-reports", None
    if re.match(r"^live-demo-commands", name) or name == "paint_cmds.txt":
        return "live-segment/commands", None
    if LIVE_RE.match(name):
        return "live-segment/captures", None
    if top == "montage":
        return "montages", None
    if CALIB_RE.match(name):
        return "calibration", None
    if PROBE_PNG_RE.match(name):
        return None, "build-log-or-probe"
    if BOOTH_RE.search(name):
        return "booth-artifacts", None
    if name.endswith(".png"):
        return "captures", None
    if name.endswith(".txt"):
        return "notes", None
    return None, "transient-note"


def main() -> int:
    if os.path.isdir(PUB):
        shutil.rmtree(PUB)
    landed = []
    withheld = {}
    for root, dirs, files in os.walk(SRC):
        dirs[:] = sorted(d for d in dirs if d not in (".git", "publish"))
        for f in sorted(files):
            full = os.path.join(root, f)
            if os.path.islink(full) or not os.path.isfile(full):
                continue
            rel = os.path.relpath(full, SRC)
            dest, hold = classify(rel)
            if dest is None:
                withheld.setdefault(hold, []).append((rel, os.path.getsize(full)))
                continue
            dst_dir = os.path.join(PUB, dest)
            os.makedirs(dst_dir, exist_ok=True)
            dst = os.path.join(dst_dir, f)
            shutil.copy2(full, dst)
            landed.append((rel, dest + "/" + f, os.path.getsize(dst), sha256(dst)))

    with open(PLAN, "w") as fh:
        fh.write("LAND\tsource\tdest\tsize\tsha256\n")
        for rel, dest, size, dg in sorted(landed, key=lambda r: r[1]):
            fh.write(f"LAND\t{rel}\t{dest}\t{size}\t{dg}\n")
        for cat in sorted(withheld):
            for rel, size in sorted(withheld[cat]):
                fh.write(f"HOLD\t{cat}\t{rel}\t{size}\n")

    total = sum(s for _, _, s, _ in landed)
    print(f"landed files {len(landed)}  bytes {total}")
    for cat in sorted(withheld):
        print(f"withheld {cat}  files {len(withheld[cat])}  bytes {sum(s for _, s in withheld[cat])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
