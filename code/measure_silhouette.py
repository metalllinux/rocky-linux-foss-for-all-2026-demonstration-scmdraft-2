#!/usr/bin/env python3
"""TASK-0042 maps 2 and 3 gate measurement, the same method dispatch 4 used for map 1.

For each map:
- whole-map real render: the editor overview thumbnail crop (the whole 256x256 map), dark
  design share and WCAG measured on that crop,
- clean-tile WCAG on the map's own main-canvas render (the viewport jumped onto the design),
- colour coverage from the code mask (the tiles the writer placed),
- a calibrated whole-map mask render from the tones measured out of the real render, and its
  4x booth sim, plus a 4x Lanczos downscale of the real main-canvas frame,
- WCAG measured on the 128x128 booth sim.

Every crop and threshold is named in the printed report. The builder measures and reports;
it does not declare legibility.
"""
import json
from collections import Counter
from PIL import Image

HERE = "/tmp/opencode/t0042"
CANVAS = (155, 105, 1878, 832)          # editor canvas interior
THUMB = (8, 105, 142, 245)              # overview thumbnail panel contents


def luminance(rgb):
    def lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb[:3]
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def ratio(a, b):
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def clusters(img, box):
    px = img.load()
    ground = Counter()
    glyph = Counter()
    for y in range(box[1], box[3], 2):
        for x in range(box[0], box[2], 2):
            p = px[x, y][:3]
            if p[0] > 120 and p[0] > 2 * max(p[1], p[2]):
                continue                       # red start marker
            lum = luminance(p)
            if lum < 0.004:
                continue                       # grid line / chrome black
            if lum > 0.15:
                ground[p] += 1
            elif lum < 0.06:
                glyph[p] += 1
    return ground, glyph


import rocky


def measure(name, cap100, jump):
    rep = {}
    # code coverage from the mask the writer actually placed
    m = rocky.MASKS[name]()
    filled = sum(sum(r) for r in m)
    xs = [x for r in range(256) for x, v in enumerate(m[r]) if v]
    ys = [y for y in range(256) for x, v in enumerate(m[y]) if v]
    cov = 100 * filled / 65536
    print(f"{name}: code coverage {filled}/{65536} tiles = {cov:.2f}%  "
          f"bbox x{min(xs)}-{max(xs)} y{min(ys)}-{max(ys)}")
    rep["code_coverage_pct"] = round(cov, 2)
    rep["code_coverage_tiles"] = filled
    rep["mask_bbox"] = [min(xs), max(xs), min(ys), max(ys)]

    # 1. whole-map real render: overview thumbnail crop from the default editor capture
    img = Image.open(f"{HERE}/{cap100}").convert("RGB")
    thumb = img.crop(THUMB)
    thumb.save(f"{HERE}/{name}-mm.png")
    px = thumb.load()
    dark = tot = 0
    for y in range(thumb.size[1]):
        for x in range(thumb.size[0]):
            p = px[x, y][:3]
            tot += 1
            if luminance(p) < 0.06 and p[0] <= 2 * max(p[1], p[2]):
                dark += 1
    print(f"{name}-mm.png thumbnail crop {thumb.size[0]}x{thumb.size[1]}: dark design share {100*dark/tot:.2f}%")
    rep["thumbnail_crop"] = list(thumb.size)
    rep["thumbnail_dark_share_pct"] = round(100 * dark / tot, 2)
    tg, ty = clusters(img, THUMB)
    if tg and ty:
        tgr, tyr = tg.most_common(1)[0][0], ty.most_common(1)[0][0]
        rt = ratio(tgr, tyr)
        print(f"{name} thumbnail WCAG: ground {tgr} lum {luminance(tgr):.5f}, "
              f"glyph {tyr} lum {luminance(tyr):.5f}, ratio {rt:.3f} (whole-map real render crop {THUMB})")
        rep["thumbnail_wcag"] = {"ground": list(tgr), "glyph": list(tyr), "ratio": round(rt, 3)}

    # 2. clean-tile WCAG on the map's own main-canvas render (viewport jumped onto the design)
    fr = Image.open(f"{HERE}/{jump}").convert("RGB")
    g, y = clusters(fr, CANVAS)
    g_rgb = g.most_common(1)[0][0]
    y_rgb = y.most_common(1)[0][0]
    r_map = ratio(g_rgb, y_rgb)
    n_g, n_y = sum(g.values()), sum(y.values())
    share = 100 * n_y / (n_g + n_y)
    print(f"{name} main-canvas WCAG (crop {CANVAS}): ground {g_rgb} lum {luminance(g_rgb):.5f}, "
          f"glyph {y_rgb} lum {luminance(y_rgb):.5f}, ratio {r_map:.3f}, dark terrain share {share:.2f}%")
    rep["main_render_contrast"] = {"crop": list(CANVAS), "ground": list(g_rgb), "glyph": list(y_rgb),
                                   "wcag": round(r_map, 3), "dark_share_pct": round(share, 2)}

    # 3. 4x booth downscales of the real main-canvas frame + a 2x enlargement of the thumbnail
    fr.crop(CANVAS).resize(((CANVAS[2]-CANVAS[0])//4, (CANVAS[3]-CANVAS[1])//4), Image.LANCZOS).save(f"{HERE}/{name}-booth4x.png")
    thumb.resize((thumb.width*2, thumb.height*2), Image.LANCZOS).save(f"{HERE}/{name}-mm-2x.png")

    # 4. calibrated whole-map mask render from the measured tones + its 4x booth sim
    full = Image.new("RGB", (256, 256))
    fpx = full.load()
    for ty2 in range(256):
        for tx in range(256):
            fpx[tx, ty2] = y_rgb if m[ty2][tx] else g_rgb
    full.resize((512, 512), Image.NEAREST).save(f"{HERE}/{name}-maskrender.png")
    full.resize((128, 128), Image.LANCZOS).save(f"{HERE}/{name}-maskrender-booth4x.png")

    sim = Image.open(f"{HERE}/{name}-maskrender-booth4x.png").convert("RGB")
    gs, ys2 = clusters(sim, (0, 0, sim.width, sim.height))
    if gs and ys2:
        rs = ratio(gs.most_common(1)[0][0], ys2.most_common(1)[0][0])
        print(f"{name} mask-render booth sim WCAG {rs:.3f} "
              f"({gs.most_common(1)[0][0]} vs {ys2.most_common(1)[0][0]})")
        rep["booth_sim_wcag"] = round(rs, 3)
    rep["mask_render"] = {"ground": list(g_rgb), "glyph": list(y_rgb)}
    return rep


def main():
    out = {}
    out["rocky-logo"] = measure("rocky-logo", "rlogo-100.png", "rlogo-jump.png")
    print()
    out["rocky-with-heart"] = measure("rocky-with-heart", "rheart-100.png", "rheart-jump.png")
    json.dump(out, open(f"{HERE}/maps23_report.json", "w"), indent=1)


if __name__ == "__main__":
    main()
