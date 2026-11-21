#!/usr/bin/env python3
"""TASK-0042 M1 gate measurement for map 4 `tux`, honest labels.

Reuses the proven measurement functions from measure_rebuild.py (the maps 2/3 rebuild
gate), so the numbers for tux are produced by the same code that measured the silhouettes
Shadow already read. Differences from that script, named:
  - the main-canvas contrast is measured on `tux-jump3.png`, the overview-jump frame that
    holds a ground-and-glyph boundary; `tux-jump.png` (viewport parked inside the body)
    is a real whole-design render but holds one tone, and `tux-jump2.png` holds only
    ground, so neither can produce a two-tone cluster pair.
  - a cluster pairing guard: if either cluster is empty the ratio field records
    `insufficient_clusters` rather than raising.
The builder measures and reports; it does not declare legibility.
"""
import json

from PIL import Image

import measure_rebuild as mr
import rocky

HERE = "/tmp/opencode/t0042"
CANVAS = mr.CANVAS            # (155, 105, 1878, 832) editor canvas interior
THUMB_PANEL = mr.THUMB_PANEL  # (8, 105, 142, 245) overview thumbnail panel
THUMB_BODY = mr.THUMB_BODY    # (4, 4, 131, 131) map body inside the panel


def open_cap(p):
    return Image.open(f"{HERE}/{p}").convert("RGB")


def main():
    name = "tux"
    rep = {}

    m = rocky.MASKS[name]()
    filled = sum(sum(r) for r in m)
    xs = [x for y in range(256) for x, v in enumerate(m[y]) if v]
    ys = [y for y in range(256) for x, v in enumerate(m[y]) if v]
    rep["code_coverage_pct"] = round(100 * filled / 65536, 2)
    rep["code_coverage_tiles"] = filled
    rep["mask_bbox"] = [min(xs), max(xs), min(ys), max(ys)]
    print(f"{name}: code coverage {filled}/65536 = {rep['code_coverage_pct']}%  "
          f"bbox x{min(xs)}-{max(xs)} y{min(ys)}-{max(ys)}")

    img = open_cap(f"{name}-100.png")
    panel = img.crop(THUMB_PANEL)
    panel.save(f"{HERE}/{name}-mm.png")                       # whole-map real render
    body = panel.crop(THUMB_BODY)                             # 127x127 map body

    px = body.load()
    dark = 0
    for y in range(body.height):
        for x in range(body.width):
            p = px[x, y][:3]
            if mr.luminance(p) < 0.06 and p[0] <= 2 * max(p[1], p[2]):
                dark += 1
    rep["thumbnail_body_dark_share_pct"] = round(100 * dark / (127 * 127), 2)
    rep["thumbnail_body_crop"] = list(THUMB_BODY)
    print(f"{name} real overview thumbnail map body 127x127: dark design share "
          f"{rep['thumbnail_body_dark_share_pct']}%")

    tg, ty = mr.clusters(img, THUMB_PANEL)
    tgr = tyr = None
    if tg and ty:
        tgr, tyr = tg.most_common(1)[0][0], ty.most_common(1)[0][0]
        rt = mr.ratio(tgr, tyr)
        rep["real_thumbnail_wcag"] = {"crop": list(THUMB_PANEL), "ground": list(tgr),
                                      "glyph": list(tyr), "ratio": round(rt, 3)}
        print(f"{name} real-thumbnail WCAG: ground {tgr}, glyph {tyr}, ratio {rt:.3f}")
    else:
        rep["real_thumbnail_wcag"] = "insufficient_clusters"

    # main-canvas contrast on the boundary frame (tux-jump3.png, crop named)
    fr = open_cap("tux-jump3.png")
    g, y = mr.clusters(fr, CANVAS)
    g_rgb = y_rgb = None
    if g and y:
        g_rgb, y_rgb = g.most_common(1)[0][0], y.most_common(1)[0][0]
        r_map = mr.ratio(g_rgb, y_rgb)
        rep["main_canvas_wcag"] = {"capture": "tux-jump3.png", "crop": list(CANVAS),
                                   "ground": list(g_rgb), "glyph": list(y_rgb),
                                   "wcag": round(r_map, 3)}
        print(f"{name} real main-canvas WCAG (crop {CANVAS}): ground {g_rgb}, "
              f"glyph {y_rgb}, ratio {r_map:.3f}")
    else:
        rep["main_canvas_wcag"] = "insufficient_clusters"
        print(f"{name} main-canvas boundary frame: insufficient clusters")

    # tones for the calibration render: prefer the main-canvas pair (matches maps 2/3),
    # fall back to the thumbnail pair, and refuse the render if neither pair is complete.
    cal_g = g_rgb if g_rgb is not None else tgr
    cal_y = y_rgb if y_rgb is not None else tyr

    # BOOTH artifact: downscales of the REAL overview thumbnail map body only.
    body.resize((64, 64), Image.LANCZOS).save(f"{HERE}/{name}-booth64.png")
    body.resize((32, 32), Image.LANCZOS).save(f"{HERE}/{name}-booth32.png")
    body.resize((254, 254), Image.LANCZOS).save(f"{HERE}/{name}-mm-2x.png")  # enlargement for reading
    b64 = open_cap(f"{name}-booth64.png")
    bg, by = mr.clusters(b64, (0, 0, 64, 64))
    if bg and by:
        rep["booth64_wcag"] = round(mr.ratio(bg.most_common(1)[0][0],
                                             by.most_common(1)[0][0]), 3)

    # CALIBRATION render (synthetic, from the mask + the two tones measured off the real
    # render). Labelled a calibration reference, never a booth simulation.
    if cal_g is not None and cal_y is not None:
        full = Image.new("RGB", (256, 256))
        fpx = full.load()
        for ty2 in range(256):
            for tx in range(256):
                fpx[tx, ty2] = cal_y if m[ty2][tx] else cal_g
        full.resize((512, 512), Image.NEAREST).save(f"{HERE}/{name}-calibration-render.png")
        full.resize((128, 128), Image.LANCZOS).save(f"{HERE}/{name}-calibration-render-4x.png")
        sim = open_cap(f"{name}-calibration-render-4x.png")
        gs, ys2 = mr.clusters(sim, (0, 0, sim.width, sim.height))
        if gs and ys2:
            rep["calibration_render_wcag"] = round(mr.ratio(gs.most_common(1)[0][0],
                                                             ys2.most_common(1)[0][0]), 3)
    else:
        rep["calibration_render_wcag"] = "skipped, no measured tone pair"

    rep["_labels"] = {
        "booth64/booth32": "downscale of the REAL editor overview thumbnail map body "
                           "(contains SCMDraft pixels); the only booth artifact",
        "calibration-render": "synthetic mask image from measured tones (contains NO "
                              "SCMDraft pixel), a calibration reference only",
        "real_thumbnail_wcag / main_canvas_wcag / booth64_wcag":
            "measured on real SCMDraft renders",
        "calibration_render_wcag":
            "measured on the synthetic calibration render, not a booth simulation",
    }
    json.dump(rep, open(f"{HERE}/tux_report.json", "w"), indent=1)
    print("\nwrote tux_report.json")


if __name__ == "__main__":
    main()
