#!/usr/bin/env python3
"""Probe candidate SCMDraft 2 temp/map files for a plaintext CHK and dump terrain sections.

Self-contained MPQ reader (no mpyq dependency) plus CHK section parser.
Read-only: nothing is written.
"""
import glob
import os
import struct
import zlib

# ---- MPQ name hashing and table decryption (same algorithm as /tmp/opencode/t0042/build_map.py) ----

def _enc_table():
    seed = 0x00100001
    tab = {}
    for i in range(256):
        idx = i
        for _ in range(5):
            seed = (seed * 125 + 3) % 0x2AAAAB
            t1 = (seed & 0xFFFF) << 0x10
            seed = (seed * 125 + 3) % 0x2AAAAB
            t2 = seed & 0xFFFF
            tab[idx] = t1 | t2
            idx += 0x100
    return tab


TABLE = _enc_table()
FLAGS = {
    0x00000001: "IMPLODE", 0x00000100: "COMPRESS", 0x00000200: "UNK200",
    0x00004000: "SECTOR_CRC", 0x00010000: "ENCRYPTED", 0x00020000: "FIX_KEY",
    0x01000000: "SINGLE_UNIT", 0x02000000: "DELETE", 0x80000000: "EXISTS",
}


def mhash(name, htype):
    s1, s2 = 0x7FED7FED, 0xEEEEEEEE
    for ch in name.upper():
        c = ord(ch)
        v = TABLE[(htype << 8) + c]
        s1 = (v ^ (s1 + s2)) & 0xFFFFFFFF
        s2 = (c + s1 + s2 + (s2 << 5) + 3) & 0xFFFFFFFF
    return s1


def decrypt(data, key):
    s1, s2 = key & 0xFFFFFFFF, 0xEEEEEEEE
    out = bytearray()
    for i in range(len(data) // 4):
        if i and i % 0x1000 == 0:
            s2 = 0xEEEEEEEE
        s2 = (s2 + TABLE[0x400 + (s1 & 0xFF)]) & 0xFFFFFFFF
        v = struct.unpack("<I", data[i * 4:i * 4 + 4])[0] ^ ((s1 + s2) & 0xFFFFFFFF)
        s1 = (((~s1 << 0x15) + 0x11111111) | (s1 >> 0x0B)) & 0xFFFFFFFF
        s2 = (v + s2 + (s2 << 5) + 3) & 0xFFFFFFFF
        out += struct.pack("<I", v)
    return bytes(out)


def flagstr(f):
    return "|".join(n for bit, n in sorted(FLAGS.items()) if f & bit) or hex(f)


def read_mpq(path):
    """Return (files, blocks) where files is a list of (name, data) for readable entries."""
    raw = open(path, "rb").read()
    if raw[:4] != b"MPQ\x1a":
        return None, None, "not an MPQ"
    hdr_size, arch_size, ver, shift, hash_off, block_off, hash_n, block_n = struct.unpack("<2I2H4I", raw[4:32])
    ht = decrypt(raw[hash_off:hash_off + hash_n * 16], mhash("(hash table)", 3))
    bt = decrypt(raw[block_off:block_off + block_n * 16], mhash("(block table)", 3))
    blocks = [struct.unpack("<4I", bt[i * 16:i * 16 + 16]) for i in range(block_n)]
    entries = []
    for i in range(hash_n):
        ha, hb, lc, flags, block = struct.unpack("<2I2HI", ht[i * 16:i * 16 + 16])
        if block != 0xFFFFFFFF:
            entries.append((ha, hb, lc, flags, block))
    # names from (listfile) if present, else unknown
    files = []
    for ha, hb, lc, flags, bidx in entries:
        if ha == 0xFFFFFFFF or hb == 0xFFFFFFFF or bidx >= block_n:
            continue
        off, size, asize, bflags = blocks[bidx]
        print(f"  block {bidx} off {off} size {size} arch {asize} flags {flagstr(bflags)} head {raw[off:off + 12].hex()}")
        if bflags & 0x00010000:
            continue
        data = raw[off:off + size]
        if bflags & 0x00000100:
            try:
                data = zlib.decompress(data[2:])
            except Exception:
                pass
        files.append((bidx, "(unnamed)", data, bflags, off, size, asize))
    return files, blocks, (hash_n, block_n, shift, arch_size)


def read_listfile(path):
    files, blocks, meta = read_mpq(path)
    return files, blocks, meta


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


def stats(name, data):
    vals = [struct.unpack("<H", data[i:i + 2])[0] for i in range(0, len(data) - 1, 2)]
    uniq = sorted(set(vals))
    groups = sorted({(v >> 4) & 0x7FF for v in vals})
    subs = sorted({v & 15 for v in vals})
    print(f"  {name}: len {len(data)} distinct {len(uniq)} min {min(vals) if vals else '-'} max {max(vals) if vals else '-'}")
    print(f"    groups {len(groups)} {groups[:30]}{'...' if len(groups) > 30 else ''}")
    print(f"    subtiles {subs[:20]}")


def probe(path):
    print(f"== {path} ({os.path.getsize(path)} B)")
    files, blocks, meta = read_mpq(path)
    if files is None:
        print(f"  {meta}")
        return
    print(f"  hash_entries {meta[0]} block_entries {meta[1]} sector_shift {meta[2]} arch {meta[3]}")
    for bidx, name, data, bflags, off, size, asize in files:
        print(f"  block {bidx} off {off} size {size} arch {asize} flags {flagstr(bflags)} head {data[:12].hex()}")
    # find scenario.chk: the block whose data starts with b'VER '
    for bidx, name, data, bflags, off, size, asize in files:
        if data[:4] == b"VER " or data[:4] == b"VCOD" or (asize > 20000 and data[:4] not in (b"MPQ\x1a",)):
            if data[:4] != b"VER ":
                print(f"  block {bidx} not plaintext CHK (head {data[:8].hex()})")
                continue
            print(f"  PLAINTEXT CHK in block {bidx}, {len(data)} bytes")
            secs = sections(data)
            covered = sum(8 + s for _, _, s in secs)
            print(f"  sections {len(secs)} covered {covered}/{len(data)}")
            for n, o, s in secs:
                print(f"    {n!r} off {o} size {s}")
            by = {n: data[o + 8:o + 8 + s] for n, o, s in secs}
            dim = by.get("DIM ")
            if dim and len(dim) >= 4:
                print(f"  DIM {struct.unpack('<HH', dim[:4])}")
            if "ERA " in by:
                print(f"  ERA {struct.unpack('<H', by['ERA '][:2])[0]}")
            for k in ("MTXM", "TILE", "ISOM"):
                if k in by:
                    stats(k, by[k])
            unit = by.get("UNIT")
            if unit:
                print(f"  UNIT len {len(unit)} nonzero {sum(1 for b in unit if b)}")
            return


def main():
    cands = []
    for pat in ("~/scmdraft-maps/**/*.tmp", "~/game-data/**/Scm*.tmp", "~/scmdraft-maps/**/*.scm"):
        cands += glob.glob(os.path.expanduser(pat), recursive=True)
    for c in sorted(set(cands)):
        try:
            probe(c)
        except Exception as exc:
            print(f"== {c}: probe error {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
