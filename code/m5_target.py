#!/usr/bin/env python3
"""TASK-0042 dispatch M5 step 3: place the rebuilt `republic-of-korea` map on the target,
capture its real SCMDraft 2 renders, and prove re-open identity.

No editor save is performed on this map. The `## Status` decision of 2026-11-21 08:40 records
that the deliverable maps never pass through an editor save, because an editor save rewrites the
container and invalidates the gate numbers measured on the shipped bytes. Launch is therefore the
viewing launch `t0042-run.sh` with the Unix path through the seat0 Wayland export, the same path
`M3` used, and not the DOS-path save launch `t0042-run-dos.sh`.

Every target step prints its own inverse. Credentials are read from ~/AI/secrets at run time by
sshpass -f and by the rdp-args file, never placed in argv of this script and never printed.
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

MAPDIR = "/home/howard/scmdraft-maps/republic-of-korea"
PLAIN = f"{MAPDIR}/republic-of-korea.scm"
OLD_SHA = "50e55299dd86fafbcf5976f841992dd326e3d9b56c4d27fecbfdebfd06ea03ca"
NEW_LOCAL = f"{HERE}/republic-of-korea.scm"
PREFIX = "m5"

ACCEPTED = {
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
    print("=== pre-state, four accepted maps plus the map this dispatch replaces ===")
    for name, (path, expect) in ACCEPTED.items():
        print(f"{name}: expect {expect}  {stat_sha(path)}")
    print(f"republic-of-korea (old): expect {OLD_SHA[:12]}  {stat_sha(PLAIN)}")

    print("\n=== step 3.1 rename the 110m build on the target ===")
    print("inverse: mv \"$HOME/scmdraft-maps/republic-of-korea/superseded-republic-of-korea-110m.scm\" "
          "\"$HOME/scmdraft-maps/republic-of-korea/republic-of-korea.scm\"")
    # Idempotent: attempt 1 of this step 3 failed at the scp because OpenSSH scp in SFTP mode does
    # not expand a literal $HOME in the remote path, and the rename had already landed.
    if "MISSING" in stat_sha(PLAIN):
        print("plain name already absent, rename already applied, nothing to do")
    else:
        print(tscript(f'mv "{PLAIN}" "{MAPDIR}/superseded-republic-of-korea-110m.scm" && echo renamed'))
    print("renamed file: ", stat_sha(f"{MAPDIR}/superseded-republic-of-korea-110m.scm"))

    print("\n=== step 3.2 place the rebuilt map at the plain name ===")
    print("inverse: rm -f \"$HOME/scmdraft-maps/republic-of-korea/republic-of-korea.scm\"")
    r = sh(SCP + [NEW_LOCAL, f"{HOST}:{MAPDIR}/republic-of-korea.scm"])
    if r.returncode:
        sys.stderr.write(f"SCP FAIL: {r.stderr.strip()}\n")
        return 2
    print("placed: ", stat_sha(PLAIN))

    print("\n=== step 3.3 launch, dismiss profile, capture the overview render ===")
    print(tscript(f'bash /tmp/t0042-run.sh "/home/howard/scmdraft-maps/republic-of-korea/republic-of-korea.scm"'))
    time.sleep(20)
    rdpev(["key", "0x1C"])
    time.sleep(2.5)
    cap("open")

    print("\n=== step 3.4 overview-jump click onto the design, capture the main-canvas frame ===")
    rdpev(["click", "110", "140"])
    time.sleep(2.5)
    cap("jump")

    print("\n=== step 3.5 kill and re-open the same disk file ===")
    kill_scm()
    print(tscript(f'bash /tmp/t0042-run.sh "/home/howard/scmdraft-maps/republic-of-korea/republic-of-korea.scm"'))
    time.sleep(20)
    rdpev(["key", "0x1C"])
    time.sleep(2.5)
    cap("reopen")
    kill_scm()

    print("\n=== post-state, map unchanged by viewing and re-open (no editor save performed) ===")
    print(f"republic-of-korea (new): {stat_sha(PLAIN)}")
    print(f"superseded 110m build: {stat_sha(f'{MAPDIR}/superseded-republic-of-korea-110m.scm')}")
    for name, (path, expect) in ACCEPTED.items():
        print(f"{name}: expect {expect}  {stat_sha(path)}")

    print("\n=== teardown of this dispatch's target captures ===")
    print("inverse-applied: rm -f /tmp/m5-*.png /tmp/t0042-run.log")
    print(tscript('rm -f /tmp/m5-*.png /tmp/t0042-run.log; ls /tmp/m5-*.png 2>/dev/null || echo captures-removed'))
    print(tscript('pgrep -af "ScmDraft[ ]2" || echo NO_SCM_RUNNING'))
    return 0


if __name__ == "__main__":
    sys.exit(main())
