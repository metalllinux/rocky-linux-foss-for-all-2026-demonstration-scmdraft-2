#!/usr/bin/env bash
# TASK-0042 dispatch 3 launch helper. Exports the seat0 Wayland session environment into the
# SSH launch context (the finding that broke the nodrv_CreateWindow wall), then launches
# SCMDraft 2 with the given map under the ~/.wine-scmdraft prefix in the background.
# Inverse: rm -f /tmp/t0042-run.sh (target).
set -u
map="$1"
export XDG_RUNTIME_DIR=/run/user/1000
export WAYLAND_DISPLAY=wayland-0
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export XDG_SESSION_TYPE=wayland
export WINEPREFIX="$HOME/.wine-scmdraft"
nohup wine64 "$HOME/scmdraft2/ScmDraft 2.exe" "$map" > "/tmp/t0042-run.log" 2>&1 &
echo "launched pid $! map=$map"
