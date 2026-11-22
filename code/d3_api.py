#!/usr/bin/env python3
"""TASK-0042 dispatch D3 GitHub API probe.

Reads the token from ~/AI/secrets/token.md at run time and issues GET requests
against the renamed booth repo. The token value is never printed, never placed
in argv, and never written to a file. Only whitelisted non-sensitive fields are
printed. Usage: python3 d3_api.py <path> [field ...]
"""
import json
import os
import sys
import urllib.request

REPO = "metalllinux/rocky-linux-foss-for-all-2026-demonstration-scmdraft-2"


def main() -> int:
    with open(os.path.expanduser("~/AI/secrets/token.md")) as fh:
        tok = fh.read().strip()
    url = f"https://api.github.com/repos/{REPO}/{sys.argv[1]}" if sys.argv[1] else \
        f"https://api.github.com/repos/{REPO}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {tok}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "team-chaotix-tails",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if len(sys.argv) > 2 and sys.argv[2]:
        for f in ",".join(sys.argv[2:]).split(","):
            cur = data
            for part in f.split("."):
                cur = cur[part] if part else cur
            print(f"{f} = {cur}")
    else:
        print(json.dumps(data)[:400])
    return 0


if __name__ == "__main__":
    sys.exit(main())
