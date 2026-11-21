#!/bin/bash
# TASK-0042 contrast dispatch: hover probe. Each rows map paints one candidate terrain
# value per tile row; hover the centre of each row and capture the status bar, which names
# the tile SCMDraft reads at that tile (for example "Ice World\Snow"). One launch per era,
# 16 hovers each, screenshots fetched at the end.
set -u
cd /tmp/opencode/t0042
SSH="sshpass -f $HOME/AI/secrets/scm_draft_pass.md ssh -o StrictHostKeyChecking=no howard@192.168.1.99"
SCP="sshpass -f $HOME/AI/secrets/scm_draft_pass.md scp -o StrictHostKeyChecking=no"
shot() { # name
  $SSH "XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus gnome-screenshot-tool -f /tmp/$1.png >/dev/null 2>&1"
}
for era in 6 1; do
  echo "=== era $era ==="
  $SSH "pkill -f 'ScmDraft[ ]2' 2>/dev/null; sleep 2; bash /tmp/t0042-run.sh '$HOME/scmdraft-maps/probe/ts$era-rows.scm'; sleep 6"
  ./rdp-input rdp-args key 0x1C >/dev/null 2>&1
  sleep 6
  shot "rows$era-open"
  for r in $(seq 0 15); do
    y=$((107 + 32*r + 16))
    ./rdp-input rdp-args move 244 "$y" >/dev/null 2>&1
    sleep 1
    shot "rows$era-$r"
  done
  $SCP "howard@192.168.1.99:/tmp/rows$era-open.png" "/tmp/opencode/t0042/rows$era-open.png" 2>/dev/null
  $SCP "howard@192.168.1.99:/tmp/rows$era-0.png" "howard@192.168.1.99:/tmp/rows$era-1.png" "howard@192.168.1.99:/tmp/rows$era-2.png" "howard@192.168.1.99:/tmp/rows$era-3.png" "howard@192.168.1.99:/tmp/rows$era-4.png" "howard@192.168.1.99:/tmp/rows$era-5.png" "howard@192.168.1.99:/tmp/rows$era-6.png" "howard@192.168.1.99:/tmp/rows$era-7.png" "howard@192.168.1.99:/tmp/rows$era-8.png" "howard@192.168.1.99:/tmp/rows$era-9.png" "howard@192.168.1.99:/tmp/rows$era-10.png" "howard@192.168.1.99:/tmp/rows$era-11.png" "howard@192.168.1.99:/tmp/rows$era-12.png" "howard@192.168.1.99:/tmp/rows$era-13.png" "howard@192.168.1.99:/tmp/rows$era-14.png" "howard@192.168.1.99:/tmp/rows$era-15.png" /tmp/opencode/t0042/ 2>/dev/null
done
$SSH "rm -f /tmp/rows*.png; pkill -f 'ScmDraft[ ]2' 2>/dev/null; pgrep -af 'ScmDraft' || echo 'no scmdraft'"
