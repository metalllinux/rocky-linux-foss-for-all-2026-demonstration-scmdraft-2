#!/usr/bin/env bash
# Screenshot helper: capture the target's live Wayland session via the GNOME Shell
# Screenshot D-Bus interface (TASK-0041 item 1 mechanism) and fetch it to the controller.
# Usage: shot.sh <remote-name> <local-name>
set -euo pipefail
REM="$1"; LOC="$2"
PASSFILE="$HOME/AI/secrets/scm_draft_pass.md"
sshpass -f "$PASSFILE" ssh -o StrictHostKeyChecking=no howard@192.168.1.99 \
  "export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus; python3 - <<'PY'
from gi.repository import Gio, GLib
bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
name = Gio.DBusProxy.new_for_bus_sync(Gio.BusType.SESSION, Gio.DBusProxyFlags.NONE, None,
    'org.gnome.ScreenSaver', '/org/gnome/ScreenSaver', 'org.gnome.ScreenSaver', None)
# Request the org.gnome.Screenshot bus name so GNOME 49 allows the call.
owner = Gio.DBusProxy.new_for_bus_sync(Gio.BusType.SESSION, Gio.DBusProxyFlags.NONE, None,
    'org.freedesktop.DBus', '/org/freedesktop/DBus', 'org.freedesktop.DBus', None)
owner.call_sync('RequestName', GLib.Variant('(su)', ('org.gnome.Screenshot', 4)),
    Gio.DBusCallFlags.NONE, -1, None)
scr = Gio.DBusProxy.new_for_bus_sync(Gio.BusType.SESSION, Gio.DBusProxyFlags.NONE, None,
    'org.gnome.Shell', '/org/gnome/Shell/Screenshot', 'org.gnome.Shell.Screenshot', None)
res = scr.call_sync('Screenshot', GLib.Variant('(bbs)', (False, False, '/tmp/${REM}')),
    Gio.DBusCallFlags.NONE, -1, None)
print('screenshot:', res)
PY"
sshpass -f "$PASSFILE" scp -o StrictHostKeyChecking=no \
  howard@192.168.1.99:/tmp/${REM} "$HOME/AI/demo-evidence/${LOC}"
ls -la "$HOME/AI/demo-evidence/${LOC}"
