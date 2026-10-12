#!/usr/bin/env python3
"""Apply the configured Hypridle timer through a persistent user service."""
import json
import os
import subprocess
import sys
from pathlib import Path

SETTINGS = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "anime-hyprlock/settings.json"
SERVICE = "anime-hypridle.service"


def run(*args):
    return subprocess.run(["systemctl", "--user", *args], text=True,
                          capture_output=True, timeout=10)


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "start"
    if action not in ("start", "restart"):
        print("Usage: idle.py [start|restart]", file=sys.stderr)
        return 2
    try:
        enabled = bool(json.loads(SETTINGS.read_text(encoding="utf-8")).get("auto_lock"))
    except (OSError, ValueError) as error:
        print(f"Could not read automatic lock settings: {error}", file=sys.stderr)
        return 1
    result = run(action if enabled else "stop", SERVICE)
    if result.returncode:
        print(result.stderr.strip() or "Could not update the idle service.", file=sys.stderr)
        return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
