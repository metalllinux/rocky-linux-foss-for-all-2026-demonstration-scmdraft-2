#!/usr/bin/env python3
"""TASK-0042 map 5 `republic-of-korea` silhouette mask, one tile per pixel into a
256x256 boolean mask, the same contract glyph.py, rocky.py, and tux.py use.

Design limits from `## Status` (Robotnik decision, maps 4 and 5 design constraints,
doc:78) and `## Review` doc:2165 (Shadow's silhouette read):
  - Coarse filled peninsula outline, silhouette-class.
  - Coastal features kept at roughly 10 tiles or larger (the feature-size floor named
    as an extrapolation by Shadow at doc:2178).
  - NO Taegeuk (the yin-yang circle is an internal counter).
  - NO trigrams (four small three-line marks inside the shape).
  - The silhouette must carry the identity through its outline alone.

Construction: the coastline polygon is taken from the Natural Earth derived simplified
South Korea GeoJSON outline (github.com/johan/world.geo.json KOR.geo.json, 17 vertices,
the DMZ border in the north, full coastline south, east, and west). Jeju Island is a
separate filled ellipse southwest of the peninsula's southern tip.

The projection maps South Korea's latitude range (34.38N to 38.61N) to the full 256-row
vertical extent, and longitude is scaled at the same km-per-tile as latitude adjusted for
the cosine correction at the midpoint latitude (36.5N), so the shape is proportionally
correct. The design fills the vertical extent from row 4 (DMZ) to row 254 (Jeju south
coast) and spans roughly columns 28 to 210 at the widest point.

The builder does not declare this silhouette legible; an independent reader does.
"""
import json
import math

W = H = 256

# South Korea mainland polygon from the Natural Earth derived simplified GeoJSON
# (github.com/johan/world.geo.json, KOR.geo.json, retrieved 2026-11-20).
# Each pair is (longitude_e, latitude_n). DMZ border at top, coastline clockwise.
_KOR_MAINLAND = json.loads(r"""
[
  [128.349716, 38.612243],
  [129.21292,  37.432392],
  [129.46045,  36.784189],
  [129.468304, 35.632141],
  [129.091377, 35.082484],
  [128.18585,  34.890377],
  [127.386519, 34.475674],
  [126.485748, 34.390046],
  [126.37392,  34.93456],
  [126.559231, 35.684541],
  [126.117398, 36.725485],
  [126.860143, 36.893924],
  [126.174759, 37.749686],
  [126.237339, 37.840378],
  [126.68372,  37.804773],
  [127.073309, 38.256115],
  [127.780035, 38.304536],
  [128.205746, 38.370397]
]
""")

# Jeju Island: a simplified ellipse centred at 126.53E, 33.37N.
# Real Jeju spans roughly 126.13-126.95E (0.82 deg) and 33.20-33.55N (0.35 deg).
# At the map's km-per-tile scale, this gives approximately 22 x 14 tiles, both
# above the 10-tile floor.
_JEJU_LON_C, _JEJU_LAT_C = 126.53, 33.37
_JEJU_LON_HALF, _JEJU_LAT_HALF = 0.41, 0.175

# Latitude range for the projection (mainland south coast to DMZ, plus Jeju margin).
_LAT_TOP = 38.85   # a small margin above the DMZ
_LAT_BOT = 33.10   # a small margin below Jeju
_LAT_SPAN = _LAT_TOP - _LAT_BOT

# Scale: km per tile (vertical), then adjust longitude for the cosine at the midpoint.
_KM_PER_DEG_LAT = 111.0
_KM_PER_TILE = _KM_PER_DEG_LAT * _LAT_SPAN / (H - 1)
_MID_LAT = (_LAT_TOP + _LAT_BOT) / 2.0
_KM_PER_DEG_LON = _KM_PER_DEG_LAT * math.cos(math.radians(_MID_LAT))

# Centre longitude for horizontal centring of the map.
_LON_CENTRE = 127.5


def _lon_to_col(lon):
    km_east = (lon - _LON_CENTRE) * _KM_PER_DEG_LON
    return (W - 1) / 2.0 + km_east / _KM_PER_TILE


def _lat_to_row(lat):
    km_south = (_LAT_TOP - lat) * _KM_PER_DEG_LAT
    return km_south / _KM_PER_TILE


def _polygon_mask(vertices):
    """Scanline fill of a closed polygon given as (col, row) float pairs."""
    m = [[0] * W for _ in range(H)]
    for y in range(H):
        yc = y + 0.5
        xints = []
        n = len(vertices)
        for i in range(n):
            x0, y0 = vertices[i]
            x1, y1 = vertices[(i + 1) % n]
            if (y0 <= yc < y1) or (y1 <= yc < y0):
                t = (yc - y0) / (y1 - y0)
                xints.append(x0 + t * (x1 - x0))
        xints.sort()
        for j in range(0, len(xints) - 1, 2):
            xa, xb = xints[j], xints[j + 1]
            x_start = max(0, int(xa + 0.5))
            x_end = min(W - 1, int(xb + 0.5))
            for x in range(x_start, x_end + 1):
                m[y][x] = 1
    return m


def _ellipse_mask(cx, cy, a, b):
    """Filled axis-aligned ellipse mask."""
    m = [[0] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            dx = (x + 0.5 - cx) / a
            dy = (y + 0.5 - cy) / b
            if dx * dx + dy * dy <= 1.0:
                m[y][x] = 1
    return m


def republic_of_korea():
    """Filled South Korea silhouette plus Jeju Island."""
    poly = [(_lon_to_col(lon), _lat_to_row(lat)) for lon, lat in _KOR_MAINLAND]
    m = _polygon_mask(poly)

    jeju_cx = _lon_to_col(_JEJU_LON_C)
    jeju_cy = _lat_to_row(_JEJU_LAT_C)
    jeju_a = _JEJU_LON_HALF * _KM_PER_DEG_LON / _KM_PER_TILE
    jeju_b = _JEJU_LAT_HALF * _KM_PER_DEG_LAT / _KM_PER_TILE

    jeju = _ellipse_mask(jeju_cx, jeju_cy, jeju_a, jeju_b)
    for y in range(H):
        for x in range(W):
            if jeju[y][x]:
                m[y][x] = 1

    return m


def _components(m):
    """4-connected component count (mainland + Jeju = 2 expected)."""
    seen = [[False] * W for _ in range(H)]
    n = 0
    for y0 in range(H):
        for x0 in range(W):
            if not m[y0][x0] or seen[y0][x0]:
                continue
            n += 1
            stack = [(x0, y0)]
            seen[y0][x0] = True
            while stack:
                x, y = stack.pop()
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and m[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = True
                        stack.append((nx, ny))
    return n


def _stats(m):
    filled = sum(sum(r) for r in m)
    xs = [x for y in range(H) for x, v in enumerate(m[y]) if v]
    ys = [y for y in range(H) for x, v in enumerate(m[y]) if v]
    return filled, min(xs), max(xs), min(ys), max(ys)


def _preview(m, sx=6, sy=10):
    return "\n".join("".join("#" if m[y][x] else "." for x in range(0, W, sx))
                     for y in range(0, H, sy))


if __name__ == "__main__":
    m = republic_of_korea()
    filled, x0, x1, y0, y1 = _stats(m)
    print(f"republic-of-korea: {filled}/{65536} = {100*filled/65536:.2f}%  "
          f"bbox x{x0}-{x1} ({x1-x0+1}w) y{y0}-{y1} ({y1-y0+1}h)  "
          f"components {_components(m)}")
    # Internal-counter check.
    reach = [[False] * W for _ in range(H)]
    stack = [(x, y) for x in range(W) for y in (0, H - 1)] + \
            [(x, y) for y in range(H) for x in (0, W - 1)]
    for x, y in stack:
        if m[y][x] == 0 and not reach[y][x]:
            reach[y][x] = True
            st = [(x, y)]
            while st:
                cx, cy = st.pop()
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < W and 0 <= ny < H and m[ny][nx] == 0 and not reach[ny][nx]:
                        reach[ny][nx] = True
                        st.append((nx, ny))
    holes = sum(1 for y in range(H) for x in range(W) if m[y][x] == 0 and not reach[y][x])
    print(f"enclosed ground (internal counter) tiles: {holes}")
    print(_preview(m))
