#!/bin/sh
# Install Anime Hyprlock for the current user. System packages are installed
# through the distribution package manager; app files stay in the user home.
set -eu

die() { printf 'Error: %s\n' "$*" >&2; exit 1; }
note() { printf '%s\n' "$*"; }

[ "$(id -u)" -ne 0 ] || die "Run this as your regular user, not as root. The script asks for sudo only for packages."
[ "$(uname -s)" = Linux ] || die "This installer supports Linux only."
[ -f /etc/os-release ] || die "Cannot identify this Linux distribution."

SRC=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
[ -f "$SRC/anime-night.png" ] || die "anime-night.png is missing from the cloned project."
[ -f "$SRC/settings.py" ] || die "settings.py is missing from the cloned project."
[ -f "$SRC/idle.py" ] || die "idle.py is missing from the cloned project."

# shellcheck disable=SC1091
. /etc/os-release
DISTRO="${ID:-} ${ID_LIKE:-}"

have_dependencies() {
    command -v hyprlock >/dev/null 2>&1 &&
    command -v hypridle >/dev/null 2>&1 &&
    command -v python3 >/dev/null 2>&1 &&
    python3 -c 'import gi; gi.require_version("Gtk", "3.0"); from gi.repository import Gtk' >/dev/null 2>&1
}

if ! have_dependencies; then
    command -v sudo >/dev/null 2>&1 || die "sudo is needed to install system packages. Install hyprlock, hypridle, Python 3, GTK 3, and PyGObject manually."
    case " $DISTRO " in
        *arch*|*manjaro*|*endeavouros*|*cachyos*)
            command -v pacman >/dev/null 2>&1 || die "pacman was not found."
            note "Installing dependencies with pacman..."
            sudo pacman -S --needed hyprlock hypridle python python-gobject gtk3
            ;;
        *fedora*|*rhel*)
            command -v dnf >/dev/null 2>&1 || die "dnf was not found."
            note "Installing dependencies with dnf..."
            sudo dnf install -y hyprlock hypridle python3 python3-gobject gtk3
            ;;
        *debian*|*ubuntu*)
            command -v apt-get >/dev/null 2>&1 || die "apt-get was not found."
            note "Installing dependencies with apt..."
            sudo apt-get update
            sudo apt-get install -y hyprlock hypridle python3 python3-gi gir1.2-gtk-3.0
            ;;
        *)
            die "Unsupported distribution ($DISTRO). Install hyprlock, hypridle, Python 3, GTK 3, and PyGObject, then rerun this script."
            ;;
    esac
fi

have_dependencies || die "Dependencies are still missing. Your distribution may not provide Hyprlock or Hypridle in its enabled repositories."
command -v hyprctl >/dev/null 2>&1 || die "Hyprland is required. Install and configure Hyprland before using this lock screen."
[ -f /etc/pam.d/hyprlock ] || die "The system Hyprlock PAM file is missing. Install Hyprlock through your distribution package manager; a copied binary is unsafe."

DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
DEST="$DATA/anime-hyprlock"
APPS="$DATA/applications"
HYPR="$CONFIG_HOME/hypr"
SYSTEMD="$CONFIG_HOME/systemd/user"
python3 - "$DEST" "$HYPR" <<'PY'
import sys
if any(any(char.isspace() for char in path) for path in sys.argv[1:]):
    raise SystemExit("Home or XDG paths containing whitespace are not supported by the Hyprlock configuration generator.")
PY
mkdir -p "$DEST" "$APPS" "$HYPR" "$SYSTEMD"

# Preserve an existing, unrelated lock/idle configuration before replacing it.
python3 - "$HYPR" <<'PY'
from datetime import datetime
from pathlib import Path
from shutil import copy2
import sys
directory = Path(sys.argv[1])
for name, marker in (("hyprlock.conf", "# Anime Hyprlock screen."),
                     ("hypridle.conf", "# Managed by Anime Lock Settings.")):
    path = directory / name
    if path.exists() and not path.read_text(encoding="utf-8").startswith(marker):
        backup = path.with_name(path.name + ".before-anime-hyprlock." + datetime.now().strftime("%Y%m%d-%H%M%S"))
        copy2(path, backup)
        print(f"Backed up {path} to {backup}")
PY

cp "$SRC/settings.py" "$SRC/idle.py" "$SRC/anime-night.png" "$DEST/"
chmod 755 "$DEST/settings.py" "$DEST/idle.py"

cat > "$APPS/anime-sleep-lock.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Anime Sleep Lock
Comment=Lock the screen with an anime night scene
Exec=hyprlock --config "$HYPR/hyprlock.conf"
TryExec=hyprlock
Terminal=false
Categories=System;Security;
Keywords=lock;sleep;anime;
EOF
cat > "$APPS/anime-lock-settings.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Anime Lock Settings
Comment=Configure the anime Hyprlock screen
Exec=/usr/bin/env python3 "$DEST/settings.py"
TryExec=/usr/bin/python3
Terminal=false
Categories=Settings;
EOF

python3 - "$DEST/settings.py" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("anime_settings", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.save(module.load())
PY

cat > "$SYSTEMD/anime-hypridle.service" <<EOF
[Unit]
Description=Anime Hyprlock automatic lock timer

[Service]
Type=simple
ExecStart=/usr/bin/env hypridle --config "$HYPR/hypridle.conf"
Restart=on-failure
RestartSec=2
EOF

# Hyprland has both traditional .conf and newer Lua configurations.
python3 - "$HYPR" "$DEST/idle.py" <<'PY'
from datetime import datetime
from pathlib import Path
from shutil import copy2
import sys
directory, idle = Path(sys.argv[1]), Path(sys.argv[2])
marker = "# Anime Hyprlock automatic lock startup"
found = False
for name in ("hyprland.conf", "hyprland.lua"):
    path = directory / name
    if not path.exists():
        continue
    found = True
    text = path.read_text(encoding="utf-8")
    if marker in text or str(idle) in text:
        continue
    backup = path.with_name(path.name + ".before-anime-hyprlock." + datetime.now().strftime("%Y%m%d-%H%M%S"))
    copy2(path, backup)
    if name.endswith(".lua"):
        addition = f'\n-- Anime Hyprlock automatic lock startup\nhl.on("hyprland.start", function()\n    hl.exec_cmd("python3 {idle} start")\nend)\n'
    else:
        addition = f'\n{marker}\nexec-once = python3 {idle} start\n'
    path.write_text(text.rstrip() + "\n" + addition, encoding="utf-8")
    print(f"Added startup command to {path} (backup: {backup})")
if not found:
    print("No Hyprland config was found. Add 'python3 " + str(idle) + " start' to your Hyprland startup commands.")
PY

if command -v systemctl >/dev/null 2>&1 && systemctl --user daemon-reload >/dev/null 2>&1; then
    if [ -n "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]; then
        python3 "$DEST/idle.py" restart || note "Idle timer could not start now. It will try again at your next Hyprland login."
    fi
else
    note "Automatic locking needs a running systemd user session. The manual lock launcher is installed."
fi

note "Installed. Search your app launcher for 'Anime Sleep Lock' and 'Anime Lock Settings'."
