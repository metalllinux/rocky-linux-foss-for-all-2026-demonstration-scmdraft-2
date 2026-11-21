#!/usr/bin/env python3
"""TASK-0042 dispatch 2 content bisect, wrapped by mkmpq (StormLib).

slD: harvested River Crossing CHK with only MTXM and TILE replaced by the writer's
     128/144 alternating flat values (same sizes, ISOM and MASK untouched).
     Tests whether the writer's terrain VALUES render inside a real CHK shell.
slE: minimal writer CHK at 64x64 with the layout defects fixed against the harvest:
     STR without the spurious u16 count header (1024 offsets then strings),
     MASK 0xFF like every harvested map, no IVE2 (real maps do not carry it),
     IOWN copied from the harvest, ISOM at 4*(W+2)*(H+1) filled 0x10,
     terrain 128/144 alternating.
"""
import struct
import subprocess
import sys

sys.path.insert(0, "/tmp/opencode/t0042")
import build_map as bm  # noqa: E402
import build_map2 as b2  # noqa: E402

HERE = "/tmp/opencode/t0042"


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
    for n, o, s in sections(chk):
        if n == name:
            assert s == len(data), f"{name} size {s} != {len(data)}"
            return chk[:o + 8] + data + chk[o + 8 + s:]
    raise KeyError(name)


def checkerboard(W, H):
    vals = [(128 if (x + y) % 2 == 0 else 144) for y in range(H) for x in range(W)]
    return struct.pack("<%dH" % len(vals), *vals)


def build_slD():
    rc = open(f"{HERE}/rc.chk", "rb").read()
    W, H = struct.unpack("<HH", dict((n, rc[o + 8:o + 8 + s]) for n, o, s in sections(rc))["DIM "])
    mt = checkerboard(W, H)
    chk = replace(rc, "MTXM", mt)
    chk = replace(chk, "TILE", mt)
    return chk


def build_slE():
    rc = open(f"{HERE}/rc.chk", "rb").read()
    ref = {n: rc[o + 8:o + 8 + s] for n, o, s in sections(rc)}
    W, H = 64, 64
    mt = checkerboard(W, H)
    isom_entries = (W + 2) * (H + 1) * 2
    isom = struct.pack("<%dH" % isom_entries, *([0x10] * isom_entries))
    # STR in the documented real layout: u16[1024] offsets then NUL-terminated strings.
    strings = [b"sl writer map", b""]
    offsets = []
    pos = 0
    for s in strings:
        offsets.append(pos)
        pos += len(s) + 1
    offsets += [0] * (1024 - len(offsets))
    str_body = b"".join(struct.pack("<H", o) for o in offsets) + b"\x00".join(strings) + b"\x00"
    chk = bytearray()
    chk += bm.section("VER ", ref["VER "])
    chk += bm.section("IVER", ref["IVER"])
    chk += bm.section("VCOD", ref["VCOD"])
    chk += bm.section("IOWN", ref["IOWN"])
    chk += bm.section("OWNR", ref["OWNR"])
    chk += bm.section("ERA ", ref["ERA "])
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
    chk += bm.section("STR ", str_body)
    chk += bm.section("UPRP", ref["UPRP"])
    chk += bm.section("UPUS", ref["UPUS"])
    chk += bm.section("MRGN", ref["MRGN"])
    chk += bm.section("TRIG", b"")  # empty triggers section, same family as PUNI/UPGR
    chk += bm.section("MBRF", b"")
    chk += bm.section("SPRP", ref["SPRP"])
    chk += bm.section("FORC", ref["FORC"])
    chk += bm.section("WAV ", ref["WAV "])
    chk += bm.section("UNIS", ref["UNIS"])
    chk += bm.section("UPGS", ref["UPGS"])
    chk += bm.section("TECS", ref["TECS"])
    return bytes(chk)


def wrap(chk_name, mode="plain"):
    open(f"{HERE}/{chk_name}.chk", "wb").write({"slD": build_slD, "slE": build_slE}[chk_name]())
    r = subprocess.run(
        [f"{HERE}/mkmpq", f"{HERE}/sl{chk_name[-1]}.scm", mode,
         "staredit\\scenario.chk", ],
        capture_output=True, text=True)
    print(chk_name, r.returncode, r.stdout.strip(), r.stderr.strip())


if __name__ == "__main__":
    # mkmpq takes name=file pairs; build the chk files then invoke explicitly.
    open(f"{HERE}/slD.chk", "wb").write(build_slD())
    open(f"{HERE}/slE.chk", "wb").write(build_slE())
    for tag in ("D", "E"):
        r = subprocess.run([f"{HERE}/mkmpq", f"{HERE}/sl{tag}.scm", "plain",
                            "staredit\\scenario.chk=" + f"{HERE}/sl{tag}.chk"],
                           capture_output=True, text=True)
        print(tag, r.returncode, r.stdout.strip(), r.stderr.strip())
