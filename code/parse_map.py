#!/usr/bin/env python3
"""Parse SCMDraft 2 .scm file to read terrain tile data."""
import struct, mpyq

MAP_PATH = "/home/howard/scmdraft-maps/foss-for-all/foss-for-all.scm"

archive = mpyq.MPQArchive(MAP_PATH, listfile=False)

print("Hash table entries:")
for name, entry in archive.entries.items():
    print(f"  {name}: offset={entry.offset}, size={entry.size}, flags=0x{entry.flags:08X}")

def read_decrypted_file(archive, filename):
    entry = archive.entries.get(filename)
    if not entry:
        return None
    key = archive._hash_string(filename.encode("utf-8"), 1)
    archive.file.seek(entry.offset)
    raw_data = archive.file.read(entry.size)
    if entry.flags & mpyq.MPQ_FILE_ENCRYPTED:
        decrypted = archive._decrypt(raw_data, key)
        return decrypted
    return raw_data

known_files = [
    "MAP ", "UNITS", "TILE", "DETAIL", "STRATUM", "MASK",
    "TERRAIN", "unit", "UNITSECT", "tile0", "wav", "wnames",
    "script", "wnames2", "dir", "wrkproc"
]

print("\nTrying known SC map entries:")
for fname in known_files:
    if fname in archive.entries:
        print(f"  Found: {fname!r}")
        data = read_decrypted_file(archive, fname)
        if data:
            print(f"    Size: {len(data)} bytes")
            print(f"    First 32 bytes: {data[:32].hex()}")
        else:
            print(f"    Failed to read")
    else:
        for name in archive.entries:
            if name.upper() == fname.upper():
                print(f"  Found: {name!r}")
                data = read_decrypted_file(archive, name)
                if data:
                    print(f"    Size: {len(data)} bytes")
                    print(f"    First 32 bytes: {data[:32].hex()}")
                break
        else:
            print(f"  NOT FOUND: {fname!r}")

archive.close()
