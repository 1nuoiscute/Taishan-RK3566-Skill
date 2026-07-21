#!/usr/bin/env python3
"""Read-only OpenCV/V4L2 camera probe for a Taishan RK3566 board.

Examples:
    python3 scripts/probe_camera.py --text
    python3 scripts/probe_camera.py --json > camera-baseline.json
    python3 scripts/probe_camera.py --device /dev/video9 --backend v4l2 \
        --width 1280 --height 720 --fps 30 --fourcc MJPG --save-frame evidence.jpg

The probe does not modify camera controls or system configuration. It may open
capture devices and optionally write one evidence frame to the requested path.
Exit codes: 0 = at least one frame read, 1 = no successful capture, 2 = bad
arguments or internal probe error.
"""

from __future__ import print_function

import argparse
import glob
import json
import os
import subprocess
import sys
import time


PROBE_VERSION = "0.1.0"


def parse_args():
    parser = argparse.ArgumentParser(description="Probe OpenCV/V4L2 cameras without changing system configuration.")
    parser.add_argument("--device", action="append", help="Device path; repeat for multiple devices. Default: /dev/video*.")
    parser.add_argument("--backend", choices=("auto", "v4l2", "any"), default="auto")
    parser.add_argument("--width", type=int, help="Optional requested width; report the actual value after opening.")
    parser.add_argument("--height", type=int, help="Optional requested height; report the actual value after opening.")
    parser.add_argument("--fps", type=float, help="Optional requested FPS; report the measured FPS separately.")
    parser.add_argument("--fourcc", help="Optional requested fourcc, for example MJPG or YUYV.")
    parser.add_argument("--frames", type=int, default=30, help="Frames to read for the short FPS sample (default: 30).")
    parser.add_argument("--save-frame", help="Optional path for the first successful evidence frame.")
    parser.add_argument("--json", action="store_true", help="Print JSON output; this is already the default.")
    parser.add_argument("--text", action="store_true", help="Print a human-readable summary instead of JSON.")
    return parser.parse_args()


def cv2_import():
    try:
        import cv2  # pylint: disable=import-outside-toplevel
        return cv2, None
    except Exception as exc:  # ImportError is not the only failure on board images.
        return None, "{}: {}".format(type(exc).__name__, exc)


def fourcc_text(cv2, value):
    try:
        number = int(value)
        if number <= 0:
            return "unknown"
        chars = [chr((number >> (8 * index)) & 0xFF) for index in range(4)]
        text = "".join(chars)
        return text if all(32 <= ord(char) <= 126 for char in text) else "unknown"
    except Exception:
        return "unknown"


def backend_candidates(cv2, requested):
    if requested == "v4l2":
        return [("v4l2", getattr(cv2, "CAP_V4L2", cv2.CAP_ANY))]
    if requested == "any":
        return [("any", cv2.CAP_ANY)]
    candidates = []
    if hasattr(cv2, "CAP_V4L2"):
        candidates.append(("v4l2", cv2.CAP_V4L2))
    candidates.append(("any", cv2.CAP_ANY))
    return candidates


def v4l2_formats(device):
    if not shutil_which("v4l2-ctl"):
        return {"status": "unavailable", "output": "v4l2-ctl not installed"}
    try:
        result = subprocess.run(
            ["v4l2-ctl", "--list-formats-ext", "-d", device],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            timeout=5,
        )
        output = result.stdout[-12000:]
        return {
            "status": "ok" if result.returncode == 0 else "failed",
            "returncode": result.returncode,
            "output": output,
        }
    except Exception as exc:
        return {"status": "failed", "error": "{}: {}".format(type(exc).__name__, exc)}


def shutil_which(name):
    """Avoid importing shutil for older board Python images."""
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        candidate = os.path.join(directory, name)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def device_list(explicit_devices):
    if explicit_devices:
        return explicit_devices
    return sorted(glob.glob("/dev/video*"))


def probe_device(cv2, device, args, save_state):
    result = {
        "device": device,
        "exists": os.path.exists(device),
        "formats": v4l2_formats(device),
        "attempts": [],
    }
    if not result["exists"]:
        result["status"] = "missing"
        return result

    for backend_name, backend in backend_candidates(cv2, args.backend):
        attempt = {"backend_requested": backend_name}
        capture = None
        try:
            capture = cv2.VideoCapture(device, backend)
            attempt["opened"] = bool(capture.isOpened())
            if not attempt["opened"]:
                attempt["status"] = "not_opened"
                result["attempts"].append(attempt)
                continue

            if args.fourcc:
                if len(args.fourcc) != 4:
                    attempt["status"] = "invalid_fourcc"
                    result["attempts"].append(attempt)
                    continue
                capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*args.fourcc))
            if args.width:
                capture.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
            if args.height:
                capture.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
            if args.fps:
                capture.set(cv2.CAP_PROP_FPS, args.fps)

            actual_width = capture.get(cv2.CAP_PROP_FRAME_WIDTH)
            actual_height = capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
            actual_fps = capture.get(cv2.CAP_PROP_FPS)
            actual_fourcc = fourcc_text(cv2, capture.get(cv2.CAP_PROP_FOURCC))
            try:
                backend_actual = capture.getBackendName()
            except Exception:
                backend_actual = backend_name

            requested_frames = max(1, args.frames)
            read_frames = 0
            first_frame = None
            start = time.monotonic()
            for _ in range(requested_frames):
                ok, frame = capture.read()
                if ok and frame is not None:
                    read_frames += 1
                    if first_frame is None:
                        first_frame = frame
            elapsed = max(time.monotonic() - start, 1e-9)
            measured_fps = read_frames / elapsed

            attempt.update({
                "status": "ok" if read_frames else "opened_no_frame",
                "backend_actual": backend_actual,
                "actual": {
                    "width": actual_width,
                    "height": actual_height,
                    "fps_property": actual_fps,
                    "fourcc": actual_fourcc,
                },
                "capture_sample": {
                    "frames_requested": requested_frames,
                    "frames_read": read_frames,
                    "measured_fps": measured_fps,
                    "elapsed_seconds": elapsed,
                },
                "first_frame": {
                    "read": bool(first_frame is not None),
                    "shape": list(first_frame.shape) if first_frame is not None else None,
                },
            })
            if first_frame is not None and args.save_frame and not save_state["saved"]:
                parent = os.path.dirname(os.path.abspath(args.save_frame))
                if parent and not os.path.isdir(parent):
                    os.makedirs(parent)
                saved = bool(cv2.imwrite(args.save_frame, first_frame))
                save_state["saved"] = saved
                attempt["first_frame"]["saved_to"] = args.save_frame if saved else None
            result["status"] = "ok" if read_frames else "opened_no_frame"
            result["selected_attempt"] = attempt
            result["attempts"].append(attempt)
            return result
        except Exception as exc:
            attempt["status"] = "error"
            attempt["error"] = "{}: {}".format(type(exc).__name__, exc)
            result["attempts"].append(attempt)
        finally:
            if capture is not None:
                capture.release()

    result["status"] = "failed"
    return result


def text_summary(report):
    print("probe: {}".format(report["probe"]))
    print("opencv: {} {}".format(report["opencv"]["status"], report["opencv"].get("version", "")))
    print("status: {}".format(report["status"]))
    print("devices: {}".format(len(report["devices"])))
    for device in report["devices"]:
        print("- {}: {}".format(device["device"], device["status"]))
        selected = device.get("selected_attempt")
        if selected:
            actual = selected.get("actual", {})
            sample = selected.get("capture_sample", {})
            print("  backend: {}".format(selected.get("backend_actual", "unknown")))
            print("  actual: {}x{} fourcc={} property_fps={}".format(
                actual.get("width"), actual.get("height"), actual.get("fourcc"), actual.get("fps_property")
            ))
            print("  sample: {}/{} frames, {:.2f} FPS".format(
                sample.get("frames_read", 0), sample.get("frames_requested", 0), sample.get("measured_fps", 0.0)
            ))
        formats = device.get("formats", {})
        print("  v4l2_formats: {}".format(formats.get("status", "unknown")))


def main():
    args = parse_args()
    if args.frames < 1:
        print("--frames must be >= 1", file=sys.stderr)
        return 2
    if args.width is not None and args.width <= 0:
        print("--width must be > 0", file=sys.stderr)
        return 2
    if args.height is not None and args.height <= 0:
        print("--height must be > 0", file=sys.stderr)
        return 2
    if args.fps is not None and args.fps <= 0:
        print("--fps must be > 0", file=sys.stderr)
        return 2
    if args.fourcc and len(args.fourcc) != 4:
        print("--fourcc must contain exactly four characters", file=sys.stderr)
        return 2

    cv2, import_error = cv2_import()
    report = {
        "probe": "taishan-rk3566/probe_camera",
        "probe_version": PROBE_VERSION,
        "status": "failed",
        "requested": {
            "devices": args.device or "auto",
            "backend": args.backend,
            "width": args.width,
            "height": args.height,
            "fps": args.fps,
            "fourcc": args.fourcc,
            "frames": args.frames,
            "save_frame": args.save_frame,
        },
        "opencv": {"status": "installed" if cv2 else "missing", "error": import_error},
        "devices": [],
        "notes": [
            "Device paths and actual values are reported from this run; requested values are not proof of support.",
            "A successful read does not prove stable long-term FPS or competition performance.",
        ],
    }
    if cv2 is None:
        if args.text:
            text_summary(report)
        else:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

    report["opencv"]["version"] = getattr(cv2, "__version__", "unknown")
    devices = device_list(args.device)
    if not devices:
        report["status"] = "no_device"
    else:
        save_state = {"saved": False}
        report["devices"] = [probe_device(cv2, device, args, save_state) for device in devices]
        successful = [item for item in report["devices"] if item.get("status") == "ok"]
        report["status"] = "ok" if successful else "failed"

    if args.text:
        text_summary(report)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
