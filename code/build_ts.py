#!/usr/bin/env python3
"""TASK-0042 contrast dispatch: build tileset-calibration and glyph maps on top of a
harvested reference CHK of ANY tileset, using the slE pipeline proven in dispatch 2/3
(harvested family sections, flat ISOM 4*(W+2)*(H+1) of 0x10, MTXM==TILE, MASK 0xFF,
mkmpq StormLib wrap). The tileset is whatever the reference CHK's ERA declares.

Modes:
  gridcalib <ref.chk> <out.base> <era>
      20x20 map, 4x4 blocks of 5x5 tiles, one harvested candidate terrain value per
      block, taken from ts-harvest/candidates.json for that era.
  pairtest <ref.chk> <out.base> <ground> <glyph>
      20x20 map, ground everywhere except a 12x20 glyph band (rows 4..15) written in
      the glyph value, to test the boundary for cliff texture.
  glyph <ref.chk> <out.base> <fg> <bgA> <bgB>
      256x256 map 1 design, glyph.py mask in `fg` over a `bgA`/`bgB` checkerboard.
"""
import json
import struct
import subprocess
import sys

sys.path.insert(0, "/tmp/opencode/t0042")
import build_map as bm  # section() helper only; build_mpq is NOT used

HERE = "/tmp/opencode/t0042"

# Sections copied verbatim from the reference map (tileset-appropriate tables).
COPY = ("VER ", "IVER", "VCOD", "IOWN", "OWNR", "ERA ", "SIDE", "PUNI", "UPGR", "PTEC",
        "UPRP", "UPUS", "MRGN", "SPRP", "FORC", "WAV ", "UNIS", "UPGS", "TECS")
# Sections written by this builder.
WRITE_MT = ("MTXM", "ISOM", "TILE")
ORDER = ["VER ", "IVER", "VCOD", "IOWN", "OWNR", "ERA ", "DIM ", "SIDE", "MTXM", "PUNI",
         "UPGR", "PTEC", "UNIT", "ISOM", "TILE", "DD2 ", "THG2", "MASK", "STR ", "UPRP",
         "UPUS", "MRGN", "TRIG", "MBRF", "SPRP", "FORC", "WAV ", "UNIS", "UPGS", "TECS"]


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
    """Real harvested layout: u16[1024] offsets then NUL-terminated strings, no leading count."""
    offsets = []
    pos = 0
    for s in strings:
        offsets.append(pos)
        pos += len(s) + 1
    offsets += [0] * (1024 - len(offsets))
    return b"".join(struct.pack("<H", o) for o in offsets) + b"\x00".join(strings) + b"\x00"


def build_chk(ref_path, W, H, tiles, name_str):
    assert len(tiles) == W * H
    assert all(0 <= t <= 0xFFFF for t in tiles)
    ref = sections(open(ref_path, "rb").read())
    for name in COPY:
        assert name in ref, f"reference {ref_path} lacks section {name!r}"
    mt = struct.pack("<%dH" % len(tiles), *tiles)
    n_entries = (W + 2) * (H + 1) * 2
    isom = struct.pack("<%dH" % n_entries, *([0x10] * n_entries))
    assert len(isom) == 4 * (W + 2) * (H + 1)
    mine = {
        "DIM ": struct.pack("<HH", W, H),
        "MTXM": mt,
        "UNIT": b"",
        "ISOM": isom,
        "TILE": mt,
        "DD2 ": b"",
        "THG2": b"",
        "MASK": b"\xff" * (W * H),
        "STR ": str_section([name_str.encode("latin1"), b""]),
        "TRIG": b"",
        "MBRF": b"",
    }
    chk = bytearray()
    for name in ORDER:
        data = mine[name] if name in mine else ref[name]
        chk += bm.section(name, data)
    return bytes(chk)


def wrap(chk_path, out_scm):
    import os
    # StormLib will not overwrite an existing archive; drop the previous build first.
    if os.path.exists(out_scm):
        os.remove(out_scm)
    r = subprocess.run([f"{HERE}/mkmpq", out_scm, "plain", "staredit\\scenario.chk=" + chk_path],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()


def main():
    mode, ref_path, out_base = sys.argv[1], sys.argv[2], sys.argv[3]
    if mode == "gridcalib":
        era = int(sys.argv[4])
        cands = json.load(open(f"{HERE}/ts-harvest/candidates.json"))[str(era)]
        assert len(cands) == 16, cands
        W = H = 20
        blk = 5  # 5x5 tiles per block, 4x4 blocks
        tiles = [cands[(y // blk) * 4 + (x // blk)] for y in range(H) for x in range(W)]
        name = f"{out_base.split('/')[-1]}-cal"
    elif mode == "pairtest":
        ground, glyph_v = int(sys.argv[4], 0), int(sys.argv[5], 0)
        W = H = 20
        tiles = [glyph_v if 4 <= y < 16 else ground for y in range(H) for x in range(W)]
        name = f"{out_base.split('/')[-1]}-pair"
    elif mode == "glyph":
        fg, bg_a, bg_b = (int(a, 0) for a in sys.argv[4:7])
        from glyph import mask
        W = H = 256
        m = mask()
        assert len(m) == H and len(m[0]) == W
        tiles = [fg if m[y][x] else (bg_a if (x + y) % 2 == 0 else bg_b)
                 for y in range(H) for x in range(W)]
        name = "foss-for-all"
    elif mode == "silhouette":
        # silhouette <ref.chk> <out.base> <fg> <bgA> <bgB> <maskname>
        # Same slE pipeline as glyph mode, but the mask is a filled silhouette from rocky.py
        # and the STR name is the out_base basename (the per-map directory name).
        fg, bg_a, bg_b, maskname = sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7]
        fg, bg_a, bg_b = (int(a, 0) for a in (fg, bg_a, bg_b))
        import rocky
        W = H = 256
        m = rocky.MASKS[maskname]()
        assert len(m) == H and len(m[0]) == W
        tiles = [fg if m[y][x] else (bg_a if (x + y) % 2 == 0 else bg_b)
                 for y in range(H) for x in range(W)]
        name = out_base.split("/")[-1]
    else:
        print("mode gridcalib|pairtest|glyph|silhouette required")
        return 2
    chk_path = f"{out_base}.chk"
    out_scm = f"{out_base}.scm"
    data = build_chk(ref_path, W, H, tiles, name)
    open(chk_path, "wb").write(data)
    rc, so, se = wrap(chk_path, out_scm)
    secs = sections(data)
    era = struct.unpack("<H", secs["ERA "] [0:2])[0]
    mt = struct.unpack("<%dH" % (len(secs["MTXM"]) // 2), secs["MTXM"])
    distinct = sorted(set(mt))
    print(f"{mode}: era {era} chk {len(data)} B MTXM {len(mt)} ISOM {len(secs['ISOM'])} "
          f"distinct {len(distinct)} {distinct[:8]} mkmpq rc {rc} {so} {se}")
    print("wrote", out_scm)
    return 0


if __name__ == "__main__":
    sys.exit(main())
