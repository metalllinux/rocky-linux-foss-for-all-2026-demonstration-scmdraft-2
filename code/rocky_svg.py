#!/usr/bin/env python3
"""TASK-0042: rasterize the Rocky Linux mark straight from the distro's shipped SVG.

The mark is not a shield and has no internal R. It is a disc with a 45-degree chevron
notch cut through its lower right. The authoritative geometry is the shipped asset
/usr/share/icons/hicolor/scalable/apps/start-here.svg (rocky-logos-100.5-3.el10), which
this module parses and rasterizes into a 256x256 boolean mask (one tile per pixel).

This replaces the inherited "shield" description that shadowed into rocky.py:10-13 from
## Plan doc:202 and doc:766. Per the Robotnik decision in ## Status and Shadow's blocker
finding, the map 2 mask is built from the shipped SVG paths, not from a hand-written
shield outline.

Method: parse each <path> d-string (M/C/L/Z), flatten cubic Beziers by dense sampling,
scanline-fill each closed subpath at pixel centres (x+0.5, y+0.5), union the two subpaths.
The union is the disc minus the notch band, exactly as the distro draws it.
"""
import re

W = H = 256

# The two shipped paths, verbatim from start-here.svg (viewBox 0 0 256 256).
PATHS = [
    "M248.877 170.21C253.492 156.994 256 142.79 256 128C256 57.3076 198.692 0 128 0"
    "C57.3076 0 0 57.3076 0 128C0 162.979 14.0307 194.681 36.771 217.785"
    "L166.611 87.9445L248.877 170.21Z",
    "M225.496 210.941L166.611 152.056L74.3971 244.27C90.7025 251.799 108.861 256 128 256"
    "C167.051 256 202.018 238.512 225.496 210.941Z",
]

TOKEN = re.compile(r"([MCLZmclz])|(-?\d+(?:\.\d+)?)")


def _tokens(d):
    """Yield command letters and numbers from a path d-string."""
    for m in TOKEN.finditer(d):
        if m.group(1):
            yield m.group(1).upper()
        else:
            yield float(m.group(2))


def _cubic(p0, c1, c2, p3, n=120):
    """Flatten a cubic Bezier to n+1 sampled points."""
    out = []
    for i in range(n + 1):
        t = i / n
        mt = 1 - t
        x = mt**3 * p0[0] + 3 * mt**2 * t * c1[0] + 3 * mt * t**2 * c2[0] + t**3 * p3[0]
        y = mt**3 * p0[1] + 3 * mt**2 * t * c1[1] + 3 * mt * t**2 * c2[1] + t**3 * p3[1]
        out.append((x, y))
    return out


def _subpaths(d):
    """Return a list of flattened closed polylines for one path d-string."""
    toks = list(_tokens(d))
    i = 0
    cmd = None
    start = cur = None
    poly = []
    polys = []

    def close():
        nonlocal poly
        if len(poly) >= 3:
            polys.append(poly)
        poly = []

    while i < len(toks):
        t = toks[i]
        if isinstance(t, str):
            cmd = t
            i += 1
        # implicit repetition uses the previous command for M too, which is invalid; here
        # every command letter is explicit, so cmd only updates on a letter.
        if cmd == "M":
            x, y = toks[i], toks[i + 1]
            i += 2
            close()
            start = cur = (x, y)
            poly = [start]
        elif cmd == "L":
            x, y = toks[i], toks[i + 1]
            i += 2
            cur = (x, y)
            poly.append(cur)
        elif cmd == "C":
            c1 = (toks[i], toks[i + 1])
            c2 = (toks[i + 2], toks[i + 3])
            p3 = (toks[i + 4], toks[i + 5])
            i += 6
            pts = _cubic(cur, c1, c2, p3)
            poly.extend(pts[1:])   # drop duplicate start point
            cur = p3
        elif cmd == "Z":
            i += 1
            if start is not None:
                poly.append(start)
            close()
        else:
            i += 1
    close()
    return polys


def _edges():
    """Collect scanline edges from every subpath of every shipped path."""
    edges = []
    for d in PATHS:
        for poly in _subpaths(d):
            for k in range(len(poly) - 1):
                (x1, y1), (x2, y2) = poly[k], poly[k + 1]
                if y1 == y2:
                    continue
                if y1 < y2:
                    edges.append((y1, y2, x1, x2))
                else:
                    edges.append((y2, y1, x2, x1))
    return edges


EDGES = _edges()


def mark_mask(scale=1.0, offx=0.0, offy=0.0):
    """Rasterize the Rocky mark. scale maps the 256 viewBox onto the map extent; offx/offy
    shift it in map coordinates. A pixel is set when its map centre maps back into the
    union of the shipped paths."""
    m = [[0] * W for _ in range(H)]
    for y in range(H):
        vy = (y + 0.5 - offy) / scale
        xs = []
        for (y1, y2, x1, x2) in EDGES:
            if y1 < vy < y2:
                # x crossing at vy via linear interpolation of the flattened edge
                t = (vy - y1) / (y2 - y1)
                xs.append(x1 + t * (x2 - x1))
        if not xs:
            continue
        xs.sort()
        # even-odd fill of the viewBox cross-section, then map x back to the map grid
        for a, b in zip(xs[0::2], xs[1::2]):
            x_lo = int(a * scale + offx)
            x_hi = int(b * scale + offx)
            for x in range(max(0, x_lo), min(W, x_hi + 1)):
                m[y][x] = 1
    return m


if __name__ == "__main__":
    m = mark_mask()
    filled = sum(sum(r) for r in m)
    xs = [x for row in range(H) for x, v in enumerate(m[row]) if v]
    ys = [y for y in range(H) for x, v in enumerate(m[y]) if v]
    print(f"rocky-mark (SVG raster): {filled}/{65536} = {100*filled/65536:.2f}% "
          f"bbox x{min(xs)}-{max(xs)} y{min(ys)}-{max(ys)}")
    print("\n".join("".join("#" if m[y][x] else "." for x in range(0, W, 6))
                    for y in range(0, H, 10)))
