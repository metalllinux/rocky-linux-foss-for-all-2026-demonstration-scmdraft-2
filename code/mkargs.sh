#!/usr/bin/env bash
# Build the xfreerdp/rdp-pointer args file. Password is read from the secrets file
# into a shell variable, never placed on a command line and never printed.
set -euo pipefail
umask 077
# `## Security` finding 2, `Omega`'s `O1` ruling 2026-11-26: the server certificate is pinned by its
# SHA-256 fingerprint, read from the one file this repository publishes at code/rdp-cert-pin.txt. The
# verify-and-continue option this finding is about is not used here. Direct dial plus pin is the
# posture `O1` endorses as the fallback; the pinned-SSH-forward posture is in booth_loop.py.
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
cat > /tmp/opencode/t0042/rdp-args <<EOF
/v:192.168.1.99
/u:howard
/p:${P}
/cert:fingerprint:sha256:${RDP_PIN}
/w:1920
/h:1080
EOF
unset P
stat -c '%a %n' /tmp/opencode/t0042/rdp-args
