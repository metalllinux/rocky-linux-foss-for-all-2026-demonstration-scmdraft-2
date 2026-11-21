#!/usr/bin/env python3
"""TASK-0042 contrast dispatch: harvest every .scm on the controller copy of the
target's 1.16.1 maps tree into plaintext CHKs and build a per-tileset inventory of
terrain values actually used by maps that render. Read-only over the maps; outputs
live under /tmp/opencode/t0042/ts-harvest."""
import json
import os
import struct
import subprocess

HERE = "/tmp/opencode/t0042"
OUT = f"{HERE}/ts-harvest"
TILESETS = {0: "Badlands", 1: "Space Platform", 2: "Installation", 3: "Ash World",
            4: "Jungle World", 5: "Desert World", 6: "Ice World", 7: "Twilight World"}


def sections(chk):
    out = {}
    pos = 0
    while pos + 8 <= len(chk):
        name = chk[pos:pos + 4]
        if not all(32 <= b <= 126 for b in name):
            break
        size = struct.unpack("<I", chk[pos + 4:pos + 8])[0]
        out[name.decode("latin1")] = chk[pos + 8:pos + 8 + size]
        pos += 8 + size
    return out


def main():
    rows = []
    fails = []
    for root, _, files in os.walk(f"{HERE}/maps-all"):
        for fn in sorted(files):
            if not fn.endswith(".scm"):
                continue
            src = os.path.join(root, fn)
            chk_name = fn.replace("/", "_")[:-4] + ".chk"
            chk_path = os.path.join(OUT, chk_name)
            r = subprocess.run(
                [f"{HERE}/chkdump", src, "staredit\\scenario.chk", chk_path],
                capture_output=True, text=True)
            if r.returncode != 0 or not os.path.exists(chk_path):
                fails.append((fn, r.stderr.strip()[:80]))
                continue
            data = open(chk_path, "rb").read()
            if data[:4] != b"VER ":
                fails.append((fn, "bad head " + data[:4].hex()))
                os.remove(chk_path)
                continue
            s = sections(data)
            era = struct.unpack("<H", s["ERA "][:2])[0] if len(s.get("ERA ", b"")) >= 2 else -1
            w, h = struct.unpack("<HH", s["DIM "]) if len(s.get("DIM ", b"")) == 4 else (-1, -1)
            mt = s.get("MTXM", b"")
            vals = struct.unpack("<%dH" % (len(mt) // 2), mt)
            freq = {}
            for v in vals:
                freq[v] = freq.get(v, 0) + 1
            top = sorted(freq.items(), key=lambda kv: -kv[1])[:40]
            rows.append({"map": fn, "chk": chk_name, "era": era, "tileset": TILESETS.get(era, f"?{era}"),
                         "w": w, "h": h, "tiles": len(vals), "distinct": len(freq),
                         "top": top})
    json.dump({"rows": rows, "fails": fails}, open(f"{OUT}/inventory.json", "w"))
    print("maps harvested:", len(rows), "fails:", len(fails))
    by_ts = {}
    for r in rows:
        by_ts.setdefault((r["era"], r["tileset"]), []).append(r)
    for (era, ts), rs in sorted(by_ts.items()):
        print(f"ERA {era} {ts}: {len(rs)} maps")
        for r in sorted(rs, key=lambda r: -r["tiles"])[:4]:
            print(f"   {r['map']} {r['w']}x{r['h']} distinct {r['distinct']} top {[v for v,_ in r['top'][:8]]}")
    if fails:
        print("FAILS:")
        for f in fails[:10]:
            print("  ", f)


if __name__ == "__main__":
    main()
