# Anime Hyprlock

An anime-themed lock screen for **Hyprland on Linux**. It uses Hyprlock for the password screen, Hypridle for automatic locking, and a GTK settings window for the background, colors, message, clock, date, and idle timeout. The background image is included in this repository.

## Install from GitHub

Clone this repository, then run the installer **as your regular user** from a terminal inside your Hyprland session:

```sh
git clone https://github.com/YOUR_USERNAME/anime-hyprlock.git
cd anime-hyprlock
sh install.sh
```

Replace `YOUR_USERNAME` with the GitHub account hosting the repository. The script asks for your administrator password through `sudo` only when it needs to install system packages. Enter it in your terminal, never in a GitHub issue or chat.

The installer supports Arch-based distributions (`pacman`), Fedora (`dnf`), and Debian/Ubuntu (`apt`) **when their enabled repositories provide Hyprlock and Hypridle**. It installs Python 3, GTK 3, and PyGObject as needed. On distributions without those packages, install them from your distribution's trusted repository, then rerun `sh install.sh`. A system Hyprlock package must provide `/etc/pam.d/hyprlock`; a copied binary alone cannot safely authenticate your password.

The installation has been tested on Arch Linux with Hyprland. The Fedora and Debian/Ubuntu package paths are included but have not been tested on those distributions.

The app requires a Hyprland desktop and a systemd user session for automatic locking. Manual locking works through the **Anime Sleep Lock** launcher. The installer detects both `hyprland.conf` and `hyprland.lua` and adds a startup command to whichever exists. If neither exists, it prints the command to add manually.

## Use

- **Anime Sleep Lock** in your app launcher opens the anime lock screen immediately.
- **Anime Lock Settings** lets you choose colors and an image, set a message, show or hide the clock and date, and enable locking after 1–240 minutes of inactivity. Click **Save lock screen** to apply changes.
- Unlock with your Linux account password. The app never stores it.

The generated files are placed under your XDG user directories, typically `~/.local/share/anime-hyprlock/`, `~/.local/share/applications/`, and `~/.config/hypr/`. The installer backs up any existing Hyprlock or Hypridle config before its first replacement. Re-running `sh install.sh` updates the installed app without duplicating the Hyprland startup command.

## Publish your own repository

Create an empty GitHub repository named `anime-hyprlock`, then from this folder run:

```sh
git init
git add .
git commit -m "Initial anime Hyprlock release"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/anime-hyprlock.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username. After the push, others can use the clone and install commands above.

## Remove

Remove the two app launcher entries, `~/.local/share/anime-hyprlock/`, `~/.config/anime-hyprlock/`, and `~/.config/systemd/user/anime-hypridle.service`. Remove the installer-added startup lines from your Hyprland config. Restore any `.before-anime-hyprlock.*` backup if you had a previous lock configuration. System packages remain installed until you remove them with your package manager.
