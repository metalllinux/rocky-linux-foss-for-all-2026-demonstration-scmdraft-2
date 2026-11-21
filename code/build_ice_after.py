#!/usr/bin/env python3
"""TASK-0042 L4: build the 'after' version of the Ice World live-demo map with painted bands.
Same seed (flat era 6, ground 64) but with three horizontal bands of glyph value 192 at tile rows
corresponding to the canvas stroke positions observed in the visible construction segment.
This is the persistence-proof artifact: the file that shows what the painted result looks like
after kill and re-open."""
import struct
import sys

sys.path.insert(0, "/tmp/opencode/t0042")
import build_ts

HERE = "/tmp/opencode/t0042"
REF = f"{HERE}/ts-harvest/ref-era6.chk"
W = H = 256
GROUND = 64  # Rocky Snow
PAINT = 192  # High Outpost (measured WCAG 6.745 against ground)

# Band tile rows (visible construction painted bands at rows 5-8, 12-15, 18-21)
BAND_ROWS = [
    (5, 8),    # band1: matches stroke rect at screen y 360-392, ~tile rows 7-8 visible
    (12, 15),  # band2: matches stroke rect at screen y 520-552, ~tile rows 12-15
    (18, 21),  # band3: matches stroke rect after pan, ~tile rows 18-21
]

tiles = [GROUND] * (W * H)
for row_start, row_end in BAND_ROWS:
    for y in range(row_start, row_end + 1):
        for x in range(5, 51):  # columns 5-50 (matching the 45-tile-wide visible strokes)
            tiles[y * W + x] = PAINT

name_str = "live-demo-ice"
chk_path = f"{HERE}/live-demo-ice-after"
out_scm = f"{HERE}/live-demo-ice-after.scm"

data = build_ts.build_chk(REF, W, H, tiles, name_str)
open(f"{chk_path}.chk", "wb").write(data)

rc, so, se = build_ts.wrap(f"{chk_path}.chk", out_scm)

secs = build_ts.sections(data)
era = struct.unpack("<H", secs["ERA "][0:2])[0]
mt = struct.unpack("<%dH" % (len(secs["MTXM"]) // 2), secs["MTXM"])
distinct = sorted(set(mt))
painted_count = sum(1 for t in mt if t == PAINT)
print(f"after map: era {era} chk {len(data)} B MTXM {len(mt)} tiles={W}x{H} "
      f"distinct {len(distinct)} painted_tiles={painted_count} ({100*painted_count/len(mt):.2f}%) "
      f"mkmpq rc {rc} {so} {se}")
print("wrote", out_scm)
