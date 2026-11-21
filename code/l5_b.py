#!/usr/bin/env python3
"""TASK-0042 L5 phase B: the save attempt on the map that phase A opened as C:\\Maps\\... .

Sequence, keyboard only (no injected click on any dialog button):
  Ctrl+S            -> Compatibility Warning (era 6 is a Broodwar tileset)
  Enter             -> accepts the Compatibility Warning's Save button, opens the "Save map" dialog
  capture           -> read what the File name field now holds (the L4 capture held a slashed Unix path)
  Enter             -> accepts the dialog's pre-filled name (Save button)
  Escape            -> dismisses whatever remains
Then size and SHA-256 of the prefix copy are read before and after, the directory is listed for
side-effect files, the four deliverables and the L4 live-demo map are re-hashed, and the saved file
is re-opened through the same DOS-path launch if the save wrote anything.
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
CAP = "l5"
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
    out = tscript(f"stat -c '%s %Y' '{PREFIX_COPY}' 2>&1; sha256sum '{PREFIX_COPY}' 2>&1; ls -la {MAPDIR}")
    print(f"--- disk [{label}] ---\n{out}")
    return out


print("=== BEFORE SAVE ===")
before = disk("before save")

print("=== Ctrl+S ===")
rdpev(["keydown", "0x1D", "key", "0x1F", "keyup", "0x1D"])
time.sleep(4)
cap("ctrls")

print("=== Enter on the Compatibility Warning Save button ===")
rdpev(["key", "0x1C"])
time.sleep(4)
cap("savedlg")

print("=== Enter on the Save map dialog (accepts its pre-filled File name) ===")
rdpev(["key", "0x1C"])
time.sleep(5)
cap("after_enter")

after = disk("after save enter")
changed = after.splitlines()[1].split()[0] != before.splitlines()[1].split()[0]
print(f"prefix copy changed: {changed}")

if not changed:
    print("=== Escape: dismiss whatever dialog is open ===")
    rdpev(["key", "0x01"])
    time.sleep(3)
    cap("after_escape")
    rdpev(["key", "0x01"])
    time.sleep(3)
    cap("after_escape2")
    disk("after escapes")

print("=== title bar and status bar after the attempt ===")
tscript(f'XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus '
        f'gnome-screenshot-tool -f /tmp/{CAP}-final.png')
time.sleep(0.6)
sh(SCP + [f"{HOST}:/tmp/{CAP}-final.png", f"{HERE}/{CAP}-final.png"])
print("scmdraft processes still alive:", tscript("pgrep -af 'ScmDraft[ ]2' || echo none"))

print("=== kill ===")
tscript("pkill -f 'ScmDraft[ ]2' || true; pkill -f 'start[.]exe /exec' || true; true")
time.sleep(3)
print(tscript("pgrep -af 'ScmDraft[ ]2' || echo none"))
disk("after kill")

print("=== re-open the prefix copy through the same DOS path ===")
print(tscript(f"bash {RUN} '{DOS_ARGV}'"))
time.sleep(9)
rdpev(["key", "0x1C"])
time.sleep(3)
cap("reopen")
tscript("pkill -f 'ScmDraft[ ]2' || true; pkill -f 'start[.]exe /exec' || true; true")
time.sleep(2)
print(tscript("pgrep -af 'ScmDraft[ ]2' || echo none"))
disk("after reopen")

print("=== deliverable byte-stability ===")
for name, (path, exp) in DELIVERABLES.items():
    sha = tscript(f"sha256sum '{path}'").split()[0]
    print(f"  {name}: {sha[:12]} expected {exp} match={sha.startswith(exp)}")
sha_src = tscript(f"sha256sum '{SRC}'").split()[0]
print(f"  live-demo-ice (source, must be untouched): {sha_src[:12]} "
      f"match={sha_src.startswith('9a9c2466')}")

print("=== target scratch cleanup ===")
print(tscript(f"rm -f /tmp/{CAP}-*.png /tmp/t0042-run.log && ls -la /tmp/{CAP}-*.png 2>&1 | head -3"))
