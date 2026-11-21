#!/usr/bin/env python3
"""Glyph mask for map 1 `foss-for-all`. Block-letter bitmap font, rendered one tile
per pixel into a 256x256 boolean mask: True where the glyph (foreground terrain) goes.

The word is two lines:  line 1 "FOSS",  line 2 "FOR ALL". Each font cell becomes
S_X x S_Y tiles so every stroke is at least S_X tiles thick (one tile per pixel,
no drag brush), which is what fixes the two structural legibility causes recorded by
Shadow (doc:1443, doc:1444): stroke width vs glyph counter, and drag-band overshoot.
"""
import sys

W = H = 256
S_X = 6            # tiles per font cell, horizontally (stroke thickness)
S_Y = 8            # tiles per font cell, vertically (taller glyphs, fills vertical extent)
GAP = 1            # font cells between letters
SPACE = 2          # font cells wide for a space

# 5-wide x 7-tall font, 1 = ink.
# K, E and the 3-cell I-beam I were added by dispatch M7 for `i-love-korea`. The mask()
# entry point and the existing keys are byte-unchanged, so map 1 `foss-for-all` still
# reproduces from this same module (its LINES use only F, O, S, R, A, L and space).
FONT = {
    "F": ["11111", "10000", "11110", "10000", "10000", "10000", "10000"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    # 3-cell I-beam: full-width serif bars top and bottom, 1-cell stem between.
    "I": ["111", "010", "010", "010", "010", "010", "111"],
    " ": ["00", "00", "00", "00", "00", "00", "00"],
}

LINES = ["FOSS", "FOR ALL"]


def line_cells_width(line):
    w = 0
    for ch in line:
        w += len(FONT[ch][0]) if ch != " " else SPACE
        w += GAP
    return w - GAP


def render(text, s_x, s_y, x0, y0):
    """Parameterized form of the mask() blit, added by dispatch M7: one line of FONT text,
    each font cell scaled to s_x by s_y tiles, blitted with its top-left cell at tiles
    (x0, y0). Same cell scaling, same GAP semantics as mask(), so M7 reuses this letterform
    renderer rather than duplicating it. mask() itself is untouched."""
    m = [[0] * W for _ in range(H)]
    cx = 0
    for ch in text:
        if ch == " ":
            cx += SPACE + GAP
            continue
        grid = FONT[ch]
        cw = len(grid[0])
        for r in range(7):
            for c in range(cw):
                if grid[r][c] == "1":
                    for dy in range(s_y):
                        for dx in range(s_x):
                            yy = y0 + r * s_y + dy
                            xx = x0 + cx * s_x + c * s_x + dx
                            if 0 <= yy < H and 0 <= xx < W:
                                m[yy][xx] = 1
        cx += cw + GAP
    return m


def mask():
    m = [[0] * W for _ in range(H)]
    line_h = 7 * S_Y
    total_h = line_h * len(LINES) + (len(LINES) - 1) * 2 * S_Y
    y0 = (H - total_h) // 2
    for li, line in enumerate(LINES):
        lw = line_cells_width(line)
        x0 = (W - lw * S_X) // 2
        y_line = y0 + li * (line_h + 2 * S_Y)
        cx = 0  # cell offset from the line's left edge
        for ch in line:
            grid = FONT[ch]
            cw = SPACE if ch == " " else len(grid[0])
            if ch != " ":
                for r in range(7):
                    for c in range(5):
                        if grid[r][c] == "1":
                            for dy in range(S_Y):
                                for dx in range(S_X):
                                    yy = y_line + r * S_Y + dy
                                    xx = x0 + cx * S_X + c * S_X + dx
                                    if 0 <= yy < H and 0 <= xx < W:
                                        m[yy][xx] = 1
            cx += cw + GAP
    return m


if __name__ == "__main__":
    m = mask()
    filled = sum(sum(row) for row in m)
    xs = [x for r in range(H) for x, v in enumerate(m[r]) if v]
    ys = [y for y in range(H) for x, v in enumerate(m[y]) if v]
    print(f"mask {W}x{H} filled tiles {filled} ({filled/(W*H)*100:.1f}%) "
          f"bbox x{min(xs)}-{max(xs)} y{min(ys)}-{max(ys)}", file=sys.stderr)
    # ASCII preview (downsample 8x)
    for y in range(0, H, 8):
        print("".join("#" if m[y][x] else "." for x in range(0, W, 4)))
