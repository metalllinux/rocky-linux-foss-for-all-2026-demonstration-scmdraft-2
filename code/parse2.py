#!/usr/bin/env python3
"""Inspect a StarCraft .scm map MPQ: entry names, sizes, MAP header, terrain array dimensions."""
import struct, sys, mpyq

path = sys.argv[1]
ar = mpyq.MPQArchive(path, listfile=False)

print("== hash-table entries ==")
for name, e in ar.entries.items():
    print(f"  {name!r}: offset={e.offset} size={e.size} flags=0x{e.flags:08X}")

# candidate names with exact-case variants (SC entries are hash-looked-up, case matters)
cands = [
    "MAP ", "map ", "MAP", "map",
    "UNITS", "units", "unit", "Unit",
    "TILE", "tile", "TERRAIN", "terrain",
    "STRATUM", "stratum", "MASK", "mask", "DETAIL", "detail",
    "tile0", "TILE0", "wav", "wnames", "wnames2", "script",
    "UNITSECT", "unitsect", "dir", "wrkproc", "winattr", "trigger",
    "collision", "SMETXMPQ", "(listfile)",
]

def readname(name):
    # try as-is, then try to find a hash-table entry that hashes to it
    try:
        return ar.read_file(name)
    except Exception:
        return None

print("\n== reading candidate entries ==")
data = {}
for name in cands:
    d = readname(name)
    if d is not None:
        data[name] = d
        print(f"  {name!r}: len={len(d)}  head={d[:16].hex()}")

# MAP header
mapd = data.get("MAP ") or data.get("map ") or data.get("MAP") or data.get("map")
if mapd:
    w, h = struct.unpack("<HH", mapd[0:4])
    print(f"\nMAP header: bytes={len(mapd)} width={w} height={h}")
    print(f"  raw: {mapd[:17].hex()}")
    for off in (4, 6, 8, 10, 12, 14):
        if len(mapd) >= off + 2:
            print(f"  u16@{off}={struct.unpack('<H', mapd[off:off+2])[0]}")

# terrain array dims vs W*H
WH = None
for nm in ("TILE", "tile0", "TERRAIN", "STRATUM", "MASK", "DETAIL"):
    if nm in data:
        n = len(data[nm])
        print(f"{nm}: {n} bytes")
ar.close()
