#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MEM0_BIN="$ROOT_DIR/node_modules/.bin/mem0"
if [ ! -x "$MEM0_BIN" ]; then
    if command -v mem0 >/dev/null 2>&1; then
        MEM0_BIN="$(command -v mem0)"
    else
        echo "Mem0 CLI not found in this repo or on PATH." >&2
        echo "Install it for this project with: bun add -d @mem0/cli" >&2
        echo "Or restore repo dependencies with: bun install" >&2
        exit 1
    fi
fi

if [ ! -x "$MEM0_BIN" ]; then
    echo "Resolved Mem0 CLI path is not executable: $MEM0_BIN" >&2
    exit 1
fi

if [ -f "$ROOT_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    . "$ROOT_DIR/.env"
    set +a
fi

has_arg() {
    local needle="$1"
    shift
    for arg in "$@"; do
        if [ "$arg" = "$needle" ]; then
            return 0
        fi
    done
    return 1
}

if [ "$#" -eq 0 ] || has_arg "--help" "$@" || [ "${1:-}" = "help" ] || [ "${1:-}" = "init" ] || [ "${1:-}" = "config" ]; then
    exec "$MEM0_BIN" "$@"
fi

if ! has_arg "--api-key" "$@" && [ -z "${MEM0_API_KEY:-}" ]; then
    echo "Missing Mem0 API key." >&2
    echo "1. Copy .env.example to .env if needed." >&2
    echo "2. Set MEM0_API_KEY in .env." >&2
    echo "3. Re-run ./scripts/mem0-cli.sh <command>." >&2
    exit 1
fi

connection_args=()
if ! has_arg "--api-key" "$@" && [ -n "${MEM0_API_KEY:-}" ]; then
    connection_args+=(--api-key "$MEM0_API_KEY")
fi

if ! has_arg "--base-url" "$@" && [ -n "${MEM0_HOST:-}" ]; then
    connection_args+=(--base-url "$MEM0_HOST")
fi

exec "$MEM0_BIN" "$@" "${connection_args[@]}"