#!/usr/bin/env python3
"""Build a StarCraft map: unencrypted combined CHK (staredit\scenario.chk) wrapped in a fresh MPQ.
Terrain is written one u16 per tile into MTXM and TILE from a fill function. No encryption."""
import struct, sys, zlib

# ---- MPQ name hashing (uppercase, standard MPQ HASH_A/HASH_B), no external deps ----
def _enc_table():
    seed=0x00100001; tab={}
    for i in range(256):
        idx=i
        for j in range(5):
            seed=(seed*125+3)%0x2AAAAB; t1=(seed&0xFFFF)<<0x10
            seed=(seed*125+3)%0x2AAAAB; t2=(seed&0xFFFF)
            tab[idx]=t1|t2; idx+=0x100
    return tab
TABLE=_enc_table()
def mhash(name, htype):
    s1=0x7FED7FED; s2=0xEEEEEEEE
    for ch in name.upper():
        c=ord(ch); v=TABLE[(htype<<8)+c]
        s1=(v^(s1+s2))&0xFFFFFFFF
        s2=(c+s1+s2+(s2<<5)+3)&0xFFFFFFFF
    return s1

MPQ_EXISTS=0x80000000; MPQ_SINGLE=0x01000000

def crypt(data, key):
    """MPQ decrypt (symmetric-in-name only): seed updates with the decrypted value."""
    s1=key&0xFFFFFFFF; s2=0xEEEEEEEE; out=bytearray()
    for i in range(len(data)//4):
        if i and i%0x1000==0: s2=0xEEEEEEEE
        s2=(s2+TABLE[0x400+(s1&0xFF)])&0xFFFFFFFF
        v=struct.unpack("<I", data[i*4:i*4+4])[0] ^ ((s1+s2)&0xFFFFFFFF)
        s1=(((~s1<<0x15)+0x11111111)|(s1>>0x0B))&0xFFFFFFFF
        s2=(v+s2+(s2<<5)+3)&0xFFFFFFFF
        out+=struct.pack("<I", v)
    return bytes(out)

def crypt_enc(data, key):
    """MPQ encrypt: seed updates with the PLAINTEXT input value (so decrypt inverts it)."""
    s1=key&0xFFFFFFFF; s2=0xEEEEEEEE; out=bytearray()
    for i in range(len(data)//4):
        if i and i%0x1000==0: s2=0xEEEEEEEE
        s2=(s2+TABLE[0x400+(s1&0xFF)])&0xFFFFFFFF
        plain=struct.unpack("<I", data[i*4:i*4+4])[0]
        ciph=plain ^ ((s1+s2)&0xFFFFFFFF)
        s1=(((~s1<<0x15)+0x11111111)|(s1>>0x0B))&0xFFFFFFFF
        s2=(plain+s2+(s2<<5)+3)&0xFFFFFFFF
        out+=struct.pack("<I", ciph)
    return bytes(out)

def build_mpq(files):
    # files: list of (name, bytes). Store each single-unit, unencrypted, uncompressed.
    HASH_ENTRIES=1024
    hdr_size=32
    data_off=hdr_size
    blocks=[]; offset=data_off
    for name, blob in files:
        blocks.append((offset, len(blob), len(blob), MPQ_EXISTS|MPQ_SINGLE))
        offset+=len(blob)
    hash_off=offset
    block_off=hash_off+HASH_ENTRIES*16
    archive_size=block_off+len(blocks)*16
    # header matches mpyq MPQFileHeader struct '<4s2I2H4I' (28 bytes) + 4 reserved = 32
    out=bytearray()
    out+=b"MPQ\x1a"
    out+=struct.pack("<I",hdr_size)          # header_size
    out+=struct.pack("<I",archive_size)      # archive_size (u32 for v0)
    out+=struct.pack("<H",0)                # format_version
    out+=struct.pack("<H",3)                # sector_size_shift
    out+=struct.pack("<I",hash_off)         # hash_table_offset
    out+=struct.pack("<I",block_off)        # block_table_offset
    out+=struct.pack("<I",HASH_ENTRIES)     # hash_table_entries
    out+=struct.pack("<I",len(blocks))      # block_table_entries
    assert len(out)==32, len(out)
    # file data
    for i,(name,blob) in enumerate(files):
        out+=blob
    # hash table (then encrypt with the standard hash-table key, matching the target maps' layout)
    ht=bytearray()
    for i,(name,_) in enumerate(files):
        ha=mhash(name,1); hb=mhash(name,2)
        ht+=struct.pack("<2I2HI", ha, hb, 0, 0, i)
    for _ in range(HASH_ENTRIES-len(files)):
        ht+=struct.pack("<2I2HI",0xFFFFFFFF,0xFFFFFFFF,0,0,0xFFFFFFFF)
    out+=crypt_enc(ht, mhash("(hash table)",3))
    # block table (encrypted with the standard block-table key)
    bt=bytearray()
    for off,size,asize,flags in blocks:
        bt+=struct.pack("<4I", off, asize, size, flags)
    out+=crypt_enc(bt, mhash("(block table)",3))
    return bytes(out)

def section(name, data):
    assert len(name)==4
    return struct.pack("<4sI", name.encode("latin1"), len(data)) + data

def build_chk(W, H, fill, era=4, ver=205):
    n=W*H
    tiles=[fill(x,y) for y in range(H) for x in range(W)]  # left-to-right, top-to-bottom
    mtxm=b"".join(struct.pack("<H",t) for t in tiles)
    tile=b"".join(struct.pack("<H",t) for t in tiles)
    isom=b"\x00" * ((W//2 + 1) * (H + 1) * 4)
    chk=bytearray()
    chk+=section("VER ", struct.pack("<H",ver))
    chk+=section("IVE2", struct.pack("<H",11))
    chk+=section("IVER", struct.pack("<H",10))
    vcod=b"\x00"*(256*4)+b"\x00"*16
    chk+=section("VCOD", vcod)
    ownr=bytes([1]*8+[0]*3+[7])  # players 1-8 computer, 9-11 inactive, 12 neutral
    chk+=section("OWNR", ownr)
    chk+=section("ERA ", struct.pack("<H",era))
    chk+=section("DIM ", struct.pack("<HH",W,H))
    side=bytes([1]*8+[7]*3+[4])
    chk+=section("SIDE", side)
    chk+=section("MTXM", mtxm)
    chk+=section("UNIT", b"")
    chk+=section("ISOM", isom)
    chk+=section("TILE", tile)
    chk+=section("DD2 ", b"")
    chk+=section("THG2", b"")
    chk+=section("MASK", b"\x00"*n)
    # STR: 1024 offsets then strings; name/desc strings
    strings=[b"testmap", b""]
    offsets=[]; pos=0
    for s in strings:
        offsets.append(pos); pos+=len(s)+1
    offsets+= [0]*(1024-len(offsets))
    body=b"".join(struct.pack("<H",o) for o in offsets)+b"\x00".join(strings)+b"\x00"
    chk+=section("STR ", struct.pack("<H",len(offsets))+body)
    chk+=section("SPRP", struct.pack("<HH",1,2))
    chk+=section("FORC", bytes([1,0,0,0]))
    return bytes(chk)

def write_map(path, W, H, fill):
    chk=build_chk(W,H,fill)
    listfile=("staredit\\scenario.chk\r\n").encode("latin1")
    files=[("staredit\\scenario.chk", chk), ("(listfile)", listfile)]
    mpq=build_mpq(files)
    open(path,"wb").write(mpq)
    return len(chk), len(mpq)

if __name__=="__main__":
    out=sys.argv[1] if len(sys.argv)>1 else "/tmp/calib.scm"
    W=H=64
    # calibration: 8x8 blocks of 8 tiles, each block a distinct candidate megatile value
    def fill(x,y):
        bx=x//8; by=y//8; idx=by*8+bx
        return idx  # 0..63 candidate megatiles
    c,m=write_map(out,W,H,fill)
    print("wrote",out,"chk",c,"mpq",m)
