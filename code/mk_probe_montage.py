#!/usr/bin/env python3
from PIL import Image
import os
base = "/tmp/opencode/t0042"; os.makedirs(f"{base}/montage", exist_ok=True)
names = ["launch", "ctrlu", "ctrld", "ctrlt"]
ims = []
for n in names:
    p = f"{base}/probe-{n}.png"
    if os.path.exists(p):
        ims.append(Image.open(p).convert("RGB").resize((475, 268)))
sheet = Image.new("RGB", (475 * len(ims), 268), (200, 200, 200))
for i, im in enumerate(ims):
    sheet.paste(im, (i * 475, 0))
sheet.save(f"{base}/montage/probe_layer_montage.png")
print("saved", sheet.size, names)
