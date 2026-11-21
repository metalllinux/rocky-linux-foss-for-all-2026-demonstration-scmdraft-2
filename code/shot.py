#!/usr/bin/env python3
"""GNOME screenshot via the org.gnome.Screenshot service, activating it first."""
import shutil
import sys
import time
import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib

out = sys.argv[1]
bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
dbus = Gio.DBusProxy.new_sync(bus, Gio.DBusProxyFlags.NONE, None,
                              "org.freedesktop.DBus", "/org/freedesktop/DBus",
                              "org.freedesktop.DBus", None)
dbus.call_sync("RequestName", GLib.Variant("(su)", ("org.gnome.Screenshot", 4)),
               Gio.DBusCallFlags.NONE, -1, None)
shot = None
for _ in range(40):
    shot = Gio.DBusProxy.new_sync(bus, Gio.DBusProxyFlags.NONE, None,
                                  "org.gnome.Screenshot", "/org/gnome/Screenshot",
                                  "org.gnome.Screenshot", None)
    if shot.get_name_owner() is not None:
        break
    time.sleep(0.5)
else:
    raise SystemExit("org.gnome.Screenshot never became available")
res = shot.call_sync("Screenshot", GLib.Variant("(bb)", (False, False)),
                     Gio.DBusCallFlags.NONE, -1, None)
path = res.unpack()[0]
shutil.copy(path, out)
print("saved", out, "from", path)
