#!/bin/bash
# Control: launch the real protected River Crossing map, read-only, to validate the
# screenshot path renders a known-good map in this session.
export XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus XDG_SESSION_TYPE=wayland
export WINEPREFIX=$HOME/.wine-scmdraft
nohup wine64 "$HOME/scmdraft2/ScmDraft 2.exe" "$HOME/game-data/sc-clean/Starcraft/maps/(2)River Crossing.scm" > /tmp/hrc.log 2>&1 &
echo launched $!
