#!/usr/bin/env python3
"""Read-only serial probe for a Taishan RK3566 Linux board.

Examples:
    python3 scripts/probe_uart.py --text
    python3 scripts/probe_uart.py --device /dev/ttyS7 --baudrate 115200 --json

The default mode never transmits bytes. It only discovers candidate devices,
opens them, and listens for a short window. Transmission is deliberately not
implemented in this first safe probe so that it cannot trigger a controller.
Exit codes: 0 = at least one port opened, 1 = no port opened, 2 = bad args.
"""

from __future__ import print_function

import argparse
import glob
import json
import os
import stat
import sys
import time


PROBE_VERSION = "0.1.0"


def parse_args():
    parser = argparse.ArgumentParser(description="Probe UART devices without transmitting data.")
    parser.add_argument("--device", action="append", help="Device path; repeat for multiple devices. Default: auto.")
    parser.add_argument("--baudrate", type=int, default=115200, help="Baudrate candidate (default: 115200).")
    parser.add_argument("--read-seconds", type=float, default=1.0, help="Listen window in seconds (default: 1.0).")
    parser.add_argument("--json", action="store_true", help="Print JSON output; this is already the default.")
    parser.add_argument("--text", action="store_true", help="Print a human-readable summary instead of JSON.")
    return parser.parse_args()


def serial_import():
    try:
        import serial  # pylint: disable=import-outside-toplevel
        return serial, None
    except Exception as exc:
        return None, "{}: {}".format(type(exc).__name__, exc)


def discover_devices(explicit):
    if explicit:
        return explicit
    patterns = ("/dev/ttyS*", "/dev/ttyUSB*", "/dev/ttyACM*", "/dev/serial/by-id/*")
    devices = []
    for pattern in patterns:
        devices.extend(glob.glob(pattern))
    return sorted(set(devices))


def device_kind(path):
    try:
        mode = os.stat(path).st_mode
        if stat.S_ISCHR(mode):
            return "character_device"
        if os.path.islink(path):
            return "symlink"
        return "other"
    except OSError:
        return "missing"


def probe_device(serial, device, args):
    result = {
        "device": device,
        "exists": os.path.exists(device),
        "kind": device_kind(device),
        "readable": os.access(device, os.R_OK),
        "writable": os.access(device, os.W_OK),
        "status": "unknown",
        "requested": {
            "baudrate": args.baudrate,
            "bytesize": 8,
            "parity": "N",
            "stopbits": 1,
        },
        "received": {
            "bytes": 0,
            "hex_preview": "",
            "text_preview": "",
        },
    }
    if not result["exists"]:
        result["status"] = "missing"
        return result
    if not result["readable"]:
        result["status"] = "permission_denied"
        return result

    port = None
    try:
        port = serial.Serial(
            port=device,
            baudrate=args.baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.1,
            write_timeout=0.5,
        )
        result["opened"] = bool(port.is_open)
        start = time.monotonic()
        received = bytearray()
        while time.monotonic() - start < args.read_seconds:
            waiting = getattr(port, "in_waiting", 0)
            chunk = port.read(waiting or 1)
            if chunk:
                received.extend(chunk)
            if not waiting:
                time.sleep(0.01)
        result["status"] = "opened"
        result["received"] = {
            "bytes": len(received),
            "hex_preview": bytes(received[:256]).hex(" "),
            "text_preview": bytes(received[:256]).decode("utf-8", errors="replace"),
        }
        result["notes"] = [
            "No bytes were transmitted by this probe.",
            "An opened idle port is not proof that the selected UART is connected to the intended controller.",
        ]
    except Exception as exc:
        result["status"] = "failed"
        result["error"] = "{}: {}".format(type(exc).__name__, exc)
    finally:
        if port is not None:
            try:
                port.close()
            except Exception:
                pass
    return result


def print_text(report):
    print("probe: {}".format(report["probe"]))
    print("serial: {} {}".format(report["serial"]["status"], report["serial"].get("version", "")))
    print("status: {}".format(report["status"]))
    print("devices: {}".format(len(report["devices"])))
    for item in report["devices"]:
        received = item.get("received", {})
        print("- {}: {} readable={} writable={} bytes={}".format(
            item["device"], item["status"], item.get("readable"), item.get("writable"), received.get("bytes", 0)
        ))


def main():
    args = parse_args()
    if args.baudrate <= 0 or args.read_seconds < 0:
        print("--baudrate must be > 0 and --read-seconds must be >= 0", file=sys.stderr)
        return 2

    serial, import_error = serial_import()
    report = {
        "probe": "taishan-rk3566/probe_uart",
        "probe_version": PROBE_VERSION,
        "status": "failed",
        "requested": {
            "devices": args.device or "auto",
            "baudrate": args.baudrate,
            "read_seconds": args.read_seconds,
            "transmit": False,
        },
        "serial": {"status": "installed" if serial else "missing", "error": import_error},
        "devices": [],
        "notes": [
            "The probe never transmits bytes.",
            "Device names, permissions, baudrate and protocol must be confirmed for the current image and wiring.",
        ],
    }
    if serial is None:
        if args.text:
            print_text(report)
        else:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

    report["serial"]["version"] = getattr(serial, "VERSION", "unknown")
    devices = discover_devices(args.device)
    report["devices"] = [probe_device(serial, device, args) for device in devices]
    opened = [item for item in report["devices"] if item.get("status") == "opened"]
    report["status"] = "ok" if opened else ("no_device" if not devices else "failed")

    if args.text:
        print_text(report)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if opened else 1


if __name__ == "__main__":
    sys.exit(main())
