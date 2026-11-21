#!/usr/bin/env python3
"""TASK-0042 L4: build a flat 256x256 Ice World era 6 seed map (ground value 64 everywhere)
using the proven slE pipeline. Output: live-demo-ice.chk and live-demo-ice.scm."""
import struct
import sys

sys.path.insert(0, "/tmp/opencode/t0042")
import build_map as bm
import build_ts  # reuse build_chk and wrap

HERE = "/tmp/opencode/t0042"
REF = f"{HERE}/ts-harvest/ref-era6.chk"
W = H = 256
GROUND = 64  # Ice World flat ground value (measured WCAG 6.745 against glyph 192)

tiles = [GROUND] * (W * H)
name_str = "live-demo-ice"

chk_path = f"{HERE}/live-demo-ice"
out_scm = f"{HERE}/live-demo-ice.scm"

data = build_ts.build_chk(REF, W, H, tiles, name_str)
open(f"{chk_path}.chk", "wb").write(data)

rc, so, se = build_ts.wrap(f"{chk_path}.chk", out_scm)

# Verify
secs = build_ts.sections(data)
era = struct.unpack("<H", secs["ERA "][0:2])[0]
mt = struct.unpack("<%dH" % (len(secs["MTXM"]) // 2), secs["MTXM"])
distinct = sorted(set(mt))
print(f"flat seed: era {era} chk {len(data)} B MTXM {len(mt)} tiles={W}x{H} "
      f"distinct {len(distinct)} {distinct} mkmpq rc {rc} {so} {se}")
print("wrote", out_scm)
