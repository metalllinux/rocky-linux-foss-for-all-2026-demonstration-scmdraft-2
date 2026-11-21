#!/usr/bin/env python3
"""Build three verdict montages for the L1 live construction segment."""
from PIL import Image
import os
base = "/tmp/opencode/t0042"; os.makedirs(f"{base}/montage", exist_ok=True)

def load(n):
    p = f"{base}/live-{n}.png"
    return Image.open(p).convert("RGB") if os.path.exists(p) else None

def canvas(name, box=(160, 120, 1895, 855), size=(470, 201)):
    im = load(name)
    return None if im is None else im.crop(box).resize(size)

# A: before -> band1 -> band2 -> reopen  (SAME top-left viewport, pristine then painted)
A = [x for x in ["before", "band1_rocky", "band2_highdirt", "reopen"] if canvas(x)]
sheetA = Image.new("RGB", (470 * len(A), 201), (200, 200, 200))
for i, n in enumerate(A): sheetA.paste(canvas(n), (i * 470, 0))
sheetA.save(f"{base}/montage/verdict_beforeafter.png"); print("A", sheetA.size, A)

# B: status bar across the four layer-switch steps (proves Ctrl+T/U/D switched the editing layer)
layers = ["layer_terrain", "layer_units", "layer_doodads", "layer_back_terrain"]
crops = [load(n).crop((160, 1050, 1920, 1080)) for n in layers if load(n)]
sheetB = Image.new("RGB", (crops[0].width, sum(c.height for c in crops) + 4 * 16), (255, 255, 255))
y = 0
for c in crops: sheetB.paste(c, (0, y)); y += c.height + 16
sheetB.save(f"{base}/montage/verdict_layers.png"); print("B", sheetB.size, layers)

# C: reopen / reopen_down1 / reopen_down2 (persistence of painted bands across the vertical extent)
C = [x for x in ["reopen", "reopen_down1", "reopen_down2"] if canvas(x)]
sheetC = Image.new("RGB", (470 * len(C), 201), (200, 200, 200))
for i, n in enumerate(C): sheetC.paste(canvas(n), (i * 470, 0))
sheetC.save(f"{base}/montage/verdict_persist.png"); print("C", sheetC.size, C)
