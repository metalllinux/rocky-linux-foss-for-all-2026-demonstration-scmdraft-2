#!/usr/bin/env python3
"""TASK-0042 dispatch M9 step 3: measure the two-line `i-love-korea` rebuild from its own
real SCMDraft 2 renders on disk. Reuses the pure helper functions from m7_measure.py (WCAG,
tone classification, component labelling, mask-Lanczos binary, per-letter survival, crop diff,
chrome share). The builder does not declare the map legible; M10 decides that.

Gate numbers produced from these artifacts, all measured here:
  1 coverage (mask area, and the real thumbnail dark-pixel census)
  2 WCAG contrast on this map's own real render (thumbnail body and main-canvas frame)
  3 booth artifacts: uniform single-step Lanczos at 0.5 and 0.25 of a located body crop
  4 re-open identity (open vs reopen body-crop pixel diff, disk size/SHA/mtime)
Plus: stroke and gap widths in tiles, measured letter height per line, per-letter ink
retention at the 64 px artifact, and a viewport-indicator overlay check on the body crop.
"""
import json
import math
import struct
import subprocess
from collections import Counter

import m7_measure as M7   # pure helpers only; importing does not run M7's main

HERE = "/tmp/opencode/t0042"
W = H = 256
SCM = f"{HERE}/i-love-korea.scm"
WRITTEN_CHK = f"{HERE}/i-love-korea.chk"
EXTRACTED_CHK = f"{HERE}/m9-extracted.chk"
OPEN_PNG = f"{HERE}/m9-open.png"
REOPEN_PNG = f"{HERE}/m9-reopen.png"
ZOOM_PNG = f"{HERE}/m9-zoom25.png"
JUMP_PNG = f"{HERE}/m9-jump.png"

# B1-measured panel geometry (mm per screen pixel), horizontal axis used for width figures.
MM_PX_H = 0.177083
MM_PX_V = 0.175926

ratio = M7.ratio
lum = M7.lum
is_map_tone = M7.is_map_tone
components = M7.components


def extract_chk():
    r = subprocess.run([f"{HERE}/chkdump", SCM, "staredit\\scenario.chk", EXTRACTED_CHK],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()


def read_chk(path):
    data = open(path, "rb").read()
    pos, out = 0, {}
    while pos + 8 <= len(data):
        name = data[pos:pos + 4]
        if not all(32 <= b <= 126 for b in name):
            break
        size = struct.unpack("<I", data[pos + 4:pos + 8])[0]
        out[name.decode("latin1")] = data[pos + 8:pos + 8 + size]
        pos += 8 + size
    return out


def mask_from(chk):
    mt = struct.unpack("<%dH" % (len(chk["MTXM"]) // 2), chk["MTXM"])
    vals = sorted(set(mt))
    return [[1 if mt[y * W + x] == 192 else 0 for x in range(W)] for y in range(H)], vals


# B1/M8-confirmed overview thumbnail body: origin (18,112), 128x128 px, 0.5 px per tile.
# Verified this capture's body is ground 11161 / glyph 5149 / other 74 px inside this box.
BODY_BOX = (18, 112, 146, 240)


def locate_body(img):
    """Return the confirmed 128x128 overview body box, verified by counting map-tone pixels
    inside it rather than trusting the box blindly. The outer corner is the panel bevel, so the
    test is a map-tone share, not a single corner pixel."""
    x0, y0, x1, y1 = BODY_BOX
    px = img.load()
    tone = 0
    for yy in range(y0, y1):
        for xx in range(x0, x1):
            if is_map_tone(px[xx, yy][:3]):
                tone += 1
    if tone >= 0.8 * (x1 - x0) * (y1 - y0):
        return BODY_BOX
    return None


def make_booth(body_img, scale, out):
    from PIL import Image
    sm = body_img.resize((int(128 * scale), int(128 * scale)), Image.LANCZOS)
    sm.save(out)
    return sm.size


def glyph_windows(mask):
    """Label the seven shapes for the two-line layout: line 1 (y<128) sorted left-to-right is
    I then heart; line 2 (y>=128) sorted left-to-right is K O R E A. Grouped by band, not by a
    single x0 sort across both lines, which would mislabel because KOREA's left edge (x12) sits
    left of the I (x53)."""
    comps = sorted(components(mask, conn=8), key=lambda c: (c["y0"] // 128, c["x0"]))
    out = []
    for c in comps:
        out.append({"label": None, "x0": c["x0"], "x1": c["x1"], "y0": c["y0"], "y1": c["y1"],
                    "w": c["w"], "h": c["h"], "area": c["area"],
                    "line": 1 if c["y0"] < 128 else 2,
                    "kind": "letter"})
    line1 = [c for c in out if c["line"] == 1]
    line2 = [c for c in out if c["line"] == 2]
    line1.sort(key=lambda c: c["x0"])
    line2.sort(key=lambda c: c["x0"])
    for i, c in enumerate(line1):
        c["label"] = ["I", "heart"][i] if i < 2 else f"line1#{i}"
        if c["label"] == "heart":
            c["kind"] = "silhouette"
    for i, c in enumerate(line2):
        c["label"] = "KOREA"[i] if i < 5 else f"line2#{i}"
    return out


def binary_from_lanczos(mask, scale):
    from PIL import Image
    im = Image.new("L", (W, H))
    im.putdata([255 if mask[y][x] else 0 for y in range(H) for x in range(W)])
    sm = im.resize((W // scale, H // scale), Image.LANCZOS)
    d = sm.tobytes()
    return [[1 if d[y * (W // scale) + x] >= 128 else 0 for x in range(W // scale)]
            for y in range(H // scale)]


def grid_pitch(path, x0, y0, x1, y1):
    from PIL import Image
    im = Image.open(path).convert("L")
    a = im.load()
    cols = []
    for x in range(x0, x1):
        dark = sum(1 for y in range(y0, y1) if a[x, y] < 120)
        if dark > (y1 - y0) * 0.5:
            cols.append(x)
    groups = []
    if cols:
        s = p = cols[0]
        for c in cols[1:]:
            if c - p > 2:
                groups.append((s + p) // 2)
                s = c
            p = c
        groups.append((s + p) // 2)
    diffs = sorted(groups[i + 1] - groups[i] for i in range(len(groups) - 1))
    med = diffs[len(diffs) // 2] if diffs else None
    return len(groups), groups[:6], med


def main():
    rep = {}

    rc, so, se = extract_chk()
    rep["chk_extract"] = {"rc": rc, "stdout": so, "stderr": se}
    chk = read_chk(EXTRACTED_CHK)
    mask, vals = mask_from(chk)
    written = open(WRITTEN_CHK, "rb").read()
    extracted = open(EXTRACTED_CHK, "rb").read()

    rep["container"] = {
        "extracted_chk_bytes": len(extracted),
        "controller_written_chk_bytes": len(written),
        "extracted_equals_written": extracted == written,
        "era": struct.unpack("<H", chk["ERA "][:2])[0],
        "dim": struct.unpack("<HH", chk["DIM "][:4]),
        "mtxm_equals_tile": chk["MTXM"] == chk["TILE"],
        "mtxm_bytes": len(chk["MTXM"]), "isom_bytes": len(chk["ISOM"]),
        "isom_bytes_distinct": sorted(set(chk["ISOM"]))[:4],
        "str_name": M7.str_name(chk["STR "]),
        "distinct_values": vals,
    }

    filled = sum(sum(r) for r in mask)
    rep["coverage"] = {"glyph_tiles": filled, "total_tiles": W * H,
                       "coverage_pct": round(100 * filled / (W * H), 2)}

    windows = glyph_windows(mask)
    rep["components"] = windows
    rep["feature_floor_ok"] = all((c["w"] >= 10 and c["h"] >= 10) for c in windows)
    rep["letter_height_tiles"] = max(c["h"] for c in windows if c["kind"] == "letter")
    # line bands from the grouped windows
    line1 = [c for c in windows if c["line"] == 1]
    line2 = [c for c in windows if c["line"] == 2]
    rep["lines"] = {
        "line1": {"labels": [c["label"] for c in line1],
                  "y0": min(c["y0"] for c in line1), "y1": max(c["y1"] for c in line1)},
        "line2": {"labels": [c["label"] for c in line2],
                  "y0": min(c["y0"] for c in line2), "y1": max(c["y1"] for c in line2)},
    }

    # thinnest stroke and gap widths, in tiles (for the 2x2 point-sample thumbnail)
    def thinnest_run(mask, c):
        best = 10**9
        for y in range(c["y0"], c["y1"] + 1):
            run = 0; row_min = 10**9
            for x in range(c["x0"], c["x1"] + 1):
                if mask[y][x]: run += 1
                else:
                    if run: row_min = min(row_min, run)
                    run = 0
            if run: row_min = min(row_min, run)
            if row_min < 10**9: best = min(best, row_min)
        return best
    rep["thinnest_letter_stroke_tiles"] = min(thinnest_run(mask, c) for c in windows if c["kind"] == "letter")
    rep["thinnest_letter_stroke_tiles_note"] = "min horizontal ink run inside each letter window"

    # inter-component gaps in tiles, within each line (thumbnail 2x2 point-sample: a gap < 2
    # tiles collapses, a stroke < 2 tiles is sampled at its top-left tile only)
    def line_gaps(seq):
        g = []
        for a, b in zip(seq, seq[1:]):
            g.append({"between": [a["label"], b["label"]], "x_gap_tiles": b["x0"] - a["x1"] - 1})
        return g
    rep["gaps_tiles_line1"] = line_gaps(line1)
    rep["gaps_tiles_line2"] = line_gaps(line2)
    rep["interline_gap_tiles"] = min(c["y0"] for c in line2) - max(c["y1"] for c in line1) - 1

    # ---- booth artifacts from the located body crop ----
    from PIL import Image
    open_im = Image.open(OPEN_PNG).convert("RGB")
    reopen_im = Image.open(REOPEN_PNG).convert("RGB")
    body = locate_body(open_im)
    rep["body_crop_open"] = list(body) if body else None
    body2 = locate_body(reopen_im)
    rep["body_crop_reopen"] = list(body2) if body2 else None

    if body:
        body_img = open_im.crop(body)
        body_img.save(f"{HERE}/i-love-korea-2line-thumbnail128.png")
        b64 = make_booth(body_img, 0.5, f"{HERE}/i-love-korea-2line-booth64.png")
        b32 = make_booth(body_img, 0.25, f"{HERE}/i-love-korea-2line-booth32.png")
        rep["booth_artifacts"] = {
            "booth64": {"size": list(b64), "scale": 0.5, "source": "located body crop",
                        "interp": "single-step LANCZOS uniform"},
            "booth32": {"size": list(b32), "scale": 0.25, "source": "located body crop",
                        "interp": "single-step LANCZOS uniform"},
        }
        # real thumbnail dark-pixel census (whole-map render)
        tc = M7.tone_composition(open_im, body)
        rep["thumbnail_tone_composition"] = tc
        # re-open identity: open vs reopen over the body crop
        rep["reopen_body_diff"] = M7.diff_crops(open_im, reopen_im, body)
        # viewport-indicator overlay check: map-tone census must be near 100% inside body
        rep["body_chrome_share"] = M7.chrome_share_crop = {
            "crop": list(body),
            "map_tone_share_pct": round(100 * tc["ground_px"] + 100 * tc["glyph_px"]) / tc["total_px"],
            "nontone_px": tc["nonground_px"],
            "nontone_share_pct": tc["other_share_pct"],
        }
        # viewport-indicator / overlay detection: locate every non-map-tone pixel inside the body,
        # map to tile coords, report each glyph window it lands on and the overlay-vs-ground contrast.
        bx0, by0, bx1, by1 = body
        px = open_im.load()
        overlay = []
        for yy in range(by0, by1):
            for xx in range(bx0, bx1):
                p = px[xx, yy][:3]
                if not is_map_tone(p):
                    tile_x = (xx - bx0) * 2
                    tile_y = (yy - by0) * 2
                    on = [c["label"] for c in windows if c["x0"] <= tile_x <= c["x1"] and c["y0"] <= tile_y <= c["y1"]]
                    overlay.append({"px": [xx, yy], "tile": [tile_x, tile_y],
                                    "rgb": list(p), "covers_glyph": on})
        rep["viewport_indicator_overlay"] = {
            "nontone_px_in_body": len(overlay),
            "covers_glyph_positions": [o for o in overlay if o["covers_glyph"]][:40],
            "sample": overlay[:8],
            "note": "non-map-tone pixels inside the body crop; tile coords are body-local*2",
        }
        # contrast of the dominant overlay tone against the dominant ground tone, if any
        gdom = tc.get("ground_dominant")
        if gdom and overlay:
            ocnt = Counter(tuple(o["rgb"]) for o in overlay)
            odom, _ = ocnt.most_common(1)[0]
            rep["viewport_indicator_overlay"]["dominant_overlay_rgb"] = list(odom)
            rep["viewport_indicator_overlay"]["overlay_vs_ground_contrast"] = round(ratio(odom, gdom), 3)

    # WCAG on the main-canvas 25% frame
    zoom_im = Image.open(ZOOM_PNG).convert("RGB")
    canvas = (155, 105, 1878, 832)
    rep["canvas25_tone_composition"] = M7.tone_composition(zoom_im, canvas)

    # grid pitch: confirm zoom applied
    # grid pitch: confirm zoom applied. zoom25 sampled on a ground-only left strip because the
    # glyph fills the mid canvas there.
    n1, f1, p1 = grid_pitch(OPEN_PNG, 400, 150, 1500, 820)
    n2, f2, p2 = grid_pitch(ZOOM_PNG, 168, 140, 285, 700)
    rep["grid_pitch"] = {
        "open_100pct": {"lines": n1, "first": f1, "median_pitch_px": p1},
        "zoom25": {"lines": n2, "first": f2, "median_pitch_px": p2},
    }

    # per-letter ink retention at the 64 px artifact = 0.25 px/tile mask Lanczos (scale 4)
    binary64 = binary_from_lanczos(mask, 4)
    # expected ink per window at scale 4: window area / 16, clamped by surviving geometry
    expect = {}
    for c in windows:
        ax0, ax1 = c["x0"] // 4, (c["x1"] + 3) // 4
        ay0, ay1 = c["y0"] // 4, (c["y1"] + 3) // 4
        expect[c["label"]] = None  # use area-derived expectation below
    surv = M7.survival(binary64, windows, None)
    # recompute expect per window from mask area / scale^2
    for s, c in zip(surv, windows):
        exp_ink = c["area"] // 16
        ink = s["ink_px"]
        s["expected_ink_px"] = exp_ink
        s["ink_vs_expect"] = round(ink / exp_ink, 3) if exp_ink else None
        s["survives"] = bool(ink >= 0.5 * exp_ink and s["rows_with_ink"] >= 0.8 * s["expected_rows"])
    rep["ink_retention_booth64"] = surv

    # ---- real-render per-letter ink retention ----
    # The 64 px booth artifact is a Lanczos downscale of the real 128 px thumbnail body, which
    # already carries the editor's 2x2 top-left point sample (M8 fact). Measure ink retention on
    # that real artifact, not on the mask. Window coords map /4 (256-tile -> 64-px).
    def real_retention(artifact_path, scale_denom):
        im = Image.open(artifact_path).convert("RGB")
        n = im.size[0]
        px = im.load()
        glyph = [[0] * n for _ in range(n)]
        for y in range(n):
            for x in range(n):
                p = px[x, y][:3]
                if is_map_tone(p) and lum(p) <= 0.15:
                    glyph[y][x] = 1
        res = []
        for c in windows:
            ax0, ax1 = c["x0"] // scale_denom, (c["x1"] + scale_denom) // scale_denom
            ay0, ay1 = c["y0"] // scale_denom, (c["y1"] + scale_denom) // scale_denom
            ax1, ay1 = min(ax1, n), min(ay1, n)
            ink = sum(glyph[y][x] for y in range(ay0, ay1) for x in range(ax0, ax1))
            exp_rows = ay1 - ay0
            rows_with_ink = 0
            for y in range(ay0, ay1):
                if any(glyph[y][x] for x in range(ax0, ax1)):
                    rows_with_ink += 1
            exp_ink = max(1, c["area"] // (scale_denom * scale_denom))
            res.append({
                "label": c["label"], "px_window": [ax0, ay0, ax1, ay1],
                "ink_px": ink, "expected_ink_px_area_model": exp_ink,
                "ink_vs_area": round(ink / exp_ink, 3),
                "rows_with_ink": rows_with_ink, "expected_rows": exp_rows,
                "vertical_coverage": round(rows_with_ink / exp_rows, 3) if exp_rows else None,
                "reads": bool(ink > 0 and exp_rows and rows_with_ink >= 0.8 * exp_rows),
            })
        return res
    if body:
        rep["ink_retention_real_booth64"] = real_retention(
            f"{HERE}/i-love-korea-2line-booth64.png", 4)
        rep["ink_retention_real_thumbnail128"] = real_retention(
            f"{HERE}/i-love-korea-2line-thumbnail128.png", 2)

    out = f"{HERE}/i-love-korea-2line_report.json"
    json.dump(rep, open(out, "w"), indent=2)
    print(json.dumps(rep, indent=2))
    print("wrote", out)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
