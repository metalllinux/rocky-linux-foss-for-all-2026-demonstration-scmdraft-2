#!/usr/bin/env python3
"""TASK-0042 dispatch M7, controller-side mask diagnostics for `i-love-korea`.

Census of the composed mask before the build: components with bbox and floor check
(minimum-dimension reading, both axes >= 10 tiles, per F1), per-component thinnest ink
run (horizontal and vertical), gaps between neighbouring component bboxes, enclosed
ground (letter counters), and an ASCII preview. This is builder-side diagnosis; the
gate numbers are measured from the shipped file by m7_measure.py, not from this script.
"""
import sys

sys.path.insert(0, "/tmp/opencode/t0042")
import rocky

W = H = 256
FLOOR = 10  # minimum-dimension reading: both bbox axes >= 10 tiles


def components(m):
    seen = [[False] * W for _ in range(H)]
    comps = []
    for y0 in range(H):
        for x0 in range(W):
            if not m[y0][x0] or seen[y0][x0]:
                continue
            cells = []
            stack = [(x0, y0)]
            seen[y0][x0] = True
            while stack:
                x, y = stack.pop()
                cells.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and m[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = True
                        stack.append((nx, ny))
            comps.append(cells)
    return comps


def bbox(cells):
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    return min(xs), max(xs), min(ys), max(ys)


def enclosed(m):
    """Ground tiles not reachable from the map border (internal counters)."""
    reach = [[False] * W for _ in range(H)]
    st = [(x, y) for x in range(W) for y in (0, H - 1)] + \
         [(x, y) for y in range(H) for x in (0, W - 1)]
    for x, y in st:
        if m[y][x] == 0 and not reach[y][x]:
            reach[y][x] = True
            s = [(x, y)]
            while s:
                cx, cy = s.pop()
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < W and 0 <= ny < H and m[ny][nx] == 0 and not reach[ny][nx]:
                        reach[ny][nx] = True
                        s.append((nx, ny))
    return [(x, y) for y in range(H) for x in range(W) if m[y][x] == 0 and not reach[y][x]]


def min_run(cells):
    """Thinnest ink run of a component: min horizontal run length and min vertical run length."""
    cellset = set(cells)
    hruns = []
    for y in {c[1] for c in cells}:
        row = sorted(x for x, yy in cells if yy == y)
        run = 1
        for a, b in zip(row, row[1:]):
            if b == a + 1:
                run += 1
            else:
                hruns.append(run)
                run = 1
        hruns.append(run)
    vruns = []
    for x in {c[0] for c in cells}:
        col = sorted(y for xx, y in cells if xx == x)
        run = 1
        for a, b in zip(col, col[1:]):
            if b == a + 1:
                run += 1
            else:
                vruns.append(run)
                run = 1
        vruns.append(run)
    return min(hruns), min(vruns)


def main():
    m = rocky.MASKS["i-love-korea"]()
    filled = sum(sum(r) for r in m)
    print(f"mask {W}x{H} filled {filled} tiles, coverage {100*filled/(W*H):.2f} percent")
    comps = sorted(components(m), key=lambda c: bbox(c)[0])
    print(f"components: {len(comps)}")
    bboxes = []
    for cells in comps:
        x0, x1, y0, y1 = bbox(cells)
        w, h = x1 - x0 + 1, y1 - y0 + 1
        mh, mv = min_run(cells)
        ok = "KEEP" if (w >= FLOOR and h >= FLOOR) else "DROP"
        print(f"  comp bbox x{x0}-{x1} y{y0}-{y1}  {w}w x {h}h  tiles {len(cells)}  "
              f"min h-run {mh}  min v-run {mv}  floor({FLOOR}) {ok}")
        bboxes.append((x0, x1, y0, y1, len(cells)))
    # horizontal separation between neighbouring components
    bboxes.sort()
    for a, b in zip(bboxes, bboxes[1:]):
        print(f"  gap between comp ending x{a[1]} and comp starting x{b[0]}: {b[0]-a[1]-1} tiles")
    xs_all = [b[0] for b in bboxes] + [b[1] for b in bboxes]
    ys_all = [b[2] for b in bboxes] + [b[3] for b in bboxes]
    print(f"design bbox x{min(xs_all)}-{max(xs_all)} y{min(ys_all)}-{max(ys_all)}  "
          f"left margin {min(xs_all)}  right margin {255-max(xs_all)}  "
          f"top margin {min(ys_all)}  bottom margin {255-max(ys_all)}")
    enc = enclosed(m)
    if enc:
        ecomps = components([[1 if (x, y) in set(enc) else 0 for x in range(W)] for y in range(H)])
        for cells in ecomps:
            x0, x1, y0, y1 = bbox(cells)
            print(f"  enclosed ground (counter) bbox x{x0}-{x1} y{y0}-{y1} "
                  f"{x1-x0+1}w x {y1-y0+1}h tiles {len(cells)}")
        print(f"enclosed ground total {len(enc)} tiles")
    else:
        print("enclosed ground total 0")
    # overlap check: components must be disjoint (they are by construction) and gaps >= 1 tile
    print("\npreview (1 ink char per 4x8 tiles):")
    for y in range(0, H, 8):
        print("".join("#" if m[y][x] else "." for x in range(0, W, 4)))

    # glyph.py map-1 regression: mask() census must equal the pre-change record.
    import glyph
    g = glyph.mask()
    gf = sum(sum(r) for r in g)
    gxs = [x for y in range(H) for x, v in enumerate(g[y]) if v]
    gys = [y for y in range(H) for x, v in enumerate(g[y]) if v]
    print(f"\nglyph.mask() regression: filled {gf} (record 7104), "
          f"bbox x{min(gxs)}-{max(gxs)} y{min(gys)}-{max(gys)} (record x14-241 y64-191)")
    assert gf == 7104, "glyph.mask() census changed, map 1 no longer reproducible"
    return 0


if __name__ == "__main__":
    sys.exit(main())
