#!/usr/bin/env bash
# TASK-0042 live-demo launch helper variant: cd into the map's own directory and pass a BARE
# filename, so SCMDraft 2's "Save map" dialog filename field holds "live-demo.scm" with no path
# separators. The default launch (absolute path) makes that dialog reject the slashed relative
# path with "Invalid character(s) in path". Inverse: rm -f /tmp/t0042-run-cwd.sh (target).
set -u
mapdir="$1"; fname="$2"
export XDG_RUNTIME_DIR=/run/user/1000
export WAYLAND_DISPLAY=wayland-0
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export XDG_SESSION_TYPE=wayland
export WINEPREFIX="$HOME/.wine-scmdraft"
cd "$mapdir" || exit 1
nohup wine64 "$HOME/scmdraft2/ScmDraft 2.exe" "$fname" > /tmp/t0042-run.log 2>&1 &
echo "launched pid $! cwd=$(pwd) map=$fname"
