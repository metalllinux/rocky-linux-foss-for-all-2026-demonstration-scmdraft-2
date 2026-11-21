#!/usr/bin/env python3
"""TASK-0042 dispatch M5 step 2: rasterize the Natural Earth admin-0 South Korea ring at
110m, 50m and 10m under one projection, and measure whether the higher-resolution ring
restores the coastal bays. No builder code is imported; the shipped mask is read out of
republic-of-korea.chk directly.

Every number this prints is written to m5_raster_report.json for the planning-doc record.
"""
import json
import math
import struct
import sys

sys.path.insert(0, "/tmp/opencode/t0042")
import korea_10m as k

W = k.W
H = k.H
UP = k.UP

# ---------------------------------------------------------------- source geometry
def source_stats(path):
    fc = json.load(open(path))
    f = [x for x in fc["features"] if x["properties"].get("ISO_A2") == "KR"][0]
    p = f["properties"]
    geom = f["geometry"]
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    rings = [r for poly in polys for r in poly]
    pairs = sum(len(r) for r in rings)
    distinct = len({tuple(c) for r in rings for c in r})
    lons = [c[0] for r in rings for c in r]
    lats = [c[1] for r in rings for c in r]
    props = {kk: p.get(kk) for kk in ("name", "name_long", "formal_en", "ISO_A2", "adm0_a3",
                                      "featurecla", "scalerank", "min_zoom", "continent",
                                      "region_un")}
    return {"geometry_type": geom["type"], "polygons": len(polys), "rings": len(rings),
            "coordinate_pairs": pairs, "distinct_vertices": distinct,
            "lon_min": min(lons), "lon_max": max(lons), "lat_min": min(lats), "lat_max": max(lats),
            "props": props}


def jeju_ring(path):
    """The ring in the Jeju latitude band, reported in degrees and in map tiles."""
    out = []
    for name, ring, raw in k.rings_from_geojson(path):
        lats = [c[1] for c in raw]
        if max(lats) < 34.0:
            lons = [c[0] for c in raw]
            out.append({"ring": name, "pairs": len(raw),
                        "lon": [min(lons), max(lons)], "lat": [min(lats), max(lats)],
                        "deg_w": max(lons) - min(lons), "deg_h": max(lats) - min(lats)})
    return out


# ---------------------------------------------------------------- mask measurement
def stats(m):
    filled = sum(sum(r) for r in m)
    xs = [x for y in range(H) for x, v in enumerate(m[y]) if v]
    ys = [y for y in range(H) for x, v in enumerate(m[y]) if v]
    return filled, min(xs), max(xs), min(ys), max(ys)


def row_runs(m):
    """Rows carrying two or more separate glyph runs, and the largest ground gap enclosed
    between two glyph runs in the same row (Shadow's coastal-articulation metrics).
    Dimensions are taken from the mask itself so the same metric runs on the 256-tile masks
    and on the 128 / 64 / 32 decimations (attempt 1 died here on a 128-wide mask)."""
    h = len(m)
    w = len(m[0])
    runs_rows = 0
    total_runs = 0
    max_gap = 0
    min_run = 10 ** 9
    for y in range(h):
        row = m[y]
        runs = []
        x = 0
        while x < w:
            if row[x]:
                x0 = x
                while x < w and row[x]:
                    x += 1
                runs.append((x0, x - 1))
                min_run = min(min_run, x - x0)
            else:
                x += 1
        if len(runs) >= 2:
            runs_rows += 1
            total_runs += len(runs)
            for a, b in zip(runs, runs[1:]):
                max_gap = max(max_gap, b[0] - a[1] - 1)
    return {"rows_with_two_or_more_runs": runs_rows, "total_runs": total_runs,
            "largest_enclosed_ground_gap_tiles": max_gap,
            "narrowest_glyph_run_tiles": min_run}


def perimeter_tiles(m):
    """Count of glyph-to-ground or glyph-to-outside boundary edges of the filled shape."""
    p = 0
    for y in range(H):
        for x in range(W):
            if not m[y][x]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < W and 0 <= ny < H and m[ny][nx]):
                    p += 1
    return p


def decimate(m, factor):
    """Area-average decimation then 50 percent threshold, the same rule Shadow used."""
    f = factor
    out = [[0] * (W // f) for _ in range(H // f)]
    for y in range(H // f):
        for x in range(W // f):
            s = sum(m[y * f + dy][x * f + dx] for dy in range(f) for dx in range(f))
            if s * 2 >= f * f:
                out[y][x] = 1
    return out


def iou(a, b):
    inter = sum(1 for y in range(H) for x in range(W) if a[y][x] and b[y][x])
    uni = sum(1 for y in range(H) for x in range(W) if a[y][x] or b[y][x])
    return inter, uni, (inter / uni if uni else 0.0)


def edge_deviation(a, b):
    """Per-row left and right glyph edge position, tiles, for rows present in either mask."""
    devs = []
    for y in range(H):
        ea = [x for x in range(W) if a[y][x]]
        eb = [x for x in range(W) if b[y][x]]
        if not ea and not eb:
            continue
        da = abs((min(ea) if ea else -1) - (min(eb) if eb else -1))
        db = abs((max(ea) if ea else -1) - (max(eb) if eb else -1))
        devs.append(da)
        devs.append(db)
    devs.sort()
    return {"rows_compared": len(devs) // 2, "mean_tiles": round(sum(devs) / len(devs), 3),
            "worst_tiles": devs[-1], "deviations_over_10_tiles": sum(1 for d in devs if d > 10)}


def shipped_mask():
    """The accepted 25.01 percent mask, read from MTXM in republic-of-korea.chk."""
    chk = open("/tmp/opencode/t0042/republic-of-korea.chk", "rb").read()
    pos = 0
    mt = None
    while pos + 8 <= len(chk):
        name = chk[pos:pos + 4]
        size = struct.unpack("<I", chk[pos + 4:pos + 8])[0]
        if name == b"MTXM":
            mt = struct.unpack("<%dH" % (size // 2), chk[pos + 8:pos + 8 + size])
            break
        pos += 8 + size
    vals = sorted(set(mt))
    return [[1 if mt[y * W + x] == 192 else 0 for x in range(W)] for y in range(H)], vals


# ---------------------------------------------------------------- named coastal probes
# Approximate anchor coordinates. The expected class is my geographic reading, stated as
# such; the claim this script makes is the measured difference between the two masks at the
# same anchor, not the correctness of the anchor.
PROBES = [
    ("Incheon / Han estuary mouth", 126.55, 37.55, "sea"),
    ("Ganghwa Strait west of Ganghwado", 126.42, 37.65, "sea"),
    ("Asan Bay inner", 126.75, 36.78, "sea"),
    ("Seosan / Seosancheon bay head", 126.45, 36.75, "sea"),
    ("Taean peninsula coast", 126.30, 36.75, "land"),
    ("Geum estuary at Gunsan", 126.72, 35.99, "sea"),
    ("Yeongjiang / Hwangnyong bay mouth", 126.40, 35.60, "sea"),
    ("Mokpo / Yeongsan estuary", 126.40, 34.75, "sea"),
    ("Seosanman coast west of Yeonggwang", 126.05, 35.05, "sea"),
    ("Gwangyang Bay inner", 127.62, 34.93, "sea"),
    ("Haenam coast", 126.80, 34.60, "sea"),
    ("Jinhae Bay inner", 128.62, 35.16, "sea"),
    ("Busan coast", 129.06, 35.10, "land"),
    ("Namhae strait coast", 127.90, 34.80, "sea"),
    ("Pohang neck", 129.38, 36.03, "land"),
    ("Ulsan coast", 129.32, 35.55, "land"),
    ("Gangneung east coast", 129.10, 37.75, "land"),
    ("Donghae / Mukho inlet", 129.10, 37.55, "sea"),
    ("Ulleungdo island", 130.90, 37.48, "land"),
    ("NE corner near Seokjin", 128.50, 38.55, "land"),
    ("NE tip at the Tumen mouth", 129.25, 38.40, "land"),
    ("Jeju main body", 126.55, 33.40, "land"),
    ("Jeju strait (mainland side)", 126.55, 33.95, "sea"),
]


def probe_masks(masks):
    out = []
    for name, lon, lat, expected in PROBES:
        col = int(round(k.lon_to_col(lon)))
        row = int(round(k.lat_to_row(lat)))
        row_d = {"probe": name, "lon": lon, "lat": lat, "expected_class": expected,
                 "col": col, "row": row, "in_map": 0 <= col < W and 0 <= row < H}
        for label, m in masks.items():
            if row_d["in_map"]:
                cls = "glyph" if m[row][col] else "ground"
            else:
                cls = "off-map"
            row_d[label] = cls
            row_d.setdefault("class_mismatch", []).append(
                0 if cls in (expected, "off-map") else 1)
        out.append(row_d)
    return out


def main():
    rep = {"upstream": {}, "masks": {}, "probes": [], "comparison": {}}

    shipped, vals = shipped_mask()
    rep["shipped_values"] = vals

    scales = {"110m": f"{UP}/ne_110m_admin_0_countries.geojson",
              "50m": f"{UP}/ne_50m_admin_0_countries.geojson",
              "10m": k.SRC_10M}
    masks = {"shipped-110m-centre": shipped}
    for scale, path in scales.items():
        rep["upstream"][scale] = source_stats(path)
        rings = k.rings_from_geojson(path)
        centre = k.rasterize_centre(rings)
        sub = k.rasterize(rings)
        for label, m in ((f"{scale}-centre", centre), (f"{scale}-subpixel", sub)):
            filled, x0, x1, y0, y1 = stats(m)
            comps = k.components(m)
            masks[label] = m
            rep["masks"][label] = {
                "filled_tiles": filled, "coverage_pct": round(100.0 * filled / 65536, 2),
                "bbox_x": [x0, x1], "bbox_w": x1 - x0 + 1, "bbox_y": [y0, y1],
                "bbox_h": y1 - y0 + 1, "components": len(comps),
                "enclosed_ground_tiles": k.enclosed_ground(m),
                "perimeter_boundary_edges": perimeter_tiles(m),
                **row_runs(m),
                "component_sizes_tiles": sorted((c["area"] for c in comps), reverse=True)[:12],
                "components_below_10_tiles": sum(1 for c in comps if c["area"] < 10),
            }

    rep["jeju_upstream_rings"] = {s: jeju_ring(p) for s, p in scales.items()}

    # Rings of the 10m feature that fall partly or wholly outside the recorded 256-tile
    # extent, and rings that sit off the peninsula. Recorded rather than silently clipped.
    clipped = []
    for name, ring, raw in k.rings_from_geojson(k.SRC_10M):
        cols = [c for c, _ in ring]
        rows = [r for _, r in ring]
        lons = [c[0] for c in raw]
        lats = [c[1] for c in raw]
        outside = any(c < 0 or c > W - 1 or r < 0 or r > H - 1 for c, r in ring)
        off_peninsula = max(lons) < 125.9 or min(lons) > 130.95
        if outside or off_peninsula:
            clipped.append({"ring": name, "pairs": len(raw),
                            "col": [round(min(cols), 1), round(max(cols), 1)],
                            "row": [round(min(rows), 1), round(max(rows), 1)],
                            "lon": [min(lons), max(lons)], "lat": [min(lats), max(lats)],
                            "outside_extent": outside, "off_peninsula": off_peninsula})
    rep["extent_clipped_or_off_peninsula_rings"] = clipped

    # Candidate shipped mask for M5: 10m subpixel, the recorded feature floor, internal
    # ground counters filled to glyph. This is the mask build_ts.py will write.
    kept = k.republic_of_korea_10m()
    rings10 = k.rings_from_geojson(k.SRC_10M)
    raw10 = k.rasterize(rings10)
    _floored, keep, drop = k.apply_feature_floor(raw10)
    filled_before = k.enclosed_ground(_floored)
    filled_from_floor, holes_before, tiles_filled = k.fill_enclosed_ground(_floored)
    # Consistency check: the mask the builder module ships must equal the mask this analysis
    # assembled step by step. A mismatch fails here rather than in the map build.
    assert kept == filled_from_floor, "korea_10m.republic_of_korea_10m() disagrees with m5_raster assembly"
    filled, x0, x1, y0, y1 = stats(kept)
    comps = k.components(kept)
    masks["10m-shipped"] = kept
    rep["build_candidate"] = {
        "rule": "10m admin-0 rings, 4x4 subpixel even-odd fill, tile glyph at >=50 percent "
                "subpixel coverage, 8-connected components dropped when either bbox axis is "
                "below 10 tiles, then every 4-connected internal ground counter filled to glyph",
        "filled_tiles": filled, "coverage_pct": round(100.0 * filled / 65536, 2),
        "bbox_x": [x0, x1], "bbox_w": x1 - x0 + 1, "bbox_y": [y0, y1], "bbox_h": y1 - y0 + 1,
        "components": len(comps),
        "enclosed_ground_tiles": k.enclosed_ground(kept),
        "enclosed_ground_tiles_before_fill": filled_before,
        "enclosed_ground_components_before_fill": len(holes_before),
        "tiles_filled": tiles_filled,
        "perimeter_boundary_edges": perimeter_tiles(kept),
        **row_runs(kept),
        "kept_components": [{kk: vv for kk, vv in c.items() if kk != "cells"} for c in
                            sorted(keep, key=lambda c: -c["area"])],
        "dropped_components": [{kk: vv for kk, vv in c.items() if kk != "cells"} for c in
                               sorted(drop, key=lambda c: -c["area"])],
    }

    for label, m in masks.items():
        rep.setdefault("decimation", {})[label] = {}
        for size, factor in ((128, 2), (64, 4), (32, 8)):
            d = decimate(m, factor)
            rep["decimation"][label][str(size)] = {
                "filled": sum(sum(r) for r in d),
                "coverage_pct": round(100.0 * sum(sum(r) for r in d) / (size * size), 2),
                **row_runs(d)}

    for label, m in masks.items():
        if label == "shipped-110m-centre":
            continue
        inter, uni, v = iou(shipped, m)
        rep["comparison"][label] = {"iou_vs_shipped": round(v, 4), "intersection": inter,
                                   "union": uni, **edge_deviation(shipped, m)}

    rep["probes"] = probe_masks({"110m-centre": masks["110m-centre"],
                                 "10m-subpixel": masks["10m-subpixel"],
                                 "10m-shipped": masks["10m-shipped"]})

    json.dump(rep, open("/tmp/opencode/t0042/m5_raster_report.json", "w"), indent=1)

    print("=== upstream geometry ===")
    for s in ("110m", "50m", "10m"):
        u = rep["upstream"][s]
        print(f"{s}: {u['geometry_type']} polygons {u['polygons']} rings {u['rings']} "
              f"pairs {u['coordinate_pairs']} distinct {u['distinct_vertices']} "
              f"lon {u['lon_min']:.6f}..{u['lon_max']:.6f} lat {u['lat_min']:.6f}..{u['lat_max']:.6f}")
        print("   props:", u["props"])
    print("\n=== masks ===")
    for label, v in rep["masks"].items():
        print(f"{label}: coverage {v['coverage_pct']}% bbox {v['bbox_w']}w x {v['bbox_h']}h "
              f"comps {v['components']} enclosed {v['enclosed_ground_tiles']} "
              f"perimeter {v['perimeter_boundary_edges']} "
              f"rows>=2runs {v['rows_with_two_or_more_runs']} runs {v['total_runs']} "
              f"maxgap {v['largest_enclosed_ground_gap_tiles']} narrowest {v['narrowest_glyph_run_tiles']}")
    bc = rep["build_candidate"]
    print(f"\nbuild candidate: coverage {bc['coverage_pct']}% bbox {bc['bbox_w']}w x {bc['bbox_h']}h "
          f"comps {bc['components']} enclosed {bc['enclosed_ground_tiles']} "
          f"perimeter {bc['perimeter_boundary_edges']} rows>=2runs {bc['rows_with_two_or_more_runs']} "
          f"kept {len(bc['kept_components'])} dropped {len(bc['dropped_components'])}")
    print("\nkept components above the floor:")
    for c in sorted(bc["kept_components"], key=lambda c: -c["area"])[:10]:
        print(f"   area {c['area']:6d} x{c['x0']}-{c['x1']} y{c['y0']}-{c['y1']} {c['w']}w x {c['h']}h")
    print("dropped components (top 10 by area):")
    for c in sorted(bc["dropped_components"], key=lambda c: -c["area"])[:10]:
        print(f"   area {c['area']:5d} x{c['x0']}-{c['x1']} y{c['y0']}-{c['y1']} {c['w']}w x {c['h']}h")
    print("\n=== comparison vs shipped 25.01 percent mask ===")
    for label, v in rep["comparison"].items():
        print(f"{label}: IoU {v['iou_vs_shipped']} edge mean {v['mean_tiles']} worst {v['worst_tiles']}")
    print("\n=== decimation survival ===")
    for label, d in rep["decimation"].items():
        for size in ("128", "64", "32"):
            v = d[size]
            print(f"{label} @{size}: cov {v['coverage_pct']}% rows>=2runs {v['rows_with_two_or_more_runs']} "
                  f"maxgap {v['largest_enclosed_ground_gap_tiles']}")
    print("\n=== probes (110m-centre / 10m-subpixel / 10m-floored) ===")
    for p in rep["probes"]:
        print(f"{p['probe']:<36} exp {p['expected_class']:<5} col {p['col']:>4} row {p['row']:>4}  "
              f"110m {p['110m-centre']:<7} 10m {p['10m-subpixel']:<7} shipped {p['10m-shipped']}")
    print("\n=== Jeju rings in the upstream data ===")
    for s, rs in rep["jeju_upstream_rings"].items():
        for r in rs:
            print(f"{s} {r['ring']}: pairs {r['pairs']} lon {r['lon'][0]:.6f}..{r['lon'][1]:.6f} "
                  f"lat {r['lat'][0]:.6f}..{r['lat'][1]:.6f} ({r['deg_w']:.4f} x {r['deg_h']:.4f} deg)")
    half = (W - 1) / 2.0 * k._KM_PER_TILE / k._KM_PER_DEG_LON
    print(f"\nrecorded map extent: lon {k._LON_CENTRE - half:.4f}..{k._LON_CENTRE + half:.4f} "
          f"lat {k._LAT_BOT:.4f}..{k._LAT_TOP:.4f}")
    print("10m rings outside that extent or off the peninsula:")
    for r in rep["extent_clipped_or_off_peninsula_rings"]:
        print(f"  {r['ring']} pairs {r['pairs']} lon {r['lon'][0]:.4f}..{r['lon'][1]:.4f} "
              f"lat {r['lat'][0]:.4f}..{r['lat'][1]:.4f} col {r['col']} row {r['row']} "
              f"outside_extent {r['outside_extent']} off_peninsula {r['off_peninsula']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
