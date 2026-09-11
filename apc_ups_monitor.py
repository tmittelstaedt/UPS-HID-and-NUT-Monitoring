#!/usr/bin/env python3
"""
UPS Status Monitor for Ubuntu (GNOME)
- Runs /usr/sbin/apcaccess every minute
- Shows AppIndicator icon in GNOME top bar
- Changes icon color based on UPS status
- Sends desktop notification on status change
- Menu shows live UPS stats
- Instant refresh when menu is opened
- Flashes red icon when UPS is on battery
"""

import gi
gi.require_version('Gtk', '3.0')  # Force GTK 3 for AppIndicator
gi.require_version('AppIndicator3', '0.1')

from gi.repository import Gtk, AppIndicator3, GLib
import subprocess
import shlex
import signal
import sys

# Paths to icons
ICON_GREEN      = "/home/tedm/local-programs/icon_green.png"
ICON_RED        = "/home/tedm/local-programs/icon_red.png"
ICON_GREY       = "/home/tedm/local-programs/icon_grey.png"
ICON_RED_FLASH  = "/home/tedm/local-programs/icon_red_flash.png"

# Command to check UPS status
APCACCESS_CMD = "/usr/sbin/apcaccess"

class UPSMonitor:
    def __init__(self):
        self.indicator = AppIndicator3.Indicator.new(
            "ups-monitor",
            ICON_GREY,
            AppIndicator3.IndicatorCategory.SYSTEM_SERVICES
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        self.last_status = None
        self.last_stats = {}
        self.flash_timer_id = None
        self.flash_state = False  # For toggling red flash

        # Build initial menu
        self.build_menu()

        # Poll every 60 seconds
        GLib.timeout_add_seconds(60, self.check_status)
        self.check_status()  # initial check

    def send_notification(self, title, message):
        try:
            cmd = f'notify-send "{title}" "{message}"'
            subprocess.run(shlex.split(cmd), check=True)
        except Exception as e:
            print(f"Notification error: {e}", file=sys.stderr)

    def parse_apcaccess_output(self, output):
        """
        Parse apcaccess output to determine UPS status and stats.
        Returns: (status_color, stats_dict)
        """
        stats = {}
        status_color = "grey"

        for line in output.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip().upper()
            value = value.strip()

            if key == "STATUS":
                if value.upper() == "ONLINE":
                    status_color = "green"
                elif value.upper() in ("ONBATT", "LOWBATT"):
                    status_color = "red"
                else:
                    status_color = "grey"

            if key in ("MODEL", "LINEV", "LOADPCT", "BCHARGE", "BATTV", "TIMELEFT"):
                stats[key] = value

        return status_color, stats

    def build_menu(self):
        """Builds the AppIndicator menu with live UPS stats."""
        menu = Gtk.Menu()

        # Add UPS stats
        for key in ("MODEL", "LINEV", "LOADPCT", "BCHARGE", "BATTV", "TIMELEFT"):
            value = self.last_stats.get(key, "N/A")
            item = Gtk.MenuItem(label=f"{key}: {value}")
            item.set_sensitive(False)  # not clickable
            menu.append(item)

        menu.append(Gtk.SeparatorMenuItem())

        # Refresh option
        refresh_item = Gtk.MenuItem(label="Refresh Now")
        refresh_item.connect("activate", self.manual_refresh)
        menu.append(refresh_item)

        # Quit option
        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", self.quit)
        menu.append(quit_item)

        menu.show_all()
        self.indicator.set_menu(menu)

    def start_flashing(self):
        """Start flashing the red icon."""
        if self.flash_timer_id is None:
            self.flash_state = False
            self.flash_timer_id = GLib.timeout_add_seconds(1, self.flash_red_icon)

    def stop_flashing(self):
        """Stop flashing and reset icon."""
        if self.flash_timer_id is not None:
            GLib.source_remove(self.flash_timer_id)
            self.flash_timer_id = None
            self.flash_state = False

    def flash_red_icon(self):
        """Toggle between red and grey icon."""
        self.flash_state = not self.flash_state
        if self.flash_state:
            self.indicator.set_icon_full(ICON_RED, "UPS on battery or low")
        else:
            self.indicator.set_icon_full(ICON_RED_FLASH, "UPS on battery or low")
        return True  # keep flashing

    def check_status(self):
        """Runs apcaccess and updates icon/menu."""
        try:
            result = subprocess.run(
                [APCACCESS_CMD],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                status = "grey"
                stats = {}
            else:
                status, stats = self.parse_apcaccess_output(result.stdout)
        except Exception as e:
            print(f"Error running apcaccess: {e}", file=sys.stderr)
            status = "grey"
            stats = {}

        # Update icon and flashing if status changed
        if status != self.last_status:
            if status == "green":
                self.stop_flashing()
                self.indicator.set_icon_full(ICON_GREEN, "UPS online")
                self.send_notification("UPS Status", "UPS is online (green).")
            elif status == "red":
                self.start_flashing()
                self.send_notification("UPS Status", "UPS is on battery or low (red)!")
            else:
                self.stop_flashing()
                self.indicator.set_icon_full(ICON_GREY, "UPS status unknown")
                self.send_notification("UPS Status", "UPS status unknown or lost (grey).")
            self.last_status = status

        # Update stats and rebuild menu
        self.last_stats = stats
        self.build_menu()

        return True  # keep the timer running

    def manual_refresh(self, _):
        """Refresh immediately when menu item clicked."""
        self.check_status()

    def quit(self, _):
        self.stop_flashing()
        Gtk.main_quit()

def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # allow Ctrl+C
    UPSMonitor()
    Gtk.main()

if __name__ == "__main__":
    main()
