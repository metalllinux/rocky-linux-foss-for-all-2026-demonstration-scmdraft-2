#!/usr/bin/env python3
"""TASK-0042 L1 Phase 2: replay the construction steps in live-demo-commands.txt against the
already-running SCMDraft 2 (cwd-launched live-demo.scm, profile dismissed), capturing one frame
per step. Does NOT save yet. Credentials via mode-600 rdp-args + sshpass -f; never echoed."""
import subprocess, time, shlex, sys, os
HERE = "/tmp/opencode/t0042"
SSH_PASS = os.path.expanduser("~/AI/secrets/scm_draft_pass.md")
HOST = "howard@192.168.1.99"
SSH = ["sshpass", "-f", SSH_PASS, "ssh", "-o", "StrictHostKeyChecking=no", HOST]
SCP = ["sshpass", "-f", SSH_PASS, "scp", "-o", "StrictHostKeyChecking=no"]

def tscript(s):
    r = subprocess.run(SSH + [s], capture_output=True, text=True)
    if r.returncode: sys.stderr.write("SSHERR: " + r.stderr)
    return r.stdout.strip()

def cap(name):
    tscript('XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus '
            f'gnome-screenshot-tool -f /tmp/live-{name}.png')
    time.sleep(0.8)
    subprocess.run(SCP + [f"{HOST}:/tmp/live-{name}.png", f"{HERE}/live-{name}.png"],
                   capture_output=True)

def rdpev(tokens):
    r = subprocess.run([f"{HERE}/rdp-input", "rdp-args"] + tokens, capture_output=True, text=True)
    ok = "done.\n" in r.stdout
    if not ok: sys.stderr.write("RDPERR: " + (r.stdout + r.stderr)[-300:])
    return ok

# parse steps
steps = []; name, ev = None, []
for raw in open(f"{HERE}/live-demo-commands.txt"):
    line = raw.strip()
    if not line or (line.startswith("#") and not line.startswith("#STEP")): continue
    if line.startswith("#STEP"):
        if name is not None: steps.append((name, ev))
        name = line.split("#STEP",1)[1].strip(); ev = []
    else: ev.append(shlex.split(line))
if name is not None: steps.append((name, ev))

os.chdir(HERE)
for name, lines in steps:
    print(f"== {name} ==")
    for tokens in lines:
        rdpev(tokens); time.sleep(1.4)
    time.sleep(1.4)
    cap(name); time.sleep(0.4)
    print(f"   captured live-{name}.png")
print("PHASE2 DONE")