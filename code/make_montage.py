#!/usr/bin/env python3
"""Build a vertical montage of the canvas region from the prior live-run captures
so one image read can judge whether the construction segment was visually legible."""
from PIL import Image
import os

base = "/tmp/opencode/t0042"
os.makedirs(f"{base}/montage", exist_ok=True)
names = ["before", "water_a", "dirt_a", "rocky_b", "mud_c",
         "after_ctrl_s", "reopen", "reopen_down1", "reopen_down2"]
crops = []
for n in names:
    p = f"{base}/live-{n}.png"
    if not os.path.exists(p):
        print("MISSING", p); continue
    im = Image.open(p).convert("RGB")
    c = im.crop((160, 120, 1895, 855)).resize((430, 184))
    crops.append((n, c, im.size))

W = 430
H = sum(c.height for _, c, _ in crops)
sheet = Image.new("RGB", (W, H), (255, 255, 255))
y = 0
for n, c, full in crops:
    print(n, "full", full)
    sheet.paste(c, (0, y)); y += c.height
sheet.save(f"{base}/montage/steps_montage.png")
print("saved", sheet.size)
