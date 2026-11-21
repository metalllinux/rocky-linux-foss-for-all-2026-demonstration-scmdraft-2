#!/usr/bin/env python3
"""TASK-0042 contrast dispatch, map 1 rebuild on Ice World: build the gate artifacts and
measure them.

- whole-map real render crops from the editor overview thumbnail (open and re-open),
- 4x Lanczos booth downscales of the real main-canvas frames,
- a calibrated mask render built from the tones measured out of the real render, and its 4x booth sim,
- WCAG ratio measured directly from the map-1 render (ground cluster and glyph cluster),
- colour coverage numbers with the crop and the test named.
"""
import json
from collections import Counter

from PIL import Image

from glyph import mask

HERE = "/tmp/opencode/t0042"
CANVAS = (155, 105, 1878, 832)          # editor canvas interior, from the captures
THUMB = (8, 105, 142, 245)              # overview thumbnail panel contents, from the captures


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
    """Split the canvas into the two terrain clusters of map 1: bright ground and dark glyph.
    Grid lines (near-black 1-2 px separators) and the red start marker are excluded."""
    px = img.load()
    ground = Counter()
    glyph = Counter()
    for y in range(box[1], box[3], 2):
        for x in range(box[0], box[2], 2):
            p = px[x, y][:3]
            if p[0] > 120 and p[0] > 2 * max(p[1], p[2]):
                continue                       # red marker
            lum = luminance(p)
            if lum < 0.004:
                continue                       # grid line / chrome black
            if lum > 0.15:
                ground[p] += 1
            elif lum < 0.06:
                glyph[p] += 1
    return ground, glyph


def main():
    report = {}
    # 1. whole-map real renders: the editor overview thumbnail, open and re-opened
    for src, dst in (("foss-ice-100.png", "foss-ice-mm.png"),
                     ("foss-ice-reopen.png", "foss-ice-reopen-mm.png")):
        img = Image.open(f"{HERE}/{src}").convert("RGB")
        img.crop(THUMB).save(f"{HERE}/{dst}")
        thumb = img.crop(THUMB)
        px = thumb.load()
        dark = tot = 0
        for y in range(thumb.size[1]):
            for x in range(thumb.size[0]):
                p = px[x, y][:3]
                tot += 1
                if luminance(p) < 0.06 and p[0] <= 2 * max(p[1], p[2]):
                    dark += 1
        report[dst] = {"size": list(thumb.size), "dark_design_share_pct": round(100 * dark / tot, 2)}
        print(f"{dst}: {thumb.size[0]}x{thumb.size[1]} px, dark design share {100*dark/tot:.2f}%")

    # 2. tones measured from the real main-canvas frames, then WCAG on the map itself
    frame = Image.open(f"{HERE}/ice25-page1.png").convert("RGB")
    g, y = clusters(frame, CANVAS)
    g_rgb = g.most_common(1)[0][0]
    y_rgb = y.most_common(1)[0][0]
    r_map = ratio(g_rgb, y_rgb)
    n_g, n_y = sum(g.values()), sum(y.values())
    cover = 100 * n_y / (n_g + n_y)
    print(f"map 1 render (ice25-page1 canvas crop {CANVAS}): ground {g_rgb} lum {luminance(g_rgb):.5f}, "
          f"glyph {y_rgb} lum {luminance(y_rgb):.5f}, WCAG {r_map:.3f}, dark share of terrain px {cover:.2f}%")
    report["map1_render_contrast"] = {"ground": list(g_rgb), "glyph": list(y_rgb),
                                      "wcag": round(r_map, 3), "dark_share_pct": round(cover, 2)}

    # 3. 4x booth downscales of the real main-canvas frames, and a 2x enlargement of the
    # thumbnail crop (the thumbnail is already smaller than a 4x booth sim would be, so it
    # is enlarged for reading and is not named as a booth simulation).
    for src, dst in (("ice25-page1.png", "foss-ice-booth4x-foss.png"),
                     ("ice25-page2.png", "foss-ice-booth4x-all.png")):
        img = Image.open(f"{HERE}/{src}").convert("RGB").crop(CANVAS)
        img.resize((img.width // 4, img.height // 4), Image.LANCZOS).save(f"{HERE}/{dst}")
    thumb = Image.open(f"{HERE}/foss-ice-mm.png").convert("RGB")
    thumb.resize((thumb.width * 2, thumb.height * 2), Image.LANCZOS).save(f"{HERE}/foss-ice-mm-2x.png")
    for name in ("foss-ice-booth4x-foss.png", "foss-ice-booth4x-all.png", "foss-ice-mm-2x.png"):
        out = Image.open(f"{HERE}/{name}")
        print(f"{name}: {out.size[0]}x{out.size[1]}")

    # 4. calibrated whole-map mask render from the measured tones, plus its 4x booth sim
    m = mask()
    full = Image.new("RGB", (256, 256))
    fpx = full.load()
    for ty in range(256):
        for tx in range(256):
            fpx[tx, ty] = y_rgb if m[ty][tx] else g_rgb
    full.resize((512, 512), Image.NEAREST).save(f"{HERE}/foss-ice-maskrender.png")
    full.resize((128, 128), Image.LANCZOS).save(f"{HERE}/foss-ice-maskrender-booth4x.png")
    filled = sum(sum(r) for r in m)
    print(f"foss-ice-maskrender.png 512x512 and foss-ice-maskrender-booth4x.png 128x128 from "
          f"measured tones; design tiles {filled} = {100*filled/65536:.2f}%")
    report["mask_render"] = {"design_tiles": filled, "design_pct": round(100 * filled / 65536, 2),
                            "ground": list(g_rgb), "glyph": list(y_rgb)}

    # 5. WCAG measured on the 4x booth sim
    sim = Image.open(f"{HERE}/foss-ice-maskrender-booth4x.png").convert("RGB")
    gs, ys = clusters(sim, (0, 0, sim.width, sim.height))
    if gs and ys:
        rs = ratio(gs.most_common(1)[0][0], ys.most_common(1)[0][0])
        print(f"booth sim WCAG {rs:.3f} ({gs.most_common(1)[0][0]} vs {ys.most_common(1)[0][0]})")
        report["booth_sim_wcag"] = round(rs, 3)
    json.dump(report, open(f"{HERE}/ts-harvest/map1_ice_report.json", "w"), indent=1)


if __name__ == "__main__":
    main()
