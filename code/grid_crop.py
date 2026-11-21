#!/usr/bin/env python3
"""Gridded crop of the SCMDraft bottom-left tree so exact click coordinates can be read.
Grid lines every 25 source px, labels in SOURCE coordinates (x0,y0)+(x1,y1)."""
from PIL import Image, ImageDraw
import os, sys
base = "/tmp/opencode/t0042"
os.makedirs(f"{base}/montage", exist_ok=True)

def grid_crop(src, x0, y0, x1, y1, out, scale=3, step=25):
    im = Image.open(src).convert("RGB")
    c = im.crop((x0, y0, x1, y1))
    W, H = (x1 - x0), (y1 - y0)
    big = Image.new("RGB", (W * scale, H * scale + 20), (255, 255, 255))
    big.paste(c.resize((W * scale, H * scale)), (0, 20))
    d = ImageDraw.Draw(big)
    for gx in range(x0, x1 + 1, step):
        px = (gx - x0) * scale
        col = (255, 0, 0) if (gx - x0) % 50 == 0 else (200, 200, 200)
        d.line([(px, 20), (px, 20 + H * scale)], fill=col)
        if (gx - x0) % 50 == 0:
            d.text((px + 1, 4), str(gx), fill=(0, 0, 255))
    for gy in range(y0, y1 + 1, step):
        py = (gy - y0) * scale + 20
        col = (255, 0, 0) if (gy - y0) % 50 == 0 else (200, 200, 200)
        d.line([(0, py), (W * scale, py)], fill=col)
        if (gy - y0) % 50 == 0:
            d.text((1, py + 1), str(gy), fill=(0, 0, 255))
    big.save(out)
    print("saved", out, big.size, f"src region x[{x0},{x1}] y[{y0},{y1}]")

if __name__ == "__main__":
    which = sys.argv[1]
    if which == "tree_units":
        grid_crop(f"{base}/live-ctrl_u_units.png", 0, 640, 175, 1010, f"{base}/montage/grid_tree_units.png", scale=3)
    elif which == "tree_before":
        grid_crop(f"{base}/live-before.png", 0, 640, 175, 1010, f"{base}/montage/grid_tree_before.png", scale=3)
