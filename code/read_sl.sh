#!/bin/bash
# Read StormLib-written maps: kill only ScmDraft processes this loop started, launch under the
# proven seat0 export, dismiss the profile with rdp-input Enter, capture with gnome-screenshot-tool.
set -u
cd /tmp/opencode/t0042
SSH="sshpass -f $HOME/AI/secrets/scm_draft_pass.md ssh -o StrictHostKeyChecking=no howard@192.168.1.99"
SCP="sshpass -f $HOME/AI/secrets/scm_draft_pass.md scp -o StrictHostKeyChecking=no"
for v in rc A B C; do
  if [ "$v" = rc ]; then map="$HOME/game-data/sc-clean/Starcraft/maps/(2)River Crossing.scm"; else map="$HOME/scmdraft-maps/probe/sl$v.scm"; fi
  echo "=== $v ==="
  $SSH "pkill -f 'ScmDraft[ ]2' 2>/dev/null; sleep 2; bash /tmp/run_sl.sh '$map'; sleep 5"
  ./rdp-input rdp-args key 0x1C >/dev/null 2>&1
  sleep 7
  $SSH "XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus gnome-screenshot-tool -f /tmp/sl$v-shot.png >/dev/null 2>&1"
  $SCP "howard@192.168.1.99:/tmp/sl$v-shot.png" "/tmp/opencode/t0042/sl$v-shot.png" 2>/dev/null
done
echo "=== final target process state ==="
$SSH "pgrep -af 'ScmDraft' || echo 'no scmdraft'; echo wineserver:; pgrep -af wineserver || echo none; ls -la ~/scmdraft-maps/probe/sl*.scm"
