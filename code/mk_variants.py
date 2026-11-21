#!/usr/bin/env python3
"""Build test maps from a harvested real CHK plus writer-style terrain variants.

Usage: mk_variants.py <harvested.chk> <outdir>

Variants (all wrapped by build_map.build_mpq, the container proven to be accepted by SCMDraft 2):
  harvA.scm  control: the harvested map's own terrain arrays, unchanged.
  harvB.scm  writer-style terrain: uniform group*16 fill, ISOM at the writer's half size, ISOM zeros.
  harvC.scm  writer-style fill but with harvested values: modal 4x4 terrain window tiled over the map,
             ISOM at the real size filled with the harvested dominant ISOM value.
"""
import collections
import struct
import sys

sys.path.insert(0, "/tmp")
import build_map as bm  # noqa: E402


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


def replace(chk, name, data):
    """Replace one section's payload in place (same size required)."""
    for n, o, s in sections(chk):
        if n == name:
            assert s == len(data), f"{name} size {s} != replacement {len(data)}"
            return chk[:o + 8] + data + chk[o + 8 + s:]
    raise KeyError(name)


def resize(chk, name, data):
    """Replace one section's payload, allowing a different payload length."""
    for n, o, s in sections(chk):
        if n == name:
            head = chk[:o] + struct.pack("<4sI", name.encode("latin1"), len(data))
            return head + data + chk[o + 8 + s:]
    raise KeyError(name)


def u16s(data):
    return [struct.unpack("<H", data[i:i + 2])[0] for i in range(0, len(data) - 1, 2)]


def by_name(chk):
    return {n: chk[o + 8:o + 8 + s] for n, o, s in sections(chk)}


def modal_window(vals, W, H, size=4):
    """Return the most frequent size x size terrain window and its frequency."""
    cnt = collections.Counter()
    for y in range(0, H - size + 1):
        for x in range(0, W - size + 1):
            w = tuple(vals[(y + dy) * W + (x + dx)] for dy in range(size) for dx in range(size))
            cnt[w] += 1
    win, freq = cnt.most_common(1)[0]
    return win, freq


def tile_window(win, W, H, size=4):
    out = []
    for y in range(H):
        for x in range(W):
            out.append(win[(y % size) * size + (x % size)])
    return struct.pack("<%dH" % len(out), *out)


def main(chk_path, outdir):
    chk = open(chk_path, "rb").read()
    by = by_name(chk)
    W, H = struct.unpack("<HH", by["DIM "])
    mtxm, tile, isom = by["MTXM"], by["TILE"], by["ISOM"]
    mv = u16s(mtxm)
    isom_entries = len(u16s(isom))
    dom_isom = collections.Counter(u16s(isom)).most_common(1)[0]
    win, freq = modal_window(mv, W, H)
    print(f"harvest {W}x{H} ERA {struct.unpack('<H', by['ERA '][:2])[0]} "
          f"MTXM {len(mtxm)} ISOM {len(isom)} bytes ({isom_entries} entries) "
          f"dominant ISOM {dom_isom} modal 4x4 window freq {freq}")

    # A: control, terrain verbatim
    write(outdir + "/harvA.scm", chk)

    # D: terrain verbatim but ISOM payload zeroed in place. Isolates whether ISOM content matters.
    write(outdir + "/harvD.scm", replace(chk, "ISOM", b"\x00" * len(isom)))

    # B: the writer's own structure, 64x64, fill = harvested flat value (group 8, subtile 0).
    flat_val = 8 * 16
    b_chk = bm.build_chk(64, 64, lambda x, y: flat_val)
    write(outdir + "/harvB.scm", b_chk)

    # C: same writer fill, but ISOM at the harvested size (4*(W+2)*(H+1) bytes) and at the
    # harvested dominant ISOM value. Tests the writer's ISOM size and value at once.
    c_chk = bm.build_chk(64, 64, lambda x, y: flat_val)
    right_isom = struct.pack("<%dH" % (2 * (64 + 2) * (64 + 1)),
                             *([dom_isom[0]] * (2 * (64 + 2) * (64 + 1))))
    c_chk = resize(c_chk, "ISOM", right_isom)
    write(outdir + "/harvC.scm", c_chk)
    print("writer ISOM bytes for 64x64:", (64 // 2 + 1) * (64 + 1) * 4,
          "harvested-size ISOM bytes for 64x64:", 4 * (64 + 2) * (64 + 1))


def write(path, chk):
    files = [("staredit\\scenario.chk", chk), ("(listfile)", b"staredit\\scenario.chk\r\n")]
    open(path, "wb").write(bm.build_mpq(files))
    print("wrote", path)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
