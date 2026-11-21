#!/usr/bin/env python3
"""TASK-0042 dispatch D2 staging.

Re-publish staging for the booth repo. The classification rules are D0's rules,
applied unchanged by importing d0_stage.classify, with five named D2 deltas
listed below and stated in the PUBLISH-STATUS.md and MANIFEST.md prose. Nothing
is copied into a git-tracked path of the team repo by this script.

D2 deltas, applied only to the exact names listed and never overriding a D0
hard exclusion (credential, shipped game data, harvested CHKs, upstream code or
datasets, compiled binaries, iso or image):
  1. superseded-i-love-korea.scm and superseded-i-love-korea-2line.scm land in
     maps/superseded/ at their ratified prefixed names. Under D0's rules these
     two names fell through to the transient-note hold; D0 staged before they
     existed as accepted-set neighbours.
  2. The four M7-era i-love-korea booth artifacts (mm, mm-2x, booth32, booth64)
     move out of the accepted booth-artifacts/ set into booth-artifacts/superseded/
     with their names unchanged, because F2 measured that they belong to the
     superseded M7 single-row build.
  3. The F2 re-cut and control images land as a set under booth-artifacts/f2-recut/
     so their provenance reads as one verification run.
  4. f2_artifact_check.json and f2_control.json land in gate-reports/.
  5. i-love-korea-2line-thumbnail128.png is the accepted build's 128 px booth
     thumbnail and lands in booth-artifacts/, not captures/.

Hard rules inherited unchanged from D0:
  - no .scx / .chk / shipped StarCraft map / harvested reference CHK
  - no ISO, no container image, no SCMDraft or Wine binary or prefix
  - no credential file, no file whose bytes contain a credential value
  - no upstream library or upstream dataset copy
"""
import hashlib
import os
import shutil
import sys

SRC = "/tmp/opencode/t0042"
PUB = "/tmp/opencode/t0042/publish"
PLAN = "/tmp/opencode/t0042/d2_stage_plan.tsv"

sys.path.insert(0, SRC)
import d0_stage  # noqa: E402  the D0 ruleset, used unchanged as the fallback

from d0_reasons import HOLD_REASONS  # noqa: E402,F401  single source of withheld reasons

HARD_HOLDS = {
    "credential", "harvested-reference-chks", "upstream-library", "upstream-dataset",
    "build-artifact", "iso-or-image", "shipped-starcraft-data", "chk-or-scx-intermediate",
    "upstream-code", "compiled-binary", "raw-desktop-capture", "undocumented-binary",
}

SUPERSEDED_MAPS_D2 = {"superseded-i-love-korea.scm", "superseded-i-love-korea-2line.scm"}
SUPERSEDED_BOOTH_D2 = {
    "i-love-korea-mm.png", "i-love-korea-mm-2x.png",
    "i-love-korea-booth32.png", "i-love-korea-booth64.png",
}
F2_REPORTS_D2 = {"f2_artifact_check.json", "f2_control.json"}


def classify(rel: str):
    """Return (destination_or_None, hold_category_or_None). D0 rules with the five D2 deltas."""
    name = os.path.basename(rel)
    top = rel.split("/")[0] if "/" in rel else ""

    dest, hold = d0_stage.classify(rel)
    if hold in HARD_HOLDS:
        return None, hold  # a D0 hard exclusion is never overridden by a delta
    if name in SUPERSEDED_MAPS_D2:
        return "maps/superseded", None
    if name in SUPERSEDED_BOOTH_D2:
        return "booth-artifacts/superseded", None
    if top == "f2-recut" and name.endswith(".png"):
        return "booth-artifacts/f2-recut", None
    if name in F2_REPORTS_D2:
        return "gate-reports", None
    if name == "i-love-korea-2line-thumbnail128.png":
        return "booth-artifacts", None
    return dest, hold


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    if os.path.isdir(PUB):
        shutil.rmtree(PUB)
    landed = []
    withheld = {}
    for root, dirs, files in os.walk(SRC):
        # booth-repo and booth-verify are git clones of the published tree, not
        # source content. They did not exist when D0 staged. Walking them would
        # republish the repository back into itself.
        dirs[:] = sorted(d for d in dirs if d not in
                         (".git", "publish", "booth-repo", "booth-verify", "booth-verify-d2"))
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
