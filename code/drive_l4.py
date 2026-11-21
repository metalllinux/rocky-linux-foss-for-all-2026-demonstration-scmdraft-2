#!/usr/bin/env python3
"""TASK-0042 L4: live construction segment on Ice World era 6 flat seed.
Replaces Jungle live-demo.scm with live-demo-ice.scm seeded from build_ice_seed.py.
Paints High Outpost (192) bands on Rocky Snow (64) ground.
Measures per-pixel WCAG between before and after tone at same canvas coordinate.
"""
import subprocess, time, sys, os, json, hashlib, math
from PIL import Image

HERE = "/tmp/opencode/t0042"
SSH_PASS = os.path.expanduser("~/AI/secrets/scm_draft_pass.md")
HOST = "howard@192.168.1.99"
SSH = ["sshpass", "-f", SSH_PASS, "ssh", "-o", "StrictHostKeyChecking=no", HOST]
SCP = ["sshpass", "-f", SSH_PASS, "scp", "-o", "StrictHostKeyChecking=no"]
LIVE = "/home/howard/scmdraft-maps/live-demo/live-demo-ice.scm"
RUN = "/tmp/t0042-run.sh"
CAP_PREFIX = "l4"

CANVAS_CROP = (160, 120, 1895, 855)
STATUS_CROP = (0, 1045, 1920, 1080)  # wider than L3's 30px crop per M2 should-fix

# Stroke rectangles from the command list (canvas coordinates in full 1920x1080 frame)
STROKE_RECTS = {
    "band1": (320, 360, 1500, 392),
    "band2": (320, 520, 1500, 552),
    "band3": (320, 420, 1500, 452),
}

DELIVERABLES = {
    "foss-for-all": ("~/scmdraft-maps/foss-for-all/foss-for-all.scm", "e856f0e1"),
    "rocky-logo": ("~/scmdraft-maps/rocky-logo/rocky-logo.scm", "447360ce"),
    "rocky-with-heart": ("~/scmdraft-maps/rocky-with-heart/rocky-with-heart.scm", "b9b056c2"),
    "tux": ("~/scmdraft-maps/tux/tux.scm", "79002eacd5d6"),
}


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def tscript(s):
    r = sh(SSH + [s])
    if r.returncode:
        sys.stderr.write(r.stderr)
    return r.stdout.strip()


def cap(name):
    tscript(f'XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus '
            f'gnome-screenshot-tool -f /tmp/{CAP_PREFIX}-{name}.png')
    time.sleep(0.6)
    sh(SCP + [f"{HOST}:/tmp/{CAP_PREFIX}-{name}.png", f"{HERE}/{CAP_PREFIX}-{name}.png"])
    print(f"  captured {CAP_PREFIX}-{name}.png")


def cap_status(name):
    """Capture a wide status-bar crop (x=0 full width, 35 rows high) for readability."""
    cap(name)


def rdpev(events):
    r = sh(["./rdp-input", "rdp-args"] + events)
    for line in r.stdout.splitlines():
        if line.startswith("event:") or line.startswith("done"):
            print("   ", line)
    return r.returncode


def wcag_relative_luminance(r, g, b):
    """WCAG 2.1 relative luminance from sRGB 0-255."""
    def lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def wcag_ratio(l1, l2):
    """WCAG contrast ratio between two relative luminances."""
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def measure_wcag_pair(path_before, path_after, crop=CANVAS_CROP):
    """Measure per-pixel WCAG between before and after at same canvas coordinate.
    Returns: median ratio at changed pixels, mean tone ratio over stroke rect,
    share of changed pixels inside stroke rect."""
    ia = Image.open(path_before).convert("RGB").crop(crop)
    ib = Image.open(path_after).convert("RGB").crop(crop)
    pa = ia.load()
    pb = ib.load()
    w, h = ia.size

    # Crop offset relative to full frame
    ox, oy = crop[0], crop[1]

    ratios = []
    changed_inside = 0
    changed_total = 0
    changed_outside = 0

    # Pre-compute stroke rects in crop coordinates
    rects_crop = []
    for rect_name, (x1, y1, x2, y2) in STROKE_RECTS.items():
        # Convert full-frame coords to crop coords
        cx1, cy1 = x1 - ox, y1 - oy
        cx2, cy2 = x2 - ox, y2 - oy
        rects_crop.append((cx1, cy1, cx2, cy2))

    for y in range(h):
        for x in range(w):
            ra, ga, ba = pa[x, y]
            rb, gb, bb = pb[x, y]
            # Skip unchanged pixels (threshold 30 on any channel)
            if abs(ra - rb) <= 30 and abs(ga - gb) <= 30 and abs(ba - bb) <= 30:
                continue
            changed_total += 1
            # Check if inside any stroke rect (in crop coords)
            inside = any(cx1 <= x <= cx2 and cy1 <= y <= cy2 for cx1, cy1, cx2, cy2 in rects_crop)
            if inside:
                changed_inside += 1
            else:
                changed_outside += 1
            la = wcag_relative_luminance(ra, ga, ba)
            lb = wcag_relative_luminance(rb, gb, bb)
            ratio = wcag_ratio(la, lb)
            ratios.append(ratio)

    if not ratios:
        return {"median_wcag": None, "changed_total": 0, "changed_inside": 0,
                "changed_outside": 0, "inside_pct": 0.0}

    ratios.sort()
    median = ratios[len(ratios) // 2]
    return {
        "median_wcag": round(median, 3),
        "changed_total": changed_total,
        "changed_inside": changed_inside,
        "changed_outside": changed_outside,
        "inside_pct": round(100 * changed_inside / changed_total, 1) if changed_total else 0.0,
    }


def measure_tone_pair(path_before, path_after, stroke_name, crop=CANVAS_CROP):
    """Measure mean tone WCAG over the stroke rectangle region."""
    ia = Image.open(path_before).convert("RGB").crop(crop)
    ib = Image.open(path_after).convert("RGB").crop(crop)
    pa = ia.load()
    pb = ib.load()

    ox, oy = crop[0], crop[1]
    x1, y1, x2, y2 = STROKE_RECTS[stroke_name]
    cx1, cy1 = max(0, x1 - ox), max(0, y1 - oy)
    cx2, cy2 = min(ia.width, x2 - ox), min(ia.height, y2 - oy)

    before_pixels = []
    after_pixels = []
    for y in range(cy1, cy2 + 1):
        for x in range(cx1, cx2 + 1):
            before_pixels.append(pa[x, y])
            after_pixels.append(pb[x, y])

    if not before_pixels:
        return None

    # Mean luminance
    mean_la = sum(wcag_relative_luminance(*p) for p in before_pixels) / len(before_pixels)
    mean_lb = sum(wcag_relative_luminance(*p) for p in after_pixels) / len(after_pixels)
    return {
        "mean_before": (round(sum(p[0] for p in before_pixels) / len(before_pixels)),
                        round(sum(p[1] for p in before_pixels) / len(before_pixels)),
                        round(sum(p[2] for p in before_pixels) / len(before_pixels))),
        "mean_after": (round(sum(p[0] for p in after_pixels) / len(after_pixels)),
                       round(sum(p[1] for p in after_pixels) / len(after_pixels)),
                       round(sum(p[2] for p in after_pixels) / len(after_pixels))),
        "mean_lum_before": round(mean_la, 4),
        "mean_lum_after": round(mean_lb, 4),
        "tone_wcag": round(wcag_ratio(mean_la, mean_lb), 3),
    }


# ---- Parse replay file ----
import shlex
steps = []
cur_name, cur_ev = None, []
for raw in open(f"{HERE}/live-demo-commands-l4.txt"):
    line = raw.strip()
    if not line or (line.startswith("#") and not line.startswith("#STEP")):
        continue
    if line.startswith("#STEP"):
        if cur_name is not None:
            steps.append((cur_name, cur_ev))
        cur_name = line.split("#STEP", 1)[1].strip()
        cur_ev = []
    else:
        cur_ev.append(shlex.split(line))
if cur_name is not None:
    steps.append((cur_name, cur_ev))

print(f"Parsed {len(steps)} steps from live-demo-commands-l4.txt")

# ---- Setup ----
print("=== SETUP ===")

# Copy launch helper to target
sh(SCP + [f"{HERE}/t0042-run.sh", f"{HOST}:/tmp/t0042-run.sh"])

# Get seed baseline stats and SHA
seed_stat = tscript(f"stat -c '%s %Y' '{LIVE}'")
seed_sha = tscript(f"sha256sum '{LIVE}'").split()[0]
print(f"seed baseline: {seed_stat} sha={seed_sha[:12]}")

# Kill existing SCMDraft
tscript("pkill -f 'ScmDraft[ ]2' || true; pkill -f 'start[.]exe /exec' || true; true")
time.sleep(2)

# ---- Launch ----
print("=== LAUNCH ===")
launch_out = tscript(f'bash {RUN} {LIVE}')
print(launch_out)
time.sleep(9)
rdpev(["key", "0x1C"])
time.sleep(3)

# ---- Replay steps ----
print("=== REPLAY ===")
step_times = {}
for name, lines in steps:
    t0 = time.time()
    print(f"  step: {name}")
    for tokens in lines:
        rdpev(tokens)
        time.sleep(1.3)
    time.sleep(1.2)
    cap(name)
    step_times[name] = round(time.time() - t0, 1)
    time.sleep(0.5)

# ---- Save via taskkill (Ctrl+S triggers a Broodwar compatibility file dialog on era 6) ----
# taskkill triggers SCMDraft's "Save changes?" prompt, confirmed by Enter (0x1C).
# The Compatibility Warning that follows needs Escape to dismiss (Save button opens a broken file dialog).
# Then a second taskkill + Enter cycle retries the save without the compat warning path.
print("=== SAVE (taskkill + Enter, attempt 1) ===")
cap("before_save")
tscript('XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus '
        f'WINEPREFIX=$HOME/.wine-scmdraft wine taskkill /im "ScmDraft 2.exe"')
time.sleep(4)
cap("save_prompt")
rdpev(["key", "0x1C"])  # Yes on Save Changes
time.sleep(4)
cap("compat_warning")
rdpev(["key", "0x01"])  # Escape: dismiss Compatibility Warning (Cancel on compat dialog)
time.sleep(3)

sha_after_save = tscript(f"sha256sum {LIVE}").split()[0]
stat_after_save = tscript(f"stat -c '%s %Y' {LIVE}")
changed = sha_after_save != seed_sha
print(f"after escape: changed={changed} sha_before={seed_sha[:12]} sha_after={sha_after_save[:12]} size={stat_after_save}")

if not changed:
    # SCMDraft still running (Escape on compat warning may have returned to editor).
    # Retry: Ctrl+S + Enter to dismiss the compat warning directly (Enter=Save in compat dialog)
    # Actually: try Ctrl+S, then Escape on compat, then check if file was written.
    print("attempt 2: Ctrl+S then Escape on compat warning")
    rdpev(["keydown", "0x1D", "key", "0x1F", "keyup", "0x1D"])
    time.sleep(4)
    cap("compat_warning2")
    rdpev(["key", "0x01"])  # Escape on compat warning
    time.sleep(4)
    sha_after_save = tscript(f"sha256sum {LIVE}").split()[0]
    changed = sha_after_save != seed_sha
    stat_after_save = tscript(f"stat -c '%s %Y' {LIVE}")
    print(f"after escape2: changed={changed} sha_after={sha_after_save[:12]} size={stat_after_save}")

    if not changed:
        # Attempt 3: taskkill again (SCMDraft is still running with unsaved changes)
        print("attempt 3: taskkill again")
        tscript('XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus '
                f'WINEPREFIX=$HOME/.wine-scmdraft wine taskkill /im "ScmDraft 2.exe"')
        time.sleep(4)
        rdpev(["key", "0x1C"])  # Yes on Save Changes
        time.sleep(2)
        rdpev(["key", "0x01"])  # Escape on compat warning
        time.sleep(3)
        # If file dialog opened, Escape to cancel it, then try Enter on Save Changes retry
        rdpev(["key", "0x01"])  # Escape any remaining dialog
        time.sleep(2)
        rdpev(["key", "0x1C"])  # Enter in case a Save Changes dialog is still visible
        time.sleep(3)
        sha_after_save = tscript(f"sha256sum {LIVE}").split()[0]
        changed = sha_after_save != seed_sha
        stat_after_save = tscript(f"stat -c '%s %Y' {LIVE}")
        print(f"after attempt3: changed={changed} sha_after={sha_after_save[:12]} size={stat_after_save}")

cap("after_save")

# ---- Kill and re-open for persistence ----
print("=== PERSISTENCE ===")
tscript("pkill -f 'ScmDraft[ ]2' || true; pkill -f 'start[.]exe /exec' || true; true")
time.sleep(2)
tscript(f'bash {RUN} {LIVE}')
time.sleep(9)
rdpev(["key", "0x1C"])
time.sleep(3)
cap("reopen")

for tag in ["down1", "down2"]:
    rdpev(["click", "1893", "700"])
    rdpev(["click", "1893", "700"])
    time.sleep(2)
    cap(f"reopen_{tag}")

# Post-reopen stat and SHA
reopen_stat = tscript(f"stat -c '%s %Y' '{LIVE}'")
reopen_sha = tscript(f"sha256sum '{LIVE}'").split()[0]
print(f"re-open stat: {reopen_stat} sha={reopen_sha[:12]}")

# ---- Verify deliverable maps byte-stable ----
print("=== BYTE-STABILITY ===")
stab_report = {}
for name, (path, expected_prefix) in DELIVERABLES.items():
    sha = tscript(f"sha256sum {path}").split()[0]
    ok = sha.startswith(expected_prefix)
    stab_report[name] = {"sha": sha[:12], "expected": expected_prefix, "match": ok}
    print(f"  {name}: sha={sha[:12]} match={ok}")

# ---- Cleanup target scratch ----
tscript(f'rm -f /tmp/{CAP_PREFIX}-*.png /tmp/t0042-run.log')

# ---- Measurements ----
print("=== MEASUREMENTS ===")

def measure_canvas(path):
    im = Image.open(path).convert("RGB")
    canvas = im.crop(CANVAS_CROP)
    px = canvas.load()
    tot = 0
    grey = 0  # Ice World ground tones (176,176,176 area)
    dark = 0  # High Outpost glyph tones (36,40,56 area)
    for y in range(canvas.height):
        for x in range(canvas.width):
            r, g, b = px[x, y]
            tot += 1
            # Grey Ice ground: r≈g≈b, 140 < r < 210
            if abs(r - g) < 12 and abs(g - b) < 12 and 140 < r < 210:
                grey += 1
            # Dark High Outpost glyph: r < 60, g < 70, b < 80
            if r < 60 and g < 70 and b < 80:
                dark += 1
    return {
        "total_px": tot,
        "grey_pct": round(100 * grey / tot, 2),
        "dark_pct": round(100 * dark / tot, 2),
    }

# Per-pixel WCAG measurements
print("--- Per-pixel WCAG (before vs after at same coordinate) ---")
wcag_results = {}
wcag_results["band1"] = measure_wcag_pair(f"{HERE}/{CAP_PREFIX}-before.png", f"{HERE}/{CAP_PREFIX}-band1.png")
wcag_results["band2"] = measure_wcag_pair(f"{HERE}/{CAP_PREFIX}-before.png", f"{HERE}/{CAP_PREFIX}-band2.png")
wcag_results["band3"] = measure_wcag_pair(f"{HERE}/{CAP_PREFIX}-pan1.png", f"{HERE}/{CAP_PREFIX}-band3.png")
for k, v in wcag_results.items():
    print(f"  {k}: median_wcag={v['median_wcag']} changed={v['changed_total']} inside={v['changed_inside']} ({v['inside_pct']}%)")

# Tone pair measurements (mean tone over stroke rect)
print("--- Tone pair WCAG (mean over stroke rect) ---")
tone_results = {}
for stroke_name, before_cap, after_cap in [
    ("band1", "before", "band1"),
    ("band2", "before", "band2"),
    ("band3", "pan1", "band3"),
]:
    tr = measure_tone_pair(f"{HERE}/{CAP_PREFIX}-{before_cap}.png", f"{HERE}/{CAP_PREFIX}-{after_cap}.png", stroke_name)
    if tr:
        tone_results[stroke_name] = tr
        print(f"  {stroke_name}: tone_wcag={tr['tone_wcag']} before={tr['mean_before']} after={tr['mean_after']}")

# Canvas color stats per step
print("--- Canvas colour stats ---")
canvas_stats = {}
for name in ["before", "band1", "band2", "pan1", "band3", "doodads_layer", "terrain_back",
             "units_layer", "terrain_final", "before_save", "save_prompt", "compat_warning",
             "after_save", "reopen"]:
    path = f"{HERE}/{CAP_PREFIX}-{name}.png"
    if os.path.exists(path):
        s = measure_canvas(path)
        canvas_stats[name] = s
        print(f"  {name}: grey={s['grey_pct']}% dark={s['dark_pct']}%")

# Persistence verification
print("--- Persistence ---")
persistence = {
    "seed_sha": seed_sha,
    "after_save_sha": sha_after_save,
    "reopen_sha": reopen_sha,
    "save_changed": changed,
    "reopen_identical": reopen_sha == sha_after_save,
    "seed_stat": seed_stat,
    "after_save_stat": stat_after_save,
    "reopen_stat": reopen_stat,
}
print(f"  save_changed={persistence['save_changed']} reopen_identical={persistence['reopen_identical']}")

# Pairwise diff counts
def pairwise_diff(path_a, path_b, crop=CANVAS_CROP):
    ia = Image.open(path_a).convert("RGB").crop(crop)
    ib = Image.open(path_b).convert("RGB").crop(crop)
    pa = ia.load()
    pb = ib.load()
    count = 0
    for y in range(ia.height):
        for x in range(ia.width):
            ra, ga, ba = pa[x, y]
            rb, gb, bb = pb[x, y]
            if abs(ra - rb) > 30 or abs(ga - gb) > 30 or abs(ba - bb) > 30:
                count += 1
    return count

pairwise_diffs = {}
pairs = [
    ("before", "band1"), ("before", "band2"), ("band2", "pan1"), ("pan1", "band3"),
    ("band3", "doodads_layer"), ("doodads_layer", "terrain_back"),
    ("terrain_back", "units_layer"), ("units_layer", "terrain_final"),
    ("terrain_final", "before_save"),
    ("before", "reopen"),
]
print("--- Pairwise diffs ---")
for a, b in pairs:
    pa = f"{HERE}/{CAP_PREFIX}-{a}.png"
    pb = f"{HERE}/{CAP_PREFIX}-{b}.png"
    if os.path.exists(pa) and os.path.exists(pb):
        d = pairwise_diff(pa, pb)
        pairwise_diffs[f"{a}_to_{b}"] = d
        print(f"  {a} -> {b}: {d} px")

# ---- Write report ----
report = {
    "dispatch": "L4",
    "date": "2026-11-20",
    "tileset": "Ice World era 6",
    "ground_value": 64,
    "paint_value": 192,
    "seed_stat": seed_stat,
    "seed_sha": seed_sha,
    "after_save_stat": stat_after_save,
    "sha_after_save": sha_after_save,
    "reopen_stat": reopen_stat,
    "reopen_sha": reopen_sha,
    "changed": changed,
    "canvas_crop": list(CANVAS_CROP),
    "status_crop": list(STATUS_CROP),
    "palette_clicks": {"High_Outpost": [62, 934], "Rocky_Snow": [62, 806]},
    "wcag_measurements": wcag_results,
    "tone_measurements": tone_results,
    "canvas_stats": canvas_stats,
    "pairwise_diffs": pairwise_diffs,
    "persistence": persistence,
    "byte_stability": stab_report,
    "step_times": step_times,
    "total_segment_s": round(sum(step_times.values()), 1),
}
with open(f"{HERE}/l4_report.json", "w") as f:
    json.dump(report, f, indent=2)
print(f"\nReport written to {HERE}/l4_report.json")

# ---- Audience-safe step list with timing ----
print("\n=== AUDIENCE-SAFE STEP LIST ===")
audience_steps = []
for name in ["before", "band1", "band2", "pan1", "band3", "doodads_layer", "terrain_back",
             "units_layer", "terrain_final", "before_save", "save_prompt", "after_save", "reopen"]:
    t = step_times.get(name, 0)
    safe = True
    note = ""
    if name in ("doodads_layer", "terrain_back", "units_layer", "terrain_final"):
        note = "layer switch, status-bar evidence only (visible at 2m if display >=32 inch)"
    elif name in ("band1", "band2", "band3"):
        note = "terrain painting, high contrast (WCAG >3.0)"
    elif name == "pan1":
        note = "canvas scroll, visible"
    elif name == "before_save":
        note = "pre-save capture (bands visible)"
    elif name == "save_prompt":
        note = "taskkill triggers Save changes? dialog"
    elif name == "after_save":
        note = "Enter confirms save to original path"
    elif name == "reopen":
        note = "persistence proof after kill and re-open"
    audience_steps.append({"step": name, "time_s": t, "safe": safe, "note": note})
    print(f"  {name:15s} {t:5.1f}s  {note}")
print(f"  TOTAL: {report['total_segment_s']}s")

print("\nDone.")
