#!/usr/bin/env python3
import socket
import json
import time
import os
import sys
from datetime import datetime

# ===== CONFIGURATION =====
SERVER_IP = "192.168.1.50"   # IP of first machine running Monitor-UPS.ps1 --Server
SERVER_PORT = 50000          # TCP port
CHECK_INTERVAL = 30          # Seconds between checks
SHUTDOWN_DELAY = 300         # Seconds to wait before shutdown after going on battery
ENABLE_LOG = True            # Set to False to disable logging
LOG_FILE = "/var/log/ups-shutdown-monitor.log"
# =========================

shutdown_pending = False
shutdown_start_time = None

def log_message(message):
    """Write a timestamped message to stdout and optional log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} {message}"
    print(log_entry)
    if ENABLE_LOG:
        try:
            os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
            with open(LOG_FILE, "a") as f:
                f.write(log_entry + "\n")
        except PermissionError:
            print(f"[WARN] Cannot write to log file {LOG_FILE} (permission denied)")

def get_ups_status(ip, port):
    """Connect to UPS server and retrieve JSON status."""
    try:
        with socket.create_connection((ip, port), timeout=5) as sock:
            data = sock.recv(4096).decode("utf-8").strip()
            if data:
                return json.loads(data)
    except (socket.error, json.JSONDecodeError) as e:
        log_message(f"Failed to get UPS status: {e}")
    return None

def shutdown_system():
    """Shutdown the Ubuntu system."""
    log_message("Shutting down system now...")
    os.system("sudo shutdown -h now")

def main():
    global shutdown_pending, shutdown_start_time

    log_message(f"Shutdown Monitor started. Monitoring UPS at {SERVER_IP}:{SERVER_PORT}")

    while True:
        status_obj = get_ups_status(SERVER_IP, SERVER_PORT)

        if status_obj:
            current_status = status_obj.get("Status", "Unknown")
            battery = status_obj.get("BatteryPercent", "Unknown")
            timestamp = status_obj.get("TimestampUTC", "")

            log_message(f"[{timestamp}] UPS Status: {current_status}, Battery: {battery}%")

            if current_status == "On Battery":
                if not shutdown_pending:
                    shutdown_pending = True
                    shutdown_start_time = time.time()
                    log_message(f"Power failure detected. Shutdown scheduled in {SHUTDOWN_DELAY} seconds unless power returns.")
                else:
                    elapsed = time.time() - shutdown_start_time
                    if elapsed >= SHUTDOWN_DELAY:
                        log_message(f"AC power still offline after {SHUTDOWN_DELAY} seconds. Initiating shutdown.")
                        shutdown_system()
                        break  # Exit after shutdown command
            elif current_status == "Online":
                if shutdown_pending:
                    log_message("AC power restored. Shutdown canceled.")
                shutdown_pending = False
                shutdown_start_time = None
            else:
                log_message("UPS status unknown. No shutdown action taken.")
        else:
            log_message("No UPS data received from server.")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_message("Shutdown Monitor stopped by user.")
        sys.exit(0)
