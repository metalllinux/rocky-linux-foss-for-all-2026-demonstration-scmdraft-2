#!/usr/bin/env python3
"""TASK-0042 dispatch F2 step 3 control: quantify what the viewport indicator contributes
to the re-cut booth artifacts, and name the element bounding boxes from my own decode.

Control: replace every indicator pixel in the 100 percent body crop with the dominant
ground tone, re-run the same single-step Lanczos, and count the pixels that move, both
overall and inside each glyph element's bounding box in artifact coordinates. An element
whose glyph cells carry no indicator cannot move.
"""
import json
import struct
from collections import deque

from PIL import Image

HERE = "/tmp/opencode/t0042"
W = H = 256
GLYPH = 192
GROUND_RGB = (176, 176, 176)
BODY = (18, 112, 146, 240)
SRC = f"{HERE}/m9-open.png"
OUT = f"{HERE}/f2-recut"


def sections(path):
    data = open(path, "rb").read()
    pos, out = 0, {}
    while pos + 8 <= len(data):
        name = data[pos:pos + 4]
        if not all(32 <= b <= 126 for b in name):
            break
        size = struct.unpack("<I", data[pos + 4:pos + 8])[0]
        out[name.decode("latin-1")] = data[pos + 8:pos + 8 + size]
        pos += 8 + size
    return out


def str_name(secs):
    raw = secs.get("STR ", b"")
    if not raw:
        return None
    # STR block layout verified on these three files: u16 name length including the
    # terminating NUL at block offset 2, the name string itself at block offset 2048.
    n = struct.unpack("<H", raw[2:4])[0]
    return raw[2048:2048 + n].decode("latin-1").rstrip("\x00")


def mask_from_chk(path):
    m = sections(path)["MTXM"]
    return [[m[2 * (y * W + x)] == GLYPH for x in range(W)] for y in range(H)]


def components(mask):
    seen = [[False] * W for _ in range(H)]
    out = []
    for y in range(H):
        for x in range(W):
            if not mask[y][x] or seen[y][x]:
                continue
            q = deque([(x, y)])
            seen[y][x] = True
            cells = []
            while q:
                cx, cy = q.popleft()
                cells.append((cx, cy))
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < W and 0 <= ny < H and mask[ny][nx] and not seen[ny][nx]:
                            seen[ny][nx] = True
                            q.append((nx, ny))
            xs = [c[0] for c in cells]
            ys = [c[1] for c in cells]
            out.append({
                "tiles": len(cells),
                "cols": [min(xs), max(xs)],
                "rows": [min(ys), max(ys)],
                "w": max(xs) - min(xs) + 1,
                "h": max(ys) - min(ys) + 1,
            })
    return sorted(out, key=lambda c: (c["rows"][0], c["cols"][0]))


def main():
    rep = {}
    for label, chk in (("accepted", f"{HERE}/i-love-korea.chk"),
                       ("2line", f"{HERE}/i-love-korea-2line.chk"),
                       ("superseded_m7", f"{HERE}/superseded-i-love-korea.chk")):
        rep[f"str_name_{label}"] = str_name(sections(chk))

    mask = mask_from_chk(f"{HERE}/i-love-korea.chk")
    comps = components(mask)
    rep["components"] = comps
    rep["glyph_tiles"] = sum(c["tiles"] for c in comps)

    body = Image.open(SRC).convert("RGB").crop(BODY)
    px = list(body.getdata())
    ind_idx = [i for i, p in enumerate(px) if min(p) >= 240]

    # decimated glyph map at 128 px (top-left sample of each 2x2 tile block)
    g128 = set()
    for y in range(128):
        for x in range(128):
            if mask[2 * y][2 * x]:
                g128.add((x, y))
    rep["indicator_in_crop"] = {
        "px": len(ind_idx),
        "on_glyph": sum(1 for i in ind_idx if (i % 128, i // 128) in g128),
        "on_ground": sum(1 for i in ind_idx if (i % 128, i // 128) not in g128),
    }

    inp = list(px)
    for i in ind_idx:
        inp[i] = GROUND_RGB
    body_inp = Image.new("RGB", (128, 128))
    body_inp.putdata(inp)

    controls = {}
    for label, n in (("booth64", 64), ("booth32", 32)):
        a = list(body.resize((n, n), Image.LANCZOS).getdata())
        b = list(body_inp.resize((n, n), Image.LANCZOS).getdata())
        diff = [i for i, (p, q) in enumerate(zip(a, b)) if p != q]
        maxd = max((max(abs(p[k] - q[k]) for k in range(3)) for p, q in zip(a, b)), default=0)
        # per-element: diff pixels inside the element's bounding box in artifact coords
        per = []
        step = 256 // n   # tiles per artifact pixel on each axis

        def block_has_glyph(ax, ay):
            t0 = ax * step
            r0 = ay * step
            return any(mask[r0 + dy][t0 + dx] for dy in range(step) for dx in range(step))

        for c in comps:
            x0, x1 = c["cols"][0] // step, c["cols"][1] // step + 1
            y0, y1 = c["rows"][0] // step, c["rows"][1] // step + 1
            in_box = sum(1 for i in diff if x0 <= i % n < x1 and y0 <= i // n < y1)
            on_glyph = sum(1 for i in diff if x0 <= i % n < x1 and y0 <= i // n < y1
                           and block_has_glyph(i % n, i // n))
            per.append({"cols": c["cols"], "rows": c["rows"], "tiles": c["tiles"],
                        "artifact_box": [x0, y0, x1, y1], "diff_px_in_box": in_box,
                        "diff_px_in_box_on_glyph": on_glyph})
        controls[label] = {"total_diff_px": len(diff), "max_channel_delta": maxd,
                           "n_px": n * n, "per_element": per}
        body_inp.resize((n, n), Image.LANCZOS).save(f"{OUT}/{label}_inpainted.png")

        # glyph-tone census, published artifact against the inpainted control.
        # My criterion, stated so it can be compared with M10's: within 40 of
        # (36,40,56) and closer to glyph than to ground.
        def drgb(p, q):
            return sum((p[k] - q[k]) ** 2 for k in range(3)) ** 0.5

        def is_glyph(p):
            dg = drgb(p, (36, 40, 56))
            return dg <= 40 and dg < drgb(p, GROUND_RGB)

        ga = list(body.resize((n, n), Image.LANCZOS).getdata())
        gb = list(body_inp.resize((n, n), Image.LANCZOS).getdata())

        def glyph_cells(step2):
            out = {}
            for ax in range(n):
                for ay in range(n):
                    t0, r0 = ax * step2, ay * step2
                    hit = [(t0 + dx, r0 + dy) for dy in range(step2) for dx in range(step2)
                           if mask[r0 + dy][t0 + dx]]
                    if hit:
                        out[(ax, ay)] = hit
            return out

        cells_by_block = glyph_cells(256 // n)
        cens = []
        for c in comps:
            cells = {blk for blk, hit in cells_by_block.items()
                     if all(c["cols"][0] <= x <= c["cols"][1] and c["rows"][0] <= y <= c["rows"][1]
                            for x, y in hit)}
            na = sum(1 for i, p in enumerate(ga) if is_glyph(p) and (i % n, i // n) in cells)
            nb = sum(1 for i, p in enumerate(gb) if is_glyph(p) and (i % n, i // n) in cells)
            white = sum(1 for i, p in enumerate(ga) if min(p) >= 240 and (i % n, i // n) in cells)
            cens.append({"cols": c["cols"], "rows": c["rows"], "tiles": c["tiles"],
                         "ideal_px": c["tiles"] * (n / 256) ** 2,
                         "glyph_blocks": len(cells),
                         "glyph_tone_px_as_published": na,
                         "glyph_tone_px_inpainted": nb, "delta_px": na - nb,
                         "near_white_px_in_glyph_blocks": white})
        controls[label]["glyph_tone_census"] = cens
    rep["inpaint_control"] = controls
    print(json.dumps(rep, indent=1))
    with open(f"{HERE}/f2_control.json", "w") as fh:
        json.dump(rep, fh, indent=1)


if __name__ == "__main__":
    main()
