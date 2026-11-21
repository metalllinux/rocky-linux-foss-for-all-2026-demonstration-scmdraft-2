#!/usr/bin/env python3
"""TASK-0042 L1 probe stage 1. Launch live-demo.scm (pristine River Crossing seed),
dismiss the profile with Enter, then press Ctrl+U, Ctrl+D, Ctrl+T and capture a full frame
after each, to learn (a) whether layer switching is visibly reflected and (b) where the
Units/Doodads/Locations nodes sit in the tree right after a fresh launch."""
import subprocess, time, os, sys
HERE = "/tmp/opencode/t0042"
SSH_PASS = os.path.expanduser("~/AI/secrets/scm_draft_pass.md")
HOST = "howard@192.168.1.99"
SSH = ["sshpass", "-f", SSH_PASS, "ssh", "-o", "StrictHostKeyChecking=no", HOST]
SCP = ["sshpass", "-f", SSH_PASS, "scp", "-o", "StrictHostKeyChecking=no"]
LIVE = "/home/howard/scmdraft-maps/live-demo/live-demo.scm"
RUN = "/tmp/t0042-run.sh"

def sh(cmd, **kw): return subprocess.run(cmd, capture_output=True, text=True, **kw)
def tscript(s):
    r = sh(SSH + [s])
    if r.returncode: sys.stderr.write(r.stderr)
    return r.stdout.strip()
def cap(name):
    tscript(f'XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus '
            f'gnome-screenshot-tool -f /tmp/probe-{name}.png')
    time.sleep(0.6)
    sh(SCP + [f"{HOST}:/tmp/probe-{name}.png", f"{HERE}/probe-{name}.png"])
def rdpev(events):
    r = sh(["./rdp-input", "rdp-args"] + events)
    return r.returncode

print("launch pristine live-demo")
tscript(f'bash {RUN} {LIVE}')
time.sleep(9)
rdpev(["key", "0x1C"]); time.sleep(2)   # dismiss the "unused unprotector" / profile dialog
cap("launch"); time.sleep(0.4)

print("Ctrl+U (units)")
rdpev(["keydown", "0x1D", "key", "0x16", "keyup", "0x1D"]); time.sleep(1.5); cap("ctrlu"); time.sleep(0.4)

print("Ctrl+D (doodads)")
rdpev(["keydown", "0x1D", "key", "0x07", "keyup", "0x1D"]); time.sleep(1.5); cap("ctrld"); time.sleep(0.4)

print("Ctrl+T (terrain)")
rdpev(["keydown", "0x1D", "key", "0x14", "keyup", "0x1D"]); time.sleep(1.5); cap("ctrlt"); time.sleep(0.4)

tscript('rm -f /tmp/probe-*.png')
print("probe stage1 done")
