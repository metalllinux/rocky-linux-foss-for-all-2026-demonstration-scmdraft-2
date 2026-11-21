#!/usr/bin/env python3
"""TASK-0042 dispatch M9 step 2: replace `i-love-korea` on the target with the two-line
rebuild, capture its real SCMDraft 2 renders (overview thumbnail and a main-canvas frame),
attempt the fit-to-line zoom, and prove re-open identity.

No editor save is performed. Deliverable maps never pass through an editor save (## Status
2026-11-21 08:40); the launch is the viewing launch /tmp/t0042-run.sh with an absolute Unix
path. scp destinations are absolute paths (M5 carried fact: SFTP scp does not expand $HOME).

Every target step prints its own inverse. Credentials are read from ~/AI/secrets at run time by
sshpass -f and by the rdp-args file, never placed in argv and never printed.
"""
import subprocess
import sys
import time
import os

HERE = "/tmp/opencode/t0042"
SSH_PASS = os.path.expanduser("~/AI/secrets/scm_draft_pass.md")
HOST = "howard@192.168.1.99"
SSH = ["sshpass", "-f", SSH_PASS, "ssh", "-o", "StrictHostKeyChecking=no", HOST]
SCP = ["sshpass", "-f", SSH_PASS, "scp", "-o", "StrictHostKeyChecking=no"]

MAPDIR = "/home/howard/scmdraft-maps/i-love-korea"
MAP = f"{MAPDIR}/i-love-korea.scm"
OLD = f"{MAPDIR}/superseded-i-love-korea.scm"
LOCAL = f"{HERE}/i-love-korea.scm"
PREFIX = "m9"

# The five other accepted deliverables, and the M7 build being superseded.
ACCEPTED = {
    "foss-for-all": ("/home/howard/scmdraft-maps/foss-for-all/foss-for-all.scm", "e856f0e1"),
    "rocky-logo": ("/home/howard/scmdraft-maps/rocky-logo/rocky-logo.scm", "447360ce"),
    "rocky-with-heart": ("/home/howard/scmdraft-maps/rocky-with-heart/rocky-with-heart.scm", "b9b056c2"),
    "tux": ("/home/howard/scmdraft-maps/tux/tux.scm", "79002eacd5d6"),
    "republic-of-korea (M5 rebuild)": ("/home/howard/scmdraft-maps/republic-of-korea/republic-of-korea.scm", "c773a534a564"),
}
M7_SHA = "82589b4205f5"   # shipped single-row build being superseded


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def tscript(s):
    r = sh(SSH + [s])
    if r.returncode:
        sys.stderr.write(f"SSH FAIL rc {r.returncode}: {r.stderr.strip()}\n")
    return r.stdout.strip()


def stat_sha(path):
    out = tscript(f'if [ -f "{path}" ]; then stat -c "%s %y" "{path}"; sha256sum "{path}"; '
                  f'else echo MISSING; fi')
    return out.replace("\n", "  |  ")


def cap(name):
    tscript(f'XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus '
            f'gnome-screenshot-tool -f /tmp/{PREFIX}-{name}.png')
    time.sleep(0.6)
    r = sh(SCP + [f"{HOST}:/tmp/{PREFIX}-{name}.png", f"{HERE}/{PREFIX}-{name}.png"])
    if r.returncode:
        sys.stderr.write(f"SCP FAIL: {r.stderr.strip()}\n")
    print(f"captured {PREFIX}-{name}.png")


def rdpev(events):
    r = sh(["./rdp-input", "rdp-args"] + events, cwd=HERE)
    for line in (r.stdout or "").splitlines():
        if line.startswith("event:") or line.startswith("done") or line.startswith("error"):
            print("   rdp", line)
    if r.returncode:
        print("   rdp rc", r.returncode, (r.stderr or "").strip()[:200])
    return r.returncode


def kill_scm():
    print(tscript("pkill -f 'ScmDraft[ ]2'; pkill -f 'start[.]exe /exec'; sleep 2; "
                  "pgrep -a -x wineserver | head -3; echo killed"))


def main():
    print("=== pre-state, five accepted deliverables + shipped i-love-korea ===")
    for name, (path, expect) in ACCEPTED.items():
        print(f"{name}: expect {expect}  {stat_sha(path)}")
    print(f"i-love-korea (M7 shipped) expect {M7_SHA}: {stat_sha(MAP)}")

    print("\n=== step 2.1 rename the shipped build to superseded- and place the rebuild ===")
    print('inverse: mv "$HOME/scmdraft-maps/i-love-korea/superseded-i-love-korea.scm" '
          '"$HOME/scmdraft-maps/i-love-korea/i-love-korea.scm"')
    print(tscript(f'cd "{MAPDIR}" && mv -f i-love-korea.scm superseded-i-love-korea.scm && echo renamed'))
    r = sh(SCP + [LOCAL, f"{HOST}:{MAP}"])
    if r.returncode:
        sys.stderr.write(f"SCP FAIL: {r.stderr.strip()}\n")
        return 2
    print("superseded: ", stat_sha(OLD))
    print("new i-love-korea: ", stat_sha(MAP))

    print("\n=== step 2.2 launch, dismiss profile, capture the overview render (default zoom) ===")
    print(tscript(f'bash /tmp/t0042-run.sh "{MAP}"'))
    time.sleep(20)
    rdpev(["key", "0x1C"])
    time.sleep(2.5)
    cap("open")

    print("\n=== step 2.3 attempt the fit-to-line zoom (editor floor 25%) ===")
    # Open the zoom combo and walk it down with extended Down-arrow (AT set 1 e0 50).
    # The exact fit-to-line zoom (21%) is below this build's 25% floor, so 25% is the target.
    rdpev(["click", "385", "90"])
    time.sleep(1.0)
    for _ in range(6):
        rdpev(["keyx", "0x50"])
        time.sleep(0.4)
    rdpev(["key", "0x1C"])
    time.sleep(2.5)
    cap("zoom25")

    print("\n=== step 2.4 overview-jump click onto the design centre, capture the main-canvas frame ===")
    rdpev(["click", "81", "175"])
    time.sleep(2.5)
    cap("jump")

    print("\n=== step 2.5 kill and re-open the same disk file ===")
    kill_scm()
    print(tscript(f'bash /tmp/t0042-run.sh "{MAP}"'))
    time.sleep(20)
    rdpev(["key", "0x1C"])
    time.sleep(2.5)
    cap("reopen")
    kill_scm()

    print("\n=== post-state, i-love-korea unchanged by viewing and re-open (no editor save) ===")
    print(f"i-love-korea: {stat_sha(MAP)}")
    print(f"superseded-i-love-korea: {stat_sha(OLD)}")
    for name, (path, expect) in ACCEPTED.items():
        print(f"{name}: expect {expect}  {stat_sha(path)}")

    print("\n=== teardown of this dispatch's target captures ===")
    print("inverse-applied: rm -f /tmp/m9-*.png /tmp/t0042-run.log")
    print(tscript('rm -f /tmp/m9-*.png /tmp/t0042-run.log; ls /tmp/m9-*.png 2>/dev/null || echo captures-removed'))
    print(tscript('pgrep -af "ScmDraft[ ]2" || echo NO_SCM_RUNNING'))
    return 0


if __name__ == "__main__":
    sys.exit(main())
