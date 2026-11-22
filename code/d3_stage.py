#!/usr/bin/env python3
"""TASK-0042 dispatch D3 staging.

Re-publish staging for the booth repo, dispatch D3. The classification rules are
D0's rules, applied unchanged by importing d0_stage.classify, plus D2's five
deltas applied unchanged, plus the three named D3 deltas below. Nothing is copied
into a git-tracked path of the team repo by this script.

D3 deltas:
  1. s1a-run-log.jsonl, the booth loop's measured step log, lands in booth-loop/.
     Under D0/D2 rules its name fell to the transient-note catch-all, the same
     catch-all class from which D2 promoted the superseded i-love-korea builds.
     It is not a D0 hard exclusion, and a credential scan of every landing file
     runs before any copy (see credential_scan below).
  2. BOOTH-RUNBOOK.md lands at the repository root, copied into the clone outside
     this walk exactly as the root documents DEMO-LOG.md, LICENSE, README.md and
     the three planning docs are, listed in MANIFEST.md like every other file.
  3. Walk-scope exclusion. The scratch directories s1a-build/ and s1a-rebuild/
     are excluded from the walk. Their .chk files were already held by the hard
     chk-or-scx-intermediate rule, and their .scm files carry the deliverable
     basenames, so under the unchanged rule they would copy byte-identical
     duplicates of the six published maps into maps/deliverable/. Each rebuild
     byte-matches its published map at the recorded SHA-256 (S1a/S1b SHA gates,
     re-verified before this staging), so excluding them loses no content and
     keeps one copy of each map in the tree. The clone exclusion list extends
     D2's with booth-verify-d3.

Hard rules inherited unchanged from D0 and re-applied unchanged:
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
PLAN = "/tmp/opencode/t0042/d3_stage_plan.tsv"

sys.path.insert(0, SRC)
import d0_stage  # noqa: E402  the D0 ruleset, used unchanged as the fallback
import d2_stage  # noqa: E402  the D2 delta set, re-applied unchanged

from d0_reasons import HOLD_REASONS  # noqa: E402,F401  single source of withheld reasons

RUN_LOG_D3 = "s1a-run-log.jsonl"
ROOTDOC_D3 = "BOOTH-RUNBOOK.md"  # staged into the clone root, outside this classify walk

# Secret values are read at run time from the operator's secrets directory and are
# only ever compared against, never printed. The scan enforces the D0 rule "no file
# whose bytes contain a credential value" mechanically over every landing candidate.
SECRET_FILES = ("scm_draft_pass.md", "scm_draft_rdp_pass.md", "token.md", "pass.txt")


def secrets():
    vals = []
    for name in SECRET_FILES:
        p = os.path.expanduser(f"~/AI/secrets/{name}")
        if os.path.exists(p):
            with open(p, "rb") as fh:
                v = fh.read().strip()
            if len(v) >= 6:
                vals.append(v)
    return vals


def credential_scan(src_path: str, secret_vals) -> bool:
    with open(src_path, "rb") as fh:
        data = fh.read()
    return any(v in data for v in secret_vals)


def classify(rel: str):
    """D0 rules unchanged, D2 deltas unchanged, then the named D3 delta."""
    name = os.path.basename(rel)
    top = rel.split("/")[0] if "/" in rel else ""

    dest, hold = d2_stage.classify(rel)  # d2_stage.classify already chains d0_stage
    if hold in d2_stage.HARD_HOLDS:
        return None, hold  # a D0 hard exclusion is never overridden by a delta
    if name == RUN_LOG_D3:
        return "booth-loop", None
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
    secret_vals = secrets()
    landed = []
    withheld = {}
    rootdocs = []
    for root, dirs, files in os.walk(SRC):
        # clones, the publish target, and the scratch rebuild outputs are not source
        # content. See the walk-scope delta in the header.
        dirs[:] = sorted(d for d in dirs if d not in
                         (".git", "publish", "booth-repo", "booth-verify", "booth-verify-d2",
                          "booth-verify-d3", "s1a-build", "s1a-rebuild"))
        for f in sorted(files):
            full = os.path.join(root, f)
            if os.path.islink(full) or not os.path.isfile(full):
                continue
            rel = os.path.relpath(full, SRC)
            if rel == ROOTDOC_D3:
                # root document, copied into the clone at assembly rather than
                # classified; recorded here so the plan accounts for every file
                rootdocs.append((rel, os.path.getsize(full), sha256(full)))
                continue
            dest, hold = classify(rel)
            if dest is None:
                withheld.setdefault(hold, []).append((rel, os.path.getsize(full)))
                continue
            if credential_scan(full, secret_vals):
                print(f"CREDENTIAL SCAN FAIL: {rel} contains a secret value, not staged")
                return 2
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
        for rel, size, dg in rootdocs:
            fh.write(f"ROOT\t{rel}\t{size}\t{dg}\n")

    total = sum(s for _, _, s, _ in landed)
    print(f"landed files {len(landed)}  bytes {total}")
    print(f"root documents staged outside the walk: {[r for r, _, _ in rootdocs]}")
    print(f"credential scan ran over every landing file, secrets compared: {len(secret_vals)}")
    for cat in sorted(withheld):
        print(f"withheld {cat}  files {len(withheld[cat])}  bytes {sum(s for _, s in withheld[cat])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
