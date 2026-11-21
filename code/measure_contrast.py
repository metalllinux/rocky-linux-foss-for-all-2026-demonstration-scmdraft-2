#!/usr/bin/env python3
"""TASK-0042 contrast dispatch: measure the rendered tone of each calibration block and
compute WCAG 2.x contrast ratios between every glyph/ground candidate pair per tileset.

Geometry: each gridcalib map is 20x20 tiles drawn 4x4 blocks of 5x5 tiles, anchored at the
canvas top-left. The map region is located automatically as the rows/columns inside the
canvas window whose majority of pixels are neither pure black (empty canvas) nor light chrome.
Block tone = the modal (most common) RGB inside the central 3x3 tiles of the block, which is
immune to small overlays such as the start-location diamond.

WCAG relative luminance per WCAG 2.1 (sRGB linearisation), ratio = (L_hi+0.05)/(L_lo+0.05).
"""
import json
import sys
from collections import Counter
from PIL import Image

CANVAS = (155, 105, 1885, 840)  # editor canvas window inside the chrome, from the captures


def is_terrain(px):
    r, g, b = px[:3]
    if max(r, g, b) < 14:
        return False          # empty canvas black
    if min(r, g, b) > 185 and max(r, g, b) - min(r, g, b) < 30:
        return False          # white / grey chrome
    return True


def luminance(rgb):
    def lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb[:3]
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def ratio(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def map_bbox(img):
    """Locate the rendered map rectangle: columns that are terrain for most of their height,
    then rows that are terrain for most of the width found in the first pass."""
    x0, y0, x1, y1 = CANVAS
    step = 4
    px = img.load()
    ny = len(range(y0, y1, step))
    cols = [x for x in range(x0, x1)
            if sum(1 for y in range(y0, y1, step) if is_terrain(px[x, y])) >= 0.5 * ny]
    if not cols:
        return None
    mx0, mx1 = cols[0], cols[-1] + 1
    nx = len(range(mx0, mx1, step))
    rows = [y for y in range(y0, y1)
            if sum(1 for x in range(mx0, mx1, step) if is_terrain(px[x, y])) >= 0.5 * nx]
    if not rows:
        return None
    return mx0, rows[0], mx1, rows[-1] + 1


def block_tones(img, n_blocks=4, tiles=20):
    bb = map_bbox(img)
    if bb is None:
        return None, None
    x0, y0, x1, y1 = bb
    bw = (x1 - x0) / n_blocks
    bh = (y1 - y0) / n_blocks
    px = img.load()
    tones = []
    for br in range(n_blocks):
        for bc in range(n_blocks):
            cx = int(x0 + (bc + 0.5) * bw)
            cy = int(y0 + (br + 0.5) * bh)
            half_w = int(bw * 0.3)
            half_h = int(bh * 0.3)
            cnt = Counter()
            for y in range(cy - half_h, cy + half_h + 1, 2):
                for x in range(cx - half_w, cx + half_w + 1, 2):
                    cnt[px[x, y][:3]] += 1
            tones.append(cnt.most_common(1)[0][0])
    return bb, tones


def main():
    cands = json.load(open("/tmp/opencode/t0042/ts-harvest/candidates.json"))
    out = {}
    for era in (0, 1, 2, 3, 5, 6, 7):
        img = Image.open(f"/tmp/opencode/t0042/ts{era}-cal-shot.png").convert("RGB")
        bb, tones = block_tones(img)
        if tones is None:
            print(f"era {era}: no map region detected (map did not render)")
            out[era] = None
            continue
        vals = cands[str(era)]
        print(f"=== era {era} bbox {bb} block size {(bb[2]-bb[0])/4:.1f}x{(bb[3]-bb[1])/4:.1f} px")
        rows = []
        for v, t in zip(vals, tones):
            rows.append({"value": v, "group": v >> 4, "subtile": v & 15, "rgb": list(t),
                         "lum": round(luminance(t), 5)})
            print(f"   value {v:5d} g{v>>4:<4d} s{v&15:<2d} rgb {t} lum {luminance(t):.5f}")
        out[era] = rows
    json.dump(out, open("/tmp/opencode/t0042/ts-harvest/tones.json", "w"), indent=1)
    print("\nWCAG best pairs per tileset")
    for era, rows in out.items():
        if not rows:
            print(f"era {era}: no render")
            continue
        best = []
        for i in range(len(rows)):
            for j in range(len(rows)):
                if i == j:
                    continue
                ri, rj = rows[i], rows[j]
                # glyph candidate i against ground candidate j
                best.append((ratio(ri["rgb"], rj["rgb"]), ri["value"], rj["value"]))
        best.sort(reverse=True)
        print(f"era {era}: top 5 ratios (ratio, glyph, ground):", [(round(r, 3), g, gr) for r, g, gr in best[:5]])


if __name__ == "__main__":
    main()
