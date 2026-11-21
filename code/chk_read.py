import mpyq, struct, zlib, bz2, sys

TABLE = mpyq.MPQArchive.encryption_table

def raw_hash(name, htype):
    seed1 = 0x7FED7FED; seed2 = 0xEEEEEEEE
    for ch in name:
        c = ord(ch)
        v = TABLE[(htype << 8) + c]
        seed1 = (v ^ (seed1 + seed2)) & 0xFFFFFFFF
        seed2 = (c + seed1 + seed2 + (seed2 << 5) + 3) & 0xFFFFFFFF
    return seed1

def crypt(data, key):
    seed1 = key & 0xFFFFFFFF; seed2 = 0xEEEEEEEE; out = bytearray()
    for i in range(len(data) // 4):
        if i and i % 0x1000 == 0: seed2 = 0xEEEEEEEE
        seed2 = (seed2 + TABLE[0x400 + (seed1 & 0xFF)]) & 0xFFFFFFFF
        v = struct.unpack("<I", data[i*4:i*4+4])[0] ^ ((seed1 + seed2) & 0xFFFFFFFF)
        seed1 = (((~seed1 << 0x15) + 0x11111111) | (seed1 >> 0x0B)) & 0xFFFFFFFF
        seed2 = (v + seed2 + (seed2 << 5) + 3) & 0xFFFFFFFF
        out += struct.pack("<I", v)
    return bytes(out)

def dq_any(data):
    if not data: return None
    t = data[0]
    try:
        if t == 0: return data
        if t == 2: return zlib.decompressobj(15).decompress(data[1:])
        if t == 16: return bz2.decompress(data[1:])
    except Exception: return None
    return None

def parse_chk(data):
    i=0; secs=[]
    while i+8 <= len(data):
        name=data[i:i+4]; size=struct.unpack('<I', data[i+4:i+8])[0]
        if not all(32<=b<=126 for b in name): break
        secs.append((name,size,i))
        if size>0x80000: break
        i += 8+size
    return secs

if __name__=="__main__":
    p=sys.argv[1]
    ar=mpyq.MPQArchive(p,listfile=False)
    NAME="staredit\\scenario.chk"
    key=raw_hash(NAME,3)
    print("file key (case-preserving) 0x%08X"%key)
    # listfile sanity
    bl=ar.block_table[3]; ar.file.seek(bl.offset); rawl=ar.file.read(bl.archived_size)
    k2=raw_hash("(listfile)",3)
    d2=crypt(rawl+b"\0"*((-len(rawl))%4),k2)[:len(rawl)]
    print("listfile key 0x%08X dec0:"%k2, d2[:12].hex(), "->dq:", (dq_any(d2) or b"")[:40])
    # blob
    bi=max(range(len(ar.block_table)), key=lambda i: ar.block_table[i].size)
    be=ar.block_table[bi]; ar.file.seek(be.offset); raw=ar.file.read(be.archived_size)
    d=crypt(raw,key)
    print("blob dec0:", d[:16].hex())
    out=dq_any(d)
    src="decrypted-decompressed"
    if out is None:
        out=d; src="decrypted-raw"
    print(src,"len",len(out))
    secs=parse_chk(out)
    for n,s,o in secs: print(f"   {n!r} size={s} @ {o}")
    open("/tmp/chk_dec.bin","wb").write(out)
