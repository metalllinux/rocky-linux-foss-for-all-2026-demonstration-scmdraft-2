import mpyq, struct, sys, glob, os
cands=["MAP ","UNITS","unit","TILE","TILEI","TERRAIN","STRATUM","MASK","tile0","wav",
 "wnames","wnames2","script","UNITSECT","dir","wrkproc","winattr","trigger"]
for p in sorted(glob.glob("/home/howard/game-data/sc-clean/Starcraft/maps/*.scm")):
    try:
        ar=mpyq.MPQArchive(p, listfile=False)
    except Exception as e:
        print(os.path.basename(p), "ERR", e); continue
    # try to find classic names via hash table
    resolved=[]
    for nm in cands:
        he=ar.get_hash_table_entry(nm)
        if he and he.block_table_index not in (0,0xFFFFFFFF):
            be=ar.block_table[he.block_table_index]
            resolved.append((nm,be.size,be.flags))
    nblk=len(ar.block_table)
    print(f"{os.path.basename(p):30} blocks={nblk} resolved={len(resolved)}")
    if resolved:
        for nm,sz,fl in resolved:
            comp=bool(fl & mpyq.MPQ_FILE_COMPRESS); enc=bool(fl & mpyq.MPQ_FILE_ENCRYPTED)
            print(f"   {nm:10} size={sz:8} flags=0x{fl:08X} comp={comp} enc={enc}")
