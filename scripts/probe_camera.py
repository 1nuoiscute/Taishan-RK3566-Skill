#!/usr/bin/env python3
"""Read-only OpenCV/V4L2 camera probe for a Taishan RK3566 board.

Examples:
    python3 scripts/probe_camera.py --text
    python3 scripts/probe_camera.py --json > camera-baseline.json
    python3 scripts/probe_camera.py --device /dev/video9 --backend v4l2 \
        --width 1280 --height 720 --fps 30 --fourcc MJPG --save-frame evidence.jpg
    python3 scripts/probe_camera.py --stable-condition fps --stable-window 30 \
        --stable-tolerance 5.0 --stable-timeout 60

The probe does not modify camera controls or system configuration. It may open
capture devices and optionally write one evidence frame to the requested path.

When --stable-condition is set the probe reads frames continuously until the
chosen metric stabilises within the tolerance window or the timeout expires.
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


PROBE_VERSION = "0.1.2"


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
    parser.add_argument("--stable-condition", choices=("fps", "brightness", "framesize"),
                        help="Enable stability monitoring using this metric.")
    parser.add_argument("--stable-window", type=int, default=30,
                        help="Consecutive frames required within tolerance (default: 30).")
    parser.add_argument("--stable-tolerance", type=float, default=5.0,
                        help="Tolerance percentage for the chosen metric (default: 5.0).")
    parser.add_argument("--stable-timeout", type=float, default=60.0,
                        help="Maximum seconds to wait for stability (default: 60.0).")
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


def monitor_until_stable(capture, first_frame, actual_width, actual_height, args,
                         monotonic=time.monotonic, sleep=time.sleep):
    condition = args.stable_condition
    window_size = max(5, args.stable_window)
    tolerance = max(0.1, args.stable_tolerance) / 100.0
    timeout = max(1.0, args.stable_timeout)

    history = []
    start = monotonic()
    previous_frame_at = start if first_frame is not None else None
    total_read = 1 if first_frame is not None else 0
    def metric(frame, width, height, captured_at):
        if condition == "fps":
            if previous_frame_at is None:
                return None
            interval = captured_at - previous_frame_at
            return 1.0 / interval if interval > 0 else None
        elif condition == "brightness":
            try:
                return float(frame.mean())
            except Exception:
                return None
        elif condition == "framesize":
            return float(width * height)
        return None

    if first_frame is not None:
        val = metric(first_frame, actual_width, actual_height, start)
        if val is not None:
            history.append(val)

    stable_at = None
    reason = "timeout"

    while monotonic() - start < timeout:
        ok, frame = capture.read()
        if not ok or frame is None:
            sleep(0.005)
            continue
        captured_at = monotonic()
        total_read += 1
        val = metric(frame, actual_width, actual_height, captured_at)
        previous_frame_at = captured_at
        if val is not None:
            history.append(val)
            if len(history) > window_size:
                history = history[-window_size:]
            if len(history) >= window_size:
                mean_val = sum(history) / len(history)
                if mean_val > 0:
                    max_dev = max(abs(v - mean_val) for v in history)
                    cv_pct = max_dev / mean_val
                    if cv_pct <= tolerance:
                        stable_at = monotonic()
                        reason = "stable"
                        break

    elapsed = max(monotonic() - start, 1e-9)

    if condition == "fps":
        measured = total_read / elapsed
    else:
        measured = None

    stability_result = {
        "condition": condition,
        "window_size": window_size,
        "tolerance_pct": args.stable_tolerance,
        "timeout_s": args.stable_timeout,
        "outcome": reason,
        "total_frames_read": total_read,
        "elapsed_s": elapsed,
        "measured_fps": measured,
        "stable_at_s": round(stable_at - start, 3) if stable_at is not None else None,
        "history_size": len(history),
        "notes": [],
    }
    if condition == "brightness" and history:
        stability_result["brightness_mean"] = round(sum(history) / len(history), 4)
        stability_result["brightness_range"] = [round(min(history), 4), round(max(history), 4)]
    elif condition == "fps":
        stability_result["notes"].append(
            "fps stability uses per-frame intervals; measured_fps is the overall rate"
        )
    elif condition == "framesize":
        stability_result["notes"].append("framesize condition always returns the same value for a given device; stability is trivially met")

    return stability_result, total_read


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

            if args.stable_condition:
                ok, frame = capture.read()
                if ok and frame is not None:
                    first_frame = frame
                stability, read_frames = monitor_until_stable(
                    capture, first_frame, actual_width, actual_height, args,
                )
            else:
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
                    "frames_requested": requested_frames if not args.stable_condition else stability["total_frames_read"],
                    "frames_read": read_frames,
                    "measured_fps": measured_fps,
                    "elapsed_seconds": elapsed,
                },
                "first_frame": {
                    "read": bool(first_frame is not None),
                    "shape": list(first_frame.shape) if first_frame is not None else None,
                },
            })
            if args.stable_condition:
                attempt["stability"] = stability
                if stability["outcome"] == "stable":
                    attempt["notes"] = attempt.get("notes", [])
                    attempt["notes"].append(
                        "Stability outcome 'stable' means the metric stayed within "
                        "tolerance for the window; it does not guarantee long-term "
                        "stability over hours or across power cycles."
                    )
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
            stab = selected.get("stability")
            if stab:
                print("  stability: outcome={} metric={} window={} tolerance={:.1f}% elapsed={:.1f}s".format(
                    stab.get("outcome"), stab.get("condition"),
                    stab.get("window_size"), stab.get("tolerance_pct"),
                    stab.get("elapsed_s"),
                ))
                if stab.get("stable_at_s") is not None:
                    print("  stable_at: {:.1f}s".format(stab["stable_at_s"]))
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
    if args.stable_condition:
        if args.stable_window < 5:
            print("--stable-window must be >= 5", file=sys.stderr)
            return 2
        if args.stable_tolerance <= 0:
            print("--stable-tolerance must be > 0", file=sys.stderr)
            return 2
        if args.stable_timeout <= 0:
            print("--stable-timeout must be > 0", file=sys.stderr)
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
            "stable_condition": args.stable_condition,
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
