#!/usr/bin/env python3
"""TASK-0042 maps 2 and 3 rebuild gate measurement, honest labels.

Per the Robotnik decision in ## Status and Shadow's blockers:
- The booth artifact is a downscale of the captured REAL editor overview thumbnail (the
  whole-map real SCMDraft render), so it contains SCMDraft pixels. It is named -booth64 /
  -booth32 and is a real render, not a synthetic image.
- The code-generated mask image is named -calibration-render, and its contrast figure is
  reported as calibration_render_wcag, never as a booth simulation. It contains no SCMDraft
  pixel and is labelled a calibration reference.
- Contrast (WCAG) and coverage are measured on the map's own REAL render, and every crop and
  threshold is named. The builder measures and reports; it does not declare legibility.
"""
import json
from collections import Counter
from PIL import Image

import rocky

HERE = "/tmp/opencode/t0042"
CANVAS = (155, 105, 1878, 832)     # editor canvas interior (real main-canvas frame)
THUMB_PANEL = (8, 105, 142, 245)   # overview thumbnail panel
THUMB_BODY = (4, 4, 131, 131)      # the 127x127 map body inside the panel


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
    ground, glyph = Counter(), Counter()
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


def measure(name, cap100, jump):
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

    img = Image.open(f"{HERE}/{cap100}").convert("RGB")
    panel = img.crop(THUMB_PANEL)
    panel.save(f"{HERE}/{name}-mm.png")                       # whole-map real render
    body = panel.crop(THUMB_BODY)                             # 127x127 map body

    # dark-design share over the 127x127 map body (crop named)
    px = body.load(); dark = 0
    for y in range(body.height):
        for x in range(body.width):
            p = px[x, y][:3]
            if luminance(p) < 0.06 and p[0] <= 2 * max(p[1], p[2]):
                dark += 1
    rep["thumbnail_body_dark_share_pct"] = round(100 * dark / (127 * 127), 2)
    rep["thumbnail_body_crop"] = list(THUMB_BODY)
    print(f"{name} real overview thumbnail map body 127x127: dark design share {rep['thumbnail_body_dark_share_pct']}%")

    # contrast on the real whole-map thumbnail render (region-mean)
    tg, ty = clusters(img, THUMB_PANEL)
    if tg and ty:
        tgr, tyr = tg.most_common(1)[0][0], ty.most_common(1)[0][0]
        rt = ratio(tgr, tyr)
        rep["real_thumbnail_wcag"] = {"ground": list(tgr), "glyph": list(tyr), "ratio": round(rt, 3)}
        print(f"{name} real-thumbnail WCAG: ground {tgr}, glyph {tyr}, ratio {rt:.3f}")

    # contrast on the real main-canvas frame (region-mean)
    fr = Image.open(f"{HERE}/{jump}").convert("RGB")
    g, y = clusters(fr, CANVAS)
    g_rgb, y_rgb = g.most_common(1)[0][0], y.most_common(1)[0][0]
    r_map = ratio(g_rgb, y_rgb)
    rep["main_canvas_wcag"] = {"crop": list(CANVAS), "ground": list(g_rgb), "glyph": list(y_rgb), "wcag": round(r_map, 3)}
    print(f"{name} real main-canvas WCAG (crop {CANVAS}): ground {g_rgb}, glyph {y_rgb}, ratio {r_map:.3f}")

    # BOOTH artifact: 4x-equivalent downscales of the REAL overview thumbnail map body
    # (contains SCMDraft pixels; this is the honest booth artifact the DoD box asks for)
    body.resize((64, 64), Image.LANCZOS).save(f"{HERE}/{name}-booth64.png")
    body.resize((32, 32), Image.LANCZOS).save(f"{HERE}/{name}-booth32.png")
    body.resize((254, 254), Image.LANCZOS).save(f"{HERE}/{name}-mm-2x.png")  # 2x enlargement for reading
    # WCAG on the 64px booth artifact, measured on its own real pixels
    b64 = Image.open(f"{HERE}/{name}-booth64.png").convert("RGB")
    bg, by = clusters(b64, (0, 0, 64, 64))
    if bg and by:
        rep["booth64_wcag"] = round(ratio(bg.most_common(1)[0][0], by.most_common(1)[0][0]), 3)

    # CALIBRATION render (synthetic, from the mask + the two tones measured off the real
    # render). Renamed so it no longer claims to be a booth simulation.
    full = Image.new("RGB", (256, 256)); fpx = full.load()
    for ty2 in range(256):
        for tx in range(256):
            fpx[tx, ty2] = y_rgb if m[ty2][tx] else g_rgb
    full.resize((512, 512), Image.NEAREST).save(f"{HERE}/{name}-calibration-render.png")
    full.resize((128, 128), Image.LANCZOS).save(f"{HERE}/{name}-calibration-render-4x.png")
    sim = Image.open(f"{HERE}/{name}-calibration-render-4x.png").convert("RGB")
    gs, ys2 = clusters(sim, (0, 0, sim.width, sim.height))
    if gs and ys2:
        rep["calibration_render_wcag"] = round(ratio(gs.most_common(1)[0][0], ys2.most_common(1)[0][0]), 3)
    print(f"{name}: booth artifacts from real thumbnail at 64 and 32 px; calibration render labelled synthetic")
    return rep


def main():
    out = {
        "rocky-logo": measure("rocky-logo", "rocky-logo-100.png", "rocky-logo-jump.png"),
        "rocky-with-heart": measure("rocky-with-heart", "rocky-with-heart-100.png", "rocky-with-heart-jump.png"),
    }
    out["_labels"] = {
        "booth64/booth32": "downscale of the REAL editor overview thumbnail map body (contains SCMDraft pixels)",
        "calibration-render": "synthetic mask image from measured tones (contains NO SCMDraft pixel), a calibration reference only",
        "real_thumbnail_wcag / main_canvas_wcag / booth64_wcag": "measured on real SCMDraft renders",
        "calibration_render_wcag": "measured on the synthetic calibration render, not a booth simulation",
    }
    json.dump(out, open(f"{HERE}/maps23_rebuild_report.json", "w"), indent=1)
    print("\nwrote maps23_rebuild_report.json")


if __name__ == "__main__":
    main()
