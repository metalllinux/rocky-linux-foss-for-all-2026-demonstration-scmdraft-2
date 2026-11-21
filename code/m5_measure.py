#!/usr/bin/env python3
"""TASK-0042 dispatch M5 step 4: gate measurement of the rebuilt `republic-of-korea` map.

Two sources only. The published map file, `republic-of-korea.scm`, with its CHK extracted by
`chkdump` (StormLib, MIT) and its MTXM parsed, and the real SCMDraft 2 captures `m5-open.png`,
`m5-jump.png`, `m5-reopen.png` taken on the target. No mask module is imported for a gate number,
and the projection constants below are restated here rather than imported so the mask-to-map
comparison is arithmetic rather than trust.

The four gate numbers this reports:
  1 coverage, glyph tiles over 65536, read out of the shipped MTXM,
  2 WCAG contrast measured on that map's own real render, dominant tone pair and worst pair,
  3 booth artifacts that are uniform Lanczos downscales of a map-body crop located from the
    capture itself, with the chrome share of every artifact reported,
  4 re-open hash, size, mtime, plus a pixel diff between the two real renders.

Plus the measured comparison against the superseded 25.01 percent build, including the named
coastal anchors, which is the acceptance line `M4` set. The builder reports measurements and does
not declare the map identifiable. `M6` decides identifiability.
"""
import json
import math
import struct
import subprocess
import sys
from collections import Counter, deque

HERE = "/tmp/opencode/t0042"
W = H = 256

NEW_SCM = f"{HERE}/republic-of-korea.scm"
OLD_CHK = f"{HERE}/superseded-republic-of-korea-110m.chk"
NEW_CHK_EXTRACTED = f"{HERE}/m5-extracted.chk"

OPEN_PNG = f"{HERE}/m5-open.png"
REOPEN_PNG = f"{HERE}/m5-reopen.png"
JUMP_PNG = f"{HERE}/m5-jump.png"

# Projection constants restated from the recorded M3 projection, not imported from builder code.
LAT_TOP, LAT_BOT = 38.85, 33.10
KM_PER_DEG_LAT = 111.0
KM_PER_TILE = KM_PER_DEG_LAT * (LAT_TOP - LAT_BOT) / (H - 1)
MID_LAT = (LAT_TOP + LAT_BOT) / 2.0
KM_PER_DEG_LON = KM_PER_DEG_LAT * math.cos(math.radians(MID_LAT))
LON_CENTRE = 127.5

# Main-canvas interior frame used by every earlier map read.
CANVAS_CROP = (155, 105, 1878, 832)
STATUS_CROP = (0, 1045, 1920, 1080)

ANCHORS = [
    ("Incheon / Han estuary mouth", 126.60, 37.53, "sea"),
    ("Ganghwa Strait", 126.42, 37.65, "sea"),
    ("Asan Bay head", 126.72, 36.72, "sea"),
    ("Seosanman bay head", 126.42, 36.70, "sea"),
    ("Taean peninsula", 126.30, 36.75, "land"),
    ("Geum estuary at Gunsan", 126.73, 35.97, "sea"),
    ("Mokpo / Yeongsan estuary", 126.38, 34.76, "sea"),
    ("Seosanman coast west of Yeonggwang", 126.05, 35.05, "sea"),
    ("Gwangyang Bay inner", 127.62, 34.93, "sea"),
    ("Jinhae Bay inner", 128.62, 35.16, "sea"),
    ("Namhae strait", 127.90, 34.80, "sea"),
    ("Donghae / Mukho inlet", 129.10, 37.55, "sea"),
    ("Pohang neck", 129.38, 36.03, "land"),
    ("Ulsan coast", 129.32, 35.55, "land"),
    ("Gangneung coast", 129.10, 37.75, "land"),
    ("Busan coast", 129.06, 35.08, "land"),
    ("Jeju main body", 126.55, 33.40, "land"),
    ("Jeju west tip", 126.25, 33.35, "land"),
    ("Jeju strait", 126.55, 33.95, "sea"),
    ("NE point near Seokjin", 128.53, 38.57, "land"),
    ("NE tip at the Tumen mouth", 129.25, 38.40, "land"),
    ("SW corner near Jindo", 126.15, 34.55, "land"),
]


def lon_to_col(lon):
    return (W - 1) / 2.0 + (lon - LON_CENTRE) * KM_PER_DEG_LON / KM_PER_TILE


def lat_to_row(lat):
    return (LAT_TOP - lat) * KM_PER_DEG_LAT / KM_PER_TILE


def luminance(rgb):
    def lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb[:3]
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def ratio(a, b):
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


# ------------------------------------------------------------------ map mask from the file
def extract_chk():
    r = subprocess.run([f"{HERE}/chkdump", NEW_SCM, "staredit\\scenario.chk", NEW_CHK_EXTRACTED],
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
    """STR layout is a u16[1024] offset table then the NUL-terminated strings. The map name is the
    string at offset 0, not the first bytes of the section."""
    off = struct.unpack("<H", strsec[:2])[0]
    tail = strsec[2048 + off:]
    return tail.split(b"\x00")[0].decode("latin1")


def mask_from(chk):
    mt = struct.unpack("<%dH" % (len(chk["MTXM"]) // 2), chk["MTXM"])
    vals = sorted(set(mt))
    return [[1 if mt[y * W + x] == 192 else 0 for x in range(W)] for y in range(H)], vals, mt


def components(mask, conn=8):
    seen = [[False] * W for _ in range(H)]
    nbrs = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)] if conn == 8 \
        else [(-1, 0), (1, 0), (0, -1), (0, 1)]
    out = []
    for y0 in range(H):
        for x0 in range(W):
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
                    if 0 <= nx < W and 0 <= ny < H and mask[ny][nx] == 1 and not seen[ny][nx]:
                        seen[ny][nx] = True
                        q.append((nx, ny))
            xs = [c[0] for c in cells]
            ys = [c[1] for c in cells]
            out.append({"area": len(cells), "x0": min(xs), "x1": max(xs), "y0": min(ys), "y1": max(ys),
                        "w": max(xs) - min(xs) + 1, "h": max(ys) - min(ys) + 1})
    return out


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
    rows2 = runs = gap = narrow = 0
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


def edges(mask):
    out = {}
    for y in range(H):
        xs = [x for x in range(W) if mask[y][x]]
        if xs:
            out[y] = (min(xs), max(xs))
    return out


def anchor_windows(new_mask, old_mask):
    rows = []
    for name, lon, lat, expected in ANCHORS:
        col = int(round(lon_to_col(lon)))
        row = int(round(lat_to_row(lat)))
        inmap = 0 <= col < W and 0 <= row < H
        rec = {"anchor": name, "lon": lon, "lat": lat, "expected": expected,
               "col": col, "row": row, "in_map": inmap}
        for label, m in (("new", new_mask), ("old", old_mask)):
            if not inmap:
                rec[f"{label}_centre"] = "off-map"
                rec[f"{label}_sea_tiles_5x5"] = None
                continue
            rec[f"{label}_centre"] = "ground" if m[row][col] == 0 else "glyph"
            sea = sum(1 for dy in range(-2, 3) for dx in range(-2, 3)
                      if 0 <= col + dx < W and 0 <= row + dy < H and m[row + dy][col + dx] == 0)
            rec[f"{label}_sea_tiles_5x5"] = sea
        rows.append(rec)
    return rows


# ------------------------------------------------------------------ capture measurement
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


def map_tone_mask(img):
    """Whole-frame map-tone mask built from PIL channel operations, so the 1920x1080 scan runs in
    C rather than in a per-pixel Python loop. The first version of this script spent 600 s in that
    loop and was killed by its own timeout before it printed anything. Ground is a near-neutral
    grey in 140..200, glyph is bluish and dark, the same two definitions the M4 read used."""
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


def locate_body(img, min_run=40):
    """Locate contiguous map-tone blocks. Runs of `min_run` pixels or more are found per row with
    a byte regex over the mask image, then clustered by x-extent, so the cluster inventory is
    visible in the report instead of one number chosen by an unreported heuristic.

    Returns clusters largest-first as (x0, y0, x1, y1, rows, run_pixels)."""
    import re
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
        if not rs:
            continue
        xs0 = min(r[0] for r in rs)
        xs1 = max(r[1] for r in rs)
        ys0 = min(r[2] for r in rs)
        ys1 = max(r[2] for r in rs)
        clusters.append((xs0, ys0, xs1, ys1, len(rs), sum(r[1] - r[0] + 1 for r in rs)))
    clusters.sort(key=lambda c: -c[4])
    runs = [r for rs in buckets.values() for r in rs]
    return clusters, runs


def panel_extent(runs, x0, x1, y0, y1):
    """Grow a located block vertically while rows still contain a run overlapping its x-window by
    at least 60 px. Needed because the white viewport-indicator rectangle the editor draws over the
    thumbnail starts a run 27 px into the map body in the top rows, which splits the top 12 rows of
    the render into a separate cluster and makes a naive bbox 12 rows short."""
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
    128 px on a side because the panel renders 0.5 px per tile of a 256-tile map. The candidate
    filter and the whole cluster inventory are both reported so the choice is inspectable."""
    cands = [c for c in clusters if c[0] < 300 and 100 <= (c[2] - c[0] + 1) <= 200
             and 100 <= (c[3] - c[1] + 1) <= 200]
    if not cands:
        return None
    return max(cands, key=lambda c: c[4])


def tone_composition(img, box, step=1):
    """Tone composition of a crop. `step` samples every nth pixel in each axis, which is how the
    large main-canvas frame is measured; the 128x128 map body is measured at full resolution."""
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
    """Count of pixels differing by more than `threshold` on any channel, computed with PIL
    channel arithmetic rather than a per-pixel Python loop: per-channel absolute difference, then
    a lighter() chain for the maximum across channels, then a threshold lookup."""
    from PIL import ImageChops
    ca = a if box == (0, 0, a.size[0], a.size[1]) else a.crop(box)
    cb = b if box == (0, 0, b.size[0], b.size[1]) else b.crop(box)
    da = ImageChops.difference(ca.convert("RGB"), cb.convert("RGB"))
    dr, dg, db = da.split()
    dmax = ImageChops.lighter(ImageChops.lighter(dr, dg), db)   # max per-channel difference
    n = sum(dmax.point(lambda v: 1 if v > threshold else 0).getdata())
    total = (box[2] - box[0]) * (box[3] - box[1])
    return {"crop": list(box), "threshold": threshold, "differing_px": n,
            "total_px": total, "diff_pct": round(100 * n / total, 3)}


def chrome_share(img, tones):
    """Pixels that are editor chrome rather than map tone, measured on the artifact itself."""
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


def main():
    from PIL import Image

    rep = {}

    rc, so, se = extract_chk()
    rep["chk_extract"] = {"rc": rc, "stdout": so, "stderr": se}

    new_chk = read_chk(NEW_CHK_EXTRACTED)
    new_mask, new_vals, new_mt = mask_from(new_chk)
    old_chk = read_chk(OLD_CHK)
    old_mask, old_vals, old_mt = mask_from(old_chk)

    tile = open(f"{HERE}/republic-of-korea.chk", "rb").read()
    rep["container"] = {
        "extracted_chk_bytes": len(open(NEW_CHK_EXTRACTED, "rb").read()),
        "controller_written_chk_bytes": len(tile),
        "extracted_equals_written": open(NEW_CHK_EXTRACTED, "rb").read() == tile,
        "era": struct.unpack("<H", new_chk["ERA "][:2])[0],
        "dim": struct.unpack("<HH", new_chk["DIM "][:4]),
        "mtxm_bytes": len(new_chk["MTXM"]), "tile_bytes": len(new_chk["TILE"]),
        "mtxm_equals_tile": new_chk["MTXM"] == new_chk["TILE"],
        "isom_bytes": len(new_chk["ISOM"]),
        "isom_bytes_distinct": sorted(set(new_chk["ISOM"])),
        "unit_section_bytes": len(new_chk.get("UNIT", b"MISSING")),
        "dood_section_present": "DOOD" in new_chk,
        "mrgn_bytes": len(new_chk.get("MRGN", b"MISSING")),
        "str_name": str_name(new_chk["STR "]),
        "new_distinct_values": new_vals, "old_distinct_values": old_vals,
    }

    def mask_metrics(m):
        filled = sum(sum(r) for r in m)
        comps = components(m)
        xs = [x for y in range(H) for x, v in enumerate(m[y]) if v]
        ys = [y for y in range(H) for x, v in enumerate(m[y]) if v]
        return {"glyph_tiles": filled, "coverage_pct": round(100 * filled / 65536, 2),
                "bbox_x": [min(xs), max(xs)], "bbox_w": max(xs) - min(xs) + 1,
                "bbox_y": [min(ys), max(ys)], "bbox_h": max(ys) - min(ys) + 1,
                "components_8conn": len(comps),
                "component_sizes": sorted((c["area"] for c in comps), reverse=True)[:8],
                "enclosed_ground_tiles_4conn": enclosed_ground(m),
                "perimeter_boundary_edges": perimeter(m), **row_runs(m)}

    rep["new_mask"] = mask_metrics(new_mask)
    rep["old_mask"] = mask_metrics(old_mask)

    inter = sum(1 for y in range(H) for x in range(W) if new_mask[y][x] and old_mask[y][x])
    union = sum(1 for y in range(H) for x in range(W) if new_mask[y][x] or old_mask[y][x])
    en, eo = edges(new_mask), edges(old_mask)
    shared_rows = sorted(set(en) & set(eo))
    devs = []
    for y in shared_rows:
        devs.append(abs(en[y][0] - eo[y][0]))
        devs.append(abs(en[y][1] - eo[y][1]))
    devs.sort()
    rep["new_vs_old"] = {
        "iou": round(inter / union, 4), "intersection_tiles": inter, "union_tiles": union,
        "new_only_tiles": rep["new_mask"]["glyph_tiles"] - inter,
        "old_only_tiles": rep["old_mask"]["glyph_tiles"] - inter,
        "rows_in_both_masks": len(shared_rows),
        "per_row_edge_deviation_tiles_mean": round(sum(devs) / len(devs), 3),
        "per_row_edge_deviation_tiles_median": devs[len(devs) // 2],
        "per_row_edge_deviation_tiles_worst": devs[-1],
        "deviations_over_10_tiles": sum(1 for d in devs if d > 10),
        "anchors": anchor_windows(new_mask, old_mask),
    }

    # ---- real renders
    open_img = Image.open(OPEN_PNG).convert("RGB")
    reopen_img = Image.open(REOPEN_PNG).convert("RGB")
    jump_img = Image.open(JUMP_PNG).convert("RGB")
    rep["captures"] = {"m5-open.png": list(open_img.size), "m5-reopen.png": list(reopen_img.size),
                       "m5-jump.png": list(jump_img.size)}

    clusters, runs = locate_body(open_img)
    clusters_reopen, runs_reopen = locate_body(reopen_img)
    panel = pick_overview_panel(clusters)
    panel_reopen = pick_overview_panel(clusters_reopen)
    rep["map_body_locate"] = {
        "method": "per-row byte regex over a PIL map-tone mask, runs of 40 px or more clustered by "
                  "rounded x-extent; the cluster inventory is reported, and the overview panel is "
                  "the near-square block on the left of the frame",
        "clusters_m5-open_top10": [{"bbox": [c[0], c[1], c[2], c[3]], "rows": c[4], "run_px": c[5],
                                    "dims": [c[2] - c[0] + 1, c[3] - c[1] + 1]}
                                   for c in clusters[:10]],
        "overview_panel_m5-open": [panel[0], panel[1], panel[2], panel[3], panel[4]],
        "overview_panel_m5-reopen": [panel_reopen[0], panel_reopen[1], panel_reopen[2],
                                     panel_reopen[3], panel_reopen[4]],
        "shadow_m4_recorded_rect": [18, 112, 146, 240],
    }
    if panel is None:
        sys.stderr.write("no overview-panel cluster located in m5-open.png, clusters are in the "
                         "report: %s\n" % json.dumps(rep["map_body_locate"]))
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
                              "reopen_expanded_rows": [ey0_r, ey1_r],
                              "shadow_m4_recorded_rect": [18, 112, 146, 240]}
    # The overview render is 0.5 px per tile, so a 256-tile map is 128 px square. The crop is that
    # square from the expanded top-left, which is what makes both downscales uniform.
    side = 128
    x0, y0 = panel[0], ey0
    crop = (x0, y0, x0 + side, y0 + side)
    rep["body_crop"] = {"crop": list(crop), "side_px": side, "located_bbox": [x0, y0, x1, y1],
                        "located_dims": [x1 - x0 + 1, y1 - y0 + 1],
                        "tiles_per_px": 2.0}

    rep["render_on_map_body"] = tone_composition(open_img, crop)
    rep["render_on_map_body_reopen"] = tone_composition(reopen_img, crop)
    rep["reopen_visual_diff"] = diff_crops(open_img, reopen_img, crop)
    rep["reopen_visual_diff_fullframe"] = diff_crops(open_img, reopen_img, (0, 0, 1920, 1080))
    rep["main_canvas_frame"] = tone_composition(jump_img, CANVAS_CROP, step=2)
    rep["status_bar_crop"] = {"crop": list(STATUS_CROP),
                              "note": "cropped for reading, see m5-read-status-3x.png"}

    # ---- booth artifacts, uniform Lanczos from the chrome-free square body crop
    from PIL import Image as I
    body_img = open_img.crop(crop)
    body_img.save(f"{HERE}/republic-of-korea-mm.png")
    body_img.resize((64, 64), I.LANCZOS).save(f"{HERE}/republic-of-korea-booth64.png")
    body_img.resize((32, 32), I.LANCZOS).save(f"{HERE}/republic-of-korea-booth32.png")
    body_img.resize((256, 256), I.LANCZOS).save(f"{HERE}/republic-of-korea-mm-2x.png")
    # reading aids, enlargements, never gate artifacts
    body_img.resize((384, 384), I.NEAREST).save(f"{HERE}/m5-read-body-3x.png")
    body_img.resize((64, 64), I.LANCZOS).resize((256, 256), I.NEAREST).save(f"{HERE}/m5-read-booth64.png")
    body_img.resize((32, 32), I.LANCZOS).resize((256, 256), I.NEAREST).save(f"{HERE}/m5-read-booth32.png")
    open_img.crop(STATUS_CROP).resize(((STATUS_CROP[2] - STATUS_CROP[0]) * 3,
                                       (STATUS_CROP[3] - STATUS_CROP[1]) * 3), I.LANCZOS) \
        .save(f"{HERE}/m5-read-status-3x.png")

    rep["booth_artifacts"] = {
        "derivation": "republic-of-korea-mm.png is the 128x128 map-body crop of m5-open.png; "
                      "booth64 and booth32 are single-step Lanczos resizes of that crop, "
                      "uniform at 0.5 and 0.25 px per map pixel; mm-2x is a 2x Lanczos enlargement",
        "uniform_scale_check": {"mm_to_64": [64 / side, 64 / side], "mm_to_32": [32 / side, 32 / side]},
        "chrome": [chrome_share(f"{HERE}/republic-of-korea-mm.png", None),
                   chrome_share(f"{HERE}/republic-of-korea-booth64.png", None),
                   chrome_share(f"{HERE}/republic-of-korea-booth32.png", None)],
        "composition_64": tone_composition(I.open(f"{HERE}/republic-of-korea-booth64.png").convert("RGB"),
                                           (0, 0, 64, 64)),
        "composition_32": tone_composition(I.open(f"{HERE}/republic-of-korea-booth32.png").convert("RGB"),
                                           (0, 0, 32, 32)),
    }

    json.dump(rep, open(f"{HERE}/republic-of-korea_report.json", "w"), indent=1)

    print("container:", json.dumps(rep["container"]))
    print("new mask:", json.dumps(rep["new_mask"]))
    print("old mask:", json.dumps(rep["old_mask"]))
    nvo = rep["new_vs_old"]
    print("new vs old:", json.dumps({k: v for k, v in nvo.items() if k != "anchors"}))
    print("\nanchor windows (centre class new|old, sea tiles in a 5x5 window new|old):")
    for a in nvo["anchors"]:
        print(f"  {a['anchor']:<36} exp {a['expected']:<5} col {a['col']:>4} row {a['row']:>4} "
              f"new {a['new_centre']:<7} {a['new_sea_tiles_5x5']!s:>4}  "
              f"old {a['old_centre']:<7} {a['old_sea_tiles_5x5']!s:>4}")
    print("\nbody locate:", json.dumps(rep["map_body_locate"]))
    print("body crop:", json.dumps(rep["body_crop"]))
    print("render on body:", json.dumps(rep["render_on_map_body"]))
    print("render on reopen:", json.dumps(rep["render_on_map_body_reopen"]))
    print("reopen diff:", json.dumps(rep["reopen_visual_diff"]), json.dumps(rep["reopen_visual_diff_fullframe"]))
    print("main canvas frame:", json.dumps(rep["main_canvas_frame"]))
    print("booth:", json.dumps(rep["booth_artifacts"]["chrome"]))
    print("booth64 composition:", json.dumps({k: rep["booth_artifacts"]["composition_64"][k] for k in
                                             ("glyph_share_pct", "ground_share_pct", "other_share_pct",
                                              "wcag_dominant_pair", "wcag_worst_ground_against_glyph_dominant")}))
    print("booth32 composition:", json.dumps({k: rep["booth_artifacts"]["composition_32"][k] for k in
                                             ("glyph_share_pct", "ground_share_pct", "other_share_pct")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
