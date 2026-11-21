#!/usr/bin/env bash
# TASK-0042 L1 setup: regenerate the mode-600 RDP args file from ~/AI/secrets at run time
# (never echoed, never on a command line), reset live-demo.scm to the pristine seed on the
# target, copy the launch helper to the target, and clear any SCMDraft this dispatch owns.
# Inverse at dispatch end: rm -f /tmp/opencode/t0042/rdp-args; rm -f /tmp/t0042-run.sh (target).
set -eu
umask 077
HERE=/tmp/opencode/t0042
RDP_SECRET="$HOME/AI/secrets/scm_draft_rdp_pass.md"
SSH_PASS="$HOME/AI/secrets/scm_draft_pass.md"
HOST=howard@192.168.1.99
SEED='/home/howard/game-data/sc-clean/Starcraft/maps/(2)River Crossing.scm'
LIVE=/home/howard/scmdraft-maps/live-demo/live-demo.scm

# 1. args file: fixed lines then the credential read via redirection (not argv), one line
{
  printf '/v:192.168.1.99\n/u:howard\n/p:'
  tr -d '\n\r' < "$RDP_SECRET"
  printf '\n/cert:ignore\n/w:1920\n/h:1080\n+disp\n'
} > "$HERE/rdp-args"
chmod 600 "$HERE/rdp-args"
echo "rdp-args written ($(wc -l < "$HERE/rdp-args") lines, $(stat -c '%a' "$HERE/rdp-args"))"

# 2. target: ensure live-demo dir, reset live-demo.scm to pristine seed, record baseline
sshpass -f "$SSH_PASS" ssh -o StrictHostKeyChecking=no "$HOST" \
  "mkdir -p ~/scmdraft-maps/live-demo && cp '$SEED' '$LIVE' && stat -c '%s %Y' '$LIVE' && sha256sum '$LIVE'"

# 3. copy launch helper to target
sshpass -f "$SSH_PASS" scp -o StrictHostKeyChecking=no "$HERE/t0042-run.sh" "$HOST:/tmp/t0042-run.sh"

# 4. kill only SCMDraft processes this dispatch owns (none existed at dispatch start)
# Bracket trick on BOTH patterns: 'ScmDraft[ ]2' matches the wine-launched 'ScmDraft 2.exe'
# and 'start[.]exe' matches 'start.exe', but neither regex matches its own command line
# (which contains the literal '[ ]' / '[.]'), so pkill cannot kill its own ssh session. The
# unbracketed 'start.exe /exec' regex was what matched the bash -c cmdline and returned 255.
sshpass -f "$SSH_PASS" ssh -o StrictHostKeyChecking=no "$HOST" \
  "pkill -f 'ScmDraft[ ]2' || true; pkill -f 'start[.]exe /exec' || true; true"
echo "setup done"
