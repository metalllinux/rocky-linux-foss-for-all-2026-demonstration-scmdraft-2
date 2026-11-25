#!/usr/bin/env python3
"""TASK-0042 dispatch S1a: booth loop runner.

One controller command drives the booth cycle the operator recorded on 2026-11-21 22:05:
build each deliverable map deterministically from the committed mask code, verify the rebuilt
file reproduces its recorded SHA-256 BEFORE anything is sent, transfer it to the target Wine
prefix `C:\\Maps\\` by absolute path, open it in SCMDraft 2 by its drive-qualified path, hold it
on the panel for a configured display window using scripted main-canvas frames measured at the
8.00 px per tile floor, then tear that map down.

Rules this file encodes, each traceable to a recorded decision:
  - deterministic rebuild: `build_ts.py` plus the mask registry, no ad-hoc mask code here.
  - SHA-256 verification before transfer (`## Status` 2026-11-21 22:05, decision 1).
  - absolute paths everywhere (OpenSSH scp in SFTP mode does not expand a literal $HOME, `M5`).
  - drive-qualified open via /tmp/t0042-run-dos.sh (`L5`: era 6 maps open and save only from
    inside the prefix).
  - NO editor save on a deliverable map (`## Status` 2026-11-21 08:40). The only map this
    runner touches on the target outside C:\\Maps\\ is the scratch map, and even it is not saved.
  - painting segment on the scratch map inside the cycle (`## Status` 2026-11-21 22:05, 4).
  - loop count and display seconds are parameters, not a hardcoded schedule.
  - every step is timed, logged as it completes, and carries its inverse.

S1b additions (dispatch S1b, 2026-11-22): a per-cycle `C:\\Maps\\Scm*.tmp` cleanup step, target
disk headroom read before and after every cycle, a `--tag-prefix` so several measured phases are
separable in one run log, and a summary that reports per-cycle cost and the number of complete
cycles that fit in one, two and three hours from the measured cost.

S1c additions (dispatch S1c, 2026-11-22): a `--source published` mode. `--source rebuild`, the
default and every cycle measured by `S1a` and `S1b`, rebuilds each map from the committed mask code
plus `ts-harvest/ref-era6.chk`, a harvested plaintext CHK extracted from a shipped Blizzard map that
is withheld from the published repository for licence reasons, so that mode can only run from a
working tree that holds that CHK. `--source published` skips the rebuild entirely, takes each
deliverable `.scm` from a clone of `metalllinux/rocky-linux-foss-for-all-2026-demonstration-scmdraft-2`,
verifies it against the recorded SHA-256 before transfer and again on the target, and then drives the
same open, display, painting-segment and teardown sequence with no save on any map. The frame planner
still reads the committed mask code, which the repository publishes under `code/`. The reference CHK
is never read in published mode.

Usage:
  python3 booth_loop.py --maps tux --loops 1 --display-seconds 60
  python3 booth_loop.py --maps foss-for-all,tux,i-love-korea --display-seconds 300
  python3 booth_loop.py --maps <six> --loops 1 --display-seconds 300 --tag-prefix S1b300
  python3 booth_loop.py --source published --clone <clone-of-the-booth-repo> --maps <six> \
    --loops 1 --display-seconds 300 --tag-prefix S1c300
  python3 booth_loop.py --paint-only
  python3 booth_loop.py --summary [--tag-prefix <phase>]
"""
import argparse
import atexit
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time

# HERE is the directory holding this script: the controller working tree when run there, or
# `<clone>/code` when run from a clone of the booth repo. The mask code the frame planner imports
# (`rocky.py`, `glyph.py`) lives here in both cases, because the repository publishes it in `code/`.
HERE = os.path.dirname(os.path.abspath(__file__))
# DURABLE_DIR is the machine-local controller working tree that outlives /tmp age-cleaning. The host's
# /usr/lib/tmpfiles.d/tmp.conf:11 cleans /tmp at 10 days, which is why the working set lives under
# /home/howard/AI/booth-2026 rather than /tmp/opencode. It is not a git repository and is not pushed
# anywhere, so the withheld artifacts it carries (the reference CHK, the injector binary, mkmpq) never
# sit in a git-tracked path.
DURABLE_DIR = "/home/howard/AI/booth-2026/t0042"
# WORK_DIR is machine-local scratch: captures, OCR crops, the run log, the cycle reports. It defaults
# inside the durable tree so a run survives a cleaned /tmp, and it is created at start. It is not part
# of the repository, and a published-mode run writes nothing into the clone it runs from.
WORK_DIR = os.environ.get("CHAOTIX_T0042_WORK", f"{DURABLE_DIR}/work")
# INJECTOR_DIR is machine-local and deliberately unpublished: `rdp-input` is a compiled binary,
# withheld by the D0 exclusion rules, built from the copy the repository publishes at code/rdp-input.c.
# The RDP credential is not stored here (or anywhere else outside ~/AI/secrets): see rdp_args().
INJECTOR_DIR = os.environ.get("CHAOTIX_T0042_INJECTOR", DURABLE_DIR)
BUILD_DIR = f"{WORK_DIR}/s1a-build"
LOG_PATH = f"{WORK_DIR}/s1a-run-log.jsonl"
SUMMARY_PATH = f"{WORK_DIR}/s1a_cycle_report.json"

# Published (no-rebuild) mode. Repository-side paths a clone carries, and the target-side launch
# script the published runner depends on, published at `code/t0042-run-dos.sh` and verified by
# preflight rather than assumed.
SOURCE = "rebuild"                 # recorded in every log record
CLONE = ""                         # set by --clone when --source published
PUBLISHED_MAP_SUBDIR = "maps/deliverable"
PUBLISHED_SCRATCH_SEED = "live-segment/maps/live-demo-ice.scm"
SCRATCH_SEED_SHA = "8f338a3cea24c1e0c5381088fc0175f5a35151fdd543f971337d99b14d627c74"
PUBLISHED_RUN_SCRIPT = "code/t0042-run-dos.sh"
TARGET_RUN_SCRIPT = "/tmp/t0042-run-dos.sh"

SSH_PASS = os.path.expanduser("~/AI/secrets/scm_draft_pass.md")   # read at run time by sshpass -f
RDP_PASS = os.path.expanduser("~/AI/secrets/scm_draft_rdp_pass.md")  # read at run time by rdp_args()
HOST = "howard@192.168.1.99"
# Pinned target host keys, `## Security` R2 finding 1, closed by dispatch K6. A host public key is not
# a credential: it is what proves who is answering port 22. With verification switched off, anything on
# the controller-to-target path could answer for 192.168.1.99 with its own key, `sshpass -f` then handed
# it the target SSH password, and that password is passwordless sudo on the target. Verification is on
# and it reads only the file this runner writes from the three keys below, so a key that is not one of
# them fails the connection before any authentication and the credential is never sent.
# Seeded 2026-11-25 from the operator's own ~/.ssh/known_hosts entry for 192.168.1.99 and re-checked in
# the same pass against `ssh-keyscan -t ed25519,ecdsa-sha2-nistp256,rsa 192.168.1.99`, which returned the
# identical three keys. `ssh-keygen -l` fingerprints: ED25519 SHA256:S81ZRoHpyZgZAPPZ0UKNKaIL+Rp33Pes2Dc9dZfk1R0,
# RSA SHA256:UPQQkc+zZIVM2flYhxT0Q9qEzdZDjc9vWoauXyh9AVc, ECDSA SHA256:hQKRUU6XD0olZFFH/X/1GiBpN/GdftXae6NcU9Fn+nY.
# Trust origin stated honestly: the seeded entry comes from connections made while verification was off,
# so it is the operator's own record, not an out-of-band attestation. The same three keys are published
# at scripts/remote/known_hosts in the team repository. If the target's host key legitimately changes,
# read the new key on the target itself and re-publish both.
TARGET_HOST_KEYS = (
    "192.168.1.99 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIG5/fH96iHOqxpvEXNzZ2G2QPMGsFpTc7lOpRVDvLAG2\n"
    "192.168.1.99 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCVtENBvUCK0n4f9LTJuGo4ic4j52uvS0ddAIa0HPgIt36"
    "3EIqLkhQPXazsvB6HfFr42T4Z3x2dCnIsmDxENId/zMqADpHeucjEgXcSHqt5OXfQeq+mnS8tiZFZXXbqHTMGppq5L2GpAVt"
    "8wppGgP6nfdCKO+kwbHwo4W53ykE6Zwh3amb0MF2R6ThEFZvxXGwolOWQO7d136A0iHURMdCbi3N3eof+NDDbYSqCFe1hDLUh"
    "Psi/OsINqXeWDwzzWoOmEfrfixRNI4qGPlbbONmN6OGGos9k6Ez1I7XRid7/WxzDLuHCq/2YuWBwbZROz9Netd50dLmualIbB"
    "ZsL+5+nPfADwDOA/IxCVrCIqrptyUxnQtRdQ60J3pUvkf5a0IuYKDRtmLOHSEn4V+4PTyDKsmdHdi2f/52Yv59VeIdN6kj2JS"
    "S4LH+k8usptEN9YVYeemeIFEllvN3c5REhjJXJ8JgWXQTpY4DEaWjaP4bR2oYXHnj1yEoXu/Izv/bAwg0=\n"
    "192.168.1.99 ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBP5Pzvemvvi1"
    "xpoZJKcmc/Y0To9H/ugKJHDApPWWHnjf19BPLCsJGWM5vYBAZYGBVbUCcPw+ldzDAkuqp9lQfVk=\n"
)


def _drop_pinned_known_hosts(path):
    """Remove the pinned known-hosts file on any exit path. A host-key artifact does not outlive the run."""
    try:
        os.unlink(path)
    except OSError:
        pass


def pinned_known_hosts():
    """Write TARGET_HOST_KEYS to a mode 600 file under WORK_DIR and return its path.

    OpenSSH 9.9 takes a comma inside one -o UserKnownHostsFile as a literal file name (verified on this
    host), so a pin can only be carried as a file, not as an option list. mkstemp creates it 0600, the
    chmod states the intent, and atexit removes it. The file holds no credential.
    """
    os.makedirs(WORK_DIR, exist_ok=True)
    fd, path = tempfile.mkstemp(prefix="known-hosts-pinned-", dir=WORK_DIR)
    with os.fdopen(fd, "w") as fh:
        fh.write(TARGET_HOST_KEYS)
    os.chmod(path, 0o600)
    atexit.register(_drop_pinned_known_hosts, path)
    return path


# Verified form: StrictHostKeyChecking=yes plus a known-hosts file that holds only the pinned keys.
# GlobalKnownHostsFile=/dev/null closes the system-wide file too, so nothing outside the pin is trusted.
# ConnectTimeout is new here and only bounds the TCP connect, not a command's runtime.
SSH_OPTS = ["-o", "StrictHostKeyChecking=yes", f"-o", f"UserKnownHostsFile={pinned_known_hosts()}",
            "-o", "GlobalKnownHostsFile=/dev/null", "-o", "ConnectTimeout=10"]
SSH = ["sshpass", "-f", SSH_PASS, "ssh"] + SSH_OPTS + [HOST]
SCP = ["sshpass", "-f", SSH_PASS, "scp"] + SSH_OPTS
# Injector FreeRDP geometry, the seat0 panel the loop drives (measured 1920x1080, L5).
RDP_WIDTH, RDP_HEIGHT = 1920, 1080

# Deliverable originals on the target, never written by this runner (byte-stability gate).
DELIVERABLE_DIR = "/home/howard/scmdraft-maps"
# Loop transfer destination inside the Wine prefix, i.e. C:\Maps\ as the 22:05 decision states.
PREFIX_MAPS = "/home/howard/.wine-scmdraft/drive_c/Maps"
SCRATCH_NAME = "live-demo-ice"

# The six deliverables, with the build recipe that reproduces each recorded SHA-256 and the
# recorded value itself. `mask` is the rocky.MASKS registry key, `mode` the build_ts.py mode.
MAPS = {
    "foss-for-all": dict(mode="glyph", mask=None, sha="e856f0e1d62ec8f7ecfccf8f0d5f08aee0d5798e"
                                                       "f972ea9fee996bbf3bfd3eb0"),
    "rocky-logo": dict(mode="silhouette", mask="rocky-logo",
                       sha="447360ce8077e54293bf37857402860fdb6b918eb335ca95426c7d2abc656e83"),
    "rocky-with-heart": dict(mode="silhouette", mask="rocky-with-heart",
                             sha="b9b056c27a67851508dae01493ccd92ee4df4d70846f2ab8b9cb635fe141f0d8"),
    "tux": dict(mode="silhouette", mask="tux",
                sha="79002eacd5d673c531d6e2e417dddb6c00b02d9a9b9577fab7d43373f682bca4"),
    "republic-of-korea": dict(mode="silhouette", mask="republic-of-korea-10m",
                              sha="c773a534a564d4b3bd13bb9eede10838daa1729784a693f28e6185e779c40976"),
    "i-love-korea": dict(mode="silhouette", mask="i-love-korea-2line",
                         sha="16fe455d46fd88671a98a79f3db65d934400ce0d4edd98f677313e6668d38ba9"),
}

# --- geometry, all cited ---------------------------------------------------
# B1 (measured): overview thumbnail body crop origin (18,112), 128x128 px for 256 tiles,
# 0.5 screen px per tile. Main-canvas viewport edges x167..1879 y110..863 = 1713x754 px.
# M10/F2 (measured): reachable zoom floor 8.00 px per tile (25 % combo), viewport indicator
# 216 x 96 tiles (108 x 48 thumbnail px), tone-measured 214.25 x 94.12 tiles.
THUMB_ORIGIN = (18, 112)
THUMB_BODY = (146, 240)
CANVAS = (167, 110, 1879, 863)
VP_TILES = (216, 96)          # indicator-derived frame window, F2
VP_PX = (1713, 754)           # canvas viewport pixels, B1
GROUND_RGB = (176, 176, 176)  # recorded dominant ground tone, Ice World value 64
GLYPH_RGB = (36, 40, 56)      # recorded glyph tone, value 192
ZOOM_COMBO_CLICK = (385, 90)  # M9's drivable zoom combo click
ZOOM_DOWN_STEPS = 6           # M9's 100 -> 25 walk
STATUS_CROP = (0, 1040, 1920, 1080)
PALETTE_PANEL = (0, 690, 180, 1040)
# L4's recorded coordinates, kept only as a fallback and recorded as such when used.
L4_FALLBACK = {"Rocky Snow": 806, "High Outpost": 934}

LOG = []


def log(loop, map_name, step, seconds, **extra):
    """Append one timed step record the moment it completes."""
    rec = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "loop": loop, "map": map_name,
           "step": step, "seconds": round(seconds, 2), "mode": SOURCE}
    rec.update(extra)
    LOG.append(rec)
    with open(LOG_PATH, "a") as fh:
        fh.write(json.dumps(rec) + "\n")
    print(f"[{loop}/{map_name}] {step}: {seconds:.2f}s " +
          " ".join(f"{k}={v}" for k, v in extra.items() if k != "inverse"))
    return rec


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def tscript(s):
    r = sh(SSH + [s])
    if r.returncode:
        sys.stderr.write(f"SSH FAIL rc {r.returncode}: {r.stderr.strip()}\n")
    return r.stdout.strip()


def parse_stat(s):
    """Split a `stat -c` plus `sha256sum` target read into (size, mtime, sha)."""
    import re
    m = re.search(r"\b[0-9a-f]{64}\b", s or "")
    size = s.split()[0] if s and s.split()[0].isdigit() else None
    return {"size": size, "sha": m.group(0) if m else None, "raw": s}


def target_stat(path):
    out = tscript(f'if [ -f "{path}" ]; then stat -c "%s %y" "{path}"; sha256sum "{path}"; '
                  f'else echo MISSING; fi')
    return out.replace("\n", " | ")


def capture(name, tag):
    """Real full-panel capture on the target, fetched to the controller."""
    remote = f"/tmp/{tag}.png"
    tscript(f'XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus '
            f'gnome-screenshot-tool -f {remote}')
    time.sleep(0.6)
    local = f"{WORK_DIR}/{tag}.png"
    r = sh(SCP + [f"{HOST}:{remote}", local])
    if r.returncode:
        sys.stderr.write(f"SCP FAIL: {r.stderr.strip()}\n")
    return local


def rdp_args():
    """The injector's FreeRDP argument lines, assembled at run time from the machine-local secret file.

    The runner stores no copy of the credential and never puts it in a command line: rdp-input is given
    argv[1] = /dev/stdin and reads these lines from its standard input, which its parse_args_file reads
    with fgets until EOF. Same semantics as the `sshpass -f` path, the first line of the secret file
    with only the trailing newline removed. This replaces the `rdp-args` file the earlier runner needed
    in INJECTOR_DIR, an artifact /tmp age-cleaning destroyed.
    """
    user, _, host = HOST.partition("@")
    if not os.path.exists(RDP_PASS):
        raise SystemExit(f"missing RDP password file {RDP_PASS} (machine-local, never published)")
    with open(RDP_PASS) as fh:
        password = fh.readline().rstrip("\r\n")
    return (f"/v:{host}\n/u:{user}\n/p:{password}\n/cert:ignore\n"
            f"/w:{RDP_WIDTH}\n/h:{RDP_HEIGHT}\n")


def rdpev(events):
    r = sh(["./rdp-input", "/dev/stdin"] + [str(e) for e in events], cwd=INJECTOR_DIR, input=rdp_args())
    if r.returncode:
        print("   rdp rc", r.returncode, (r.stderr or "").strip()[:200])
    return r.returncode


def launch(dos_path):
    print(tscript(f"bash /tmp/t0042-run-dos.sh '{dos_path}'"))


def kill_scm():
    out = tscript("pkill -f 'ScmDraft[ ]2'; pkill -f 'start[.]exe /exec'; sleep 2; "
                  "pgrep -af 'ScmDraft[ ]2' || echo NO_SCM_RUNNING")
    return out


# --- S1b: tmp backup cleanup and disk headroom --------------------------------

def tmp_listing():
    """Name and size every `Scm*.tmp` editor backup currently in C:\\Maps\\."""
    out = tscript(f'find {PREFIX_MAPS} -maxdepth 1 -name "Scm*.tmp" -printf "%f %s\\n" '
                  f'2>/dev/null | sort')
    files = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].isdigit():
            files.append({"name": parts[0], "bytes": int(parts[1])})
    return files


def cleanup_tmp(tag):
    """Per-cycle cleanup of the `C:\\Maps\\Scm*.tmp` backups SCMDraft's open path writes.

    Runs at the START of each cycle, so the residue a cycle leaves is bounded to that cycle's own
    opens (about 2.4 MB for six maps, S1a measurement), a multi-hour booth cannot accumulate the
    ~200 MB the S1a recommendation named, and the final cycle's residue stays on the target for
    the operator to see, which is rule r002. Alternative rejected: cleanup at cycle end, which
    leaves no residue to inspect and hides the per-cycle cost the booth plan needs."""
    t0 = time.monotonic()
    before = tmp_listing()
    total = sum(f["bytes"] for f in before)
    tscript(f'rm -f {PREFIX_MAPS}/Scm*.tmp')
    after = tmp_listing()
    return log(tag, "cycle", "tmp_cleanup", time.monotonic() - t0,
               removed=len(before), bytes_freed=total,
               removed_files=[f["name"] for f in before], remaining=len(after),
               inverse="the editor recreates Scm*.tmp on each map open; the files deleted here "
                       "are named in this record, and this deletion is permanent")


def disk_headroom(tag, when):
    """Read-only target disk headroom: `df -B1 /` plus the byte size of C:\\Maps\\."""
    t0 = time.monotonic()
    out = tscript(f'df -B1 / | tail -1; du -sb {PREFIX_MAPS} 2>/dev/null | cut -f1')
    lines = out.splitlines()
    rec = {"raw_df": lines[0] if lines else ""}
    if lines and len(lines[0].split()) >= 5:
        f = lines[0].split()
        rec["size_b"], rec["used_b"], rec["avail_b"], rec["use_pct"] = f[1], f[2], f[3], f[4]
    if len(lines) > 1 and lines[1].isdigit():
        rec["maps_dir_b"] = int(lines[1])
    return log(tag, "cycle", f"disk_headroom_{when}", time.monotonic() - t0, **rec,
               inverse="read-only, no target change")


# --- frame planning --------------------------------------------------------

def load_mask(name):
    """The committed mask code for this map, no local mask logic."""
    sys.path.insert(0, HERE)
    spec = MAPS[name]
    if spec["mode"] == "glyph":
        import glyph
        return glyph.mask()
    import rocky
    return rocky.MASKS[spec["mask"]]()


def mask_bbox(name):
    m = load_mask(name)
    xs = [x for y in range(len(m)) for x, v in enumerate(m[y]) if v]
    ys = [y for y in range(len(m)) for x, v in enumerate(m[y]) if v]
    return min(xs), max(xs), min(ys), max(ys)


def tile_windows(lo, hi, window, advance, extent=256):
    """Window start positions that cover [lo, hi] with a fixed-size window advancing by
    `advance`, clamped so a window never starts beyond the map edge."""
    span = hi - lo + 1
    n = 1 if span <= window else -((span - window) // -advance) + 1
    max_start = max(lo, extent - window)
    starts, s = [], lo
    for _ in range(n):
        starts.append(min(max(s, lo), max_start))
        s += advance
    return sorted(set(starts))


def frame_plan(name):
    """Frame windows for the display window, derived from the committed mask plus F2's
    recorded positions for i-love-korea line 2. Returns (frames, derivation_note)."""
    x0, x1, y0, y1 = mask_bbox(name)
    m = load_mask(name)
    coverage = sum(sum(r) for r in m)
    if name == "i-love-korea":
        # F2 (## Implementation doc:2539-2547): horizontal frames cols 12-227 and 28-243,
        # vertical tops row 136 and row 152 for line 2, plus line 1 at its own top.
        col_starts = [12, 28]
        row_starts = [y0, 136, 152]
        note = "F2-derived positions (doc:2539-2547) plus mask line-1 top"
    else:
        col_starts = tile_windows(x0, x1, VP_TILES[0], 200)
        row_starts = tile_windows(y0, y1, VP_TILES[1], 80)
        note = "mask bbox tiled by the 216x96 tile window, 200/80 advance"
    frames = []
    for rs in row_starts:
        for cs in col_starts:
            cx = min(max(cs + VP_TILES[0] // 2, VP_TILES[0] // 2), 256 - VP_TILES[0] // 2)
            cy = min(max(rs + VP_TILES[1] // 2, VP_TILES[1] // 2), 256 - VP_TILES[1] // 2)
            frames.append({
                "window": (cs, cs + VP_TILES[0] - 1, rs, rs + VP_TILES[1] - 1),
                "centre": (cx, cy),
                # overview click that centres the viewport on a tile: body origin + 0.5 px/tile
                "click": (THUMB_ORIGIN[0] + 0.5 * cx, THUMB_ORIGIN[1] + 0.5 * cy),
            })
    return frames, note, (x0, x1, y0, y1), coverage


# --- frame measurement -----------------------------------------------------

def mask_min_run(name):
    """Thinnest ink run in the committed mask, in tiles. The reference a stroke census divides by."""
    m = load_mask(name)
    best = None
    for row in m:
        r = 0
        for x in range(len(row) + 1):
            v = row[x] if x < len(row) else 0
            if v:
                r += 1
            else:
                if r and (best is None or r < best):
                    best = r
                r = 0
    return best


def canvas_dark_runs(png, stride_rows=25, min_run=8):
    """Dark (glyph-tone) run lengths in pixels along sampled canvas rows."""
    from PIL import Image
    im = Image.open(png).convert("RGB")
    cv = im.crop(CANVAS)
    out = []
    for y in range(0, cv.height, stride_rows):
        r = 0
        for x in range(cv.width):
            p = cv.getpixel((x, y))
            if max(abs(p[i] - GLYPH_RGB[i]) for i in range(3)) <= 30:
                r += 1
            else:
                if r >= min_run:
                    out.append(r)
                r = 0
    return sorted(out)


def run_census_px_per_tile(name, png):
    """Estimate screen px per tile by matching the drawn dark-run census on the main canvas
    against the committed mask's own horizontal ink-run census. Scale candidates are tested and
    the one that explains the most drawn runs wins, which works for thin-stroke letterforms and
    for wide filled silhouettes alike."""
    m = load_mask(name)
    mask_runs = []
    for row in m:
        r = 0
        for x in range(len(row) + 1):
            v = row[x] if x < len(row) else 0
            if v:
                r += 1
            else:
                if r:
                    mask_runs.append(r)
                r = 0
    # Runs under 16 px are excluded: at the 8 px floor they are anti-aliasing or viewport-edge
    # artifacts rather than drawn tile runs, and they can alias the census to a sub-multiple.
    drawn = canvas_dark_runs(png, min_run=16)
    if not drawn or not mask_runs:
        return None
    # Mask runs under 4 tiles are excluded from the matching set. At the 8 px floor they draw as
    # 16 px runs, which is also what a 2-tile run draws at 8 px/tile, so keeping them lets the
    # census alias to a sub-multiple of the true scale. Scales under 6 are excluded because the
    # editor's recorded zoom range in this task is 8 px/tile at the floor and 32 at 100 percent.
    uniq = sorted(u for u in set(mask_runs) if u >= 4)
    best = None
    for scale in (8, 10, 12, 16, 21, 24, 32):
        hits = sum(1 for d in drawn if any(abs(d - u * scale) <= 2 for u in uniq))
        if best is None or hits > best[1]:
            best = (scale, hits)
    alias = "possible" if any(u < 4 for u in mask_runs) else "no sub-4-tile runs in this mask"
    return {"px_per_tile": best[0], "drawn_runs": len(drawn), "explained_runs": best[1],
            "explained_pct": round(100.0 * best[1] / len(drawn), 1),
            "aliasing": alias, "mask_run_lengths": uniq[:12], "drawn_run_low6": drawn[:6]}


def frame_metrics(png, min_run_tiles=None):
    """Measure what a capture actually shows: viewport indicator extent (hence px per tile),
    the stroke census on the main canvas (thinnest drawn stroke divided by the mask's thinnest
    ink run), and tone composition on the main canvas."""
    from PIL import Image
    im = Image.open(png).convert("RGB")
    body = im.crop(THUMB_ORIGIN + THUMB_BODY)
    ind = []
    for y in range(body.height):
        for x in range(body.width):
            r, g, b = body.getpixel((x, y))
            if min(r, g, b) >= 240:
                ind.append((x, y))
    out = {"capture": os.path.basename(png)}
    if ind:
        xs = [p[0] for p in ind]
        ys = [p[1] for p in ind]
        w, h = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
        tiles_w, tiles_h = w * 2, h * 2
        out["indicator_thumb_px"] = [w, h]
        out["viewport_tiles"] = [tiles_w, tiles_h]
        out["px_per_tile_x"] = round(VP_PX[0] / tiles_w, 3)
        out["px_per_tile_y"] = round(VP_PX[1] / tiles_h, 3)
        out["indicator_on_body"] = len(ind)
    canvas = im.crop(CANVAS)
    g = gl = 0
    for y in range(0, canvas.height, 3):
        for x in range(0, canvas.width, 3):
            r, gg, b = canvas.getpixel((x, y))
            if abs(r - GLYPH_RGB[0]) <= 40 and abs(gg - GLYPH_RGB[1]) <= 40 and abs(b - GLYPH_RGB[2]) <= 40 \
                    and abs(r - GROUND_RGB[0]) > 40:
                gl += 1
            elif abs(r - GROUND_RGB[0]) <= 24 and abs(gg - GROUND_RGB[1]) <= 24 and abs(b - GROUND_RGB[2]) <= 24:
                g += 1
    n = g + gl
    out["canvas_sampled_px"] = n
    out["canvas_glyph_share_pct"] = round(100.0 * gl / n, 2) if n else None
    if min_run_tiles:
        runs = canvas_dark_runs(png)
        out["mask_min_run_tiles"] = min_run_tiles
        if runs:
            out["stroke_census_px_min"] = runs[0]
            out["stroke_census_px_low6"] = runs[:6]
            mode = max(set(runs), key=runs.count)
            out["stroke_census_px_mode"] = mode
            out["stroke_census_mode_count"] = runs.count(mode)
            out["stroke_census_n"] = len(runs)
            out["px_per_tile_stroke"] = round(mode / float(min_run_tiles), 3)
            out["px_per_tile_stroke_from_min"] = round(runs[0] / float(min_run_tiles), 3)
    return out


# --- zoom ------------------------------------------------------------------

def set_zoom_25(loop, name, mrt=None):
    """Walk the Zoom combo to the 25 % floor and verify it from the capture's indicator."""
    t0 = time.monotonic()
    rdpev(["click", ZOOM_COMBO_CLICK[0], ZOOM_COMBO_CLICK[1]])
    time.sleep(1.0)
    for _ in range(ZOOM_DOWN_STEPS):
        rdpev(["keyx", "0x50"])
        time.sleep(0.4)
    rdpev(["key", "0x1C"])
    time.sleep(2.5)
    png = capture(loop, f"{loop}-{name}-zoom")
    m = frame_metrics(png, mrt)
    tries = 1
    while m.get("viewport_tiles", [0, 0])[0] < 200 and tries <= 4:
        rdpev(["click", ZOOM_COMBO_CLICK[0], ZOOM_COMBO_CLICK[1]])
        time.sleep(0.8)
        for _ in range(2):
            rdpev(["keyx", "0x50"])
            time.sleep(0.4)
        rdpev(["key", "0x1C"])
        time.sleep(2.0)
        png = capture(loop, f"{loop}-{name}-zoom")
        m = frame_metrics(png, mrt)
        tries += 1
    log(loop, name, "zoom_set", time.monotonic() - t0,
        viewport_tiles=m.get("viewport_tiles"), px_per_tile=[m.get("px_per_tile_x"),
                                                             m.get("px_per_tile_y")],
        combo_walk_steps=ZOOM_DOWN_STEPS, verification=tries)
    return m


# --- palette re-derivation -------------------------------------------------

def derive_palette(png):
    """Re-derive the terrain palette click rows from a fresh capture by OCR of the label text.
    No hardcoded coordinate is used unless OCR fails, in which case the fallback is recorded."""
    import csv
    import io
    from PIL import Image
    im = Image.open(png).convert("RGB")
    x0, y0, x1, y1 = PALETTE_PANEL
    S = 4
    crop = im.crop(PALETTE_PANEL)
    crop = crop.resize(((x1 - x0) * S, (y1 - y0) * S), Image.LANCZOS)
    tmp = f"{WORK_DIR}/_palette_ocr.png"
    crop.save(tmp)
    r = sh(["tesseract", tmp, "-", "--psm", "6", "tsv"])
    rows = list(csv.DictReader(io.StringIO(r.stdout or ""), delimiter="\t"))
    labels = {}
    for row in rows:
        t = (row["text"] or "").strip()
        if t in ("Rocky", "Snow", "High", "Outpost", "Grass", "Dirt", "Water", "Moguls"):
            yabs = y0 + (int(row["top"]) + int(row["height"]) // 2) // S
            labels.setdefault(t, []).append(yabs)
    def pick(label, second=None):
        cand = labels.get(label, [])
        if second:
            cand = [y for y in cand if any(abs(y - z) <= 2 for z in labels.get(second, []))]
        return min(cand, key=lambda y: abs(y - L4_FALLBACK.get(label, 9999))) if cand else None
    ground = pick("Rocky")
    paint = pick("Outpost", "High")
    method = "ocr-tsv-label-rows"
    derived = {}
    if ground and paint:
        derived = {"Rocky Snow": ground, "High Outpost": paint}
    else:
        method = "l4-fallback"
        derived = dict(L4_FALLBACK)
    high_grass = None
    hg = labels.get("Grass", [])
    hg_high = labels.get("High", [])
    for y in hg:
        if any(abs(y - z) <= 2 for z in hg_high):
            high_grass = y
    return derived, method, {"ocr_rows": labels, "high_grass_row": high_grass}


# --- published (no-rebuild) mode, dispatch S1c ------------------------------

def published_map_path(name):
    """Where a clone of the booth repo carries this map's published deliverable copy."""
    return f"{CLONE}/{PUBLISHED_MAP_SUBDIR}/{name}.scm"


def published_scratch_seed():
    """Where a clone carries the flat Ice World seed the painting segment runs on."""
    return f"{CLONE}/{PUBLISHED_SCRATCH_SEED}"


def preflight_published(names):
    """Published-mode gate, controller-side only, run once per invocation before any target contact.

    Checks every repository-side thing the cycle needs against its recorded SHA-256, so a missing or
    altered published copy aborts the whole invocation before the target is touched, and names the
    three things a clone does not carry rather than discovering them mid-cycle. The withheld reference
    CHK is not needed in this mode and is never read.
    """
    t0 = time.monotonic()
    problems = []
    inj = f"{INJECTOR_DIR}/rdp-input"
    if not (os.path.exists(inj) and os.access(inj, os.X_OK)):
        problems.append(f"injector binary missing or not executable: {inj}. Build it with "
                        "gcc -O2 -Wall -o rdp-input code/rdp-input.c "
                        "$(pkg-config --cflags --libs freerdp-client3)")
    if not os.path.exists(RDP_PASS):
        problems.append(f"RDP password file missing: {RDP_PASS}, machine-local and never published")
    if not os.path.exists(SSH_PASS):
        problems.append(f"target password file missing: {SSH_PASS}, machine-local and never published")
    if not os.path.isdir(f"{CLONE}/{PUBLISHED_MAP_SUBDIR}"):
        problems.append(f"clone carries no {PUBLISHED_MAP_SUBDIR}: {CLONE}")
    for n in names:
        p = published_map_path(n)
        if not os.path.exists(p):
            problems.append(f"published map absent from the clone: {p}")
        elif sha256(p) != MAPS[n]["sha"]:
            problems.append(f"published map does not reproduce its recorded SHA-256: {p}")
    seed = published_scratch_seed()
    if not os.path.exists(seed):
        problems.append(f"published scratch seed absent from the clone: {seed}")
    elif sha256(seed) != SCRATCH_SEED_SHA:
        problems.append(f"published scratch seed does not reproduce {SCRATCH_SEED_SHA[:12]}: {seed}")
    for src in ("rocky.py", "glyph.py"):
        if not os.path.exists(f"{CLONE}/code/{src}"):
            problems.append(f"clone carries no mask code for frame planning: {CLONE}/code/{src}")
    if problems:
        log("preflight", "cycle", "preflight_published", time.monotonic() - t0, status="FAIL",
            clone=CLONE, maps_checked=len(names), problems=problems,
            inverse="read-only checks, nothing written, no target contact")
        for p in problems:
            print(f"PREFLIGHT FAIL {p}")
        return False
    log("preflight", "cycle", "preflight_published", time.monotonic() - t0, status="PASS",
        clone=CLONE, maps_checked=len(names), injector=inj, work_dir=WORK_DIR,
        clone_carries=[f"{PUBLISHED_MAP_SUBDIR}/<name>.scm", PUBLISHED_SCRATCH_SEED,
                       "code/rocky.py", "code/glyph.py", PUBLISHED_RUN_SCRIPT],
        clone_does_not_carry=["rdp-input (compiled binary, withheld)",
                              "target RDP credential (read from ~/AI/secrets at run time by rdp_args, "
                              "never stored by the runner)",
                              "target password file (credential, withheld)",
                              "ts-harvest/ref-era6.chk (harvested Blizzard CHK, withheld, "
                              "not read in this mode)"],
        inverse="read-only checks, nothing written, no target contact")
    return True


def run_script_source():
    """Which controller-side copy of the target launch script a mode installs from: the clone's
    published `code/t0042-run-dos.sh` in published mode, the working tree's own copy in rebuild mode.
    On this controller both read the same SHA-256, a85bba3c89f1."""
    return f"{CLONE}/{PUBLISHED_RUN_SCRIPT}" if SOURCE == "published" else f"{HERE}/t0042-run-dos.sh"


def preflight_target_run_script():
    """Check the target-side launch script against the copy the runner installs from, before the first
    open. Installs that copy if the target has none, which is what survives a cleaned /tmp on the
    target, and names the removal inverse. If the target carries a script that differs, aborts rather
    than overwriting machine state silently."""
    t0 = time.monotonic()
    pub = run_script_source()
    if not os.path.exists(pub):
        log("preflight", "cycle", "preflight_target_run_script", time.monotonic() - t0, status="FAIL",
            reason=f"no local copy of the target launch script at {pub}", inverse="no target change")
        return False
    want = sha256(pub)
    t = parse_stat(tscript(f'if [ -f "{TARGET_RUN_SCRIPT}" ]; then sha256sum "{TARGET_RUN_SCRIPT}"; '
                           f'else echo MISSING; fi'))
    if (t["raw"] or "").strip() == "MISSING":
        r = sh(SCP + [pub, f"{HOST}:{TARGET_RUN_SCRIPT}"])
        tscript(f'chmod 755 {TARGET_RUN_SCRIPT}')
        after = parse_stat(tscript(f'sha256sum {TARGET_RUN_SCRIPT}'))
        ok = r.returncode == 0 and after["sha"] == want
        log("preflight", "cycle", "preflight_target_run_script", time.monotonic() - t0,
            status="INSTALLED" if ok else "FAIL", target=TARGET_RUN_SCRIPT,
            sha=(after["sha"] or "")[:12], expected=want[:12], inverse=f"rm -f {TARGET_RUN_SCRIPT}")
        return ok
    ok = t["sha"] == want
    log("preflight", "cycle", "preflight_target_run_script", time.monotonic() - t0,
        status="PASS" if ok else "FAIL", target=TARGET_RUN_SCRIPT, sha=(t["sha"] or "")[:12],
        expected=want[:12], inverse="read-only check, no target change")
    if not ok:
        print(f"PREFLIGHT FAIL {TARGET_RUN_SCRIPT} does not match the published "
              f"{PUBLISHED_RUN_SCRIPT}, refusing to overwrite it")
    return ok


def preflight_rebuild():
    """Rebuild-mode gate, controller-side only, run once per invocation before any target contact.

    Rebuild mode needs four things a clone does not carry: the injector binary, the StormLib map writer
    `mkmpq` that build_ts.py calls to wrap the CHK, the withheld reference CHK, and the mask code frame
    planning imports. All four now live in the durable working tree, so a cleaned /tmp no longer decides
    whether the booth run can start. Anything missing aborts the invocation and names where it comes from.
    """
    t0 = time.monotonic()
    problems = []
    inj = f"{INJECTOR_DIR}/rdp-input"
    if not (os.path.exists(inj) and os.access(inj, os.X_OK)):
        problems.append(f"injector binary missing or not executable: {inj}. Build it with "
                        "gcc -O2 -Wall -o rdp-input code/rdp-input.c "
                        "$(pkg-config --cflags --libs freerdp-client3)")
    mk = f"{HERE}/mkmpq"
    if not (os.path.exists(mk) and os.access(mk, os.X_OK)):
        problems.append(f"map writer missing or not executable: {mk}. Rebuild it with "
                        "gcc -O2 -Wall -I stormlib/include -o mkmpq mkmpq.c stormlib/lib/libstorm.a "
                        "-lstdc++ -lm")
    ref_chk = f"{HERE}/ts-harvest/ref-era6.chk"
    if not os.path.exists(ref_chk):
        problems.append(f"reference CHK absent: {ref_chk}, withheld from the repository")
    for src in ("rocky.py", "glyph.py"):
        if not os.path.exists(f"{HERE}/{src}"):
            problems.append(f"mask code absent from the working tree: {HERE}/{src}")
    for secret in (SSH_PASS, RDP_PASS):
        if not os.path.exists(secret):
            problems.append(f"secret file absent: {secret}, machine-local and never published")
    if problems:
        log("preflight", "cycle", "preflight_rebuild", time.monotonic() - t0, status="FAIL",
            problems=problems, inverse="read-only checks, nothing written, no target contact")
        for p in problems:
            print(f"PREFLIGHT FAIL {p}")
        return False
    log("preflight", "cycle", "preflight_rebuild", time.monotonic() - t0, status="PASS", injector=inj,
        mkmpq=mk, ref_chk=ref_chk, work_dir=WORK_DIR, injector_dir=INJECTOR_DIR,
        inverse="read-only checks, nothing written, no target contact")
    return True


# --- the cycle -------------------------------------------------------------

def run_map(loop, name, display_seconds):
    spec = MAPS[name]
    target_path = f"{PREFIX_MAPS}/{name}.scm"          # absolute, scp will not expand $HOME
    dos_path = f"C:\\Maps\\{name}.scm"

    # 1. acquire this iteration's map. Rebuild mode rebuilds it from the committed mask code plus the
    #    withheld reference CHK. Published mode (S1c) reads the clone's published deliverable copy
    #    read-only and reads no CHK at all.
    t0 = time.monotonic()
    if SOURCE == "published":
        local = published_map_path(name)
        if not os.path.exists(local):
            log(loop, name, "published_source", time.monotonic() - t0, status="FAIL", source=local,
                reason="published deliverable path absent from the clone",
                inverse="nothing was written in this step")
            return False
        log(loop, name, "published_source", time.monotonic() - t0, source=local,
            bytes=os.path.getsize(local),
            inverse="read-only step, the clone copy is not modified and nothing was written")
    else:
        local = f"{BUILD_DIR}/{name}.scm"
        ref_chk = f"{HERE}/ts-harvest/ref-era6.chk"
        if not os.path.exists(ref_chk):
            log(loop, name, "build", time.monotonic() - t0, status="FAIL", ref_chk=ref_chk,
                reason="rebuild mode needs the withheld reference CHK, which the published repository "
                       "does not carry; run --source published from a clone instead",
                inverse="nothing was built or written")
            return False
        os.makedirs(BUILD_DIR, exist_ok=True)
        argv = [sys.executable, f"{HERE}/build_ts.py", spec["mode"], ref_chk,
                f"{BUILD_DIR}/{name}", "192", "64", "64"] + ([spec["mask"]] if spec["mask"] else [])
        r = sh(argv)
        build_out = (r.stdout or "").strip().splitlines()
        if r.returncode or not os.path.exists(local):
            log(loop, name, "build", time.monotonic() - t0, status="FAIL", stderr=(r.stderr or "")[:200])
            return False
        log(loop, name, "build", time.monotonic() - t0, bytes=os.path.getsize(local),
            build_line=build_out[0] if build_out else "", inverse=f"rm -f {local} {BUILD_DIR}/{name}.chk")

    # 2. SHA-256 gate before anything is sent
    t0 = time.monotonic()
    got = sha256(local)
    ok = got == spec["sha"]
    log(loop, name, "sha_verify_controller", time.monotonic() - t0, sha=got[:12],
        expected=spec["sha"][:12], status="PASS" if ok else "FAIL",
        inverse="no target change was made on this step")
    if not ok:
        print(f"ABORT {name}: rebuild does not reproduce the recorded SHA, nothing transferred")
        return False

    # 3. transfer with absolute paths, then verify the target copy against the same record
    t0 = time.monotonic()
    r = sh(SCP + [local, f"{HOST}:{target_path}"])
    tstat = parse_stat(target_stat(target_path))
    log(loop, name, "transfer", time.monotonic() - t0, target=target_path,
        status="PASS" if tstat["sha"] == spec["sha"] else "FAIL", target_size=tstat["size"],
        target_sha=(tstat["sha"] or "")[:12],
        inverse=f"rm -f {target_path}")
    if tstat["sha"] != spec["sha"]:
        print(f"ABORT {name}: target copy does not match the record")
        return False

    # 4. open on the target panel by its drive-qualified path, viewing only
    t0 = time.monotonic()
    launch(dos_path)
    time.sleep(20)
    rdpev(["key", "0x1C"])           # dismiss the Scenario-properties dialog (Enter, 0x1C)
    time.sleep(2.5)
    png = capture(loop, f"{loop}-{name}-open")
    title = title_bar(png)
    log(loop, name, "open", time.monotonic() - t0, dos_path=dos_path, title=title,
        inverse="pkill -f 'ScmDraft[ ]2'; pkill -f 'start[.]exe /exec'")

    # 5. display window: zoom to the measured floor, then the scripted frames, timed out
    mrt = mask_min_run(name)
    zm = set_zoom_25(loop, name, mrt)
    frames, derivation, bbox, coverage = frame_plan(name)
    hold = max(2.0, display_seconds / len(frames))
    t0 = time.monotonic()
    elapsed = 0.0
    for i, fr in enumerate(frames, 1):
        t_frame = time.monotonic()
        cx, cy = fr["click"]
        rdpev(["click", int(cx), int(cy)])
        time.sleep(2.5)
        shot = capture(loop, f"{loop}-{name}-f{i}")
        fm = frame_metrics(shot, mrt)
        sleep_for = max(0.0, hold - 3.0)
        time.sleep(sleep_for)
        census = run_census_px_per_tile(name, shot)
        elapsed += time.monotonic() - t_frame
        log(loop, name, f"frame{i}", time.monotonic() - t_frame, window=fr["window"],
            click=[int(cx), int(cy)], tiles=fm.get("viewport_tiles"),
            px_tile=[fm.get("px_per_tile_x"), fm.get("px_per_tile_y")],
            census_px_per_tile=census and census["px_per_tile"],
            census_explained_pct=census and census["explained_pct"],
            canvas_glyph_pct=fm.get("canvas_glyph_share_pct"))
    log(loop, name, "display_window", time.monotonic() - t0, seconds_requested=display_seconds,
        frames=len(frames), hold_per_frame=round(hold, 2), frame_derivation=derivation,
        glyph_bbox=bbox, glyph_tiles=coverage, measured_held=round(elapsed, 1),
        inverse="display only, no file change")

    # 6. teardown this map
    t0 = time.monotonic()
    state = kill_scm()
    tscript(f'rm -f {target_path} /tmp/t0042-run.log')
    gone = tscript(f'ls {target_path} 2>/dev/null || echo REMOVED')
    log(loop, name, "teardown", time.monotonic() - t0, scm=state.splitlines()[-1:],
        loop_copy=gone, inverse="the deliverable original in "
        f"{DELIVERABLE_DIR}/{name}/{name}.scm is untouched by this loop")
    return True


def title_bar(png):
    from PIL import Image
    im = Image.open(png).convert("RGB")
    c = im.crop((0, 36, 900, 62))
    c = c.resize((900 * 2, 26 * 3), Image.LANCZOS)
    c.save(f"{WORK_DIR}/_title.png")
    return sh(["tesseract", f"{WORK_DIR}/_title.png", "-", "--psm", "7"]).stdout.strip()[:160]


def status_readout(png):
    """Read the editor status strip from a capture, the L5 method (crop, 3x, tesseract psm 7)."""
    from PIL import Image
    im = Image.open(png).convert("RGB")
    c = im.crop(STATUS_CROP)
    c = c.resize(((STATUS_CROP[2] - STATUS_CROP[0]) * 3, (STATUS_CROP[3] - STATUS_CROP[1]) * 3),
                 Image.LANCZOS)
    c.save(f"{WORK_DIR}/_status.png")
    return sh(["tesseract", f"{WORK_DIR}/_status.png", "-", "--psm", "7"]).stdout.strip()[:120]


def run_paint(loop):
    """The proven painting segment, on the scratch map inside the cycle. No deliverable map
    is saved by the editor, and the scratch map is not saved either."""
    # The flat Ice World seed the segment paints on. Rebuild mode uses the controller copy that
    # build_ice_seed.py wrote; published mode uses the copy the repository carries at
    # live-segment/maps/, verified against the same recorded SHA-256 before it is transferred.
    local_seed = published_scratch_seed() if SOURCE == "published" else f"{WORK_DIR}/live-demo-ice.scm"
    seed_sha = SCRATCH_SEED_SHA
    target_path = f"{PREFIX_MAPS}/{SCRATCH_NAME}.scm"
    dos_path = f"C:\\Maps\\{SCRATCH_NAME}.scm"

    t0 = time.monotonic()
    pre = parse_stat(target_stat(target_path))
    backup = f"{target_path}.pre-s1a"
    tscript(f'cp -f {target_path} {backup}')
    log(loop, SCRATCH_NAME, "scratch_pre_state", time.monotonic() - t0, before=pre,
        inverse=f"cp -f {backup} {target_path} && rm -f {backup}")

    t0 = time.monotonic()
    if sha256(local_seed) != seed_sha:
        log(loop, SCRATCH_NAME, "scratch_seed_verify", time.monotonic() - t0, source=local_seed,
            status="FAIL")
        return False
    sh(SCP + [local_seed, f"{HOST}:{target_path}"])
    log(loop, SCRATCH_NAME, "scratch_seed_transfer", time.monotonic() - t0,
        target=target_path, seed_sha=seed_sha[:12], source=local_seed,
        inverse=f"cp -f {backup} {target_path}")

    t0 = time.monotonic()
    launch(dos_path)
    time.sleep(20)
    rdpev(["key", "0x1C"])
    time.sleep(2.5)
    png = capture(loop, f"{loop}-{SCRATCH_NAME}-open")
    log(loop, SCRATCH_NAME, "scratch_open", time.monotonic() - t0, dos_path=dos_path,
        title=title_bar(png), inverse="pkill -f 'ScmDraft[ ]2'")

    t0 = time.monotonic()
    pal = capture(loop, f"{loop}-{SCRATCH_NAME}-palette")
    derived, method, extra = derive_palette(pal)
    log(loop, SCRATCH_NAME, "palette_derive", time.monotonic() - t0, method=method,
        rows=derived, high_grass=extra.get("high_grass_row"),
        inverse="capture only")

    y_paint = derived["High Outpost"]
    steps = [
        ("band1", [("click", 62, y_paint), ("drag", 320, 360, 1500, 360, 1500, 392, 320, 392)]),
        ("band2", [("click", 62, y_paint), ("drag", 320, 520, 1500, 520, 1500, 552, 320, 552)]),
        ("pan", [("click", 1893, 700), ("click", 1893, 700), ("click", 1893, 700)]),
        ("band3", [("click", 62, y_paint), ("drag", 320, 420, 1500, 420, 1500, 452, 320, 452)]),
        ("layers", [("keydown", "0x1D", "key", "0x20", "keyup", "0x1D"),
                    ("keydown", "0x1D", "key", "0x14", "keyup", "0x1D"),
                    ("keydown", "0x1D", "key", "0x16", "keyup", "0x1D"),
                    ("keydown", "0x1D", "key", "0x14", "keyup", "0x1D")]),
    ]
    before = capture(loop, f"{loop}-{SCRATCH_NAME}-before")
    after = None
    for step_name, evs in steps:
        t0 = time.monotonic()
        for ev in evs:
            rdpev(list(ev))
            time.sleep(0.8)
        time.sleep(1.5)
        shot = capture(loop, f"{loop}-{SCRATCH_NAME}-{step_name}")
        if step_name == "band3":
            after = shot
        log(loop, SCRATCH_NAME, f"paint_{step_name}", time.monotonic() - t0,
            status_bar=status_readout(shot),
            inverse="no save is performed; teardown restores "
                    f"{target_path} from {backup}")
    t0 = time.monotonic()
    status = capture(loop, f"{loop}-{SCRATCH_NAME}-statusbar")
    log(loop, SCRATCH_NAME, "statusbar_evidence", time.monotonic() - t0, crop=STATUS_CROP,
        inverse="capture only")
    wcag = paint_wcag(before, after)
    log(loop, SCRATCH_NAME, "paint_contrast", 0.0, **wcag)

    t0 = time.monotonic()
    state = kill_scm()
    tscript(f'cp -f {backup} {target_path} && rm -f {backup} && rm -f /tmp/t0042-run.log')
    log(loop, SCRATCH_NAME, "scratch_teardown", time.monotonic() - t0, scm=state.splitlines()[-1:],
        after=parse_stat(target_stat(target_path)), inverse=f"before this step the file was {pre}")
    return True


def paint_wcag(before_png, after_png):
    """Per-pixel WCAG between the before tone and the after tone at the same canvas
    coordinates, measured in this pass rather than carried from L4."""
    from PIL import Image
    a = Image.open(before_png).convert("RGB").crop(CANVAS)
    b = Image.open(after_png).convert("RGB").crop(CANVAS)
    diffs = []
    for y in range(360, 460):
        for x in range(160, 1500, 2):
            pa, pb = a.getpixel((x, y)), b.getpixel((x, y))
            if max(abs(pa[i] - pb[i]) for i in range(3)) > 30:
                diffs.append((pa, pb))
    if not diffs:
        return {"changed_px_sampled": 0, "median_wcag": None}
    def lum(p):
        def f(c):
            c /= 255.0
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        return 0.2126 * f(p[0]) + 0.7152 * f(p[1]) + 0.0722 * f(p[2])
    ratios = []
    for pa, pb in diffs:
        l1, l2 = lum(pa), lum(pb)
        lo, hi = min(l1, l2), max(l1, l2)
        ratios.append((hi + 0.05) / (lo + 0.05))
    ratios.sort()
    return {"changed_px_sampled": len(ratios),
            "median_wcag": round(ratios[len(ratios) // 2], 3),
            "min_wcag": round(ratios[0], 3)}


def deliverable_stability():
    out = {}
    for name in MAPS:
        p = f"{DELIVERABLE_DIR}/{name}/{name}.scm"
        out[name] = target_stat(p)
    return out


def summary(tag_prefix=None):
    per_map = {}
    for rec in (json.loads(l) for l in open(LOG_PATH)):
        per_map.setdefault((rec["loop"], rec["map"]), []).append(rec)
    maps = {}
    # Per-frame records sit INSIDE the display_window record's wall span, so they are reported
    # separately and excluded from the cycle total, which would otherwise double count them.
    FRAME_STEPS = {f"frame{i}" for i in range(1, 13)}
    for (loop, name), recs in sorted(per_map.items()):
        if tag_prefix and not loop.startswith(tag_prefix):
            continue
        if name in (SCRATCH_NAME, "cycle"):
            continue
        tot = sum(r["seconds"] for r in recs if r["step"] not in FRAME_STEPS)
        disp = sum(r["seconds"] for r in recs if r["step"] == "display_window")
        maps[f"{loop}/{name}"] = {
            "build": next((r["seconds"] for r in recs
                           if r["step"] in ("build", "published_source")), None),
            "acquisition": next((r["step"] for r in recs
                                 if r["step"] in ("build", "published_source")), None),
            "sha_verify": next((r["seconds"] for r in recs if r["step"] == "sha_verify_controller"), None),
            "transfer": next((r["seconds"] for r in recs if r["step"] == "transfer"), None),
            "open": next((r["seconds"] for r in recs if r["step"] == "open"), None),
            "zoom_set": next((r["seconds"] for r in recs if r["step"] == "zoom_set"), None),
            "display_window": disp,
            "teardown": next((r["seconds"] for r in recs if r["step"] == "teardown"), None),
            "overhead_excluding_display": round(tot - disp, 2),
            "total": round(tot, 2),
            "steps": len(recs),
        }
    paint = [r for (lp, nm), rs in per_map.items()
             if nm == SCRATCH_NAME and (not tag_prefix or lp.startswith(tag_prefix))
             for r in rs]
    # Per-cycle cost: all six map totals plus the scratch paint segment plus the per-cycle
    # steps (tmp cleanup, headroom reads). Frame records are inside display_window's span and
    # are already excluded from each map total. cycles_fit_* are computed from THIS measured
    # cost, not from a projection.
    cycles = {}
    loops = sorted({l for (l, _) in per_map if not tag_prefix or l.startswith(tag_prefix)})
    for loop in loops:
        recs = [r for (l2, _), rs in per_map.items() if l2 == loop for r in rs]
        map_tot = sum(m["total"] for k, m in maps.items() if k.startswith(f"{loop}/"))
        cyc_tot = sum(r["seconds"] for r in recs if r["map"] == "cycle")
        paint_tot = sum(r["seconds"] for r in recs if r["map"] == SCRATCH_NAME)
        cost = round(map_tot + cyc_tot + paint_tot, 2)
        cycles[loop] = {
            "modes_recorded": sorted({r.get("mode", "rebuild") for r in recs}),
            "maps_total": round(map_tot, 2),
            "cycle_steps": round(cyc_tot, 2),
            "paint": round(paint_tot, 2),
            "cycle_cost_seconds": cost,
            "cycles_fit_1h": int(3600 // cost) if cost else None,
            "cycles_fit_2h": int(7200 // cost) if cost else None,
            "cycles_fit_3h": int(10800 // cost) if cost else None,
        }
    rep = {"per_map": maps,
           "cycles": cycles,
           "scratch_paint_steps": len(paint),
           "scratch_paint_seconds": round(sum(r["seconds"] for r in paint), 2),
           "log_records": len(LOG) or sum(1 for _ in open(LOG_PATH))}
    path = SUMMARY_PATH if not tag_prefix else f"{WORK_DIR}/{tag_prefix}_cycle_report.json"
    with open(path, "w") as fh:
        json.dump(rep, fh, indent=2)
    print(json.dumps(rep, indent=2))


def main():
    # Scratch defaults inside the durable tree and is created here, so a cleaned /tmp cannot break the
    # run log or a capture transfer. An explicit CHAOTIX_T0042_WORK override is created the same way.
    os.makedirs(WORK_DIR, exist_ok=True)
    ap = argparse.ArgumentParser()
    ap.add_argument("--maps", default="")
    ap.add_argument("--loops", type=int, default=1)
    ap.add_argument("--display-seconds", type=int, default=300)
    ap.add_argument("--paint-only", action="store_true")
    ap.add_argument("--no-paint", action="store_true")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--stability", action="store_true")
    ap.add_argument("--tag-prefix", default="S1b")
    ap.add_argument("--source", choices=("rebuild", "published"), default="rebuild",
                    help="rebuild builds each map from the committed mask code plus the withheld "
                         "reference CHK. published takes each map from a clone of the booth repo and "
                         "verifies it against the recorded SHA-256 instead, reading no CHK.")
    ap.add_argument("--clone", default="",
                    help="path to a clone of the booth repo, required by --source published")
    args = ap.parse_args()

    if args.stability:
        print(json.dumps(deliverable_stability(), indent=2))
        return 0
    if args.summary:
        summary(args.tag_prefix if args.tag_prefix != "S1b" else None)
        return 0

    global SOURCE, CLONE
    if args.source == "published":
        if not args.clone:
            print("--source published needs --clone <path to a clone of the booth repo>")
            return 2
        CLONE = os.path.abspath(args.clone)
    SOURCE = args.source

    names = [n for n in args.maps.split(",") if n]
    for n in names:
        if n not in MAPS:
            print(f"unknown map {n}")
            return 2
    if SOURCE == "published":
        if not preflight_published(names):
            return 4
    elif not preflight_rebuild():
        return 4
    if not preflight_target_run_script():
        return 5
    for loop_i in range(1, max(1, args.loops) + 1):
        tag = f"{args.tag_prefix}L{loop_i}"
        cleanup_tmp(tag)
        disk_headroom(tag, "before")
        for n in names:
            if not run_map(tag, n, args.display_seconds):
                return 3
        if not args.no_paint:
            run_paint(tag)
        disk_headroom(tag, "after")
    summary(args.tag_prefix)
    return 0


if __name__ == "__main__":
    sys.exit(main())
