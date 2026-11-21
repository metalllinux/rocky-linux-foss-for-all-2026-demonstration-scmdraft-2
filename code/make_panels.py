#!/usr/bin/env python3
"""Left-panel montage: confirm Ctrl+D/T/U layer switching and palette selection are visible,
and read the Units/Doodads palette layout for placement coordinates."""
from PIL import Image
import os
base = "/tmp/opencode/t0042"
os.makedirs(f"{base}/montage", exist_ok=True)
# left panel is x 0..160, full height
names = ["ctrl_d_doodads", "doodad_attempt", "ctrl_u_units", "unit_attempt", "ctrl_t_terrain"]
crops = []
for n in names:
    p = f"{base}/live-{n}.png"
    if not os.path.exists(p):
        print("MISSING", p); continue
    im = Image.open(p).convert("RGB")
    c = im.crop((0, 100, 165, 1000)).resize((200, 1090))
    crops.append((n, c))
W = 200 * len(crops)
sheet = Image.new("RGB", (W, 1090), (255, 255, 255))
for i, (n, c) in enumerate(crops):
    sheet.paste(c, (i * 200, 0))
sheet.save(f"{base}/montage/panels_montage.png")
print("saved", sheet.size)
