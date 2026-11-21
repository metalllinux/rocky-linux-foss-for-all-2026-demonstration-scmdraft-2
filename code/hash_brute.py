import mpyq, sys
p=sys.argv[1]
ar=mpyq.MPQArchive(p,listfile=False)
want={}
for he in ar.hash_table:
    if he.block_table_index not in (0,0xFFFFFFFF):
        be=ar.block_table[he.block_table_index]
        want[(he.hash_a,he.hash_b)]="blk%d size=%d flags=0x%08X"%(he.block_table_index,be.size,be.flags)
print("target hashes:")
for k,v in want.items(): print("  ",k,v)

base=["MAP ","MAP","map","UNITS","unit","Unit","TILE","TILEI","tile","TILE0","tile0",
 "TERRAIN","STRATUM","MASK","DETAIL","wav","wnames","wnames2","script","UNITSECT",
 "dir","wrkproc","winattr","trigger","collision","MAP.0","MAP.1","MAP.2"]
names=list(base)
for n in base:
    names.append(n+" "); names.append(" "+n)
for i in range(0,40):
    names.append("MAP"+str(i)); names.append("M%02d"%i); names.append("M"+str(i))
    names.append("MAP%d "%i); names.append("MAP.%d"%i)
names.append("(listfile)")
found=False
for nm in names:
    ha=ar._hash(nm,"HASH_A"); hb=ar._hash(nm,"HASH_B")
    if (ha,hb) in want:
        print(f"MATCH {nm!r} -> {want[(ha,hb)]}")
        found=True
if not found: print("NO MATCH in dictionary")
