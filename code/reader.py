import mpyq, struct, sys, zlib, bz2
from io import BytesIO

def file_key(ar, name):
    # MPQ crypt key = hash(name, type 3), same seeds as TABLE
    return ar._hash(name, "TABLE")

def decrypt(ar, data, key):
    return ar._decrypt(data, key)

def decompress(data):
    t = data[0]
    if t == 0:
        return data
    if t == 2:
        return zlib.decompress(data[1:], 15)
    if t == 16:
        return bz2.decompress(data[1:])
    raise RuntimeError("unsupported compression type %d" % t)

def read_fixed(ar, name):
    he = ar.get_hash_table_entry(name)
    if he is None:
        raise RuntimeError("no hash entry for %r" % name)
    bi = he.block_table_index
    if bi in (0, 0xFFFFFFFF):
        raise RuntimeError("bad block index %d" % bi)
    be = ar.block_table[bi]
    key = file_key(ar, name)
    off = be.offset + ar.header['offset']
    ar.file.seek(off)
    raw = ar.file.read(be.archived_size)
    single = bool(be.flags & mpyq.MPQ_FILE_SINGLE_UNIT)
    enc = bool(be.flags & mpyq.MPQ_FILE_ENCRYPTED)
    fix = bool(be.flags & mpyq.MPQ_FILE_FIX_KEY)
    comp = bool(be.flags & mpyq.MPQ_FILE_COMPRESS)
    crc = bool(be.flags & mpyq.MPQ_FILE_SECTOR_CRC)
    sector_size = 512 << ar.header['sector_size_shift']
    out = BytesIO()
    if single:
        data = raw
        if enc:
            # whole-file decryption: pad to dword
            pad = (-len(data)) % 4
            data = decrypt(ar, data + b'\0'*pad, key)[:len(raw)]
        if comp and (be.size > be.archived_size or True):
            data = decompress(data)
        out.write(data)
    else:
        sectors = be.size // sector_size + 1
        if crc:
            sectors += 1
        npos = sectors + 1
        positions = list(struct.unpack('<%dI' % npos, raw[:4*npos]))
        for i in range(sectors - (1 if crc else 0)):
            s = raw[positions[i]:positions[i+1]]
            if not s:
                continue
            if enc:
                slen = len(s)
                pad = (-slen) % 4
                s = decrypt(ar, s + b'\0'*pad, key if fix else key + i)[:slen]
            if comp:
                s = decompress(s)
            out.write(s)
    return out.getvalue(), be

if __name__ == "__main__":
    p = sys.argv[1]
    ar = mpyq.MPQArchive(p, listfile=False)
    print("blocks:", len(ar.block_table))
    for i,be in enumerate(ar.block_table): print("  blk",i,be)
    names = [n for n in ar.hash_table if n.block_table_index not in (0,0xFFFFFFFF)]
    print("trying to read known/unknown names via key hash; start with (listfile)")
    data, be = read_fixed(ar, "(listfile)")
    print("(listfile) decrypted len", len(data), repr(data))
