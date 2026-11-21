#!/usr/bin/env bash
# Args file for xfreerdp: every argument must live in the file because /args-from
# cannot be combined with any other command-line argument in FreeRDP 3.32.
set -euo pipefail
umask 077
P="$(cat "$HOME/AI/secrets/scm_draft_rdp_pass.md")"
cat > /tmp/opencode/t0042/rdp-args-kbd <<EOF
/v:192.168.1.99
/u:howard
/p:${P}
/cert:ignore
/w:1920
/h:1080
/kbd:pipe:/tmp/opencode/t0042/rdp-kbd
EOF
unset P
stat -c '%a %n' /tmp/opencode/t0042/rdp-args-kbd
