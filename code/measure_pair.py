#!/usr/bin/env python3
"""TASK-0042 contrast dispatch: measure a pairtest render.

A pairtest map is 20x20 tiles: ground value in tile rows 0..3 and 16..19, glyph value in
rows 4..15. This script measures the modal tone of each region directly from the SCMDraft
render, the WCAG contrast ratio between them, and the state of the two boundary lines:
a clean boundary is one whose strip pixels are almost entirely one of the two region tones,
with no third (cliff-texture) tone and no raised-edge ramp.
"""
import json
import sys
from collections import Counter

from PIL import Image

TILES = 20


def luminance(rgb):
    def lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb[:3]
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def ratio(a, b):
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def map_bbox(img):
    x0, y0, x1, y1 = 155, 105, 1885, 840
    step = 4
    px = img.load()

    def terrain(p):
        r, g, b = p[:3]
        if max(r, g, b) < 14:
            return False
        if min(r, g, b) > 185 and max(r, g, b) - min(r, g, b) < 30:
            return False
        return True

    ny = len(range(y0, y1, step))
    cols = [x for x in range(x0, x1)
            if sum(1 for y in range(y0, y1, step) if terrain(px[x, y])) >= 0.5 * ny]
    mx0, mx1 = cols[0], cols[-1] + 1
    nx = len(range(mx0, mx1, step))
    rows = [y for y in range(y0, y1)
            if sum(1 for x in range(mx0, mx1, step) if terrain(px[x, y])) >= 0.5 * nx]
    return mx0, rows[0], mx1, rows[-1] + 1


def modal(img, box, skip_red=True):
    px = img.load()
    cnt = Counter()
    for y in range(box[1], box[3], 2):
        for x in range(box[0], box[2], 2):
            p = px[x, y][:3]
            if skip_red and p[0] > 120 and p[0] > 2 * max(p[1], p[2]):
                continue  # start-location marker overlay
            cnt[p] += 1
    return cnt


def main():
    path = sys.argv[1]
    img = Image.open(path).convert("RGB")
    x0, y0, x1, y1 = map_bbox(img)
    tw = (x1 - x0) / TILES
    th = (y1 - y0) / TILES

    def band(r0, r1):
        return (int(x0 + 2 * tw), int(y0 + r0 * th), int(x1 - 2 * tw), int(y0 + r1 * th))

    ground = modal(img, band(0, 4))
    glyph = modal(img, band(6, 14))
    g_rgb, g_n = ground.most_common(1)[0]
    y_rgb, y_n = glyph.most_common(1)[0]
    r = ratio(g_rgb, y_rgb)
    print(f"{path}: bbox {(x0, y0, x1, y1)} tile {tw:.1f}x{th:.1f}")
    print(f"  ground tone {g_rgb} n={g_n} lum {luminance(g_rgb):.5f}  distinct {len(ground)}")
    print(f"  glyph  tone {y_rgb} n={y_n} lum {luminance(y_rgb):.5f}  distinct {len(glyph)}")
    print(f"  WCAG ratio {r:.3f}  gate>=3.0 -> {'PASS' if r >= 3.0 else 'FAIL'}")
    for name, row in (("boundary_top", 4), ("boundary_bottom", 16)):
        strip = modal(img, band(row - 1, row + 1))
        tot = sum(strip.values())
        near = 0
        third = Counter()
        for c, n in strip.items():
            if ratio(c, g_rgb) < 1.25 or ratio(c, y_rgb) < 1.25:
                near += n
            else:
                third[c] += n
        print(f"  {name}: strip {tot} px, matching a region tone {100*near/tot:.1f}%, "
              f"third-tone px {sum(third.values())}, distinct {len(strip)}")
        if third:
            print("     third-tone examples:", third.most_common(4))


if __name__ == "__main__":
    main()
