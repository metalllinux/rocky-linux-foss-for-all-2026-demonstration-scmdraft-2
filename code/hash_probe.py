import mpyq, struct, sys
p=sys.argv[1]
ar=mpyq.MPQArchive(p, listfile=False)
names=["MAP ","MAP","map","UNITS","units","unit","Unit","Units","TILE","TILEI","tile",
 "TILE0","tile0","TERRAIN","terrain","STRATUM","stratum","MASK","mask","DETAIL","detail",
 "wav","wnames","wnames2","script","UNITSECT","unitsect","dir","wrkproc","winattr",
 "trigger","Trigger","TRIGGERS","collision","M00","M01","MAP0","MAP1","MAP.0","M1.0","M2.0",
 "(listfile)","MAP2","MAP3","Map","map2","Map2","Tile","Terrain","Stratum","Mask","unit1"]
want={}
for he in ar.hash_table:
    if he.block_table_index not in (0xFFFFFFFF,0) and not(he.hash_a==0xFFFFFFFF and he.hash_b==0xFFFFFFFF):
        want[(he.hash_a,he.hash_b)]=("blk%d size=%d"%(he.block_table_index, ar.block_table[he.block_table_index].size))
for nm in names:
    ha=ar._hash(nm,"HASH_A"); hb=ar._hash(nm,"HASH_B")
    tag=want.get((ha,hb),"")
    print(f"{nm!r:<14} ha={ha:>10} hb={hb:>10} {tag}")
