#!/usr/bin/env python3
"""TASK-0042 dispatch M5: the `republic-of-korea` silhouette mask rebuilt from the
Natural Earth 10m Admin-0 country polygon, one tile per pixel into a 256x256 boolean mask.

Upstream source (recorded, nothing here is committed):
  repository github.com/nvkelso/natural-earth-vector, tag v5.1.2
             commit f1890d9f152c896d250a77557a5751a93d494776
  dataset    Natural Earth 10m Admin 0 - Countries, geojson/ne_10m_admin_0_countries.geojson
             blob sha 5ebc66e25fc1af01edaebe9375c546655e04cf1e, 13287234 B
             sha256 239eec57ac17f100a11e2536cffc56752c318b50ae765b0918ff7aab4ce8f255
  licence    LICENSE.md at the same tag: "Everything here is public domain."

Scale note stated plainly: Natural Earth "10m" is the 1:10,000,000 nominal-scale series,
not 10-metre resolution. The 110m ring the M3 build used is the 1:110,000,000 series.

Projection is inherited unchanged from korea.py (M3): latitude 38.85N..33.10N over 256 rows,
equirectangular with cosine longitude correction at the midpoint latitude, longitude centred
on 127.5E. The extent is therefore identical to the accepted build; only the input ring and
the tile-fill rule change.

Raster rule (measured alternative, see m5_measure.py):
  A  centre-point even-odd scanline, the rule M3 used (kept for comparison).
  B  4x4 subpixel sampling, a tile is glyph when at least 50 percent of its 16 subpixels are
     inside, chosen for the build because a 1593-vertex ring has sub-tile edges that centre
     sampling turns into single-tile spikes.

Feature floor (Shadow's recorded legibility floor, ## Review doc:2373): a component is kept
only when both axes of its bounding box reach MIN_FEATURE_TILES or more. Rings below the floor
are recorded in m5_measure.py output, not silently dropped.
"""
import json
import math

W = H = 256
UP = "/tmp/opencode/t0042/m5-upstream"
SRC_10M = f"{UP}/ne_10m_admin_0_countries.geojson"
SRC_110M = f"{UP}/ne_110m_admin_0_countries.geojson"
SRC_50M = f"{UP}/ne_50m_admin_0_countries.geojson"

SS = 4                      # subpixels per tile side (SS*SS = 16 samples per tile)
TILE_COVERAGE_MIN = 0.5     # fraction of a tile's subpixels inside before the tile is glyph
MIN_FEATURE_TILES = 10      # Shadow's recorded floor for a feature to survive a 64 px read

# Projection constants, copied from korea.py (M3), unchanged.
_LAT_TOP = 38.85
_LAT_BOT = 33.10
_LAT_SPAN = _LAT_TOP - _LAT_BOT
_KM_PER_DEG_LAT = 111.0
_KM_PER_TILE = _KM_PER_DEG_LAT * _LAT_SPAN / (H - 1)
_MID_LAT = (_LAT_TOP + _LAT_BOT) / 2.0
_KM_PER_DEG_LON = _KM_PER_DEG_LAT * math.cos(math.radians(_MID_LAT))
_LON_CENTRE = 127.5


def lon_to_col(lon):
    km_east = (lon - _LON_CENTRE) * _KM_PER_DEG_LON
    return (W - 1) / 2.0 + km_east / _KM_PER_TILE


def lat_to_row(lat):
    km_south = (_LAT_TOP - lat) * _KM_PER_DEG_LAT
    return km_south / _KM_PER_TILE


def rings_from_geojson(path, iso="KR"):
    """Every exterior ring of the ISO KR feature, as projected (col, row) float pairs."""
    fc = json.load(open(path))
    out = []
    for f in fc["features"]:
        if f["properties"].get("ISO_A2") != iso:
            continue
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for pi, poly in enumerate(polys):
            for ri, ring in enumerate(poly):
                pts = [c for c in ring if c[0] is not None and c[1] is not None]
                if pts[0] == pts[-1]:
                    pts = pts[:-1]
                out.append((f"poly{pi}-{ri}",
                            [(lon_to_col(c[0]), lat_to_row(c[1])) for c in pts],
                            pts))
    return out


def _fill_subgrid(sub, rings):
    """Scanline even-odd fill into an (H*SS) x (W*SS) bytearray at subpixel resolution."""
    n_sub_cols = W * SS
    n_sub_rows = H * SS
    for ring in rings:
        n = len(ring)
        for sy in range(n_sub_rows):
            yc = (sy + 0.5) / SS
            xints = []
            for i in range(n):
                x0, y0 = ring[i]
                x1, y1 = ring[(i + 1) % n]
                if (y0 <= yc < y1) or (y1 <= yc < y0):
                    t = (yc - y0) / (y1 - y0)
                    xints.append(x0 + t * (x1 - x0))
            if not xints:
                continue
            xints.sort()
            base = sy * n_sub_cols
            for j in range(0, len(xints) - 1, 2):
                a = xints[j] * SS
                b = xints[j + 1] * SS
                lo = max(0, int(math.floor(a)))
                hi = min(n_sub_cols - 1, int(math.floor(b)))
                for sx in range(lo, hi + 1):
                    sub[base + sx] = 1
    return sub


def rasterize(rings):
    """Union of the rings into a 256x256 tile mask under the recorded tile rule."""
    sub = bytearray(H * SS * W * SS)
    _fill_subgrid(sub, [r for _, r, _ in rings])
    mask = [[0] * W for _ in range(H)]
    for y in range(H):
        row_out = mask[y]
        for x in range(W):
            hits = 0
            for sy in range(SS):
                base = (y * SS + sy) * W * SS + x * SS
                hits += sum(sub[base:base + SS])
            if hits >= TILE_COVERAGE_MIN * SS * SS:
                row_out[x] = 1
    return mask


def rasterize_centre(rings):
    """Alternative A: centre-point even-odd scanline at tile centres, the M3 rule."""
    mask = [[0] * W for _ in range(H)]
    for y in range(H):
        yc = y + 0.5
        for _, ring, _ in rings:
            n = len(ring)
            xints = []
            for i in range(n):
                x0, y0 = ring[i]
                x1, y1 = ring[(i + 1) % n]
                if (y0 <= yc < y1) or (y1 <= yc < y0):
                    t = (yc - y0) / (y1 - y0)
                    xints.append(x0 + t * (x1 - x0))
            xints.sort()
            row_out = mask[y]
            for j in range(0, len(xints) - 1, 2):
                xa, xb = xints[j], xints[j + 1]
                x_start = max(0, int(math.floor(xa)))
                x_end = min(W - 1, int(math.floor(xb - 1e-9)))
                for x in range(x_start, x_end + 1):
                    row_out[x] = 1
    return mask


def components(mask):
    """8-connected components with their tile bbox, area and cell list.

    The cell list is what apply_feature_floor selects on. Attempt 1's version rebuilt the
    kept mask by flooding inside each kept component's bounding box, which silently pulled
    sub-floor islands that happened to sit inside the mainland's bbox back into the shipped
    mask (19 components reported for 3 kept components). Selection is by cell membership now.
    """
    seen = [[False] * W for _ in range(H)]
    out = []
    for y0 in range(H):
        for x0 in range(W):
            if mask[y0][x0] != 1 or seen[y0][x0]:
                continue
            stack = [(x0, y0)]
            seen[y0][x0] = True
            cells = []
            while stack:
                x, y = stack.pop()
                cells.append((x, y))
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < W and 0 <= ny < H and mask[ny][nx] == 1 and not seen[ny][nx]:
                            seen[ny][nx] = True
                            stack.append((nx, ny))
            xs = [c[0] for c in cells]
            ys = [c[1] for c in cells]
            out.append({"area": len(cells), "x0": min(xs), "x1": max(xs),
                        "y0": min(ys), "y1": max(ys),
                        "w": max(xs) - min(xs) + 1, "h": max(ys) - min(ys) + 1,
                        "cells": cells})
    return out


def apply_feature_floor(mask, floor=MIN_FEATURE_TILES):
    """Drop 8-connected components whose bbox has either axis below the floor.
    Returns (kept_mask, kept_components, dropped_components). Kept cells are copied from the
    component's own cell list, not from its bounding box."""
    comps = components(mask)
    kept = [[0] * W for _ in range(H)]
    keep, drop = [], []
    for c in comps:
        if c["w"] >= floor and c["h"] >= floor:
            keep.append(c)
            for x, y in c["cells"]:
                kept[y][x] = 1
        else:
            drop.append(c)
    return kept, keep, drop


def enclosed_ground_components(mask):
    """4-connected ground components not reachable from the map border (internal counters),
    enumerated rather than only counted."""
    reach = [[False] * W for _ in range(H)]
    seeds = [(x, 0) for x in range(W)] + [(x, H - 1) for x in range(W)]
    seeds += [(0, y) for y in range(H)] + [(W - 1, y) for y in range(H)]
    for x, y in seeds:
        if mask[y][x] == 0 and not reach[y][x]:
            reach[y][x] = True
            st = [(x, y)]
            while st:
                cx, cy = st.pop()
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < W and 0 <= ny < H and mask[ny][nx] == 0 and not reach[ny][nx]:
                        reach[ny][nx] = True
                        st.append((nx, ny))
    out = []
    seen = [[False] * W for _ in range(H)]
    for y0 in range(H):
        for x0 in range(W):
            if mask[y0][x0] != 0 or reach[y0][x0] or seen[y0][x0]:
                continue
            stack = [(x0, y0)]
            seen[y0][x0] = True
            cells = []
            while stack:
                x, y = stack.pop()
                cells.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and mask[ny][nx] == 0 and not reach[ny][nx] \
                            and not seen[ny][nx]:
                        seen[ny][nx] = True
                        stack.append((nx, ny))
            xs = [c[0] for c in cells]
            ys = [c[1] for c in cells]
            out.append({"area": len(cells), "x0": min(xs), "x1": max(xs),
                        "y0": min(ys), "y1": max(ys)})
    return out


def fill_enclosed_ground(mask):
    """Turn every internal ground counter into glyph, so the shipped silhouette carries no
    internal counter. Returns (filled_mask, holes_filled, tiles_filled)."""
    holes = enclosed_ground_components(mask)
    out = [row[:] for row in mask]
    n = 0
    for h in holes:
        for x, y in [(x, y) for y in range(h["y0"], h["y1"] + 1) for x in range(h["x0"], h["x1"] + 1)]:
            if out[y][x] == 0:
                out[y][x] = 1
                n += 1
    return out, holes, n


def enclosed_ground(mask):
    """4-connected ground tiles not reachable from the map border (internal counters)."""
    reach = [[False] * W for _ in range(H)]
    stack = []
    for x in range(W):
        stack += [(x, 0), (x, H - 1)]
    for y in range(H):
        stack += [(0, y), (W - 1, y)]
    for x, y in stack:
        if mask[y][x] == 0 and not reach[y][x]:
            reach[y][x] = True
            st = [(x, y)]
            while st:
                cx, cy = st.pop()
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < W and 0 <= ny < H and mask[ny][nx] == 0 and not reach[ny][nx]:
                        reach[ny][nx] = True
                        st.append((nx, ny))
    return sum(1 for y in range(H) for x in range(W) if mask[y][x] == 0 and not reach[y][x])


def republic_of_korea_10m():
    """The shipped M5 mask: 10m admin-0 rings, 4x4 subpixel raster, the recorded 10-tile
    component floor, then internal ground counters filled to glyph so the silhouette carries
    no internal counter (the class the shadow gate certifies)."""
    rings = rings_from_geojson(SRC_10M)
    raw = rasterize(rings)
    kept, _keep, _drop = apply_feature_floor(raw)
    filled, _holes, _n = fill_enclosed_ground(kept)
    return filled


def mask_lonlat(c):
    """Bounding box of a component converted back to degrees under the recorded projection."""
    return {"lon_w": _LON_CENTRE + (c["x0"] - (W - 1) / 2.0) * _KM_PER_TILE / _KM_PER_DEG_LON,
            "lon_e": _LON_CENTRE + (c["x1"] - (W - 1) / 2.0) * _KM_PER_TILE / _KM_PER_DEG_LON,
            "lat_n": _LAT_TOP - c["y0"] * _KM_PER_TILE / _KM_PER_DEG_LAT,
            "lat_s": _LAT_TOP - c["y1"] * _KM_PER_TILE / _KM_PER_DEG_LAT}


if __name__ == "__main__":
    rings = rings_from_geojson(SRC_10M)
    raw = rasterize(rings)
    kept, keep, drop = apply_feature_floor(raw)
    filled, holes, filled_tiles = fill_enclosed_ground(kept)

    def stats(m):
        filled_tiles_ = sum(sum(r) for r in m)
        xs = [x for y in range(H) for x, v in enumerate(m[y]) if v]
        ys = [y for y in range(H) for x, v in enumerate(m[y]) if v]
        return filled_tiles_, min(xs), max(xs), min(ys), max(ys)

    for label, m in (("10m raw", raw), ("10m floored", kept), ("10m floored+filled", filled)):
        n, x0, x1, y0, y1 = stats(m)
        comps = components(m)
        print(f"{label}: {n}/65536 = {100*n/65536:.2f}%  bbox x{x0}-{x1} "
              f"({x1-x0+1}w) y{y0}-{y1} ({y1-y0+1}h)  components {len(comps)}  "
              f"enclosed ground {enclosed_ground(m)}")

    print(f"\ncomponents above the {MIN_FEATURE_TILES}-tile floor: {len(keep)}")
    for c in sorted(keep, key=lambda c: -c["area"]):
        g = mask_lonlat(c)
        print(f"  keep area {c['area']:6d} bbox x{c['x0']}-{c['x1']} y{c['y0']}-{c['y1']} "
              f"{c['w']}w x {c['h']}h  lon {g['lon_w']:.4f}..{g['lon_e']:.4f} "
              f"lat {g['lat_s']:.4f}..{g['lat_n']:.4f}")
    print(f"components below the floor: {len(drop)}, total tiles {sum(c['area'] for c in drop)}")
    for c in sorted(drop, key=lambda c: -c["area"])[:12]:
        g = mask_lonlat(c)
        print(f"  drop area {c['area']:4d} bbox x{c['x0']}-{c['x1']} y{c['y0']}-{c['y1']} "
              f"{c['w']}w x {c['h']}h  lon {g['lon_w']:.4f}..{g['lon_e']:.4f} "
              f"lat {g['lat_s']:.4f}..{g['lat_n']:.4f}")
    print(f"\ninternal ground counters in the floored mask: {len(holes)} components, "
          f"{filled_tiles} tiles, filled to glyph in the shipped mask")
    for h in sorted(holes, key=lambda h: -h["area"])[:12]:
        print(f"  hole area {h['area']:3d} bbox x{h['x0']}-{h['x1']} y{h['y0']}-{h['y1']}")
    print("\nshipped mask preview (1 tile per 2 characters, 1 tile per row pair):")
    for y in range(0, H, 4):
        print("  " + "".join("#" if filled[y][x] else "." for x in range(0, W, 3)))

