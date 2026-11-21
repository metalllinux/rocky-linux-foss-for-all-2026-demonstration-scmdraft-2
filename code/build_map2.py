#!/usr/bin/env python3
"""TASK-0042 dispatch 2: corrected CHK writer.

Changes versus build_map.build_chk (the writer whose defects were named in the
terrain harvest, doc lines 1208-1230):
  - VER is the harvested 59, not 205.
  - VCOD is the harvested 1040-byte code table copied from rc.chk, not zeros.
  - ISOM is the full real size 4*(W+2)*(H+1) bytes, not the half size, and is
    filled with the flat brush value 0x10 (the flat default documented in the
    Unused Unprotector 2 source and the dominant value of Bottleneck), not zero.
  - MTXM/TILE use the harvested Jungle flat ground values 128 and 144 in an
    alternating pattern (River Crossing groups 8 and 9 at subtile 0), not
    arbitrary group*16 values and not groups 0 or 1.
Scalar player sections (OWNR, SIDE, FORC, ERA) are copied from the harvested
River Crossing CHK when present. Terrain arrays are written by this code.
"""
import struct
import sys

sys.path.insert(0, "/tmp/opencode/t0042")
import build_map as bm  # noqa: E402


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


def build_chk2(W, H, era_default=4):
    ref = sections(open("/tmp/opencode/t0042/rc.chk", "rb").read())
    n = W * H
    # harvested Jungle flat ground: group 8 (128) and group 9 (144), subtile 0, alternating
    def fill(x, y):
        return 128 if (x + y) % 2 == 0 else 144
    tiles = [fill(x, y) for y in range(H) for x in range(W)]
    mtxm = b"".join(struct.pack("<H", t) for t in tiles)
    tile = mtxm
    isom_entries = (W + 2) * (H + 1) * 2  # u16 entries; bytes = 4*(W+2)*(H+1)
    isom = struct.pack("<%dH" % isom_entries, *([0x10] * isom_entries))
    assert len(isom) == 4 * (W + 2) * (H + 1)

    ver = ref["VER "] if len(ref.get("VER ", b"")) >= 2 else struct.pack("<H", 59)
    vcod = ref["VCOD"] if len(ref.get("VCOD", b"")) == 256 * 4 + 16 else b"\x00" * (256 * 4 + 16)
    ownr = ref["OWNR"] if len(ref.get("OWNR", b"")) == 12 else bytes([1] * 8 + [0] * 3 + [7])
    era = ref["ERA "] if len(ref.get("ERA ", b"")) >= 2 else struct.pack("<H", era_default)
    side = ref["SIDE"] if len(ref.get("SIDE", b"")) == 12 else bytes([1] * 8 + [7] * 3 + [4])
    forc = ref["FORC"] if len(ref.get("FORC", b"")) else bytes([1, 0, 0, 0])

    chk = bytearray()
    chk += bm.section("VER ", ver)
    chk += bm.section("IVE2", struct.pack("<H", 11))
    chk += bm.section("IVER", struct.pack("<H", 10))
    chk += bm.section("VCOD", vcod)
    chk += bm.section("OWNR", ownr)
    chk += bm.section("ERA ", era)
    chk += bm.section("DIM ", struct.pack("<HH", W, H))
    chk += bm.section("SIDE", side)
    chk += bm.section("MTXM", mtxm)
    chk += bm.section("UNIT", b"")
    chk += bm.section("ISOM", isom)
    chk += bm.section("TILE", tile)
    chk += bm.section("DD2 ", b"")
    chk += bm.section("THG2", b"")
    chk += bm.section("MASK", b"\x00" * n)
    strings = [b"sl writer map", b""]
    offsets = []
    pos = 0
    for s in strings:
        offsets.append(pos)
        pos += len(s) + 1
    offsets += [0] * (1024 - len(offsets))
    body = b"".join(struct.pack("<H", o) for o in offsets) + b"\x00".join(strings) + b"\x00"
    chk += bm.section("STR ", struct.pack("<H", len(offsets)) + body)
    chk += bm.section("SPRP", struct.pack("<HH", 1, 2))
    chk += bm.section("FORC", forc)
    return bytes(chk)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/opencode/t0042/slB.chk"
    W = int(sys.argv[2]) if len(sys.argv) > 2 else 64
    H = int(sys.argv[3]) if len(sys.argv) > 3 else 64
    chk = build_chk2(W, H)
    open(out, "wb").write(chk)
    sec = sections(chk)
    print("wrote", out, "chk", len(chk),
          "ISOM bytes", len(sec["ISOM"]), "expect", 4 * (W + 2) * (H + 1),
          "MTXM bytes", len(sec["MTXM"]), "expect", W * H * 2,
          "VER", struct.unpack("<H", sec["VER "][:2])[0],
          "VCOD nonzero", sum(1 for b in sec["VCOD"] if b),
          "terrain set", sorted(set(struct.unpack("<%dH" % (W * H), sec["MTXM"])))[:4])
