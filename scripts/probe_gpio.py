#!/usr/bin/env python3
"""Read-only GPIO discovery probe for a Taishan RK3566 Linux board.

Examples:
    python3 scripts/probe_gpio.py --json
    python3 scripts/probe_gpio.py --chip /dev/gpiochip0 --text

This probe never requests a line and never changes an output value. It uses
gpioinfo when available and records the raw output for later Pinmux/IO-table
comparison. A physical 40-pin number is not converted to a Linux line number.
"""

from __future__ import print_function

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys


PROBE_VERSION = "0.1.0"


def parse_args():
    parser = argparse.ArgumentParser(description="Probe GPIO chips without changing line state.")
    parser.add_argument("--chip", action="append", help="GPIO chip path; repeat for multiple chips. Default: /dev/gpiochip*.")
    parser.add_argument("--json", action="store_true", help="Print JSON output; this is already the default.")
    parser.add_argument("--text", action="store_true", help="Print a human-readable summary instead of JSON.")
    return parser.parse_args()


def discover_chips(explicit):
    if explicit:
        return explicit
    return sorted(glob.glob("/dev/gpiochip*"))


def run_gpioinfo(chip):
    command = shutil.which("gpioinfo")
    if not command:
        return {"status": "unavailable", "error": "gpioinfo not installed"}
    try:
        result = subprocess.run(
            [command, chip],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            timeout=5,
        )
        return {
            "status": "ok" if result.returncode == 0 else "failed",
            "returncode": result.returncode,
            "output": result.stdout[-20000:],
        }
    except Exception as exc:
        return {"status": "failed", "error": "{}: {}".format(type(exc).__name__, exc)}


def chip_result(chip):
    return {
        "chip": chip,
        "exists": os.path.exists(chip),
        "readable": os.access(chip, os.R_OK),
        "gpioinfo": run_gpioinfo(chip),
        "safety": "no line requested; no output value changed",
    }


def text_summary(report):
    print("probe: {}".format(report["probe"]))
    print("status: {}".format(report["status"]))
    print("gpioinfo: {}".format(report["gpioinfo"]["status"]))
    for chip in report["chips"]:
        print("- {}: exists={} readable={} gpioinfo={}".format(
            chip["chip"], chip["exists"], chip["readable"], chip["gpioinfo"]["status"]
        ))


def main():
    args = parse_args()
    chips = discover_chips(args.chip)
    gpioinfo_installed = shutil.which("gpioinfo") is not None
    report = {
        "probe": "taishan-rk3566/probe_gpio",
        "probe_version": PROBE_VERSION,
        "status": "failed",
        "gpioinfo": {"status": "installed" if gpioinfo_installed else "missing"},
        "chips": [chip_result(chip) for chip in chips],
        "notes": [
            "This probe does not request GPIO lines or change output state.",
            "Do not infer a Linux line number from a 40-pin number or GPIOx_y name.",
            "Confirm Pinmux, direction, level and safety before any write test.",
        ],
    }
    usable = [item for item in report["chips"] if item["gpioinfo"]["status"] == "ok"]
    if usable:
        report["status"] = "ok"
    elif chips and gpioinfo_installed:
        report["status"] = "failed"
    else:
        report["status"] = "not_detected"

    if args.text:
        text_summary(report)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if usable else 1


if __name__ == "__main__":
    sys.exit(main())
