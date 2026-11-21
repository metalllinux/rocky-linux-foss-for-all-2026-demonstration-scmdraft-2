#!/usr/bin/env python3
"""TASK-0042 dispatch F2 step 1 and 3 verification, controller-side only.

Step 1: does `i-love-korea-2line.scm` hold a different map from the accepted
`i-love-korea.scm` at 16fe455d46fd..., or the same tiles under a different
internal STR name? Decided by MTXM comparison, not by size.

Step 3: re-cut the booth artifacts from the 100 percent capture only, verify
they are exact single-step Lanczos downscales, and census the viewport-indicator
(white overlay) pixels inside each capture's overview-thumbnail body, classified
against my own mask decode as on-glyph or on-ground. The counts for the 25
percent and overview-jump captures are the reason those captures are not
artifact sources.

No builder module is imported. Mask comes from MTXM, tones from the captures.
"""
import hashlib
import json
import struct
import subprocess
from collections import Counter

from PIL import Image, ImageChops

HERE = "/tmp/opencode/t0042"
W = H = 256
GLYPH = 192
GROUND = 64

CHKS = {
    "accepted": f"{HERE}/i-love-korea.chk",
    "2line": f"{HERE}/i-love-korea-2line.chk",
    "superseded_m7": f"{HERE}/superseded-i-love-korea.chk",
    "m9_extracted": f"{HERE}/m9-extracted.chk",
}
SCMS = {
    "accepted": f"{HERE}/i-love-korea.scm",
    "2line": f"{HERE}/i-love-korea-2line.scm",
    "superseded_m7": f"{HERE}/superseded-i-love-korea.scm",
}
CAPTURES = {
    "100pct_open": f"{HERE}/m9-open.png",
    "100pct_reopen": f"{HERE}/m9-reopen.png",
    "zoom25": f"{HERE}/m9-zoom25.png",
    "overview_jump": f"{HERE}/m9-jump.png",
}
BODY = (18, 112, 146, 240)   # (x0, y0, x1, y1) exclusive-end, 128x128 body
REC_CUT = f"{HERE}/f2-recut"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_sections(path):
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


def str_name(sections):
    raw = sections.get("STR ", b"")
    if not raw:
        return None
    n = struct.unpack("<H", raw[:2])[0]
    return raw[2:2 + n].decode("latin-1")


def mtxm(sections):
    """Return 256x256 low-byte terrain values plus distinct values."""
    m = sections["MTXM"]
    vals = [m[2 * (y * W + x)] for y in range(H) for x in range(W)]
    return vals


def decimate(vals):
    """Editor thumbnail rule proven by M8/M10: top-left sample of each 2x2 block."""
    return {(x, y): vals[2 * y * W + 2 * x] for y in range(64) for x in range(64)}


def decimate128(vals):
    """128 px body: each screen px covers a 2x2 tile block; glyph if the sampled tile is glyph."""
    return {(x, y): vals[2 * y * W + 2 * x] for y in range(128) for x in range(128)}


def main():
    rep = {}

    # ---------- step 1: containers, internal names, tile identity ----------
    cont = {}
    masks = {}
    for key, path in SCMS.items():
        extracted = subprocess.run(
            [f"{HERE}/chkdump", path, "staredit\\scenario.chk", f"{REC_CUT}/x-{key}.chk"],
            capture_output=True, text=True)
        secs = read_sections(f"{REC_CUT}/x-{key}.chk")
        masks[key] = mtxm(secs)
        cont[key] = {
            "file": path,
            "bytes": len(open(path, "rb").read()),
            "sha256": sha256(path),
            "chk_extract_sha256": sha256(f"{REC_CUT}/x-{key}.chk"),
            "str_name": str_name(secs),
            "mtxm_bytes": len(secs.get("MTXM", b"")),
            "distinct_low": sorted({v for v in masks[key]}),
            "glyph_tiles": sum(1 for v in masks[key] if v == GLYPH),
        }
    rep["containers"] = cont
    rep["tile_identity"] = {
        "accepted_vs_2line_identical": masks["accepted"] == masks["2line"],
        "accepted_vs_superseded_m7_identical": masks["accepted"] == masks["superseded_m7"],
        "first_differing_tile_accepted_vs_2line": next(
            (i for i, (a, b) in enumerate(zip(masks["accepted"], masks["2line"])) if a != b), None),
    }
    # cross-check against the on-disk written CHKs and the M9 extraction
    rep["chk_identity"] = {
        "extracted_2line_matches_written_chk":
            cont["2line"]["chk_extract_sha256"] == sha256(CHKS["2line"]),
        "extracted_accepted_matches_written_chk":
            cont["accepted"]["chk_extract_sha256"] == sha256(CHKS["accepted"]),
        "extracted_accepted_matches_m9_extracted":
            cont["accepted"]["chk_extract_sha256"] == sha256(CHKS["m9_extracted"]),
        "extracted_superseded_matches_written_chk":
            cont["superseded_m7"]["chk_extract_sha256"] == sha256(CHKS["superseded_m7"]),
    }

    # ---------- step 3: captures, body crop, indicator census ----------
    mask128 = decimate128(masks["accepted"])
    glyph128 = {p for p, v in mask128.items() if v == GLYPH}
    rep["mask128_glyph_px"] = len(glyph128)

    cap = {}
    for key, path in CAPTURES.items():
        im = Image.open(path).convert("RGB")
        crop = im.crop(BODY)
        px = list(crop.getdata())
        tones = Counter(px)
        # viewport indicator: near-white, all channels >= 240 (map tones are 176 ground / 36-56 glyph)
        ind = [i for i, p in enumerate(px) if min(p) >= 240]
        on_glyph = sum(1 for i in ind if (i % 128, i // 128) in glyph128)
        # indicator bounding box, body-local
        xs = [i % 128 for i in ind]
        ys = [i // 128 for i in ind]
        cap[key] = {
            "capture": path,
            "size": list(im.size),
            "body_crop": list(BODY),
            "crop_vs_published_thumbnail128_px_diff":
                ImageChops.difference(crop, Image.open(f"{HERE}/i-love-korea-2line-thumbnail128.png").convert("RGB")).getbbox() is None and 0
                or sum(1 for a, b in zip(crop.getdata(), Image.open(f"{HERE}/i-love-korea-2line-thumbnail128.png").convert("RGB").getdata()) if a != b),
            "mask_match_px_of_16384": sum(
                1 for i, p in enumerate(px)
                if ((p[0] < 100) == ((i % 128, i // 128) in glyph128))),
            "indicator_px": len(ind),
            "indicator_on_glyph_px": on_glyph,
            "indicator_on_ground_px": len(ind) - on_glyph,
            "indicator_bbox_body_local": [min(xs), min(ys), max(xs), max(ys)] if ind else None,
            "top_tones": [{"rgb": list(t), "px": n} for t, n in tones.most_common(5)],
        }
    rep["captures"] = cap

    # ---------- step 3: re-cut artifacts from the 100 percent capture only ----------
    open_im = Image.open(CAPTURES["100pct_open"]).convert("RGB")
    body = open_im.crop(BODY)
    body.save(f"{REC_CUT}/thumbnail128_recut.png")
    artifacts = {}
    for label, scale, out, pub in (
        ("booth64", 0.5, "booth64_recut.png", "i-love-korea-2line-booth64.png"),
        ("booth32", 0.25, "booth32_recut.png", "i-love-korea-2line-booth32.png"),
    ):
        n = int(128 * scale)
        lanc = body.resize((n, n), Image.LANCZOS)
        lanc.save(f"{REC_CUT}/{out}")
        nearest = body.resize((n, n), Image.NEAREST)
        published = Image.open(f"{HERE}/{pub}").convert("RGB")
        recut = list(lanc.getdata())
        pub_px = list(published.getdata())
        near_px = list(nearest.getdata())
        artifacts[label] = {
            "recut_file": f"{REC_CUT}/{out}",
            "size": [n, n],
            "source_capture": CAPTURES["100pct_open"],
            "source_crop": list(BODY),
            "interp": "single-step LANCZOS uniform",
            "published_file": pub,
            "published_sha256": sha256(f"{HERE}/{pub}"),
            "recut_sha256": sha256(f"{REC_CUT}/{out}"),
            "byte_identical_to_published": sha256(f"{REC_CUT}/{out}") == sha256(f"{HERE}/{pub}"),
            "lanczos_vs_published_px_diff": sum(1 for a, b in zip(recut, pub_px) if a != b),
            "lanczos_vs_published_max_channel_delta": max(
                (max(abs(a[i] - b[i]) for i in range(3)) for a, b in zip(recut, pub_px)), default=0),
            "nearest_vs_published_px_diff": sum(1 for a, b in zip(near_px, pub_px) if a != b),
            "nearest_vs_published_max_channel_delta": max(
                (max(abs(a[i] - b[i]) for i in range(3)) for a, b in zip(near_px, pub_px)), default=0),
            "indicator_px_carried_by_recut": sum(
                1 for a in recut if min(a) >= 240),
        }
    rep["artifacts"] = artifacts

    # counter-proof: cutting from the 25 percent and jump captures instead
    alt = {}
    for key in ("zoom25", "overview_jump"):
        im = Image.open(CAPTURES[key]).convert("RGB")
        c = im.crop(BODY)
        b64 = list(c.resize((64, 64), Image.LANCZOS).getdata())
        pub = list(Image.open(f"{HERE}/i-love-korea-2line-booth64.png").convert("RGB").getdata())
        alt[key] = {
            "crop_vs_published_thumbnail128_px_diff": cap[key]["crop_vs_published_thumbnail128_px_diff"],
            "booth64_from_this_crop_vs_published_px_diff": sum(1 for a, b in zip(b64, pub) if a != b),
            "indicator_on_glyph_px": cap[key]["indicator_on_glyph_px"],
        }
    rep["counterproof_not_artifact_sources"] = alt

    print(json.dumps(rep, indent=1))
    with open(f"{HERE}/f2_artifact_check.json", "w") as fh:
        json.dump(rep, fh, indent=1)


if __name__ == "__main__":
    main()
