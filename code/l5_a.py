#!/usr/bin/env python3
"""TASK-0042 L5 phase A: copy the Ice live-demo map into the Wine prefix drive_c, launch it by a
Windows-style DOS path (C:\\Maps\\...), and paint one band. Measures that the paint landed so the
save attempt in phase B operates on a dirty map.

Hypothesis under test (from `## Status`): SCMDraft 2 refuses an era 6 save because its filename
field holds a Unix path with forward slashes. Launching the same map from inside the prefix so the
editor sees a C:\\ path with native separators may let Ctrl+S complete.
"""
import subprocess, time, sys, os, hashlib

HERE = "/tmp/opencode/t0042"
SSH_PASS = os.path.expanduser("~/AI/secrets/scm_draft_pass.md")
RDP_PASS = os.path.expanduser("~/AI/secrets/scm_draft_rdp_pass.md")
HOST = "howard@192.168.1.99"
SSH = ["sshpass", "-f", SSH_PASS, "ssh", "-o", "StrictHostKeyChecking=no", HOST]
SCP = ["sshpass", "-f", SSH_PASS, "scp", "-o", "StrictHostKeyChecking=no"]

# Target paths. The prefix copy is the only file this phase may modify.
SRC = "/home/howard/scmdraft-maps/live-demo/live-demo-ice.scm"          # L4 banded map, must stay stable
PREFIX_COPY = "/home/howard/.wine-scmdraft/drive_c/Maps/live-demo-ice.scm"
DOS_ARGV = "C:\\Maps\\live-demo-ice.scm"   # the Windows-style path handed to wine64 as argv[1]
RUN = "/tmp/t0042-run-dos.sh"
CAP = "l5"

CANVAS_CROP = (160, 120, 1895, 855)
TITLE_CROP = (150, 0, 900, 30)
STROKE_RECT = (320, 640, 1500, 680)


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def tscript(s):
    r = sh(SSH + [s])
    if r.returncode:
        sys.stderr.write(f"[ssh rc={r.returncode}] {r.stderr}\n")
    return r.stdout.strip()


def cap(name):
    tscript(f'XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus '
            f'gnome-screenshot-tool -f /tmp/{CAP}-{name}.png')
    time.sleep(0.6)
    sh(SCP + [f"{HOST}:/tmp/{CAP}-{name}.png", f"{HERE}/{CAP}-{name}.png"])
    print(f"  captured {CAP}-{name}.png")


def rdpev(events):
    r = sh(["./rdp-input", "rdp-args"] + events)
    for line in r.stdout.splitlines():
        if line.startswith("event:") or line.startswith("done"):
            print("   ", line)
    if r.returncode:
        print("   rdp-input rc=", r.returncode, r.stderr.strip()[:200])
    return r.returncode


def canvas_tones(path):
    """Count Ice ground tones vs High Outpost glyph tones in the main-canvas crop."""
    from PIL import Image
    im = Image.open(path).convert("RGB").crop(CANVAS_CROP)
    px = im.load()
    tot = grey = dark = 0
    for y in range(im.height):
        for x in range(im.width):
            r, g, b = px[x, y]
            tot += 1
            if abs(r - g) < 12 and abs(g - b) < 12 and 140 < r < 210:
                grey += 1
            if r < 60 and g < 70 and b < 80:
                dark += 1
    return {"total": tot, "grey_pct": round(100 * grey / tot, 2), "dark_pct": round(100 * dark / tot, 2)}


def diff_pair(a, b):
    """Changed pixels between two captures in the canvas crop, and how many lie in the stroke rect."""
    from PIL import Image
    ia = Image.open(a).convert("RGB").crop(CANVAS_CROP)
    ib = Image.open(b).convert("RGB").crop(CANVAS_CROP)
    pa, pb = ia.load(), ib.load()
    ox, oy = CANVAS_CROP[0], CANVAS_CROP[1]
    x1, y1, x2, y2 = STROKE_RECT
    cx1, cy1, cx2, cy2 = x1 - ox, y1 - oy, x2 - ox, y2 - oy
    changed = inside = 0
    for y in range(ia.height):
        for x in range(ia.width):
            ra, ga, ba = pa[x, y]
            rb, gb, bb = pb[x, y]
            if abs(ra - rb) > 30 or abs(ga - gb) > 30 or abs(ba - bb) > 30:
                changed += 1
                if cx1 <= x <= cx2 and cy1 <= y <= cy2:
                    inside += 1
    return {"changed": changed, "inside_stroke_rect": inside,
            "inside_pct": round(100 * inside / changed, 1) if changed else 0.0}


# ---- 1. regenerate the mode-600 RDP args file from ~/AI/secrets (never on a command line) ----
os.umask(0o077)
with open(f"{HERE}/rdp-args", "w") as f:
    f.write("/v:192.168.1.99\n/u:howard\n/p:")
    with open(RDP_PASS) as s:
        f.write(s.read().strip("\r\n"))
    f.write("\n/cert:ignore\n/w:1920\n/h:1080\n+disp\n")
os.chmod(f"{HERE}/rdp-args", 0o600)
print("rdp-args written, mode", oct(os.stat(f"{HERE}/rdp-args").st_mode & 0o777))

# ---- 2. dispatch-start target state: nothing this dispatch starts is already running ----
print("=== DISPATCH-START STATE ===")
for pat in ["ScmDraft[ ]2", "wineserve[r]", "start[.]exe"]:
    out = tscript(f"pgrep -af '{pat}' || echo none")
    print(f"  pgrep {pat}: {out.splitlines()[0] if out else 'none'}")

# ---- 3. baseline hashes: the source map and the four deliverables must not move ----
print("=== BASELINE ===")
base = {}
for label, path in [("live-demo-ice", SRC),
                    ("foss-for-all", "/home/howard/scmdraft-maps/foss-for-all/foss-for-all.scm"),
                    ("rocky-logo", "/home/howard/scmdraft-maps/rocky-logo/rocky-logo.scm"),
                    ("rocky-with-heart", "/home/howard/scmdraft-maps/rocky-with-heart/rocky-with-heart.scm"),
                    ("tux", "/home/howard/scmdraft-maps/tux/tux.scm")]:
    out = tscript(f"stat -c '%s %Y' '{path}'; sha256sum '{path}'").splitlines()
    base[label] = {"stat": out[0], "sha": out[1].split()[0]}
    print(f"  {label}: {out[0]} sha={base[label]['sha'][:12]}")

pre_dir = tscript(f"ls -la /home/howard/.wine-scmdraft/drive_c/Maps/")
print("=== PREFIX Maps/ BEFORE ===")
print(pre_dir)

# ---- 4. target step: copy the Ice live-demo map into the Wine prefix (inverse rm -f that file) ----
print("=== COPY INTO PREFIX ===")
print(tscript(f"cp '{SRC}' '{PREFIX_COPY}' && stat -c '%s %Y' '{PREFIX_COPY}' && sha256sum '{PREFIX_COPY}'"))

# ---- 5. copy the DOS-path launch helper to the target ----
sh(SCP + [f"{HERE}/t0042-run-dos.sh", f"{HOST}:{RUN}"])
print("helper copied:", tscript(f"ls -la {RUN}"))

# ---- 6. launch by the Windows-style path ----
print("=== LAUNCH ===")
print(tscript(f"bash {RUN} '{DOS_ARGV}'"))
time.sleep(9)
rdpev(["key", "0x1C"])          # dismiss the SCMDraft profile dialog with Enter
time.sleep(3)
cap("open")
print("wine log:", tscript("tail -5 /tmp/t0042-run.log"))

# ---- 7. paint one band on the Terrain layer ----
print("=== PAINT ===")
cap("before")
rdpev(["click", "62", "934"])   # High Outpost, value 192, coordinates from l4-palette.png
time.sleep(1.3)
rdpev(["drag", "320", "640", "1500", "640", "1500", "680", "320", "680"])
time.sleep(1.5)
cap("band1")
rdpev(["click", "1893", "700"])  # page the viewport down so a second band is visible evidence
time.sleep(1.5)
cap("pan1")

# ---- 8. measurements on what was captured ----
print("=== MEASUREMENTS ===")
for name in ["open", "before", "band1", "pan1"]:
    print(f"  {name}: {canvas_tones(f'{HERE}/{CAP}-{name}.png')}")
print("  before->band1:", diff_pair(f"{HERE}/{CAP}-before.png", f"{HERE}/{CAP}-band1.png"))
print("  before->pan1:", diff_pair(f"{HERE}/{CAP}-before.png", f"{HERE}/{CAP}-pan1.png"))

print("=== PREFIX Maps/ AFTER PAINT ===")
print(tscript("ls -la /home/howard/.wine-scmdraft/drive_c/Maps/"))
print("phase A done. SCMDraft left running for phase B.")
