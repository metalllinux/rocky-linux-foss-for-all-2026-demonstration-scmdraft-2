#!/usr/bin/env bash
# Build the xfreerdp/rdp-pointer args file. Password is read from the secrets file
# into a shell variable, never placed on a command line and never printed.
set -euo pipefail
umask 077
P="$(cat "$HOME/AI/secrets/scm_draft_rdp_pass.md")"
cat > /tmp/opencode/t0042/rdp-args <<EOF
/v:192.168.1.99
/u:howard
/p:${P}
/cert:ignore
/w:1920
/h:1080
EOF
unset P
stat -c '%a %n' /tmp/opencode/t0042/rdp-args
