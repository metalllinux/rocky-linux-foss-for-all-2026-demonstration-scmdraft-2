#!/usr/bin/env python3
"""TASK-0042 dispatch D2 remote verification.

Cross-checks MANIFEST.md against the git tree of a fresh clone of the pushed
repository, re-hashes every listed file in that clone, and reports:
  - every manifest row whose size or sha256 disagrees with the file on disk
  - every tree path the manifest omits (except MANIFEST.md itself)
  - every manifest path absent from the tree
Exits non-zero on any mismatch. Takes the clone path as argv[1].
"""
import hashlib
import os
import re
import subprocess
import sys

ROW_RE = re.compile(r"^\| `([^`]+)` \| (\d+) \| `([0-9a-f]{64})` \|$")


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    repo = sys.argv[1]
    manifest = os.path.join(repo, "MANIFEST.md")
    listed = {}
    with open(manifest) as fh:
        for line in fh:
            m = ROW_RE.match(line.rstrip("\n"))
            if m:
                listed[m.group(1)] = (int(m.group(2)), m.group(3))
    tree_out = subprocess.run(
        ["git", "-C", repo, "ls-tree", "-r", "HEAD", "--name-only"],
        capture_output=True, text=True, check=True).stdout.splitlines()
    tree_paths = set(tree_out)

    hash_mismatch = []
    missing_from_tree = []
    for path, (size, dg) in sorted(listed.items()):
        if path not in tree_paths:
            missing_from_tree.append(path)
            continue
        full = os.path.join(repo, path)
        actual = (os.path.getsize(full), sha256(full))
        if actual != (size, dg):
            hash_mismatch.append((path, (size, dg), actual))
    omitted = sorted(tree_paths - set(listed) - {"MANIFEST.md"})

    dup = len(listed) != len([l for l in open(manifest) if ROW_RE.match(l.rstrip("\n"))])
    print(f"manifest rows {len(listed)} unique paths {len(set(listed))} row-line duplicates {dup}")
    print(f"tree paths {len(tree_paths)} listed {len(listed)} omitted-by-manifest {len(omitted)} listed-absent-from-tree {len(missing_from_tree)} hash-or-size-mismatches {len(hash_mismatch)}")
    for x in omitted[:20]:
        print(f"OMITTED {x}")
    for x in missing_from_tree[:20]:
        print(f"ABSENT  {x}")
    for x in hash_mismatch[:20]:
        print(f"MMISMATCH {x}")
    ok = (not omitted) and (not missing_from_tree) and (not hash_mismatch) and not dup
    print("MANIFEST CROSS-CHECK", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
