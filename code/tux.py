#!/usr/bin/env python3
"""TASK-0042 map 4 `tux` silhouette mask, one tile per pixel into a 256x256 boolean mask,
the same contract glyph.py and rocky.py use.

Design limits from `## Status` (Robotnik decision, maps 4 and 5 design constraints) and
`## Review` doc:2021 (Shadow's L2 read certifies silhouette-class shapes only):
  - ONE filled body silhouette, gated as a silhouette.
  - NO belly patch. The white belly of Tux is an internal feature inside the body, the exact
    class the silhouette read does not certify, so it is excluded until a second-tone gate.
  - NO internal counter of any kind (no eyes, no beak, no holes). The silhouette must carry
    the identity through its outline alone: rounded head bump on a wider egg body, two
    side flippers, two forward feet at the bottom.
  - Every feature above 56 tiles (Shadow's coarse-feature floor, extrapolated, named as such).
  - Fills the 256x256 extent: head top row 0, feet bottom row 255, flipper tips columns
    0 and 255.

Construction: the union of five implicit ellipses (quadratic inequalities), all filled,
chosen so every neighbour group is connected: head circle, body ellipse, two side flipper
ellipses, two foot ellipses. No rotation math is needed because the outline identity of
Tux survives axis-aligned flippers; the read of whether it does is the independent reader's.

The builder does not declare this silhouette legible; an independent reader does.
"""

W = H = 256

# Ellipse parameters in tile units, x from the left, y from the top. Chosen so the union
# fills the extent (head top row 0, feet bottom row 255, flipper tips columns 0 and 255),
# every feature clears the 56-tile coarse-feature floor in both dimensions, and the outline
# carries the identity: a narrower round head over a wider body, flippers protruding at the
# sides with a visible armpit notch, feet protruding at the lower corners.
#   feature          centre          semi-axes      extent
#   head             (128, 50)       50 x 50        y 0..100, 101 wide
#   body             (128, 155)      78 x 100       y 55..255, 157 wide
#   left flipper     (28, 150)       30 x 68        x 0..58, 137 tall
#   right flipper    (228, 150)      30 x 68        x 198..255
#   left foot        (93, 228)       42 x 30        y 198..255 clipped, 58 tall, 85 wide
#   right foot       (163, 228)      42 x 30
_ELLIPSES = (
    (128.0, 50.0, 50.0, 50.0),    # head
    (128.0, 155.0, 78.0, 100.0),  # body
    (28.0, 150.0, 30.0, 68.0),    # left flipper
    (228.0, 150.0, 30.0, 68.0),   # right flipper
    (93.0, 228.0, 42.0, 30.0),    # left foot
    (163.0, 228.0, 42.0, 30.0),   # right foot
)


def tux():
    """Filled Tux body silhouette: union of the five ellipses above."""
    m = [[0] * W for _ in range(H)]
    for y in range(H):
        yy = y + 0.5
        for x in range(W):
            xx = x + 0.5
            for cx, cy, a, b in _ELLIPSES:
                dx = (xx - cx) / a
                dy = (yy - cy) / b
                if dx * dx + dy * dy <= 1.0:
                    m[y][x] = 1
                    break
    return m


def _components(m):
    """4-connected component count, used as a connectedness gate before the build."""
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
    m = tux()
    filled, x0, x1, y0, y1 = _stats(m)
    print(f"tux: {filled}/{65536} = {100*filled/65536:.2f}%  "
          f"bbox x{x0}-{x1} ({x1-x0+1}w) y{y0}-{y1} ({y1-y0+1}h)  "
          f"components {_components(m)}")
    # internal-counter check: a filled silhouette has no ground pixel enclosed by the mask.
    # flood fill the ground from the border; any ground pixel not reached is a hole.
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
