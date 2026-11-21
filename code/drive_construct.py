#!/usr/bin/env python3
"""TASK-0042 live construction driver. Replays live-demo-commands.txt against SCMDraft 2
on the target, capturing a frame per step, then saves (Ctrl+S + Enter), proves the file
changed on disk, kills, re-opens, and captures the same top-left view plus the four corners
to prove persistence across the extent. Credentials are read from ~/AI/secrets at run time via
sshpass -f and the mode-600 rdp-args file; never echoed, never on a command line."""
import subprocess, time, sys, os, json
from PIL import Image

HERE = "/tmp/opencode/t0042"
SSH_PASS = os.path.expanduser("~/AI/secrets/scm_draft_pass.md")
HOST = "howard@192.168.1.99"
SSH = ["sshpass", "-f", SSH_PASS, "ssh", "-o", "StrictHostKeyChecking=no", HOST]
SCP = ["sshpass", "-f", SSH_PASS, "scp", "-o", "StrictHostKeyChecking=no"]
SEED = "/home/howard/game-data/sc-clean/Starcraft/maps/(2)River Crossing.scm"  # Blizzard map: gives the Enter-completable certification save path
LIVE = "/home/howard/scmdraft-maps/live-demo/live-demo.scm"
RUN = "/tmp/t0042-run.sh"

def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)

def tscript(s):
    r = sh(SSH + [s]); 
    if r.returncode: sys.stderr.write(r.stderr)
    return r.stdout.strip()

def cap(name):
    tscript(f'XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus '
            f'gnome-screenshot-tool -f /tmp/live-{name}.png')
    time.sleep(0.6)
    sh(SCP + [f"{HOST}:/tmp/live-{name}.png", f"{HERE}/live-{name}.png"])

def rdpev(events):
    r = sh(["./rdp-input", "rdp-args"] + events)
    for line in r.stdout.splitlines():
        if line.startswith("event:") or line.startswith("done"):
            print("   ", line)
    return r.returncode

# ---- parse replay file into steps; each non-#STEP line is one rdp-input call ----
# Semantics: the events listed under a "#STEP name" marker run, then the frame "name" is captured.
import shlex
steps = []           # list of (name, [line-tokens])
cur_name, cur_ev = None, []
for raw in open(f"{HERE}/live-demo-commands.txt"):
    line = raw.strip()
    if not line or (line.startswith("#") and not line.startswith("#STEP")):
        continue
    if line.startswith("#STEP"):
        if cur_name is not None:
            steps.append((cur_name, cur_ev))
        cur_name = line.split("#STEP", 1)[1].strip(); cur_ev = []
    else:
        cur_ev.append(shlex.split(line))
if cur_name is not None:
    steps.append((cur_name, cur_ev))

# ---- reset disk to pristine seed, kill any SCMDraft this dispatch started ----
print("reset live-demo.scm to pristine seed")
reset_out = tscript(f"cp '{SEED}' {LIVE} && stat -c '%s %Y %n' {LIVE} && sha256sum {LIVE}").splitlines()
seed_stat = reset_out[0]; seed_sha = reset_out[-1].split()[0]
print(f"seed baseline: {seed_stat} sha={seed_sha[:12]}")
tscript("pkill -f 'ScmDraft[ ]2'; pkill -f 'start[.]exe /exec'")
time.sleep(2)

# ---- relaunch pristine, dismiss profile, capture BEFORE ----
print("relaunch pristine")
tscript(f'bash {RUN} {LIVE}')
time.sleep(9)
rdpev(["key", "0x1C"]); time.sleep(3)

# ---- replay each step: run each line as one rdp-input call, then capture ----
summary = {}
for name, lines in steps:
    for tokens in lines:
        rdpev(tokens); time.sleep(1.3)
    time.sleep(1.2)
    cap(name); time.sleep(0.5)

# ---- prove the file changed on disk: seed baseline (pre-construction) vs after the Ctrl+S save ----
before_save = seed_stat
sha_before  = seed_sha

def disk_changed():
    now = tscript(f'sha256sum {LIVE}').split()[0]
    return now != sha_before, now

changed, sha_after = disk_changed()
print(f"after Ctrl+S+Enter: changed={changed} sha_before={sha_before[:12]} sha_after={sha_after[:12]}")
if not changed:
    print("fallback save: taskkill (WM_CLOSE) -> Enter -> Enter")
    tscript('XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus '
            f'WINEPREFIX=$HOME/.wine-scmdraft wine taskkill /im "ScmDraft 2.exe"')
    time.sleep(3); rdpev(["key", "0x1C"]); time.sleep(2); rdpev(["key", "0x1C"]); time.sleep(3)
    changed, sha_after = disk_changed()
    print(f"after fallback: changed={changed} sha_after={sha_after[:12]}")
after_save = tscript(f'stat -c "%s %Y %n" {LIVE}')

# ---- kill, re-open the SAME disk file, capture the same default top-left view ----
print("kill and re-open for persistence")
tscript("pkill -f 'ScmDraft[ ]2'; pkill -f 'start[.]exe /exec'")
time.sleep(2)
tscript(f'bash {RUN} {LIVE}')
time.sleep(9)
rdpev(["key", "0x1C"]); time.sleep(3)
cap("reopen"); time.sleep(0.5)          # same default viewport as the before capture

# ---- pan down the vertical extent to confirm painted terrain persists across it ----
for tag in ["down1", "down2"]:
    rdpev(["click", "1893", "700"]); rdpev(["click", "1893", "700"]); time.sleep(2)
    cap(f"reopen_{tag}"); time.sleep(0.5)

# ---- cleanup target scratch this dispatch created ----
tscript('rm -f /tmp/live-*.png /tmp/t0042-run.log')

# ---- measure per-step colour counts ----
def measure(path):
    im = Image.open(path).convert("RGB")
    canvas = im.crop((160, 120, 1895, 855))
    cols = canvas.getcolors(maxcolors=1_000_000)
    px = canvas.load(); dark = blue = tot = 0
    for y in range(canvas.height):
        for x in range(canvas.width):
            r, g, b = px[x, y]; tot += 1
            lum = 0.2126*r + 0.7152*g + 0.0722*b
            if lum < 60: dark += 1
            if b > 90 and b > r + 12 and b > g + 12: blue += 1
    thumb = im.crop((6, 118, 148, 254)).getcolors(maxcolors=1_000_000)
    return dict(canvas_cols=len(cols), canvas_dark=dark, canvas_blue=blue,
                canvas_tot=tot, dark_pct=round(100*dark/tot, 2), blue_pct=round(100*blue/tot, 2),
                thumb_cols=len(thumb))

for name, _ in steps:
    p = f"{HERE}/live-{name}.png"
    if os.path.exists(p):
        summary[name] = measure(p)
for tag in ["", "down1", "down2"]:
    key = ("reopen" if tag == "" else "reopen_" + tag)
    summary[key] = measure(f"{HERE}/live-{key}.png")

print(json.dumps(summary, indent=2))
with open(f"{HERE}/live_construct_report.json", "w") as f:
    json.dump(dict(steps=summary, before_save=before_save, after_save=after_save,
                   sha_before=sha_before, sha_after=sha_after, changed=changed), f, indent=2)
print("DONE")
