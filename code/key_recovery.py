#!/usr/bin/env python3
"""Known-plaintext recovery of the MPQ file-crypt seed for StarCraft map CHK blobs.

Observed on the target's own map files (Bottleneck, Boxer): every block in these MPQs is stored as
[u32 0x00000008][u32 stored_length][payload], where payload for the small unencrypted blocks is
[u16 comp_type][zlib stream] (comp_type 2) or plain text. The CHK blob is stored as
[u32 8][u32 length][encrypted payload]. Known leading plaintext therefore gives the initial seed1:
cipher0 = plain0 XOR (seed1 + (0xEEEEEEEE + TABLE[0x400 + (seed1 & 0xFF)])).

Read-only. Pure Python. No third-party binary, no game data leaves the target.
"""
import glob
import os
import struct
import zlib


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


def mhash(name, htype):
    s1, s2 = 0x7FED7FED, 0xEEEEEEEE
    for ch in name.upper():
        c = ord(ch)
        v = TABLE[(htype << 8) + c]
        s1 = (v ^ (s1 + s2)) & 0xFFFFFFFF
        s2 = (c + s1 + s2 + (s2 << 5) + 3) & 0xFFFFFFFF
    return s1


def rot(s1):
    return (((~s1 << 0x15) + 0x11111111) | (s1 >> 0x0B)) & 0xFFFFFFFF


def dec_table(data, key):
    """Decrypt a hash/block table (1024-entry reset period, as the target's maps use)."""
    s1, s2 = key & 0xFFFFFFFF, 0xEEEEEEEE
    out = bytearray()
    for i in range(len(data) // 4):
        if i and i % 0x1000 == 0:
            s2 = 0xEEEEEEEE
        s2 = (s2 + TABLE[0x400 + (s1 & 0xFF)]) & 0xFFFFFFFF
        v = struct.unpack("<I", data[i * 4:i * 4 + 4])[0] ^ ((s1 + s2) & 0xFFFFFFFF)
        s1 = rot(s1)
        s2 = (v + s2 + (s2 << 5) + 3) & 0xFFFFFFFF
        out += struct.pack("<I", v)
    return bytes(out)


def seed_candidates(cipher0, plain0):
    k = (cipher0 ^ plain0) & 0xFFFFFFFF
    target = (k - 0xEEEEEEEE) & 0xFFFFFFFF
    return [s1 for lb in range(256)
            if ((s1 := (target - TABLE[0x400 + lb]) & 0xFFFFFFFF) & 0xFF) == lb]


def decrypt_chunk(cipher, s1, s2=0xEEEEEEEE):
    out = bytearray()
    for i in range(len(cipher) // 4):
        s2 = (s2 + TABLE[0x400 + (s1 & 0xFF)]) & 0xFFFFFFFF
        v = struct.unpack("<I", cipher[i * 4:i * 4 + 4])[0] ^ ((s1 + s2) & 0xFFFFFFFF)
        s1 = rot(s1)
        s2 = (v + s2 + (s2 << 5) + 3) & 0xFFFFFFFF
        out += struct.pack("<I", v)
    return bytes(out), s1, s2


def decrypt_blob(cipher, key, mode):
    """mode: none | reseed512 | s2only512 | none_then_zlib_check"""
    out = bytearray()
    s1, s2 = key, 0xEEEEEEEE
    n = len(cipher) // 4
    for base in range(0, n, 512):
        part = cipher[base * 4:(base + 512) * 4]
        chunk, s1, s2 = decrypt_chunk(part, s1, s2)
        out += chunk
        if mode == "reseed512":
            s1, s2 = key, 0xEEEEEEEE
        elif mode == "s2only512":
            s2 = 0xEEEEEEEE
    return bytes(out)


def parse(path):
    raw = open(path, "rb").read()
    assert raw[:4] == b"MPQ\x1a", path
    hdr = struct.unpack("<2I2H4I", raw[4:32])
    _, arch_size, ver, shift, hash_off, block_off, hash_n, block_n = hdr
    ht = dec_table(raw[hash_off:hash_off + hash_n * 16], mhash("(hash table)", 3))
    bt = dec_table(raw[block_off:block_off + block_n * 16], mhash("(block table)", 3))
    blocks = [struct.unpack("<4I", bt[i * 16:i * 16 + 16]) for i in range(block_n)]
    ents = []
    for i in range(hash_n):
        ha, hb, lc, flags, bidx = struct.unpack("<2I2HI", ht[i * 16:i * 16 + 16])
        if bidx != 0xFFFFFFFF and bidx < block_n and ha != 0xFFFFFFFF:
            ents.append((ha, hb, lc, bidx))
    return raw, (ver, shift, hash_n, block_n), blocks, ents


NAMES = {
    mhash("(listfile)", 1): "(listfile)",
    mhash("staredit\\scenario.chk", 1): "staredit\\scenario.chk",
    mhash("(attributes)", 1): "(attributes)",
    mhash("(signature)", 1): "(signature)",
}


def try_decompress(payload):
    """Return (ok, text) for a decrypted payload, trying the observed [u32 8][u32 len] prefix."""
    cands = []
    if payload[:4] == b"\x08\x00\x00\x00":
        cands.append(payload[8:])
    cands.append(payload)
    for body in cands:
        if body[:2] == b"\x02\x78":
            try:
                return zlib.decompress(body[2:]), "zlib"
            except Exception:
                pass
        try:
            return zlib.decompress(body), "zlib-raw-head"
        except Exception:
            pass
    return None, None


def attack(path, verbose=True):
    raw, meta, blocks, ents = parse(path)
    ver, shift, hash_n, block_n = meta
    print(f"== {os.path.basename(path)} shift {shift} blocks {block_n}")
    for ha, hb, lc, bidx in ents:
        off, size, asize, bflags = blocks[bidx]
        nm = NAMES.get(ha, "?")
        enc = bool(bflags & 0x00010000)
        print(f"  {nm} block {bidx} off {off} size {size} arch {asize} flags {bflags:08X} enc {enc}")
        if not enc:
            body = raw[off:off + size]
            plain, kind = try_decompress(body)
            if plain is not None:
                print(f"    readable ({kind}) {len(plain)}: {plain[:60]!r}")
            else:
                print(f"    raw {body[:40]!r}")
            continue
        cipher = raw[off:off + size]
        c0 = struct.unpack("<I", cipher[0:4])[0]
        for label, p0 in (("u32_8", 8), ("zlib_head", 0x789C7802), ("zero", 0), ("ver_head", 0x20524556)):
            for s1 in seed_candidates(c0, p0):
                head, ns1, ns2 = decrypt_chunk(cipher[:40], s1)
                dws = struct.unpack("<10I", head)
                plausible = (dws[0] == p0) and (
                    (label == "u32_8" and abs(dws[1] - (size - 8)) < 4096)
                    or (label == "zlib_head" and head[4:6] == b"\x02\x78")
                )
                print(f"    cand {label} seed1 {s1:08X} head {head[:16].hex()} plausible={plausible}")
                if not plausible:
                    continue
                for mode in ("none", "reseed512", "s2only512"):
                    plain = decrypt_blob(cipher, s1, mode)
                    data, kind = try_decompress(plain)
                    if data is not None and data[:4] == b"VER ":
                        print(f"    *** DECRYPTED {nm}: mode {mode} seed1 {s1:08X} {kind} chk {len(data)} bytes")
                        return (path, nm, s1, mode, data)
                    if plain[:8] == b"\x08\x00\x00\x00" or plain[:4] == b"VER ":
                        print(f"    mode {mode} head {plain[:16].hex()}")
    return None


def main():
    pats = ("~/game-data/sc-clean/Starcraft/maps/(2)River Crossing.scm",
            "~/game-data/sc-clean/Starcraft/maps/(2)Bottleneck.scm",
            "~/game-data/sc-clean/Starcraft/maps/(2)Boxer.scm",
            "~/game-data/sc-clean/Starcraft/maps/(3)Holy Ground.scm")
    for p in [os.path.expanduser(x) for x in pats]:
        res = attack(p)
        if res:
            path, nm, seed1, mode, data = res
            out = "/tmp/harvested.chk"
            open(out, "wb").write(data)
            print(f"WROTE {out} {len(data)} bytes from {path} seed {seed1:08X} mode {mode}")
            return


if __name__ == "__main__":
    main()
