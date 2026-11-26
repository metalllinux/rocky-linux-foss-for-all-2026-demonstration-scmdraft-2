#!/usr/bin/env bash
# Args file for xfreerdp: every argument must live in the file because /args-from
# cannot be combined with any other command-line argument in FreeRDP 3.32.
set -euo pipefail
umask 077
# `## Security` finding 2, `Omega`'s `O1` ruling 2026-11-26: pinned certificate fingerprint, read from
# the one file this repository publishes at code/rdp-cert-pin.txt. See the note in mkargs.sh.
RDP_PIN="${CHAOTIX_T0042_RDP_CERT_PIN:-}"
if [ -z "$RDP_PIN" ]; then
  for _pin in "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/rdp-cert-pin.txt" \
              /home/howard/AI/booth-2026/t0042/rdp-cert-pin.txt; do
    if [ -f "$_pin" ]; then RDP_PIN="$(head -n 1 "$_pin")"; break; fi
  done
fi
[ "${#RDP_PIN}" -eq 64 ] \
  || { echo "no 64-hex RDP certificate pin found: refusing to build args without one" >&2; exit 1; }
P="$(cat "$HOME/AI/secrets/scm_draft_rdp_pass.md")"
cat > /tmp/opencode/t0042/rdp-args-kbd <<EOF
/v:192.168.1.99
/u:howard
/p:${P}
/cert:fingerprint:sha256:${RDP_PIN}
/w:1920
/h:1080
/kbd:pipe:/tmp/opencode/t0042/rdp-kbd
EOF
unset P
stat -c '%a %n' /tmp/opencode/t0042/rdp-args-kbd
