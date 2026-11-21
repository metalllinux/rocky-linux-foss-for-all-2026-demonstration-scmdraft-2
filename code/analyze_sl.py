#!/usr/bin/env python3
"""Colour analysis of StormLib-map screenshots, TASK-0042 dispatch 2.

Canvas crop (160,100)-(1905,870) matches the crop Shadow used for the item 5
booth sim and the crop used for the harvA-D read (harv 4 colours, control 1057),
so the numbers compare directly.
"""
import sys
from PIL import Image

CROP = (160, 100, 1905, 870)

for name in sys.argv[1:]:
    im = Image.open(name).convert("RGB")
    full = im.getcolors(maxcolors=1_000_000)
    canvas = im.crop(CROP)
    cc = canvas.getcolors(maxcolors=1_000_000)
    top = sorted(cc, reverse=True)[:4]
    print(f"{name}: full {len(full)} colours, canvas {len(cc)} colours, top {top}")
