#!/usr/bin/env bash
# TASK-0042 L1 Phase 1: setup (mode-600 rdp-args from ~/AI/secrets, never echoed), reset
# live-demo.scm to pristine River Crossing seed, cwd-launch SCMDraft 2, dismiss profile,
# capture the BEFORE view. Inverses recorded in DEMO-LOG.
set -eu
umask 077
HERE=/tmp/opencode/t0042
RDP_SECRET="$HOME/AI/secrets/scm_draft_rdp_pass.md"
SSH_PASS="$HOME/AI/secrets/scm_draft_pass.md"
HOST=howard@192.168.1.99
SSH="sshpass -f $SSH_PASS ssh -o StrictHostKeyChecking=no $HOST"
SCP="sshpass -f $SSH_PASS scp -o StrictHostKeyChecking=no"
SEED='/home/howard/game-data/sc-clean/Starcraft/maps/(2)River Crossing.scm'
MAPDIR=/home/howard/scmdraft-maps/live-demo
LIVE="$MAPDIR/live-demo.scm"

# 1. mode-600 RDP args file, credential read via redirection (not argv)
{ printf '/v:192.168.1.99\n/u:howard\n/p:'; tr -d '\n\r' < "$RDP_SECRET"; printf '\n/cert:ignore\n/w:1920\n/h:1080\n+disp\n'; } > "$HERE/rdp-args"
chmod 600 "$HERE/rdp-args"
echo "rdp-args: $(wc -l < "$HERE/rdp-args") lines, mode $(stat -c '%a' "$HERE/rdp-args")"

# 2. copy cwd launch helper to target
$SCP "$HERE/t0042-run-cwd.sh" "$HOST:/tmp/t0042-run-cwd.sh"

# 3. reset live-demo.scm to pristine seed, record baseline
$SSH "mkdir -p $MAPDIR && cp '$SEED' '$LIVE' && stat -c '%s %Y %n' '$LIVE' && sha256sum '$LIVE'"

# 4. kill only SCMDraft this dispatch owns (none existed at dispatch start)
$SSH "pkill -f 'ScmDraft 2.exe' || true; pkill -f 'start.exe /exec' || true; true"
sleep 2

# 5. cwd-launch (bare filename so the Save dialog filename field is clean)
$SSH "bash /tmp/t0042-run-cwd.sh $MAPDIR live-demo.scm"
sleep 10

# 6. dismiss profile dialog (Enter scancode 0x1C), then capture BEFORE (default top-left view)
cd "$HERE"
./rdp-input rdp-args key 0x1C >/dev/null 2>&1
sleep 3
$SSH "XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus gnome-screenshot-tool -f /tmp/live-before.png"
sleep 1
$SCP "$HOST:/tmp/live-before.png" "$HERE/live-before.png"
echo "before captured"