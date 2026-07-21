#!/usr/bin/env bash
# Read-only baseline probe for a Taishan RK3566 Linux board.
#
# Usage:
#   bash scripts/probe_system.sh          # JSON, default
#   bash scripts/probe_system.sh --text   # human-readable summary
#   bash scripts/probe_system.sh --help
#
# Exit codes:
#   0  Probe completed. Optional tools may still be missing; inspect status.
#   2  Invalid command-line arguments.
#   3  A required platform command failed.

set -u

PROBE_VERSION="0.1.0"
OUTPUT_MODE="json"

usage() {
    cat <<'EOF'
Usage: bash scripts/probe_system.sh [--json|--text|--help]

Collect a read-only Linux baseline for a Taishan RK3566 board.
The probe does not install packages, modify device trees, change pinmux,
open devices, or change system configuration.
EOF
}

for arg in "$@"; do
    case "$arg" in
        --json) OUTPUT_MODE="json" ;;
        --text) OUTPUT_MODE="text" ;;
        --help|-h) usage; exit 0 ;;
        *) printf 'Unknown argument: %s\n' "$arg" >&2; usage >&2; exit 2 ;;
    esac
done

json_quote() {
    local value="${1-}"
    if command -v python3 >/dev/null 2>&1; then
        printf '%s' "$value" | python3 -c 'import json, sys; print(json.dumps(sys.stdin.read(), ensure_ascii=False))'
        return 0
    fi

    value=${value//\\/\\\\}
    value=${value//"/\\"}
    value=${value//$'\n'/\\n}
    printf '"%s"' "$value"
}

first_line() {
    local value="${1-}"
    printf '%s' "$value" | sed -n '1p'
}

tool_status() {
    local name="$1"
    if command -v "$name" >/dev/null 2>&1; then
        printf 'installed'
    else
        printf 'missing'
    fi
}

tool_version() {
    local name="$1"
    if [ "$(tool_status "$name")" != "installed" ]; then
        return 0
    fi
    case "$name" in
        python3) python3 --version 2>&1 | first_line ;;
        gcc) gcc --version 2>&1 | first_line ;;
        g++) g++ --version 2>&1 | first_line ;;
        cmake) cmake --version 2>&1 | first_line ;;
        git) git --version 2>&1 | first_line ;;
        v4l2-ctl) v4l2-ctl --version 2>&1 | first_line ;;
        gpioinfo) gpioinfo --version 2>&1 | first_line ;;
        *) printf '' ;;
    esac
}

tool_json() {
    local name="$1"
    local status
    local version=""
    status=$(tool_status "$name")
    if [ "$status" = "installed" ]; then
        version=$(tool_version "$name")
    fi
    printf '%s:{"status":%s,"version":%s}' \
        "$(json_quote "$name")" "$(json_quote "$status")" "$(json_quote "$version")"
}

timestamp=$(date -Is 2>/dev/null || date 2>/dev/null || printf 'unknown')
hostname_value=$(hostname 2>/dev/null || printf 'unknown')

if ! kernel_release=$(uname -r 2>/dev/null); then
    printf 'Unable to run uname -r; this is not a supported POSIX-like runtime.\n' >&2
    exit 3
fi
if ! kernel_full=$(uname -a 2>/dev/null); then
    printf 'Unable to run uname -a.\n' >&2
    exit 3
fi
if ! architecture=$(uname -m 2>/dev/null); then
    printf 'Unable to run uname -m.\n' >&2
    exit 3
fi

board_model="unknown"
if [ -r /proc/device-tree/model ]; then
    board_model=$(tr -d '\000' < /proc/device-tree/model 2>/dev/null || printf 'unknown')
fi

os_id="unknown"
os_name="unknown"
os_version="unknown"
if [ -r /etc/os-release ]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    os_id="${ID:-unknown}"
    os_name="${PRETTY_NAME:-${NAME:-unknown}}"
    os_version="${VERSION_ID:-unknown}"
fi

tool_names=(python3 gcc g++ cmake git v4l2-ctl gpioinfo)
missing_tools=0
for name in "${tool_names[@]}"; do
    if [ "$(tool_status "$name")" = "missing" ]; then
        missing_tools=$((missing_tools + 1))
    fi
done

overall_status="ok"
if [ "$missing_tools" -gt 0 ]; then
    overall_status="partial"
fi

if [ "$OUTPUT_MODE" = "text" ]; then
    printf 'probe: taishan-rk3566/probe_system\n'
    printf 'probe_version: %s\n' "$PROBE_VERSION"
    printf 'status: %s\n' "$overall_status"
    printf 'timestamp: %s\n' "$timestamp"
    printf 'hostname: %s\n' "$hostname_value"
    printf 'board_model: %s\n' "$board_model"
    printf 'os: %s (%s)\n' "$os_name" "$os_version"
    printf 'os_id: %s\n' "$os_id"
    printf 'kernel: %s\n' "$kernel_release"
    printf 'architecture: %s\n' "$architecture"
    printf 'kernel_full: %s\n' "$kernel_full"
    printf 'optional_missing_tools: %s\n' "$missing_tools"
    for name in "${tool_names[@]}"; do
        printf '%s: %s %s\n' "$name" "$(tool_status "$name")" "$(tool_version "$name")"
    done
    exit 0
fi

printf '{'
printf '"probe":%s,' "$(json_quote 'taishan-rk3566/probe_system')"
printf '"probe_version":%s,' "$(json_quote "$PROBE_VERSION")"
printf '"status":%s,' "$(json_quote "$overall_status")"
printf '"timestamp":%s,' "$(json_quote "$timestamp")"
printf '"host":{"hostname":%s},' "$(json_quote "$hostname_value")"
printf '"platform":{"board_model":%s,"os_id":%s,"os_name":%s,"os_version":%s,"kernel_release":%s,"architecture":%s,"kernel_full":%s},' \
    "$(json_quote "$board_model")" "$(json_quote "$os_id")" "$(json_quote "$os_name")" \
    "$(json_quote "$os_version")" "$(json_quote "$kernel_release")" "$(json_quote "$architecture")" \
    "$(json_quote "$kernel_full")"
printf '"tools":{'
for index in "${!tool_names[@]}"; do
    if [ "$index" -gt 0 ]; then printf ','; fi
    tool_json "${tool_names[$index]}"
done
printf '},'
printf '"notes":{"read_only":true,"optional_missing_tools":%s}' "$missing_tools"
printf '}\n'
