#!/usr/bin/env python3
"""TASK-0042 dispatch M5, step 1 probe.

Reads the three Natural Earth admin-0 country GeoJSON scales fetched under
/tmp/opencode/t0042/m5-upstream and reports, for the South Korea feature only,
what the source actually contains at each scale: geometry type, number of
rings, coordinate-pair count, distinct vertex count, bounding box, and whether
any ring sits in the Jeju latitude band. No builder code is imported.

Upstream (recorded, see m5-upstream/ and ## Implementation):
  repository  github.com/nvkelso/natural-earth-vector  tag v5.1.2
              commit f1890d9f152c896d250a77557a5751a93d494776
  dataset     Natural Earth 10m / 50m / 110m Admin 0 - Countries
              (geojson/ne_<scale>_admin_0_countries.geojson)
  licence     LICENSE.md at that tag: "Everything here is public domain."
"""
import json
import sys

UP = "/tmp/opencode/t0042/m5-upstream"
SCALES = ["110m", "50m", "10m"]


def kor_feature(fc):
    hits = [f for f in fc["features"]
            if f["properties"].get("ISO_A2") == "KR" or f["properties"].get("adm0_a3") == "KOR"]
    return hits


def rings(geom):
    """Yield (name, ring) pairs for Polygon / MultiPolygon geometries."""
    t = geom["type"]
    if t == "Polygon":
        for i, r in enumerate(geom["coordinates"]):
            yield f"poly{i}", r
    elif t == "MultiPolygon":
        for i, p in enumerate(geom["coordinates"]):
            for j, r in enumerate(p):
                yield f"poly{i}-{j}", r
    else:
        yield "other", []


def describe(scale):
    path = f"{UP}/ne_{scale}_admin_0_countries.geojson"
    fc = json.load(open(path))
    feats = kor_feature(fc)
    print(f"\n=== {scale}: {path} ===")
    print(f"file type {fc.get('type')} features in file {len(fc['features'])}, KOR matches {len(feats)}")
    for f in feats:
        p = f["properties"]
        keys = ["name", "name_long", "formal_en", "ISO_A2", "adm0_a3", "featurecla", "scalerank",
                "min_zoom", "world_region", "subregion", "iso_a2_eh"]
        print("  props:", {k: p.get(k) for k in keys if k in p})
        geom = f["geometry"]
        tot_pairs = 0
        tot_verts = 0
        info = []
        for name, ring in rings(geom):
            if not ring:
                continue
            pairs = len(ring)
            closed = ring[0] == ring[-1]
            distinct = len({tuple(c) for c in ring})
            lons = [c[0] for c in ring]
            lats = [c[1] for c in ring]
            info.append((name, pairs, closed, distinct, min(lons), max(lons), min(lats), max(lats)))
            tot_pairs += pairs
            tot_verts += distinct
        print(f"  geometry {geom['type']} rings {len(info)} coordinate pairs {tot_pairs} distinct vertices {tot_verts}")
        for name, pairs, closed, distinct, lon0, lon1, lat0, lat1 in sorted(info, key=lambda r: -r[1]):
            flag = "  <= JEUJU BAND" if lat1 < 34.0 else ""
            print(f"    {name}: pairs {pairs} closed {closed} distinct {distinct} "
                  f"lon {lon0:.6f}..{lon1:.6f} lat {lat0:.6f}..{lat1:.6f}{flag}")
        allpts = [c for _, r in rings(geom) for c in r]
        if allpts:
            lons = [c[0] for c in allpts]
            lats = [c[1] for c in allpts]
            print(f"  overall bbox lon {min(lons):.6f}..{max(lons):.6f} lat {min(lats):.6f}..{max(lats):.6f}")
    return feats


if __name__ == "__main__":
    for s in SCALES:
        describe(s)
    lic = open(f"{UP}/LICENSE.md").read().splitlines()
    print("\n=== LICENSE.md first lines (as declared upstream) ===")
    for line in lic[:6]:
        print("  ", line)
    print("\nVERSION file:", open(f"{UP}/VERSION").read().strip())
    sys.exit(0)
