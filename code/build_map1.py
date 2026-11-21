#!/usr/bin/env python3
"""TASK-0042 dispatch 3: build map 1 `foss-for-all` and calibration maps with the
proven slE pipeline (harvested River Crossing family sections + mkmpq StormLib wrap).

Terrain model proven in dispatch 2 (doc:1392): MTXM==TILE, one u16 per tile, flat
ISOM 4*(W+2)*(H+1) of 0x10, VER 59, harvested VCOD. Terrain VALUES are the gate;
they are calibrated empirically against a real SCMDraft render before any glyph work.

Modes:
  calib <value>      64x64, whole map filled with one candidate terrain value.
  glyph <fg>         256x256, background 128/144 flat ground, glyph written in `fg`.
"""
import struct
import subprocess
import sys

sys.path.insert(0, "/tmp/opencode/t0042")
import build_map as bm  # noqa: E402  (section helper only; build_mpq is NOT used)

HERE = "/tmp/opencode/t0042"
RC = f"{HERE}/rc.chk"

# Harvested Jungle flat ground background proven to render (dispatch 2, slE): groups 8/9, subtile 0.
BG_A = 128
BG_B = 144


def sections(chk):
    out = {}
    pos = 0
    while pos + 8 <= len(chk):
        name = chk[pos:pos + 4]
        if not all(32 <= b <= 126 for b in name):
            break
        size = struct.unpack("<I", chk[pos + 4:pos + 8])[0]
        out[name.decode("latin1")] = chk[pos + 8:pos + 8 + size]
        pos += 8 + size
    return out


def str_section(strings):
    """STR in the real harvested layout: u16[1024] offsets then NUL-terminated strings, no leading count."""
    offsets = []
    pos = 0
    for s in strings:
        offsets.append(pos)
        pos += len(s) + 1
    offsets += [0] * (1024 - len(offsets))
    return b"".join(struct.pack("<H", o) for o in offsets) + b"\x00".join(strings) + b"\x00"


def build_chk(W, H, tiles, name_str):
    """tiles: list of W*H u16 terrain values, row-major (top row first)."""
    assert len(tiles) == W * H
    assert all(0 <= t <= 0xFFFF for t in tiles)
    ref = sections(open(RC, "rb").read())
    mt = struct.pack("<%dH" % len(tiles), *tiles)
    isom_entries = (W + 2) * (H + 1) * 2
    isom = struct.pack("<%dH" % isom_entries, *([0x10] * isom_entries))
    assert len(isom) == 4 * (W + 2) * (H + 1)
    chk = bytearray()
    for name in ("VER ", "IVER", "VCOD", "IOWN", "OWNR", "ERA "):
        chk += bm.section(name, ref[name])
    chk += bm.section("DIM ", struct.pack("<HH", W, H))
    chk += bm.section("SIDE", ref["SIDE"])
    chk += bm.section("MTXM", mt)
    chk += bm.section("PUNI", ref["PUNI"])
    chk += bm.section("UPGR", ref["UPGR"])
    chk += bm.section("PTEC", ref["PTEC"])
    chk += bm.section("UNIT", b"")
    chk += bm.section("ISOM", isom)
    chk += bm.section("TILE", mt)
    chk += bm.section("DD2 ", b"")
    chk += bm.section("THG2", b"")
    chk += bm.section("MASK", b"\xff" * (W * H))
    chk += bm.section("STR ", str_section([name_str.encode("latin1"), b""]))
    chk += bm.section("UPRP", ref["UPRP"])
    chk += bm.section("UPUS", ref["UPUS"])
    chk += bm.section("MRGN", ref["MRGN"])
    chk += bm.section("TRIG", b"")
    chk += bm.section("MBRF", b"")
    chk += bm.section("SPRP", ref["SPRP"])
    chk += bm.section("FORC", ref["FORC"])
    chk += bm.section("WAV ", ref["WAV "])
    chk += bm.section("UNIS", ref["UNIS"])
    chk += bm.section("UPGS", ref["UPGS"])
    chk += bm.section("TECS", ref["TECS"])
    return bytes(chk)


def wrap(chk_path, out_scm):
    r = subprocess.run(
        [f"{HERE}/mkmpq", out_scm, "plain", "staredit\\scenario.chk=" + chk_path],
        capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def bg(x, y):
    return BG_A if (x + y) % 2 == 0 else BG_B


def main():
    mode = sys.argv[1]
    if mode == "calib":
        val = int(sys.argv[2], 0)
        W = H = 64
        tiles = [val] * (W * H)
        chk_path = f"{HERE}/calib-{val}.chk"
        out = f"{HERE}/calib-{val}.scm"
    elif mode == "stripes":
        # Horizontal (x+y) bands, each a candidate terrain value, decodable top-to-bottom
        # in a single isometric screenshot: a screen row corresponds to a constant x+y.
        vals = [int(a, 0) for a in sys.argv[2:]]
        W = H = 64
        band = (126) // len(vals) + 1  # band width in x+y units
        tiles = [vals[min((x + y) // band, len(vals) - 1)] for y in range(H) for x in range(W)]
        chk_path = f"{HERE}/stripes.chk"
        out = f"{HERE}/stripes.scm"
        print("band width", band, "order", vals)
    elif mode == "glyph":
        fg = int(sys.argv[2], 0)
        from glyph import mask  # glyph layout lives in glyph.py
        W = H = 256
        m = mask()
        assert len(m) == H and len(m[0]) == W, (len(m), len(m[0]))
        tiles = [fg if m[y][x] else bg(x, y) for y in range(H) for x in range(W)]
        chk_path = f"{HERE}/foss-for-all.chk"
        out = f"{HERE}/foss-for-all.scm"
    else:
        print("mode calib|glyph required")
        return 2
    data = build_chk(W, H, tiles, "foss-for-all")
    open(chk_path, "wb").write(data)
    rc, so, se = wrap(chk_path, out)
    secs = sections(data)
    mt = struct.unpack("<%dH" % (W * H), secs["MTXM"])
    distinct = sorted(set(mt))
    print(f"{mode}: chk {len(data)} B  MTXM {len(secs['MTXM'])}  ISOM {len(secs['ISOM'])} "
          f"DIM {struct.unpack('<HH', secs['DIM '])}  distinct terrain {len(distinct)} {distinct[:6]} "
          f"mkmpq rc {rc} {so} {se}")
    print("wrote", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
