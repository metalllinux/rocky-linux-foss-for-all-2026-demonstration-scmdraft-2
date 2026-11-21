#!/usr/bin/env python3
"""Build the max-extent (256x256) test map: terrain written one u16 per tile from a bitmap mask.
Two shapes: a filled silhouette (no internal counters) and a block letterform WITH an internal counter.
Also dumps the intended mask to PNG and a 4x Lanczos downscale (booth/minimap simulation) using PIL."""
import struct, sys
from build_map import write_map, mhash, crypt, crypt_enc, build_chk
BG=1; FG=2   # placeholder megatile values; real values calibrated in SCMDraft next pass

W=H=256
def fill(x,y):
    # Shape 1: filled circle silhouette, center (72,128), radius 70
    dx=x-72; dy=y-128
    if dx*dx+dy*dy <= 70*70:
        return FG
    # Shape 2: block letter "O" with an internal counter (hole), region x[150..230] y[70..190]
    if 150<=x<=230 and 70<=y<=190:
        # outer filled
        inner = (170<=x<=210) and (100<=y<=160)   # hole => counter
        return BG if inner else FG
    return BG

if __name__=="__main__":
    out="/home/howard/scmdraft-maps/probe/max256.scm"
    c,m=write_map(out,W,H,fill)
    print("wrote",out,"chk",c,"mpq",m)
    # dump mask + booth-sim via PIL
    from PIL import Image
    img=Image.new("L",(W,H))
    px=img.load()
    fgcount=0
    for y in range(H):
        for x in range(W):
            v=fill(x,y)
            px[x,y]= 255 if v==FG else 40
            if v==FG: fgcount+=1
    img.save("/home/howard/scmdraft-maps/probe/mask_full.png")
    small=img.resize((W//4,H//4), Image.LANCZOS)
    small.save("/home/howard/scmdraft-maps/probe/mask_booth4x.png")
    print("fg tiles:",fgcount,"of",W*H,"coverage=%.3f"%(fgcount/(W*H)))
    # foreground coverage by simple value fraction (mask): white fraction
    import collections
    print("mask PNG + 4x booth-sim written")
