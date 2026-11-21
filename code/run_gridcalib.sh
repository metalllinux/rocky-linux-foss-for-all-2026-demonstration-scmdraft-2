#!/bin/bash
# TASK-0042 contrast dispatch, gridcalib capture loop.
# Launch each tileset calibration map in SCMDraft 2 on the target with the proven seat0
# Wayland export, dismiss the profile dialog with the Enter scancode, capture with
# gnome-screenshot-tool, fetch the PNG to the controller.
# pkill touches only ScmDraft processes (every one of them is started by this loop);
# the pre-existing wineserver is never targeted.
set -u
cd /tmp/opencode/t0042
SSH="sshpass -f $HOME/AI/secrets/scm_draft_pass.md ssh -o StrictHostKeyChecking=no howard@192.168.1.99"
SCP="sshpass -f $HOME/AI/secrets/scm_draft_pass.md scp -o StrictHostKeyChecking=no"
for e in 0 1 2 3 5 6 7; do
  map="$HOME/scmdraft-maps/probe/ts$e-cal.scm"
  echo "=== era $e ==="
  $SSH "pkill -f 'ScmDraft[ ]2' 2>/dev/null; sleep 2; bash /tmp/t0042-run.sh '$map'; sleep 6"
  ./rdp-input rdp-args key 0x1C >/dev/null 2>&1
  sleep 8
  $SSH "XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus gnome-screenshot-tool -f /tmp/ts$e-cal-shot.png >/dev/null 2>&1"
  $SCP "howard@192.168.1.99:/tmp/ts$e-cal-shot.png" "/tmp/opencode/t0042/ts$e-cal-shot.png" 2>/dev/null
done
echo "=== final target process state ==="
$SSH "pgrep -af 'ScmDraft' || echo 'no scmdraft'; echo wineserver:; pgrep -af wineserver || echo none"
