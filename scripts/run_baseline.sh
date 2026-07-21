#!/usr/bin/env bash
# Run the read-only Taishan RK3566 capability probes and save evidence.
#
# This runner continues when an optional probe cannot open a device. Inspect
# each JSON file and the status.tsv file instead of treating missing hardware
# as a script failure.

set -u

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-python3}"
OUTPUT_DIR=""
CAMERA_DEVICE=""
UART_DEVICE=""
UART_BAUDRATE="115200"
CAMERA_FRAMES="30"
UART_READ_SECONDS="1.0"

usage() {
    cat <<'EOF'
Usage: bash scripts/run_baseline.sh [options]

Options:
  --output-dir DIR       Evidence directory (default: baseline-<UTC timestamp>)
  --camera-device PATH   Explicit camera device, for example /dev/video9
  --uart-device PATH     Explicit UART device, for example /dev/ttyS7
  --uart-baudrate N      Candidate baudrate (default: 115200)
  --camera-frames N      Camera FPS sample length (default: 30)
  --read-seconds N       UART listen window (default: 1.0)
  --help                 Show this help

The probes are read-only. UART probing never transmits bytes and GPIO probing
never requests a line or changes an output value.
EOF
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --output-dir) OUTPUT_DIR="$2"; shift 2 ;;
        --camera-device) CAMERA_DEVICE="$2"; shift 2 ;;
        --uart-device) UART_DEVICE="$2"; shift 2 ;;
        --uart-baudrate) UART_BAUDRATE="$2"; shift 2 ;;
        --camera-frames) CAMERA_FRAMES="$2"; shift 2 ;;
        --read-seconds) UART_READ_SECONDS="$2"; shift 2 ;;
        --help|-h) usage; exit 0 ;;
        *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
    esac
done

if [ -z "$OUTPUT_DIR" ]; then
    OUTPUT_DIR="${ROOT_DIR}/baseline-$(date -u +%Y%m%dT%H%M%SZ)"
elif [ "${OUTPUT_DIR#/}" = "$OUTPUT_DIR" ]; then
    OUTPUT_DIR="${ROOT_DIR}/${OUTPUT_DIR}"
fi

mkdir -p "$OUTPUT_DIR"
STATUS_FILE="${OUTPUT_DIR}/status.tsv"
MANIFEST_FILE="${OUTPUT_DIR}/manifest.txt"
printf 'probe\texit_code\tjson\tstderr\n' > "$STATUS_FILE"
{
    printf 'created_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf 'root=%s\n' "$ROOT_DIR"
    printf 'output_dir=%s\n' "$OUTPUT_DIR"
    printf 'python=%s\n' "$PYTHON_BIN"
} > "$MANIFEST_FILE"

run_probe() {
    local name="$1"
    local json_path="${OUTPUT_DIR}/${name}.json"
    local stderr_path="${OUTPUT_DIR}/${name}.stderr.log"
    shift
    printf '$'
    printf ' %q' "$@"
    printf '\n' | tee -a "$MANIFEST_FILE"
    "$@" > "$json_path" 2> "$stderr_path"
    local code=$?
    printf '%s\t%s\t%s\t%s\n' "$name" "$code" "$json_path" "$stderr_path" >> "$STATUS_FILE"
    return 0
}

cd "$ROOT_DIR" || exit 3

run_probe system bash scripts/probe_system.sh --json

camera_args=("$PYTHON_BIN" scripts/probe_camera.py --json --frames "$CAMERA_FRAMES")
if [ -n "$CAMERA_DEVICE" ]; then
    camera_args+=(--device "$CAMERA_DEVICE")
fi
run_probe camera "${camera_args[@]}"

uart_args=("$PYTHON_BIN" scripts/probe_uart.py --json --baudrate "$UART_BAUDRATE" --read-seconds "$UART_READ_SECONDS")
if [ -n "$UART_DEVICE" ]; then
    uart_args+=(--device "$UART_DEVICE")
fi
run_probe uart "${uart_args[@]}"

run_probe gpio "$PYTHON_BIN" scripts/probe_gpio.py --json
run_probe rknn "$PYTHON_BIN" scripts/probe_rknn.py --json

printf '\nEvidence saved to: %s\n' "$OUTPUT_DIR"
printf 'Review %s and the individual JSON/stderr files before claiming a board baseline.\n' "$STATUS_FILE"
exit 0
