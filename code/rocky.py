#!/usr/bin/env python3
"""TASK-0042 rebuilt silhouette masks for maps 2 and 3, one tile per pixel into a 256x256
boolean mask, the same contract glyph.py uses for map 1.

  rocky_logo()        the Rocky Linux mark, rasterized from the shipped distro SVG
                      (rocky_svg.mark_mask): a disc with a 45-degree chevron notch through
                      its lower right. This replaces the inherited "shield" mask that
                      rocky.py:10-13 built from the wrong description in ## Plan doc:202 /
                      doc:766. No internal R, because the real mark has none.

  rocky_with_heart()  the corrected Rocky mark carrying a heart: two separate filled
                      silhouette-class shapes, the SVG mark on the left and a filled heart
                      at its lower right, sized to fill the 256x256 extent with a ground gap
                      between them and no overlap, so neither is an internal counter. This
                      satisfies the Robotnik decision (## Status) that a map named
                      rocky-with-heart must contain Rocky and a heart.

Design intent for each map is recorded in the planning doc, not asserted here. The builder
does not declare either silhouette legible; an independent reader does.

MASKS also carries map 4 `tux` from tux.py: the registry is the contract build_ts.py's
silhouette mode resolves mask names through, so the proven builder stays byte-identical
across dispatches and new masks land in their own modules.
"""
import rocky_svg as _svg
import tux as _tux
import korea as _korea
import korea_10m as _korea10
import glyph as _glyph

W = H = 256

# Map 2: the mark fills the whole map extent, viewBox 0 0 256 256 maps 1:1 onto the grid.
# Map 3: the mark is scaled down and shifted left to leave room for the heart at its lower
# right. scale 0.76 -> disc diameter about 195 tiles, notch band about 34 tiles; offy centres
# it in the left region. Placement was chosen by a programmatic search (see ## Implementation)
# for zero overlap and a >=5-tile ground gap, so each shape stays silhouette-class with no
# internal counter, while the combined design fills the 256x256 extent.
_MARK3_SCALE = 0.76
_MARK3_OFFX = 0.0
_MARK3_OFFY = 20.0

# Heart placed at the lower right, near the notch opening.
_HEART_CX, _HEART_CY = 223.0, 218.0
_HEART_HALF = 42.0   # half-extent of the heart box in tiles

# Map 6 `i-love-korea` layout constants (dispatch M7), in tiles. See the function docstring
# for how each was chosen. Width budget closes exactly: 8 + 15 + 10 + 60 + 10 + 145 + 8 = 256.
_ILK_S_X = 5           # tiles per font cell horizontally (letter stroke thickness)
_ILK_S_Y = 34          # tiles per font cell vertically (glyph height 7*34 = 238)
_ILK_X_I = 8           # left edge of the I-beam
_ILK_X_KOREA = 103     # left edge of KOREA (last ink column 247, right margin 8)
_ILK_Y_TEXT = 9        # top edge of the letter row, (256 - 238) // 2
_ILK_HEART_CX = 63.0   # heart centre x
_ILK_HEART_CY = 128.0  # heart centre y, mid-row
_ILK_HEART_HALF = 31.0 # heart scale, measured width about 60 tiles


def _heart(cx, cy, half):
    """Filled heart silhouette centred at (cx, cy), spanning about 2*half tiles, from the
    implicit curve (x^2 + y^2 - 1)^3 - x^2 y^3 <= 0. Lobes at the top, point at the bottom."""
    m = [[0] * W for _ in range(H)]
    for y in range(H):
        Y = (cy - (y + 0.5)) / half          # flip so lobes sit up
        if Y < -1.5 or Y > 1.4:
            continue
        for x in range(W):
            X = ((x + 0.5) - cx) / half
            if X < -1.7 or X > 1.7:
                continue
            v = X * X + Y * Y - 1.0
            if v * v * v - X * X * (Y ** 3) <= 0.0:
                m[y][x] = 1
    return m


def rocky_logo():
    return _svg.mark_mask()


def rocky_with_heart():
    mark = _svg.mark_mask(scale=_MARK3_SCALE, offx=_MARK3_OFFX, offy=_MARK3_OFFY)
    heart = _heart(_HEART_CX, _HEART_CY, _HEART_HALF)
    m = [[0] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            m[y][x] = 1 if (mark[y][x] or heart[y][x]) else 0
    return m


def i_love_korea():
    """Dispatch M7, map 6 `i-love-korea`: a single row reading a large capital I, one filled
    heart silhouette for the `<3`, then KOREA in capitals. Design decisions, all recorded
    rather than asserted.

    Glyph height. `## Status` (2026-11-21 09:55) makes "very big" binding on layout: the
    largest glyph height the 256x256 extent permits with a ground margin. With the 7-row font
    that is S_Y = 34, glyph height 238 tiles, ground margins 9 top and bottom; S_Y = 35 would
    give 245 with margins under 6, so 34 is the largest height keeping a margin of at least
    8 tiles on both vertical sides.

    Stroke width. Width, not height, is the binding axis for a single row of seven elements
    (I, heart, five letters). At S_X = 5: KOREA is 29 font cells (5 letters x 5 cells + 4
    in-word gaps) = 145 tiles, the I-beam 3 cells = 15, two separator gaps 20, side margins
    16, leaving 60 tiles for the heart. S_X = 6 would spend 174 on KOREA, 18 on I, 24 on gaps
    and 16 on margins, leaving the heart 24 tiles wide, a speck next to a 238-tall row, so
    S_X = 5 is chosen and its measured minimum letter stroke is 5 tiles. The trade is
    recorded for M8 to judge.

    The `<3` is the filled heart curve from this module (rocky-with-heart's proven heart
    construction), no internal counter, natural aspect kept. Capitals only, per the `## Status`
    decision. No second tone anywhere in the design. The feature floor is the minimum-dimension
    reading F1 settled (`## Status` 2026-11-21 12:15): every kept component at least 10 tiles
    on both axes.

    The builder does not declare this map legible; M8 decides that.
    """
    m = [[0] * W for _ in range(H)]
    parts = [
        _glyph.render("I", _ILK_S_X, _ILK_S_Y, _ILK_X_I, _ILK_Y_TEXT),
        _heart(_ILK_HEART_CX, _ILK_HEART_CY, _ILK_HEART_HALF),
        _glyph.render("KOREA", _ILK_S_X, _ILK_S_Y, _ILK_X_KOREA, _ILK_Y_TEXT),
    ]
    for p in parts:
        for y in range(H):
            for x in range(W):
                if p[y][x]:
                    m[y][x] = 1
    return m


MASKS = {"rocky-logo": rocky_logo, "rocky-with-heart": rocky_with_heart, "tux": _tux.tux,
         "republic-of-korea": _korea.republic_of_korea,
         # M5 rebuild: Natural Earth 10m admin-0 rings, 10-tile component floor, no internal
         # counter. The 110m entry above is left in place so the superseded build still
         # reproduces byte-for-byte from the same registry.
         "republic-of-korea-10m": _korea10.republic_of_korea_10m,
         # M7: map 6, single-row letterform design, see the function docstring.
         "i-love-korea": i_love_korea}


def _stats(m):
    filled = sum(sum(r) for r in m)
    xs = [x for y in range(H) for x, v in enumerate(m[y]) if v]
    ys = [y for y in range(H) for x, v in enumerate(m[y]) if v]
    return filled, min(xs), max(xs), min(ys), max(ys)


def _preview(m, sx=6, sy=10):
    return "\n".join("".join("#" if m[y][x] else "." for x in range(0, W, sx))
                     for y in range(0, H, sy))


if __name__ == "__main__":
    for name in ("rocky-logo", "rocky-with-heart"):
        m = MASKS[name]()
        filled, x0, x1, y0, y1 = _stats(m)
        print(f"{name}: {filled}/{65536} = {100*filled/65536:.2f}%  "
              f"bbox x{x0}-{x1} ({x1-x0+1}w) y{y0}-{y1} ({y1-y0+1}h)")
        print(_preview(m))
        print()
    # overlap check for map 3: mark and heart must not touch, so each stays silhouette-class
    mk = _svg.mark_mask(scale=_MARK3_SCALE, offx=_MARK3_OFFX, offy=_MARK3_OFFY)
    ht = _heart(_HEART_CX, _HEART_CY, _HEART_HALF)
    ov = sum(mk[y][x] and ht[y][x] for y in range(H) for x in range(W))
    print(f"map3 mark/heart overlap tiles: {ov}")
