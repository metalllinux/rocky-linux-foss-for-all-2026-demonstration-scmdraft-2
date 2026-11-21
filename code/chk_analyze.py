#!/usr/bin/env python3
"""Compare a real map CHK (harvested with StormLib) against the writer at /tmp/opencode/t0042/build_map.py.

Reads a plaintext CHK produced by chkdump and reports section layout, terrain value
statistics, and the differences that matter for terrain rendering.
"""
import collections
import struct
import sys


def sections(chk):
    out = []
    pos = 0
    while pos + 8 <= len(chk):
        name = chk[pos:pos + 4]
        if not all(32 <= b <= 126 for b in name):
            break
        size = struct.unpack("<I", chk[pos + 4:pos + 8])[0]
        out.append((name.decode("latin1"), pos, size))
        pos += 8 + size
    return out


def u16s(data):
    return [struct.unpack("<H", data[i:i + 2])[0] for i in range(0, len(data) - 1, 2)]


def main(path):
    d = open(path, "rb").read()
    secs = sections(d)
    print(f"{path}: total {len(d)} bytes, sections {len(secs)}, covered {sum(8 + s for _, _, s in secs)}")
    for n, o, s in secs:
        print(f"  {n!r} off {o} size {s}")
    by = {n: d[o + 8:o + 8 + s] for n, o, s in secs}
    W, H = struct.unpack("<HH", by["DIM "])
    print(f"DIM {W}x{H}  ERA {struct.unpack('<H', by['ERA '][:2])[0]}")
    print(f"VER {by['VER '].hex()}  IVER {by.get('IVER', b'').hex()}  IVE2 {by.get('IVE2', b'').hex()}")
    for k in ("MTXM", "TILE", "ISOM", "MASK", "STR ", "SPRP", "FORC", "UNIT", "THG2", "DD2 ", "MRGN", "TRIG", "VCOD", "OWNR", "SIDE"):
        if k in by:
            print(f"{k}: size {len(by[k])}")
    for name in ("MTXM", "TILE"):
        v = u16s(by[name])
        g = collections.Counter((x >> 4) & 0x7FF for x in v)
        sub = collections.Counter(x & 15 for x in v)
        print(f"{name}: n {len(v)} distinct {len(set(v))} min {min(v)} max {max(v)} "
              f"groups {len(g)} subtiles {sorted(sub)}")
        print(f"   top groups: {g.most_common(14)}")
        print(f"   lowest 16 values: {sorted(set(v))[:16]}")
    m, t = u16s(by["MTXM"]), u16s(by["TILE"])
    print(f"MTXM == TILE: {m == t}  differing tiles: {sum(1 for a, b in zip(m, t) if a != b)}")
    iv = u16s(by["ISOM"])
    print(f"ISOM: entries {len(iv)} distinct {len(set(iv))} min {min(iv)} max {max(iv)}")
    print(f"   size hypotheses: 4*(W+2)*(H+1)={4 * (W + 2) * (H + 1)}  "
          f"(W/2+1)*(H+1)*4={(W // 2 + 1) * (H + 1) * 4}  2*(W/2+1)*(H+1)={2 * (W // 2 + 1) * (H + 1)}")
    print(f"   top values: {collections.Counter(iv).most_common(10)}")
    print(f"MTXM row0: {m[:16]}")
    print(f"TILE row0: {t[:16]}")
    print(f"VCOD nonzero bytes: {sum(1 for b in by['VCOD'] if b)} of {len(by['VCOD'])}")
    print(f"STR head: {by['STR '][:48]!r}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/opencode/t0042/rc.chk")
