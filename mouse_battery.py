#!/usr/bin/env python3
import subprocess
import re
import time
import json
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

CACHE_FILE = Path.home() / ".cache/mouse_battery.json"

def run_solaar_show(log_to_console=False, log_to_file=False):
    stderr = subprocess.DEVNULL  # Default: discard stderr to /dev/null
    if log_to_console or log_to_file:
        stderr = subprocess.PIPE  # Capture stderr if user wants it

    try:
        result = subprocess.run(
            ["solaar", "show"],
            stdout=subprocess.PIPE,
            stderr=stderr,
            timeout=5,
            check=True
        )
        if result.stderr:
            logging.debug(f"Solaar stderr: {result.stderr.decode().strip()}")
        return result.stdout.decode()       # stdout returns bytes, .decode() turns it to a string
    except subprocess.CalledProcessError as e:
        if e.stderr:
            logging.debug(f"Solaar failed: {e.stderr.decode().strip()}")
        else:
            logging.debug(f"Solaar command failed with code {e.returncode}")
    except subprocess.TimeoutExpired:
        logging.warning("Solaar command timed out")
    except Exception as e:
        logging.debug(f"Solaar command error: {e}")
    return None

def parse_battery(solaar_output):
    if solaar_output:
        match = re.search(r'Battery:\s+(\d+)%', solaar_output)
        if match:
            return int(match.group(1))
    return None

def get_battery_with_retry(retries=2, delay=1.0, log_to_console=False, log_to_file=False):
    for attempt in range(1, retries + 1):
        logging.debug(f"Attempt {attempt}: reading battery from solaar...")
        output = run_solaar_show(log_to_console=log_to_console, log_to_file=log_to_file)
        battery = parse_battery(output)
        if battery is not None:
            logging.info(f"Battery found: {battery}%")
            return battery
        logging.debug(f"No battery info found. Retrying in {delay}s...")
        time.sleep(delay)
    logging.warning("All battery read attempts failed. Using cache if available.")
    return None

def load_last_known(ttl_hours):
    if not CACHE_FILE.exists():
        logging.debug("Cache file does not exist.")
        return None, None
    try:
        with open(CACHE_FILE, "r") as f:
            data = json.load(f)
            ts_str = data.get("timestamp")
            battery = data.get("battery")
            if ts_str:
                ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                if datetime.now() - ts <= timedelta(hours=ttl_hours):
                    logging.info(f"Loaded cached battery: {battery}% from {ts_str}")
                    return battery, ts_str
                logging.warning("Cache expired.")
    except Exception as e:
        logging.error(f"Failed to read cache: {e}")
    return None, None

def save_last_known(battery):
    try:
        with open(CACHE_FILE, "w") as f:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            json.dump({"battery": battery, "timestamp": ts}, f)
            logging.info(f"Saved battery {battery}% at {ts} to cache.")
    except Exception as e:
        logging.error(f"Failed to save to cache: {e}")

def human_readable_delta(ts_str):
    try:
        ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
        delta = datetime.now() - ts
        minutes = int(delta.total_seconds() // 60)
        hours = minutes // 60
        if minutes < 1:
            return "just now"
        elif minutes < 60:
            return f"{minutes} min ago"
        elif hours < 24:
            return f"{hours} hr ago"
        else:
            return ts.strftime("%b %d, %H:%M")
    except Exception as e:
        logging.debug(f"Failed to parse timestamp delta: {e}")
        return None

def format_battery(battery, timestamp=None, show_timestamp=False):
    if battery is None:
        return "\033[90m🖱 N/A\033[0m"  # Gray

    if battery >= 50:
        color = "\033[32m"
    elif battery >= 20:
        color = "\033[33m"
    else:
        color = "\033[31m"

    alert = " (Low Battery!)" if battery < 15 else ""
    time_info = f" ({human_readable_delta(timestamp)})" if show_timestamp and timestamp else ""

    return f"{color}🖱 {battery}%{alert}{time_info}\033[0m"

def send_notification(title, message):
    try:
        subprocess.run(["notify-send", "-u", "critical", title, message], check=False)
        logging.info(f"Sent notification: {title} - {message}")
    except Exception as e:
        logging.error(f"Failed to send notification: {e}")

def setup_logging(console_level=None, log_file=None):
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers.clear()

    if console_level:
        level = getattr(logging, console_level.upper(), logging.INFO)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        root_logger.addHandler(console_handler)
    else:
        root_logger.addHandler(logging.NullHandler())

    if log_file is not None:
        # Handle default path only if --log-file is passed without a value
        if isinstance(log_file, str):
            log_path = Path(log_file).expanduser().resolve()
        else:
            log_path = Path.home() / ".cache/mouse_battery.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
        root_logger.addHandler(file_handler)

def main():
    parser = argparse.ArgumentParser(description="Monitor Logitech mouse battery via Solaar.")
    parser.add_argument("--notify", action="store_true", help="Enable critical battery notifications")
    parser.add_argument("--ttl", type=int, default=24, help="Cache TTL in hours (default: 24)")
    parser.add_argument("--verbose", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Set log level")
    parser.add_argument(
        "--log-file",
        nargs="?",
        const=True,  # Will indicate flag was used without a path
        help="Enable logging to a file. Optionally provide a path (default: ~/.cache/mouse_battery.log)"
    )
    args = parser.parse_args()

    # Determine path only if --log-file flag was used
    log_file = None
    if args.log_file is not None:
        if isinstance(args.log_file, str):
            log_file = args.log_file
        else:
            log_file = str(Path.home() / ".cache/mouse_battery.log")

    setup_logging(args.verbose, log_file)

    setup_logging(args.verbose, args.log_file)

    log_to_console = args.verbose is not None
    log_to_file = args.log_file is not None
    battery = get_battery_with_retry(log_to_console=log_to_console, log_to_file=log_to_file)
    from_cache = False

    if battery is not None:
        save_last_known(battery)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        battery, timestamp = load_last_known(args.ttl)
        from_cache = True
        if timestamp is None:
            timestamp = "unknown"

    print(format_battery(battery, timestamp, show_timestamp=from_cache))

    if args.notify and battery is not None and battery < 10:
        send_notification("Mouse Battery Low", f"{battery}% remaining!")


if __name__ == "__main__":
    main()
