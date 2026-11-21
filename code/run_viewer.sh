#!/bin/bash
# Launch SCMDraft 2 on the target with one harvested test map, session-attached.
v="$1"
export XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus XDG_SESSION_TYPE=wayland
export WINEPREFIX=$HOME/.wine-scmdraft
nohup wine64 "$HOME/scmdraft2/ScmDraft 2.exe" "$HOME/scmdraft-maps/probe/harv$v.scm" > "/tmp/h$v.log" 2>&1 &
echo "launched pid $!"
