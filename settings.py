#!/usr/bin/env python3
"""Graphical settings for the Anime Hyprlock screen."""
import json
import os
import re
import subprocess
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

HOME = Path.home()
APP = Path(__file__).resolve().parent
CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", HOME / ".config")) / "hypr/hyprlock.conf"
IDLE_CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", HOME / ".config")) / "hypr/hypridle.conf"
SETTINGS = Path(os.environ.get("XDG_CONFIG_HOME", HOME / ".config")) / "anime-hyprlock/settings.json"
DEFAULT = {"theme": "Sakura", "message": "Sweet dreams", "clock": True,
           "date": True, "blur": False, "wallpaper": str(APP / "anime-night.png"),
           "auto_lock": True, "idle_minutes": 10}
THEMES = {
    "Sakura": ("rgb(fff2fb)", "rgb(f1b8dc)", "rgb(bc7fba)"),
    "Moonlight": ("rgb(eeefff)", "rgb(aacbff)", "rgb(7186c4)"),
    "Warm lantern": ("rgb(fff4e4)", "rgb(ffcea3)", "rgb(c7859b)"),
}


def load():
    try:
        return {**DEFAULT, **json.loads(SETTINGS.read_text(encoding="utf-8"))}
    except (OSError, ValueError, TypeError):
        return DEFAULT.copy()


def safe_message(value):
    return re.sub(r"[\r\n#{}$<>]", "", value).strip()[:60] or "Sweet dreams"


def render(data):
    theme = THEMES.get(data["theme"], THEMES["Sakura"])
    wallpaper = Path(data["wallpaper"]).expanduser()
    if not wallpaper.is_file():
        raise ValueError("The selected background image does not exist.")
    # Hyprlock config uses plain paths; reject characters with special meaning.
    if any(c in str(wallpaper) for c in "\n\r#{}$"):
        raise ValueError("The background path contains unsupported characters.")
    lines = [
        "# Anime Hyprlock screen. Edit with the Anime Lock Settings launcher.",
        "general {",
        "    fractional_scaling = 2",
        "    immediate_render = true",
        "    hide_cursor = true",
        "}", "",
        "background {",
        "    monitor =",
        f"    path = {wallpaper}",
        "    color = rgb(0b1028)",
        f"    blur_passes = {2 if data['blur'] else 0}",
        "    blur_size = 3",
        "    brightness = 0.78",
        "}", "",
    ]
    if data["clock"]:
        lines += ["label {", "    monitor =",
                  "    text = cmd[update:1000] date +\"%H:%M\"",
                  f"    color = {theme[0]}", "    font_size = 104",
                  "    font_family = Adwaita Sans", "    position = 0, 190",
                  "    halign = center", "    valign = center", "}", ""]
    if data["date"]:
        lines += ["label {", "    monitor =",
                  "    text = cmd[update:60000] date +\"%A, %B %d\"",
                  f"    color = {theme[1]}", "    font_size = 22",
                  "    font_family = Adwaita Sans", "    position = 0, 110",
                  "    halign = center", "    valign = center", "}", ""]
    lines += ["label {", "    monitor =", f"    text = {safe_message(data['message'])}",
              f"    color = {theme[1]}", "    font_size = 26",
              "    font_family = Adwaita Sans", "    position = 0, 25",
              "    halign = center", "    valign = center", "}", "",
              "input-field {", "    monitor =", "    size = 290, 58",
              "    outline_thickness = 3", "    dots_size = 0.25",
              "    dots_spacing = 0.6", "    dots_center = true",
              "    dots_rounding = -1", "    rounding = 22",
              f"    outer_color = {theme[2]}", "    inner_color = rgba(9, 13, 31, 0.78)",
              f"    font_color = {theme[0]}",
              "    placeholder_text = <i>Password to unlock</i>",
              "    fade_on_empty = false", "    position = 0, -80",
              "    halign = center", "    valign = center", "}", ""]
    return "\n".join(lines)


def save(data):
    config = render(data)
    minutes = int(data["idle_minutes"])
    if not 1 <= minutes <= 240:
        raise ValueError("Choose an automatic lock time from 1 to 240 minutes.")
    lock_command = f"hyprlock --config {CONFIG}"
    idle_config = "\n".join([
        "# Managed by Anime Lock Settings.",
        "general {",
        f"    lock_cmd = {lock_command}",
        f"    before_sleep_cmd = {lock_command}",
        "}", "",
        "listener {",
        f"    timeout = {minutes * 60}",
        f"    on-timeout = {lock_command}",
        "}", "",
    ])
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(config, encoding="utf-8")
    IDLE_CONFIG.write_text(idle_config, encoding="utf-8")
    SETTINGS.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


class Window(Gtk.Window):
    def __init__(self):
        super().__init__(title="Anime Lock Settings")
        self.data = load()
        self.set_default_size(520, 520)
        self.set_border_width(20)
        self.connect("destroy", Gtk.main_quit)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=13)
        self.add(box)
        title = Gtk.Label()
        title.set_markup("<span size='x-large' weight='bold'>Anime Lock Settings</span>")
        title.set_xalign(0)
        box.pack_start(title, False, False, 0)
        grid = Gtk.Grid(column_spacing=15, row_spacing=14)
        box.pack_start(grid, False, False, 0)
        def row(text, control, i):
            label = Gtk.Label(label=text)
            label.set_xalign(0)
            grid.attach(label, 0, i, 1, 1)
            grid.attach(control, 1, i, 1, 1)
        self.theme = Gtk.ComboBoxText()
        for name in THEMES:
            self.theme.append_text(name)
        self.theme.set_active(list(THEMES).index(self.data["theme"]) if self.data["theme"] in THEMES else 0)
        row("Colors", self.theme, 0)
        self.message = Gtk.Entry()
        self.message.set_text(self.data["message"])
        self.message.set_max_length(60)
        row("Message", self.message, 1)
        self.wallpaper = Gtk.FileChooserButton(title="Choose lock screen background")
        self.wallpaper.set_action(Gtk.FileChooserAction.OPEN)
        if Path(self.data["wallpaper"]).is_file():
            self.wallpaper.set_filename(self.data["wallpaper"])
        row("Background", self.wallpaper, 2)
        self.clock = Gtk.CheckButton(label="Show clock")
        self.clock.set_active(self.data["clock"])
        grid.attach(self.clock, 1, 3, 1, 1)
        self.date = Gtk.CheckButton(label="Show date")
        self.date.set_active(self.data["date"])
        grid.attach(self.date, 1, 4, 1, 1)
        self.blur = Gtk.CheckButton(label="Blur background")
        self.blur.set_active(self.data["blur"])
        grid.attach(self.blur, 1, 5, 1, 1)
        idle_frame = Gtk.Frame(label="Automatic lock")
        box.pack_start(idle_frame, False, False, 4)
        idle_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=9)
        idle_box.set_border_width(12)
        idle_frame.add(idle_box)
        self.auto_lock = Gtk.CheckButton(label="Lock after inactivity")
        self.auto_lock.set_active(bool(self.data["auto_lock"]))
        idle_box.pack_start(self.auto_lock, False, False, 0)
        minutes_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        idle_box.pack_start(minutes_box, False, False, 0)
        minutes_box.pack_start(Gtk.Label(label="Minutes of inactivity"), False, False, 0)
        adjustment = Gtk.Adjustment(value=int(self.data["idle_minutes"]),
                                    lower=1, upper=240, step_increment=1,
                                    page_increment=5, page_size=0)
        self.idle_minutes = Gtk.SpinButton(adjustment=adjustment, climb_rate=1, digits=0)
        minutes_box.pack_start(self.idle_minutes, False, False, 0)
        minutes_box.set_sensitive(self.auto_lock.get_active())
        self.auto_lock.connect("toggled", lambda button: minutes_box.set_sensitive(button.get_active()))
        note = Gtk.Label(label="The lock uses your Linux account password. Save before locking.")
        note.set_xalign(0)
        box.pack_start(note, False, False, 0)
        button = Gtk.Button(label="Save lock screen")
        button.get_style_context().add_class("suggested-action")
        button.connect("clicked", self.on_save)
        box.pack_end(button, False, False, 0)
        self.show_all()

    def on_save(self, *_):
        data = {"theme": self.theme.get_active_text(),
                "message": self.message.get_text(), "clock": self.clock.get_active(),
                "date": self.date.get_active(), "blur": self.blur.get_active(),
                "wallpaper": self.wallpaper.get_filename() or self.data["wallpaper"],
                "auto_lock": self.auto_lock.get_active(),
                "idle_minutes": self.idle_minutes.get_value_as_int()}
        try:
            save(data)
            result = subprocess.run(["python3", str(APP / "idle.py"), "restart"],
                                    capture_output=True, text=True, timeout=8)
            if result.returncode:
                raise OSError(result.stderr.strip() or "Could not start the idle timer.")
            msg = (Gtk.MessageType.INFO, "Lock settings saved", "The automatic lock timer is updated.")
        except (OSError, ValueError) as e:
            msg = (Gtk.MessageType.ERROR, "Could not save", str(e))
        dialog = Gtk.MessageDialog(transient_for=self, modal=True, message_type=msg[0],
                                   buttons=Gtk.ButtonsType.OK, text=msg[1])
        dialog.format_secondary_text(msg[2])
        dialog.run()
        dialog.destroy()


if __name__ == "__main__":
    if not Gtk.init_check()[0]:
        raise SystemExit("A graphical desktop session is required.")
    Window()
    Gtk.main()
