#!/usr/bin/env python3
"""Read-only RKNN/NPU runtime discovery probe for RK3566 Linux.

Examples:
    python3 scripts/probe_rknn.py --json
    python3 scripts/probe_rknn.py --text

The probe checks importable runtime/toolkit modules, likely NPU device nodes,
and common RKNN shared-library locations. It does not load a model, modify
drivers, allocate an inference context, or claim that a model can run.
"""

from __future__ import print_function

import argparse
import glob
import importlib
import importlib.util
import json
import os
import platform
import sys


PROBE_VERSION = "0.1.0"
MODULE_CANDIDATES = (
    "rknnlite.api",
    "rknn.api",
    "rknn_toolkit_lite2",
    "rknn_toolkit2",
)
DEVICE_PATTERNS = ("/dev/rknpu*", "/dev/rknn*", "/sys/class/misc/rknpu*", "/sys/class/misc/rknn*")
LIB_PATTERNS = (
    "/usr/lib*/librknn*.so*",
    "/usr/local/lib*/librknn*.so*",
    "/lib*/librknn*.so*",
    "/opt/**/librknn*.so*",
)


def parse_args():
    parser = argparse.ArgumentParser(description="Probe RKNN/NPU runtime presence without running inference.")
    parser.add_argument("--json", action="store_true", help="Print JSON output; this is already the default.")
    parser.add_argument("--text", action="store_true", help="Print a human-readable summary instead of JSON.")
    return parser.parse_args()


def module_probe(name):
    result = {"module": name, "status": "missing"}
    try:
        spec = importlib.util.find_spec(name)
        if spec is None:
            return result
        result["status"] = "found"
        result["origin"] = getattr(spec, "origin", None)
        try:
            module = importlib.import_module(name)
            result["status"] = "imported"
            result["version"] = getattr(module, "__version__", None)
        except Exception as exc:
            result["status"] = "import_failed"
            result["error"] = "{}: {}".format(type(exc).__name__, exc)
    except Exception as exc:
        result["status"] = "probe_failed"
        result["error"] = "{}: {}".format(type(exc).__name__, exc)
    return result


def unique_matches(patterns):
    matches = []
    for pattern in patterns:
        matches.extend(glob.glob(pattern, recursive=True))
    return sorted(set(matches))


def text_summary(report):
    print("probe: {}".format(report["probe"]))
    print("status: {}".format(report["status"]))
    print("architecture: {}".format(report["platform"]["architecture"]))
    print("modules:")
    for item in report["modules"]:
        print("- {}: {} {}".format(item["module"], item["status"], item.get("version", "")))
    print("device_nodes: {}".format(", ".join(report["device_nodes"]) or "none"))
    print("libraries: {}".format(", ".join(report["libraries"]) or "none"))


def main():
    args = parse_args()
    modules = [module_probe(name) for name in MODULE_CANDIDATES]
    device_nodes = unique_matches(DEVICE_PATTERNS)
    libraries = unique_matches(LIB_PATTERNS)
    imported = [item for item in modules if item["status"] == "imported"]
    found_any = bool(imported or device_nodes or libraries)
    report = {
        "probe": "taishan-rk3566/probe_rknn",
        "probe_version": PROBE_VERSION,
        "status": "partial" if found_any else "not_detected",
        "platform": {
            "architecture": platform.machine(),
            "python": sys.version.split()[0],
        },
        "modules": modules,
        "device_nodes": device_nodes,
        "libraries": libraries,
        "notes": [
            "Presence is not proof of driver compatibility or model support.",
            "This probe does not load a model or run NPU inference.",
            "Toolkit, converter, runtime, driver, model format and quantization still require a version matrix and target-board test.",
        ],
    }
    if args.text:
        text_summary(report)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if found_any else 1


if __name__ == "__main__":
    sys.exit(main())
