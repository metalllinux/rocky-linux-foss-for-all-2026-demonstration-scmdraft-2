#!/usr/bin/env python3
"""Probe stage 2a: on the Units layer, scroll the tree down toward the Units node and
capture, so exact node coordinates for unit placement can be read."""
import subprocess, time, os, sys
HERE = "/tmp/opencode/t0042"
SSH_PASS = os.path.expanduser("~/AI/secrets/scm_draft_pass.md")
HOST = "howard@192.168.1.99"
SSH = ["sshpass", "-f", SSH_PASS, "ssh", "-o", "StrictHostKeyChecking=no", HOST]
SCP = ["sshpass", "-f", SSH_PASS, "scp", "-o", "StrictHostKeyChecking=no"]
LIVE = "/home/howard/scmdraft-maps/live-demo/live-demo.scm"
RUN = "/tmp/t0042-run.sh"
def sh(c, **k): return subprocess.run(c, capture_output=True, text=True, **k)
def tscript(s):
    r = sh(SSH + [s]);
    if r.returncode: sys.stderr.write(r.stderr)
    return r.stdout.strip()
def cap(n):
    tscript(f'XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus gnome-screenshot-tool -f /tmp/probe2-{n}.png')
    time.sleep(0.6); sh(SCP + [f"{HOST}:/tmp/probe2-{n}.png", f"{HERE}/probe2-{n}.png"])
def rdpev(e): return sh(["./rdp-input", "rdp-args"] + e).returncode

print("relaunch pristine")
tscript("pkill -f 'ScmDraft[ ]2'; pkill -f 'start[.]exe /exec'")
time.sleep(2)
tscript(f'bash {RUN} {LIVE}'); time.sleep(9)
rdpev(["key", "0x1C"]); time.sleep(2)
cap("launch")
print("Ctrl+U then scroll tree down")
rdpev(["keydown", "0x1D", "key", "0x16", "keyup", "0x1D"]); time.sleep(1.2)
# click the tree scrollbar lower track (page down) several times
for _ in range(4):
    rdpev(["click", "160", "1000"]); time.sleep(0.5)
time.sleep(0.8); cap("scrolled")
tscript('rm -f /tmp/probe2-*.png')
print("done")
