#!/bin/bash
# TASK-0042 contrast dispatch: hover probe, pass 2. Same as pass 1 with a settle sleep
# after each capture (pass 1 lost captures 2..15) and a wildcard fetch.
set -u
cd /tmp/opencode/t0042
SSH="sshpass -f $HOME/AI/secrets/scm_draft_pass.md ssh -o StrictHostKeyChecking=no howard@192.168.1.99"
SCP="sshpass -f $HOME/AI/secrets/scm_draft_pass.md scp -o StrictHostKeyChecking=no"
for era in 6 1; do
  echo "=== era $era ==="
  $SSH "pkill -f 'ScmDraft[ ]2' 2>/dev/null; sleep 2; bash /tmp/t0042-run.sh '$HOME/scmdraft-maps/probe/ts$era-rows.scm'; sleep 6"
  ./rdp-input rdp-args key 0x1C >/dev/null 2>&1
  sleep 6
  for r in $(seq 0 15); do
    y=$((107 + 32*r + 16))
    ./rdp-input rdp-args move 244 "$y" >/dev/null 2>&1
    sleep 1
    $SSH "XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus gnome-screenshot-tool -f /tmp/rows$era-$r.png >/dev/null 2>&1; sleep 2"
  done
  $SSH "ls -1 /tmp/rows$era-*.png | wc -l"
  $SCP "howard@192.168.1.99:/tmp/rows$era-*.png" /tmp/opencode/t0042/probe/ 2>&1 | tail -2
done
$SSH "rm -f /tmp/rows*.png; pkill -f 'ScmDraft[ ]2' 2>/dev/null; pgrep -af 'ScmDraft' || echo 'no scmdraft'"
