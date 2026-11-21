#!/usr/bin/env bash
# TASK-0042 L5 launch helper. Same seat0 Wayland export as t0042-run.sh, but the map argument is
# passed to wine64 VERBATIM as a Windows-style DOS path (C:\Maps\...) so SCMDraft 2's internal
# filename field and its "Save map" dialog hold native backslash separators instead of the Unix
# path with forward slashes that its own validation rejects with "Invalid character(s) in path".
# Inverse: rm -f /tmp/t0042-run-dos.sh (target).
set -u
map="$1"
export XDG_RUNTIME_DIR=/run/user/1000
export WAYLAND_DISPLAY=wayland-0
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export XDG_SESSION_TYPE=wayland
export WINEPREFIX="$HOME/.wine-scmdraft"
nohup wine64 "$HOME/scmdraft2/ScmDraft 2.exe" "$map" > /tmp/t0042-run.log 2>&1 &
echo "launched pid $! argv=$map"
