#!/usr/bin/env bash
# BijMantra developer launcher for the Go-based `bij` runtime.
#
# Default behavior:
#   ./bijdev.sh
#     builds tools/bij/bij when needed and starts:
#       bij dev --profile infra
#
# Profile shortcuts:
#   ./bijdev.sh core       # PostgreSQL + backend + frontend
#   ./bijdev.sh infra      # product stack, default
#   ./bijdev.sh autonomy   # explicit experimental BeingBijmantra + Chloe/OpenClaw sidecars
#
# Utility shortcuts:
#   ./bijdev.sh status
#   ./bijdev.sh logs backend --no-follow --lines 20
#   ./bijdev.sh restart backend
#   ./bijdev.sh stop

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIJ_DIR="$ROOT_DIR/tools/bij"
BIJ_BIN="$BIJ_DIR/bij"

COMMAND="dev"
PROFILE="infra"
NO_BUILD=0
FORCE_BUILD=0
NO_COLOR=0
WITH_AUTH=0
PASSTHROUGH=()

usage() {
  cat <<'USAGE'
BijMantra developer launcher

Usage:
  ./bijdev.sh [profile]
  ./bijdev.sh [command] [args]
  ./bijdev.sh [options] -- [extra bij args]

Profiles:
  infra       Product stack: PostgreSQL, Redis, MinIO, Meilisearch, backend, frontend (default)
  core        PostgreSQL, backend, frontend
  autonomy    Explicit experimental autonomy sidecars: BeingBijmantra + Chloe/OpenClaw

Commands:
  dev         Start the TUI runtime dashboard (default)
  status      Show live service status
  logs        Tail logs; example: ./bijdev.sh logs backend --no-follow --lines 20
  restart     Restart one service; example: ./bijdev.sh restart backend
  stop        Stop services through bij
  version     Print bij version
  help        Show this help

Options:
  --profile <core|infra|autonomy>
  --core | --infra | --autonomy
  --no-color
  --no-build      Use existing tools/bij/bij only
  --rebuild       Force rebuilding tools/bij/bij before running
  --help, -h

Notes:
  Auth/Keycloak is not wired into the Go bij runtime yet.
  When --auth is selected, this launcher delegates to dev.sh without OpenClaw.
USAGE
}

die() {
  printf 'bijdev: %s\n' "$*" >&2
  exit 1
}

is_profile() {
  case "$1" in
    core|infra|autonomy) return 0 ;;
    *) return 1 ;;
  esac
}

set_profile() {
  is_profile "$1" || die "unknown profile '$1' (expected core, infra, or autonomy)"
  PROFILE="$1"
  COMMAND="dev"
}

needs_build() {
  [ "$FORCE_BUILD" -eq 1 ] && return 0
  [ ! -x "$BIJ_BIN" ] && return 0

  local newer
  newer="$(find "$BIJ_DIR/cmd" "$BIJ_DIR/internal" "$BIJ_DIR/go.mod" "$BIJ_DIR/go.sum" "$BIJ_DIR/Makefile" -newer "$BIJ_BIN" -print -quit 2>/dev/null || true)"
  [ -n "$newer" ]
}

ensure_bij() {
  if [ "$NO_BUILD" -eq 1 ]; then
    [ -x "$BIJ_BIN" ] || die "$BIJ_BIN does not exist; run ./bijdev.sh --rebuild first"
    return 0
  fi

  if needs_build; then
    command -v make >/dev/null 2>&1 || die "make is required to build tools/bij/bij"
    printf 'bijdev: building tools/bij/bij\n' >&2
    make -C "$BIJ_DIR" bij
  fi
}

podman_bin() {
  if [ -n "${CONTAINER_RUNTIME:-}" ] && [ -x "${CONTAINER_RUNTIME:-}" ]; then
    printf '%s\n' "$CONTAINER_RUNTIME"
    return 0
  fi
  if [ -x /opt/homebrew/bin/podman ]; then
    printf '%s\n' /opt/homebrew/bin/podman
    return 0
  fi
  command -v podman 2>/dev/null || return 1
}

ensure_podman_ready() {
  local podman
  podman="$(podman_bin)" || die "podman not found; install Podman or set CONTAINER_RUNTIME"

  if "$podman" compose version >/dev/null 2>&1; then
    return 0
  fi

  if "$podman" machine list >/dev/null 2>&1; then
    printf 'bijdev: starting Podman machine\n' >&2
    "$podman" machine start >/dev/null 2>&1 || true
  fi

  if "$podman" compose version >/dev/null 2>&1; then
    return 0
  fi

  die "Podman is not ready. Try: $podman machine start"
}

run_auth_fallback() {
  case "$PROFILE" in
    core)
      printf 'bijdev: --auth selected; using dev.sh auth fallback for core stack\n' >&2
      exec bash "$ROOT_DIR/dev.sh" --auth "${PASSTHROUGH[@]}"
      ;;
    infra)
      printf 'bijdev: --auth selected; using dev.sh auth fallback for product infra\n' >&2
      exec bash "$ROOT_DIR/dev.sh" --all --auth "${PASSTHROUGH[@]}"
      ;;
    autonomy)
      printf 'bijdev: --auth selected with autonomy; using explicit dev.sh chloe fallback\n' >&2
      exec bash "$ROOT_DIR/dev.sh" --chloe --auth "${PASSTHROUGH[@]}"
      ;;
    *)
      die "unknown profile '$PROFILE'"
      ;;
  esac
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --help|-h)
      usage
      exit 0
      ;;
    help)
      COMMAND="help"
      ;;
    dev|status|logs|restart|stop)
      COMMAND="$1"
      ;;
    version)
      COMMAND="version"
      ;;
    core|infra|autonomy)
      set_profile "$1"
      ;;
    --profile)
      shift || die "--profile requires a value"
      [ "$#" -gt 0 ] || die "--profile requires a value"
      set_profile "$1"
      ;;
    --core)
      set_profile core
      ;;
    --infra|--all)
      set_profile infra
      ;;
    --autonomy)
      set_profile autonomy
      ;;
    --chloe)
      printf 'bijdev: --chloe maps to explicit autonomy profile\n' >&2
      set_profile autonomy
      ;;
    --auth)
      WITH_AUTH=1
      ;;
    --no-color)
      NO_COLOR=1
      ;;
    --no-build)
      NO_BUILD=1
      ;;
    --rebuild)
      FORCE_BUILD=1
      ;;
    --)
      shift
      PASSTHROUGH+=("$@")
      break
      ;;
    *)
      PASSTHROUGH+=("$1")
      ;;
  esac
  shift || true
done

if [ "$COMMAND" = "help" ]; then
  usage
  exit 0
fi

ensure_bij

BIJ_ARGS=()
[ "$NO_COLOR" -eq 1 ] && BIJ_ARGS+=(--no-color)

case "$COMMAND" in
  dev)
    if [ "$WITH_AUTH" -eq 1 ]; then
      run_auth_fallback
    fi
    ensure_podman_ready
    exec "$BIJ_BIN" "${BIJ_ARGS[@]}" dev --profile "$PROFILE" "${PASSTHROUGH[@]}"
    ;;
  status|restart|stop)
    if [ "$WITH_AUTH" -eq 1 ]; then
      die "--auth is only valid with dev startup"
    fi
    ensure_podman_ready
    exec "$BIJ_BIN" "${BIJ_ARGS[@]}" "$COMMAND" "${PASSTHROUGH[@]}"
    ;;
  logs)
    if [ "$WITH_AUTH" -eq 1 ]; then
      die "--auth is only valid with dev startup"
    fi
    exec "$BIJ_BIN" "${BIJ_ARGS[@]}" "$COMMAND" "${PASSTHROUGH[@]}"
    ;;
  version)
    exec "$BIJ_BIN" --version
    ;;
  *)
    die "unknown command '$COMMAND'"
    ;;
esac
