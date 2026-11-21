#!/usr/bin/env python3
"""TASK-0042 dispatch M7 step 3: gate measurement of map 6 `i-love-korea`.

Two sources only. The published map file `i-love-korea.scm`, its CHK extracted with `chkdump`
(StormLib, MIT) and its MTXM parsed, and the real SCMDraft 2 captures `m7-open.png`,
`m7-jump.png`, `m7-reopen.png` taken on the target. No mask module is imported for a gate
number; the mask used for glyph metrics is re-derived from the shipped MTXM.

Gate numbers:
  1 coverage, glyph tiles over 65536, read out of the shipped MTXM,
  2 WCAG contrast measured on that map's own real render, dominant pair and worst pair,
  3 booth artifacts, uniform single-step Lanczos downscales of a chrome-free map-body crop
    located from the capture itself,
  4 re-open hash, size, mtime, plus a pixel diff between the two real renders.

Plus the dispatch-mandated measurements: glyph height in tiles, thinnest stroke width in
tiles, the component census under the F1 minimum-dimension floor, and the per-letterform
4x-downscale survival measured two ways: on the shipped mask resampled 4x, and on the real
booth64 artifact. The builder reports measurements and does not declare the map legible;
M8 decides legibility.
"""
import json
import math
import re
import struct
import subprocess
import sys
from collections import Counter, deque

HERE = "/tmp/opencode/t0042"
W = H = 256
FLOOR = 10                      # F1 minimum-dimension floor: both bbox axes >= 10 tiles

SCM = f"{HERE}/i-love-korea.scm"
WRITTEN_CHK = f"{HERE}/i-love-korea.chk"
EXTRACTED_CHK = f"{HERE}/m7-extracted.chk"

OPEN_PNG = f"{HERE}/m7-open.png"
REOPEN_PNG = f"{HERE}/m7-reopen.png"
JUMP_PNG = f"{HERE}/m7-jump.png"

CANVAS_CROP = (155, 105, 1878, 832)     # main-canvas interior, the frame every earlier read used
STATUS_CROP = (0, 1045, 1920, 1080)
# The overview panel's fixed chrome window: the editor layout is identical in every capture,
# so the search window is a chrome region, and the body is located from map-tone pixels inside it.
PANEL_WINDOW = (0, 90, 250, 330)


def luminance(rgb):
    def lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb[:3]
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def ratio(a, b):
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


_LUM_CACHE = {}


def lum(rgb):
    key = rgb[:3]
    v = _LUM_CACHE.get(key)
    if v is None:
        v = luminance(key)
        _LUM_CACHE[key] = v
    return v


def is_map_tone(p):
    r, g, b = p[:3]
    if abs(r - g) <= 8 and abs(g - b) <= 8 and 140 <= r <= 200:
        return True                                  # Ice World flat ground tone class
    if b >= r and max(r, g, b) <= 130 and lum(p) < 0.09:
        return True                                  # glyph tone class
    return False


# ---------------------------------------------------------------- shipped file
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


def str_name(strsec):
    off = struct.unpack("<H", strsec[:2])[0]
    tail = strsec[2048 + off:]
    return tail.split(b"\x00")[0].decode("latin1")


def mask_from(chk):
    mt = struct.unpack("<%dH" % (len(chk["MTXM"]) // 2), chk["MTXM"])
    vals = sorted(set(mt))
    return [[1 if mt[y * W + x] == 192 else 0 for x in range(W)] for y in range(H)], vals


def components(mask, conn=8):
    hh = len(mask)
    ww = len(mask[0])
    seen = [[False] * ww for _ in range(hh)]
    nbrs = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)] if conn == 8 \
        else [(-1, 0), (1, 0), (0, -1), (0, 1)]
    out = []
    for y0 in range(hh):
        for x0 in range(ww):
            if mask[y0][x0] != 1 or seen[y0][x0]:
                continue
            q = deque([(x0, y0)])
            seen[y0][x0] = True
            cells = []
            while q:
                x, y = q.popleft()
                cells.append((x, y))
                for dx, dy in nbrs:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < ww and 0 <= ny < hh and mask[ny][nx] == 1 and not seen[ny][nx]:
                        seen[ny][nx] = True
                        q.append((nx, ny))
            xs = [c[0] for c in cells]
            ys = [c[1] for c in cells]
            out.append({"cells": cells, "area": len(cells), "x0": min(xs), "x1": max(xs),
                        "y0": min(ys), "y1": max(ys), "w": max(xs) - min(xs) + 1,
                        "h": max(ys) - min(ys) + 1})
    return out


def min_runs(comp):
    """Thinnest ink run of a component in tiles: min over horizontal runs and min over vertical runs."""
    cells = comp["cells"]
    hruns = []
    rows = {}
    for x, y in cells:
        rows.setdefault(y, []).append(x)
    for y, xs in rows.items():
        xs.sort()
        run = 1
        for a, b in zip(xs, xs[1:]):
            if b == a + 1:
                run += 1
            else:
                hruns.append(run)
                run = 1
        hruns.append(run)
    vruns = []
    cols = {}
    for x, y in cells:
        cols.setdefault(x, []).append(y)
    for x, ys in cols.items():
        ys.sort()
        run = 1
        for a, b in zip(ys, ys[1:]):
            if b == a + 1:
                run += 1
            else:
                vruns.append(run)
                run = 1
        vruns.append(run)
    return min(hruns), min(vruns)


def enclosed_ground(mask):
    reach = [[False] * W for _ in range(H)]
    q = deque()
    for x in range(W):
        q += [(x, 0), (x, H - 1)]
    for y in range(H):
        q += [(0, y), (W - 1, y)]
    for x, y in q:
        if mask[y][x] == 0 and not reach[y][x]:
            reach[y][x] = True
            st = deque([(x, y)])
            while st:
                cx, cy = st.popleft()
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < W and 0 <= ny < H and mask[ny][nx] == 0 and not reach[ny][nx]:
                        reach[ny][nx] = True
                        st.append((nx, ny))
    return sum(1 for y in range(H) for x in range(W) if mask[y][x] == 0 and not reach[y][x])


def perimeter(mask):
    p = 0
    for y in range(H):
        for x in range(W):
            if not mask[y][x]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < W and 0 <= ny < H and mask[ny][nx]):
                    p += 1
    return p


def row_runs(mask):
    rows2 = runs = gap = 0
    narrow = 10 ** 9
    for y in range(H):
        r, x = [], 0
        while x < W:
            if mask[y][x]:
                x0 = x
                while x < W and mask[y][x]:
                    x += 1
                r.append((x0, x - 1))
                narrow = min(narrow, x - x0)
            else:
                x += 1
        if len(r) >= 2:
            rows2 += 1
            runs += len(r)
            for a, b in zip(r, r[1:]):
                gap = max(gap, b[0] - a[1] - 1)
    return {"rows_with_2plus_runs": rows2, "runs": runs, "largest_enclosed_ground_gap_tiles": gap,
            "narrowest_run_tiles": narrow}


# ---------------------------------------------------------------- captures
def map_tone_mask(img):
    from PIL import ImageChops
    r, g, b = img.split()
    d1 = ImageChops.difference(r, g).point(lambda v: 255 if v <= 8 else 0)
    d2 = ImageChops.difference(g, b).point(lambda v: 255 if v <= 8 else 0)
    rb = r.point(lambda v: 255 if 140 <= v <= 200 else 0)
    ground = ImageChops.logical_and(ImageChops.logical_and(d1.convert("1"), d2.convert("1")),
                                    rb.convert("1"))
    bluer = ImageChops.subtract(b, r).point(lambda v: 255 if v > 0 else 0)
    darkish = ImageChops.lighter(ImageChops.lighter(r, g), b).point(lambda v: 255 if v <= 130 else 0)
    glyph = ImageChops.logical_and(bluer.convert("1"), darkish.convert("1"))
    return ImageChops.logical_or(ground, glyph)


def locate_body_clusters(img, min_run=40):
    """The m5 cluster method, kept for inspectability; recorded expectation for this map is that
    it under-locates the body because no single row carries a 40 px run in the glyph band."""
    mask = map_tone_mask(img).convert("L")
    w, h = img.size
    data = mask.tobytes()
    pattern = re.compile(b"\xff{%d,}" % min_run)
    buckets = {}
    for y in range(h):
        row = data[y * w:(y + 1) * w]
        for m in pattern.finditer(row):
            key = (m.start() // 12, (m.end() - 1) // 12)
            buckets.setdefault(key, []).append((m.start(), m.end() - 1, y))
    clusters = []
    for key, rs in buckets.items():
        xs0 = min(r[0] for r in rs)
        xs1 = max(r[1] for r in rs)
        ys0 = min(r[2] for r in rs)
        ys1 = max(r[2] for r in rs)
        clusters.append((xs0, ys0, xs1, ys1, len(rs), sum(r[1] - r[0] + 1 for r in rs)))
    clusters.sort(key=lambda c: -c[4])
    return clusters


def locate_body_bbox(img):
    """Bbox of map-tone pixels inside the overview-panel chrome window. Tried first and REJECTED
    on evidence: the window catches panel scrollbars whose grey passes the ground-tone class, so
    the bbox returns the chrome window itself (7,90)-(249,329), not the map body. Kept in the
    report as the rejected alternative so the choice is inspectable."""
    mask = map_tone_mask(img).convert("L")
    w, _ = img.size
    data = mask.tobytes()
    x0w, y0w, x1w, y1w = PANEL_WINDOW
    xs, ys = [], []
    for y in range(y0w, y1w):
        row = data[y * w + x0w: y * w + x1w]
        for m in re.finditer(b"\xff", row):
            ys.append(y)
            xs.append(x0w + m.start())
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def panel_extent(runs, x0, x1, y0, y1):
    """Grow a located block vertically while rows still contain a run overlapping its x-window by
    at least 60 px, the m5 correction for the white viewport-indicator rectangle splitting the
    top rows of the render into a separate cluster."""
    rows = {}
    for rx0, rx1, y in runs:
        rows.setdefault(y, []).append((rx0, rx1))

    def overlaps(y):
        for rx0, rx1 in rows.get(y, []):
            lo, hi = max(rx0, x0), min(rx1, x1)
            if hi - lo + 1 >= 60:
                return True
        return False

    ny0, ny1 = y0, y1
    while ny0 - 1 >= 0 and overlaps(ny0 - 1):
        ny0 -= 1
    while ny1 + 1 < 1080 and overlaps(ny1 + 1):
        ny1 += 1
    return ny0, ny1, y0, y1


def pick_overview_panel(clusters):
    """The overview thumbnail is the near-square map-tone block on the left of the frame, about
    128 px on a side because the panel renders 0.5 px per tile of a 256-tile map."""
    cands = [c for c in clusters if c[0] < 300 and 100 <= (c[2] - c[0] + 1) <= 200
             and 100 <= (c[3] - c[1] + 1) <= 200]
    if not cands:
        return None
    return max(cands, key=lambda c: c[4])


def locate_runs(img, min_run=40):
    """Raw per-row runs of >= min_run map-tone pixels, for panel_extent."""
    mask = map_tone_mask(img).convert("L")
    w, h = img.size
    data = mask.tobytes()
    pattern = re.compile(b"\xff{%d,}" % min_run)
    runs = []
    for y in range(h):
        row = data[y * w:(y + 1) * w]
        for m in pattern.finditer(row):
            runs.append((m.start(), m.end() - 1, y))
    return runs


def tone_composition(img, box, step=1):
    px = img.load()
    ground, glyph, other = Counter(), Counter(), Counter()
    for y in range(box[1], box[3], step):
        for x in range(box[0], box[2], step):
            p = px[x, y][:3]
            if is_map_tone(p):
                (ground if lum(p) > 0.15 else glyph)[p] += 1
            else:
                other[p] += 1
    total = sum(ground.values()) + sum(glyph.values()) + sum(other.values())
    gdom = ground.most_common(1)[0][0] if ground else None
    ydom = glyph.most_common(1)[0][0] if glyph else None
    worst = None
    if gdom and ydom:
        worst = min(ratio(g, ydom) for g in ground)
    return {
        "crop": list(box), "total_px": total,
        "ground_px": sum(ground.values()), "glyph_px": sum(glyph.values()),
        "nonground_px": sum(other.values()),
        "distinct_ground_tones": len(ground), "distinct_glyph_tones": len(glyph),
        "distinct_other_tones": len(other),
        "ground_dominant": list(gdom) if gdom else None,
        "glyph_dominant": list(ydom) if ydom else None,
        "ground_share_pct": round(100 * sum(ground.values()) / total, 2),
        "glyph_share_pct": round(100 * sum(glyph.values()) / total, 2),
        "other_share_pct": round(100 * sum(other.values()) / total, 2),
        "wcag_dominant_pair": round(ratio(gdom, ydom), 3) if gdom and ydom else None,
        "wcag_worst_ground_against_glyph_dominant": round(worst, 3) if worst else None,
        "other_tones_top": [{"rgb": list(t), "px": n} for t, n in other.most_common(5)],
    }


def diff_crops(a, b, box, threshold=16):
    from PIL import ImageChops
    ca = a if box == (0, 0, a.size[0], a.size[1]) else a.crop(box)
    cb = b if box == (0, 0, b.size[0], b.size[1]) else b.crop(box)
    da = ImageChops.difference(ca.convert("RGB"), cb.convert("RGB"))
    dr, dg, db = da.split()
    dmax = ImageChops.lighter(ImageChops.lighter(dr, dg), db)
    mask = dmax.point(lambda v: 1 if v > threshold else 0)
    n = sum(mask.getdata())
    bbox = mask.getbbox()
    total = (box[2] - box[0]) * (box[3] - box[1])
    return {"crop": list(box), "threshold": threshold, "differing_px": n, "diff_region_bbox": bbox,
            "total_px": total, "diff_pct": round(100 * n / total, 3)}


def chrome_share(img):
    from PIL import Image
    im = Image.open(img).convert("RGB")
    px = im.load()
    n = tot = 0
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            p = px[x, y][:3]
            tot += 1
            if not is_map_tone(p):
                n += 1
    return {"artifact": img.split("/")[-1], "size": list(im.size),
            "map_tone_share_pct": round(100 * (tot - n) / tot, 2),
            "nontone_share_pct": round(100 * n / tot, 2),
            "nontone_px": n}


# ---------------------------------------------------------------- 4x survival
def glyph_windows(mask):
    """Letterform windows straight from the shipped mask: 8-connected components sorted by x0,
    labelled by their designed order in the row."""
    labels = ["I", "heart", "K", "O", "R", "E", "A"]
    comps = sorted(components(mask, conn=8), key=lambda c: c["x0"])
    out = []
    for lab, c in zip(labels, comps):
        out.append({"label": lab, "x0": c["x0"], "x1": c["x1"], "y0": c["y0"], "y1": c["y1"],
                    "w": c["w"], "h": c["h"], "area": c["area"], "kind": "silhouette" if lab == "heart" else "letter"})
    return out


def binary_from_lanczos(mask, scale=4):
    """Shipped mask resampled 1/scale with Lanczos, thresholded at mid; the resampling family the
    booth artifact pipeline uses, applied to the mask itself."""
    from PIL import Image
    im = Image.new("L", (W, H))
    im.putdata([255 if mask[y][x] else 0 for y in range(H) for x in range(W)])
    sm = im.resize((W // scale, H // scale), Image.LANCZOS)
    d = sm.tobytes()
    return [[1 if d[y * (W // scale) + x] >= 128 else 0 for x in range(W // scale)]
            for y in range(H // scale)]


def survival(binary, windows, expect_ink):
    """Per-letterform survival on a binary at 0.25 px per tile. Survives = glyph ink present,
    ink at least 50 percent of the area-derived expectation, and vertical coverage at least 0.8
    of the window's px rows. Reported with counts rather than asserted."""
    n = len(binary)
    res = []
    for w in windows:
        ax0, ax1 = w["x0"] // 4, (w["x1"] + 3) // 4
        ay0, ay1 = w["y0"] // 4, (w["y1"] + 3) // 4
        ax1, ay1 = min(ax1, n), min(ay1, n)
        ink = 0
        rows_with_ink = 0
        min_run = 10 ** 9
        for y in range(ay0, ay1):
            row_runs_local = 0
            run = 0
            for x in range(ax0, ax1):
                if binary[y][x]:
                    run += 1
                else:
                    if run:
                        row_runs_local = max(row_runs_local, run)
                        min_run = min(min_run, run)
                    run = 0
            if run:
                row_runs_local = max(row_runs_local, run)
                min_run = min(min_run, run)
            if row_runs_local:
                rows_with_ink += 1
                ink += 1
        # count ink properly
        ink = sum(1 for y in range(ay0, ay1) for x in range(ax0, ax1) if binary[y][x])
        exp_rows = ay1 - ay0
        res.append({
            "label": w["label"], "px_window": [ax0, ay0, ax1, ay1],
            "ink_px": ink, "expected_ink_px": expect_ink,
            "ink_vs_expect": round(ink / expect_ink, 3) if expect_ink else None,
            "rows_with_ink": rows_with_ink, "expected_rows": exp_rows,
            "vertical_coverage": round(rows_with_ink / exp_rows, 3) if exp_rows else None,
            "thinnest_run_px": min_run if min_run < 10 ** 9 else None,
            "survives": (None if expect_ink is None or not exp_rows else
                         bool(ink >= 0.5 * expect_ink and rows_with_ink >= 0.8 * exp_rows)),
        })
    return res


def real_glyph_map(img, box):
    """Binary glyph-tone map of a real crop: 1 where the pixel is the glyph tone class."""
    px = img.load()
    n = box[2] - box[0]
    out = [[0] * n for _ in range(box[3] - box[1])]
    for y in range(box[1], box[3]):
        for x in range(box[0], box[2]):
            p = px[x, y][:3]
            if is_map_tone(p) and lum(p) <= 0.15:
                out[y - box[1]][x - box[0]] = 1
    return out


def main():
    from PIL import Image
    from PIL import Image as I

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
        "mtxm_bytes": len(chk["MTXM"]), "tile_bytes": len(chk["TILE"]),
        "mtxm_equals_tile": chk["MTXM"] == chk["TILE"],
        "isom_bytes": len(chk["ISOM"]),
        "isom_bytes_distinct": sorted(set(chk["ISOM"]))[:4],
        "unit_section_bytes": len(chk.get("UNIT", b"MISSING")),
        "dood_section_present": "DOOD" in chk,
        "mrgn_bytes": len(chk.get("MRGN", b"MISSING")),
        "str_name": str_name(chk["STR "]),
        "distinct_values": vals,
    }

    filled = sum(sum(r) for r in mask)
    comps8 = sorted(components(mask, 8), key=lambda c: c["x0"])
    comps4 = components(mask, 4)
    labels = ["I", "heart", "K", "O", "R", "E", "A"]
    comp_rows = []
    for lab, c in zip(labels, comps8):
        mh, mv = min_runs(c)
        comp_rows.append({"label": lab, "bbox": [c["x0"], c["y0"], c["x1"], c["y1"]],
                          "w": c["w"], "h": c["h"], "tiles": c["area"],
                          "min_h_run_tiles": mh, "min_v_run_tiles": mv,
                          "floor_min_dim_10": "KEEP" if c["w"] >= FLOOR and c["h"] >= FLOOR else "DROP"})
    letter_rows = [r for r in comp_rows if r["label"] != "heart"]
    xs = [x for y in range(H) for x, v in enumerate(mask[y]) if v]
    ys = [y for y in range(H) for x, v in enumerate(mask[y]) if v]
    rep["gate1_coverage"] = {
        "glyph_tiles": filled, "coverage_pct": round(100 * filled / 65536, 2),
        "bbox_x": [min(xs), max(xs)], "bbox_w": max(xs) - min(xs) + 1,
        "bbox_y": [min(ys), max(ys)], "bbox_h": max(ys) - min(ys) + 1,
        "components_8conn": len(comps8), "components_4conn": len(comps4),
        "components_4conn_areas": sorted((c["area"] for c in comps4), reverse=True),
        "enclosed_ground_tiles_4conn": enclosed_ground(mask),
        "perimeter_boundary_edges": perimeter(mask), **row_runs(mask),
    }

    rep["glyph_metrics"] = {
        "floor_rule": "minimum-dimension reading per F1: every kept component at least 10 tiles on both axes",
        "letterform_components_8conn": comp_rows,
        "glyph_height_tiles": max(r["h"] for r in letter_rows),
        "letter_stroke_min_tiles": min(r["min_h_run_tiles"] for r in letter_rows),
        "letter_bar_thickness_tiles": min(r["min_v_run_tiles"] for r in letter_rows),
        "heart_bbox_tiles": next([r["w"], r["h"]] for r in comp_rows if r["label"] == "heart"),
        "heart_min_run_tiles": next(r["min_h_run_tiles"] for r in comp_rows if r["label"] == "heart"),
        "separator_gaps_tiles": [
            comps8[i + 1]["x0"] - comps8[i]["x1"] - 1 for i in range(len(comps8) - 1)],
        "margins_tiles": {"left": min(xs), "right": 255 - max(xs), "top": min(ys), "bottom": 255 - max(ys)},
    }

    # ---- 4x survival on the shipped mask, resampled with Lanczos
    b64 = binary_from_lanczos(mask, 4)
    b64box = binary_from_lanczos(mask, 8)
    windows = glyph_windows(mask)
    rep["survival_4x_mask_lanczos"] = {
        "method": "shipped MTXM mask resized 256->64 single-step Lanczos, threshold >= 128",
        "components_after_4x_8conn": len(components(b64, 8)),
        "components_after_4x_4conn": len(components(b64, 4)),
        "per_letterform": survival(b64, windows, None),
        "components_after_8x_8conn": len(components(b64box, 8)),
    }
    # fill expectations from area/16
    for w, s in zip(windows, rep["survival_4x_mask_lanczos"]["per_letterform"]):
        exp = w["area"] / 16
        s["expected_ink_px"] = round(exp, 1)
        s["ink_vs_expect"] = round(s["ink_px"] / exp, 3)
        s["survives"] = bool(s["ink_px"] >= 0.5 * exp and s["rows_with_ink"] >= 0.8 * s["expected_rows"])

    # ---- real renders
    open_img = Image.open(OPEN_PNG).convert("RGB")
    reopen_img = Image.open(REOPEN_PNG).convert("RGB")
    jump_img = Image.open(JUMP_PNG).convert("RGB")
    rep["captures"] = {"m7-open.png": list(open_img.size), "m7-reopen.png": list(reopen_img.size),
                       "m7-jump.png": list(jump_img.size)}

    clusters = locate_body_clusters(open_img)
    runs = locate_runs(open_img)
    clusters_reopen = locate_body_clusters(reopen_img)
    runs_reopen = locate_runs(reopen_img)
    panel = pick_overview_panel(clusters)
    panel_reopen = pick_overview_panel(clusters_reopen)
    rep["map_body_locate"] = {
        "method": "per-row byte regex over a PIL map-tone mask, runs of 40 px or more clustered "
                  "by rounded x-extent, the block grown vertically while rows still overlap its "
                  "x-window by 60 px or more (the m5 viewport-indicator correction). The bbox-"
                  "inside-panel-window alternative was tried and rejected, its report entry names "
                  "why: it returns the chrome window because scrollbar greys pass the ground-tone class.",
        "bbox_method_rejected": (locate_body_bbox(open_img) and list(locate_body_bbox(open_img))),
        "cluster_method_open_top5": [{"bbox": [c[0], c[1], c[2], c[3]], "rows": c[4],
                                      "dims": [c[2] - c[0] + 1, c[3] - c[1] + 1]} for c in clusters[:5]],
        "cluster_method_reopen_top5": [{"bbox": [c[0], c[1], c[2], c[3]], "rows": c[4],
                                        "dims": [c[2] - c[0] + 1, c[3] - c[1] + 1]} for c in clusters_reopen[:5]],
        "panel_cluster_open": [panel[0], panel[1], panel[2], panel[3], panel[4]] if panel else None,
        "panel_cluster_reopen": [panel_reopen[0], panel_reopen[1], panel_reopen[2],
                                 panel_reopen[3], panel_reopen[4]] if panel_reopen else None,
        "earlier_reads_rect": [18, 112, 145, 239],
    }
    if panel is None or panel_reopen is None:
        sys.stderr.write("no overview-panel cluster located, clusters are in the report\n")
        return 3
    x0, y0, x1, y1, nrows, _runpx = panel
    ey0, ey1, raw_y0, raw_y1 = panel_extent(runs, x0, x1, y0, y1)
    ey0_r, ey1_r, _, _ = panel_extent(runs_reopen, panel_reopen[0], panel_reopen[2],
                                      panel_reopen[1], panel_reopen[3])
    rep["panel_expansion"] = {"raw_cluster_rows": [raw_y0, raw_y1],
                              "expanded_rows": [ey0, ey1],
                              "rows_recovered_above": raw_y0 - ey0,
                              "rows_recovered_below": ey1 - raw_y1,
                              "expanded_dims": [x1 - x0 + 1, ey1 - ey0 + 1],
                              "reopen_expanded_rows": [ey0_r, ey1_r]}
    side = 128
    crop = (x0, ey0, x0 + side, ey0 + side)
    crop_reopen = (panel_reopen[0], ey0_r, panel_reopen[0] + side, ey0_r + side)
    rep["body_crop"] = {"crop": list(crop), "crop_reopen": list(crop_reopen), "side_px": side,
                        "tiles_per_px": 2.0,
                        "note": "128x128 square crop from the located, expanded top-left; "
                                "uniform on both axes"}

    rep["gate2_render_body"] = tone_composition(open_img, crop)
    rep["gate2_render_body_reopen"] = tone_composition(reopen_img, crop_reopen)
    rep["gate4_reopen_diff_body"] = diff_crops(open_img, reopen_img, crop)
    rep["gate4_reopen_diff_fullframe"] = diff_crops(open_img, reopen_img, (0, 0, 1920, 1080))
    rep["gate2_main_canvas_frame"] = tone_composition(jump_img, CANVAS_CROP, step=2)
    rep["status_bar_crop"] = {"crop": list(STATUS_CROP), "note": "cropped for reading, see m7-read-status-3x.png"}

    # ---- booth artifacts, uniform Lanczos from the located square body crop
    body_img = open_img.crop(crop)
    body_img.save(f"{HERE}/i-love-korea-mm.png")
    body_img.resize((64, 64), I.LANCZOS).save(f"{HERE}/i-love-korea-booth64.png")
    body_img.resize((32, 32), I.LANCZOS).save(f"{HERE}/i-love-korea-booth32.png")
    body_img.resize((256, 256), I.LANCZOS).save(f"{HERE}/i-love-korea-mm-2x.png")
    body_img.resize((384, 384), I.NEAREST).save(f"{HERE}/m7-read-body-3x.png")
    body_img.resize((64, 64), I.LANCZOS).resize((256, 256), I.NEAREST).save(f"{HERE}/m7-read-booth64.png")
    body_img.resize((32, 32), I.LANCZOS).resize((256, 256), I.NEAREST).save(f"{HERE}/m7-read-booth32.png")
    open_img.crop(STATUS_CROP).resize(((STATUS_CROP[2] - STATUS_CROP[0]) * 3,
                                       (STATUS_CROP[3] - STATUS_CROP[1]) * 3), I.LANCZOS) \
        .save(f"{HERE}/m7-read-status-3x.png")

    booth64 = Image.open(f"{HERE}/i-love-korea-booth64.png").convert("RGB")
    booth32 = Image.open(f"{HERE}/i-love-korea-booth32.png").convert("RGB")
    rep["gate3_booth_artifacts"] = {
        "derivation": "i-love-korea-mm.png is the 128x128 map-body crop of m7-open.png; booth64 and "
                      "booth32 are single-step Lanczos resizes of it at 0.5 and 0.25 on both axes; "
                      "mm-2x is a 2x Lanczos enlargement",
        "uniform_scale_check": {"mm_to_64": [64 / side, 64 / side], "mm_to_32": [32 / side, 32 / side]},
        "chrome": [chrome_share(f"{HERE}/i-love-korea-mm.png"),
                   chrome_share(f"{HERE}/i-love-korea-booth64.png"),
                   chrome_share(f"{HERE}/i-love-korea-booth32.png")],
        "composition_64": tone_composition(booth64, (0, 0, 64, 64)),
        "composition_32": tone_composition(booth32, (0, 0, 32, 32)),
    }

    # ---- 4x survival on the REAL booth artifact: glyph-tone pixels of booth64
    real64 = real_glyph_map(booth64, (0, 0, 64, 64))
    rep["survival_4x_real_booth64"] = {
        "method": "glyph-tone-classified pixel map of the real booth64 artifact (0.25 px per tile "
                  "of the real overview render), per-letterform windows from the shipped MTXM",
        "components_after_4x_8conn": len(components(real64, 8)),
        "per_letterform": survival(real64, windows, None),
    }
    for w, s in zip(windows, rep["survival_4x_real_booth64"]["per_letterform"]):
        exp = w["area"] / 16
        s["expected_ink_px"] = round(exp, 1)
        s["ink_vs_expect"] = round(s["ink_px"] / exp, 3)
        s["survives"] = bool(s["ink_px"] >= 0.5 * exp and s["rows_with_ink"] >= 0.8 * s["expected_rows"])

    json.dump(rep, open(f"{HERE}/i-love-korea_report.json", "w"), indent=1)

    print("container:", json.dumps(rep["container"]))
    print("gate1 coverage:", json.dumps(rep["gate1_coverage"]))
    print("glyph metrics:", json.dumps(rep["glyph_metrics"]))
    print("body locate:", json.dumps(rep["map_body_locate"]))
    print("body crop:", json.dumps(rep["body_crop"]))
    print("gate2 body:", json.dumps(rep["gate2_render_body"]))
    print("gate2 body reopen:", json.dumps(rep["gate2_render_body_reopen"]))
    print("gate2 main canvas:", json.dumps(rep["gate2_main_canvas_frame"]))
    print("gate4 reopen diff:", json.dumps(rep["gate4_reopen_diff_body"]),
          json.dumps(rep["gate4_reopen_diff_fullframe"]))
    print("gate3 booth:", json.dumps(rep["gate3_booth_artifacts"]["chrome"]))
    print("gate3 booth64 composition:", json.dumps({k: rep["gate3_booth_artifacts"]["composition_64"][k] for k in
                                                    ("glyph_share_pct", "ground_share_pct", "other_share_pct",
                                                     "wcag_dominant_pair", "wcag_worst_ground_against_glyph_dominant")}))
    print("gate3 booth32 composition:", json.dumps({k: rep["gate3_booth_artifacts"]["composition_32"][k] for k in
                                                    ("glyph_share_pct", "ground_share_pct", "other_share_pct")}))
    print("survival mask-4x:", json.dumps(rep["survival_4x_mask_lanczos"], indent=1))
    print("survival booth64:", json.dumps(rep["survival_4x_real_booth64"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
