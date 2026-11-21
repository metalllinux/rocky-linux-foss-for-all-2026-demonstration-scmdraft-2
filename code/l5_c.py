#!/usr/bin/env python3
"""TASK-0042 L5 phase C: the same save attempt as phase B, taken to the dialog depth the first
attempt revealed. Phase B reached `Save map / File already exists. Do you want to replace it?`
with Yes focused and stopped there, so the question "did the file on disk change" was never
answered. This run repeats the identical launch, the identical paint, and the identical keyboard
chain one level deeper: Ctrl+S, Enter (Compatibility Warning Save), Enter (Save map dialog Save),
Enter (Yes on the overwrite confirmation). Keyboard only, no click on any dialog button.

Target file in the blast radius: ~/.wine-scmdraft/drive_c/Maps/live-demo-ice.scm, the copy this
dispatch created, inverse already recorded. The four deliverable maps and the L4 source map are
re-hashed afterwards.
"""
import subprocess, time, sys, os

HERE = "/tmp/opencode/t0042"
SSH_PASS = os.path.expanduser("~/AI/secrets/scm_draft_pass.md")
HOST = "howard@192.168.1.99"
SSH = ["sshpass", "-f", SSH_PASS, "ssh", "-o", "StrictHostKeyChecking=no", HOST]
SCP = ["sshpass", "-f", SSH_PASS, "scp", "-o", "StrictHostKeyChecking=no"]

SRC = "/home/howard/scmdraft-maps/live-demo/live-demo-ice.scm"
PREFIX_COPY = "/home/howard/.wine-scmdraft/drive_c/Maps/live-demo-ice.scm"
DOS_ARGV = "C:\\Maps\\live-demo-ice.scm"
RUN = "/tmp/t0042-run-dos.sh"
CAP = "l5c"
MAPDIR = "/home/howard/.wine-scmdraft/drive_c/Maps"

DELIVERABLES = {
    "foss-for-all": ("/home/howard/scmdraft-maps/foss-for-all/foss-for-all.scm", "e856f0e1"),
    "rocky-logo": ("/home/howard/scmdraft-maps/rocky-logo/rocky-logo.scm", "447360ce"),
    "rocky-with-heart": ("/home/howard/scmdraft-maps/rocky-with-heart/rocky-with-heart.scm", "b9b056c2"),
    "tux": ("/home/howard/scmdraft-maps/tux/tux.scm", "79002eacd5d6"),
}


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


def disk(label):
    out = tscript(f"stat -c '%s %Y' '{PREFIX_COPY}' 2>&1; sha256sum '{PREFIX_COPY}' 2>&1; ls -l {MAPDIR}")
    print(f"--- disk [{label}] ---\n{out}")
    return out.splitlines()


print("=== launch by the DOS path ===")
print(tscript(f"bash {RUN} '{DOS_ARGV}'"))
time.sleep(9)
rdpev(["key", "0x1C"])
time.sleep(3)
cap("open")

before = disk("before paint")

print("=== paint one band ===")
rdpev(["click", "62", "934"])
time.sleep(1.3)
rdpev(["drag", "320", "640", "1500", "640", "1500", "680", "320", "680"])
time.sleep(1.5)
cap("band1")

print("=== Ctrl+S ===")
rdpev(["keydown", "0x1D", "key", "0x1F", "keyup", "0x1D"])
time.sleep(4)
cap("ctrls")

print("=== Enter 1: Compatibility Warning Save ===")
rdpev(["key", "0x1C"])
time.sleep(4)
cap("enter1")

print("=== Enter 2: Save map dialog Save ===")
rdpev(["key", "0x1C"])
time.sleep(4)
cap("enter2")

print("=== Enter 3: Yes on 'File already exists. Do you want to replace it?' ===")
rdpev(["key", "0x1C"])
time.sleep(6)
cap("enter3")

after = disk("after enter3")
changed = after[1].split()[0] != before[1].split()[0]
print(f"PREFIX COPY CHANGED: {changed}")
print(f"  before: {before[0]}  {before[1].split()[0]}")
print(f"  after : {after[0]}  {after[1].split()[0]}")

print("=== Enter 4 and captures: whatever dialog remains ===")
cap("post_save")
rdpev(["key", "0x01"])
time.sleep(3)
cap("esc1")
rdpev(["key", "0x01"])
time.sleep(3)
cap("esc2")
print("alive:", tscript("pgrep -af 'ScmDraft[ ]2' || echo none"))

print("=== kill, then hash again ===")
tscript("pkill -f 'ScmDraft[ ]2' || true; pkill -f 'start[.]exe /exec' || true; true")
time.sleep(3)
print(tscript("pgrep -af 'ScmDraft[ ]2' || echo none"))
disk("after kill")

print("=== re-open the saved file through the same DOS path ===")
print(tscript(f"bash {RUN} '{DOS_ARGV}'"))
time.sleep(9)
rdpev(["key", "0x1C"])
time.sleep(3)
cap("reopen")
print("alive:", tscript("pgrep -af 'ScmDraft[ ]2' || echo none"))
disk("after reopen")
tscript("pkill -f 'ScmDraft[ ]2' || true; pkill -f 'start[.]exe /exec' || true; true")
time.sleep(2)
print(tscript("pgrep -af 'ScmDraft[ ]2' || echo none"))

print("=== deliverable byte-stability ===")
for name, (path, exp) in DELIVERABLES.items():
    sha = tscript(f"sha256sum '{path}'").split()[0]
    print(f"  {name}: {sha[:12]} expected {exp} match={sha.startswith(exp)}")
sha_src = tscript(f"sha256sum '{SRC}'").split()[0]
print(f"  live-demo-ice source: {sha_src[:12]} match={sha_src.startswith('9a9c2466')}")

print("=== target scratch cleanup ===")
print(tscript(f"rm -f /tmp/{CAP}-*.png /tmp/t0042-run.log && ls /tmp/{CAP}-*.png 2>&1 | head -2"))
