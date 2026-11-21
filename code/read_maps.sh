#!/bin/bash
# Read harvB, harvC, harvD in order: kill prior SCMDraft (not the pre-existing wineserver),
# launch the map under the proven seat0 export, dismiss the profile with rdp-input Enter,
# settle, capture with the restored screenshot path, and copy the PNG back to the controller.
set -u
cd /tmp/opencode/t0042
SSH="sshpass -f $HOME/AI/secrets/scm_draft_pass.md ssh -o StrictHostKeyChecking=no howard@192.168.1.99"
SCP="sshpass -f $HOME/AI/secrets/scm_draft_pass.md scp -o StrictHostKeyChecking=no"
for v in B C D; do
  echo "=== harv$v ==="
  $SSH "pkill -f 'ScmDraft[ ]2' 2>/dev/null; sleep 2; bash /tmp/run_viewer.sh $v; sleep 5"
  ./rdp-input rdp-args key 0x1C >/dev/null 2>&1
  sleep 7
  $SSH "XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus gnome-screenshot-tool -f /tmp/harv$v-shot.png >/dev/null 2>&1"
  $SCP "howard@192.168.1.99:/tmp/harv$v-shot.png" "/tmp/opencode/t0042/harv$v-shot.png" 2>/dev/null
done
echo "=== final target process state ==="
$SSH "pgrep -af 'ScmDraft' || echo 'no scmdraft'; echo wineserver:; pgrep -af wineserver || echo none"
