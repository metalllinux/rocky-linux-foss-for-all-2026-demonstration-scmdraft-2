#!/usr/bin/env python3
"""Inspect a StarCraft .scm MPQ using mpyq internals: names, block offset/size/flags, raw vs decompressed."""
import struct, sys, mpyq

path = sys.argv[1]
ar = mpyq.MPQArchive(path, listfile=False)

print("hash_table entries:", len(ar.hash_table), " block_table entries:", len(ar.block_table))

cands = ["MAP ", "map ", "UNITS", "unit", "TILE", "tile0", "TERRAIN", "STRATUM",
         "MASK", "DETAIL", "wav", "wnames", "wnames2", "script", "UNITSECT",
         "dir", "wrkproc", "winattr", "trigger", "(listfile)", "collision"]

found = {}
for name in cands:
    try:
        he = ar.get_hash_table_entry(name)
    except Exception as ex:
        he = None
    if he is None:
        continue
    idx = he.block_table_index
    if idx is None or idx >= len(ar.block_table) or idx == 0xFFFFFFFF:
        print(f"  {name!r}: hash present, block idx invalid {idx}")
        continue
    be = ar.block_table[idx]
    dec = None
    try:
        dec = ar.read_file(name)
    except Exception as ex:
        print(f"  {name!r}: read fail {ex}")
    found[name] = (he, be, dec)
    flags = be.flags
    comp = bool(flags & mpyq.MPQ_FILE_COMPRESS)
    enc = bool(flags & mpyq.MPQ_FILE_ENCRYPTED)
    print(f"  {name!r}: block idx={idx} offset={be.offset} size={be.size} "
          f"csize={getattr(be,'compressed_size',None)} flags=0x{flags:08X} comp={comp} enc={enc} "
          f"dec_len={len(dec) if dec is not None else None}")

mapd = (found.get("MAP ") or found.get("map "))
if mapd and mapd[2]:
    m = mapd[2]
    w, h = struct.unpack("<HH", m[0:4])
    print(f"\nMAP: W={w} H={h} len={len(m)} raw={m[:17].hex()}")
    for off in (4,6,8,10,12,14):
        if len(m)>=off+2: print(f"  u16@{off}={struct.unpack('<H',m[off:off+2])[0]}")

ar.close()
