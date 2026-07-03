#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
# dev.sh — BijMantra Next-Gen Runtime Orchestrator
#
# Usage:
#   ./dev.sh                Start PostgreSQL + backend + frontend
#   ./dev.sh --all          Start product infra (Redis, MinIO, Meilisearch)
#   ./dev.sh --chloe        Start experimental autonomy sidecars (BeingBijmantra + Chloe)
#   ./dev.sh --minimal      Start PostgreSQL only
#   ./dev.sh --auth         Include Keycloak (combine with other modes)
#   ./dev.sh --stop         Stop all BijMantra containers
#   ./dev.sh --setup        First-time setup (build, migrate, seed, install)
#   ./dev.sh --status       Show running containers and runtime probes
#
# UX flags:
#   --compact               Shorter terminal output
#   --full                  Cinematic banner + staged boot (default on TTY)
#   --quiet                 Only essential output
#   --debug                 Stream command logs to terminal
#   --no-color              Disable ANSI colors
#   --no-animation          Disable spinners / typewriter effects
#   --menu                  Interactive mode picker (uses gum when present)
# ─────────────────────────────────────────────────────────────────────

# ── Bash 4+ guard ─────────────────────────────────────────────────────
# macOS ships bash 3.2 which lacks associative arrays (declare -A).
# Re-exec with Homebrew bash 5 when running under bash < 4.
if [[ -z "${BASH_VERSINFO:-}" || "${BASH_VERSINFO[0]}" -lt 4 ]]; then
  if command -v brew >/dev/null 2>&1; then
    HOMEBREW_BASH="$(brew --prefix)/bin/bash"
    if [[ -x "$HOMEBREW_BASH" ]]; then
      exec "$HOMEBREW_BASH" "$0" "$@"
    fi
  fi
  echo "ERROR: Bash 4+ required. Install with: brew install bash" >&2
  exit 1
fi
# ─────────────────────────────────────────────────────────────────────

# Use -Eeo (not -Eeuo) so set -u does not fire on associative-array
# key misses in dashboard/state loops.
set -Eeo pipefail

# ─────────────────────────────────────────────────────────────────────
# ROOT
# ─────────────────────────────────────────────────────────────────────
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# ─────────────────────────────────────────────────────────────────────
# RUNTIME STATE
# ─────────────────────────────────────────────────────────────────────
MODE="dev"
UI_MODE="${BIJMANTRA_STARTUP_UI:-full}"
QUIET=0
DEBUG=0
NO_COLOR_FLAG=0
NO_ANIMATION=0
MENU=0
WITH_AUTH=0

RUNTIME=""
RUNTIME_NAME=""
COMPOSE=()
UNICODE_ENABLED=0
ANIMATION_ENABLED=0
TERM_WIDTH=80

BACKEND_PID=""
FRONTEND_PID=""
TELEMETRY_PID=""
SHUTTING_DOWN=0
START_SECONDS="$(date +%s)"

LOG_DIR="$ROOT_DIR/logs"
RUN_STAMP="$(date '+%Y%m%d-%H%M%S')"
STARTUP_LOG="$LOG_DIR/dev-startup-$RUN_STAMP.log"
BACKEND_LOG="$LOG_DIR/backend-dev.log"
FRONTEND_LOG="$LOG_DIR/frontend-dev.log"
EVENT_LOG="$LOG_DIR/runtime-events.log"

POSTGRES_PORT="${POSTGRES_PORT:-5432}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5656}"
REDIS_PORT="${REDIS_PORT:-6379}"
MINIO_PORT="${MINIO_PORT:-9000}"
MINIO_CONSOLE_PORT="${MINIO_CONSOLE_PORT:-9001}"
MEILISEARCH_PORT="${MEILISEARCH_PORT:-7700}"
KEYCLOAK_PORT="${KEYCLOAK_PORT:-8084}"
BEINGBIJMANTRA_SURREAL_PORT="${BEINGBIJMANTRA_SURREAL_PORT:-8083}"
OPENCLAW_GATEWAY_PORT="${OPENCLAW_GATEWAY_PORT:-18790}"

# Color/symbol variables — populated by init_terminal
BOLD="" RESET=""
FG_MUTED="" FG_PRIMARY="" FG_SECONDARY="" FG_ACCENT="" FG_OK="" FG_WARN="" FG_ERR="" FG_INFO=""
OK="ok" WARN="warn" FAIL="fail" RUN=".." SKIP="--"
BOX_H="-" BOX_V="|" BOX_TL="+" BOX_TR="+" BOX_BL="+" BOX_BR="+"

# ─────────────────────────────────────────────────────────────────────
# SERVICE REGISTRY  (associative arrays — requires bash 4+)
# ─────────────────────────────────────────────────────────────────────
declare -A SERVICE_STATE
declare -A SERVICE_LABEL
declare -A SERVICE_PORT
declare -A SERVICE_PID
declare -A SERVICE_START
declare -A SERVICE_DURATION

DECLARE_ORDER=(postgres redis minio meilisearch beingbijmantra keycloak backend frontend chloe)

SERVICE_LABEL[postgres]="PostgreSQL"
SERVICE_LABEL[redis]="Redis"
SERVICE_LABEL[minio]="MinIO"
SERVICE_LABEL[meilisearch]="Meilisearch"
SERVICE_LABEL[beingbijmantra]="BeingBijmantra"
SERVICE_LABEL[keycloak]="Keycloak"
SERVICE_LABEL[backend]="Backend API"
SERVICE_LABEL[frontend]="Frontend"
SERVICE_LABEL[chloe]="Chloe Runtime"

SERVICE_PORT[postgres]="$POSTGRES_PORT"
SERVICE_PORT[redis]="$REDIS_PORT"
SERVICE_PORT[minio]="$MINIO_PORT"
SERVICE_PORT[meilisearch]="$MEILISEARCH_PORT"
SERVICE_PORT[beingbijmantra]="$BEINGBIJMANTRA_SURREAL_PORT"
SERVICE_PORT[keycloak]="$KEYCLOAK_PORT"
SERVICE_PORT[backend]="$BACKEND_PORT"
SERVICE_PORT[frontend]="$FRONTEND_PORT"
SERVICE_PORT[chloe]="$OPENCLAW_GATEWAY_PORT"

# Pre-initialize all state to avoid unbound-variable errors
for _svc in "${DECLARE_ORDER[@]}"; do
  SERVICE_STATE[$_svc]="waiting"
  SERVICE_DURATION[$_svc]="-"
  SERVICE_PID[$_svc]=""
  SERVICE_START[$_svc]=""
done
unset _svc

# ─────────────────────────────────────────────────────────────────────
# ARGUMENT PARSING
# ─────────────────────────────────────────────────────────────────────
parse_args() {
    for arg in "$@"; do
        case "$arg" in
            --all)          MODE="all" ;;
            --minimal)      MODE="minimal" ;;
            --chloe)        MODE="chloe" ;;
            --auth)         WITH_AUTH=1 ;;
            --stop)         MODE="stop" ;;
            --setup)        MODE="setup" ;;
            --status)       MODE="status" ;;
            --help|-h)      MODE="help" ;;
            --compact)      UI_MODE="compact" ;;
            --full)         UI_MODE="full" ;;
            --quiet)        QUIET=1; UI_MODE="compact"; NO_ANIMATION=1 ;;
            --debug)        DEBUG=1; QUIET=0 ;;
            --no-color)     NO_COLOR_FLAG=1 ;;
            --no-animation) NO_ANIMATION=1 ;;
            --menu)         MENU=1 ;;
            *) ;;  # unknown flags silently ignored (historical behaviour)
        esac
    done
}

# ─────────────────────────────────────────────────────────────────────
# TERMINAL INIT
# ─────────────────────────────────────────────────────────────────────
term_width() {
    local w
    w="$(tput cols 2>/dev/null || printf '80')"
    [[ "$w" =~ ^[0-9]+$ ]] && [ "$w" -gt 0 ] && printf '%s' "$w" || printf '80'
}

refresh_terminal_size() {
    TERM_WIDTH="$(term_width)"
    [ "$TERM_WIDTH" -lt 72 ] && [ "$UI_MODE" = "full" ] && UI_MODE="compact"
    return 0
}

supports_unicode() {
    case "${LC_ALL:-${LC_CTYPE:-${LANG:-}}}" in
        *UTF-8*|*utf8*) return 0 ;;
        *) return 1 ;;
    esac
}

hide_cursor() { tput civis 2>/dev/null || true; }
show_cursor()  { tput cnorm 2>/dev/null || true; }

init_terminal() {
    refresh_terminal_size

    if supports_unicode && [ "${BIJMANTRA_ASCII:-0}" != "1" ]; then
        UNICODE_ENABLED=1
        OK="✓" WARN="!" FAIL="✕" RUN="•" SKIP="–"
        BOX_H="─" BOX_V="│" BOX_TL="╭" BOX_TR="╮" BOX_BL="╰" BOX_BR="╯"
    fi

    if [ "$NO_COLOR_FLAG" -eq 0 ] \
        && [ -z "${NO_COLOR:-}" ] \
        && [ "${TERM:-}" != "dumb" ] \
        && [ -t 1 ] \
        && [ "$(tput colors 2>/dev/null || printf '0')" -ge 8 ]; then
        BOLD=$'\033[1m'
        RESET=$'\033[0m'
        FG_MUTED=$'\033[38;5;244m'
        FG_PRIMARY=$'\033[38;2;94;234;212m'
        FG_SECONDARY=$'\033[38;2;132;173;255m'
        FG_ACCENT=$'\033[38;5;141m'
        FG_OK=$'\033[38;2;83;220;135m'
        FG_WARN=$'\033[38;2;245;194;96m'
        FG_ERR=$'\033[38;2;255;110;110m'
        FG_INFO=$'\033[38;2;180;160;255m'
    fi

    [ "$NO_ANIMATION" -eq 0 ] && [ -t 1 ] && [ "$DEBUG" -eq 0 ] && ANIMATION_ENABLED=1
    return 0
}

# ─────────────────────────────────────────────────────────────────────
# LOGGING / OUTPUT HELPERS
# ─────────────────────────────────────────────────────────────────────
has_cmd() { command -v "$1" >/dev/null 2>&1; }

log_note() {
    mkdir -p "$LOG_DIR"
    printf '%s\n' "$*" >> "$STARTUP_LOG"
}

say()   { [ "$QUIET" -eq 1 ] && return 0; printf '%b\n' "$*"; }
plain() { printf '%b\n' "$*"; }

fatal() {
    show_cursor
    plain "${FG_ERR}${FAIL}${RESET} $*"
    [ -n "${STARTUP_LOG:-}" ] && plain "${FG_MUTED}Startup log: $STARTUP_LOG${RESET}"
    exit 1
}

warn()    { say "${FG_WARN}${WARN}${RESET} $*"; log_note "WARN: $*"; }
success() { say "${FG_OK}${OK}${RESET} $*";     log_note "OK: $*"; }
info()    { say "${FG_INFO}${RUN}${RESET} $*";  log_note "INFO: $*"; }

emit_event() {
    local level="$1" msg="$2"
    printf '[%s] %-8s %s\n' "$(date '+%H:%M:%S')" "$level" "$msg" >> "$EVENT_LOG"
}

# ─────────────────────────────────────────────────────────────────────
# PORTABLE MILLISECOND CLOCK  (macOS BSD date lacks %3N)
# ─────────────────────────────────────────────────────────────────────
now_ms() {
    local value
    value="$(date +%s%3N 2>/dev/null || true)"
    if [[ "$value" =~ ^[0-9]+$ ]]; then
        printf '%s\n' "$value"
        return 0
    fi
    if has_cmd python3; then
        python3 -c 'import time; print(int(time.time() * 1000))'
    else
        printf '%s000\n' "$(date +%s)"
    fi
}

elapsed_seconds() { printf '%s' "$(( $(date +%s) - $1 ))"; }

format_duration() {
    local s="$1"
    [ "$s" -lt 60 ] && printf '%ss' "$s" || printf '%sm%02ss' "$((s/60))" "$((s%60))"
}

runtime_clock() {
    local s
    s="$(elapsed_seconds "$START_SECONDS")"
    printf "%02d:%02d" "$((s/60))" "$((s%60))"
}

# ─────────────────────────────────────────────────────────────────────
# RENDERING PRIMITIVES
# ─────────────────────────────────────────────────────────────────────
repeat_char() {
    local char="$1" count="$2" out=""
    while [ "$count" -gt 0 ]; do out="${out}${char}"; count=$((count-1)); done
    printf '%s' "$out"
}

center_text() {
    local text="$1" width="${2:-$TERM_WIDTH}" len pad=0
    len="${#text}"
    [ "$width" -gt "$len" ] && pad=$(( (width - len) / 2 ))
    printf '%*s%s\n' "$pad" "" "$text"
}

divider() {
    [ "$QUIET" -eq 1 ] && return 0
    local label="${1:-}" width="$TERM_WIDTH"
    [ "$width" -gt 100 ] && width=100
    [ "$width" -lt 48 ]  && width=48
    if [ -n "$label" ]; then
        local ll=$(( width - ${#label} - 4 ))
        [ "$ll" -lt 4 ] && ll=4
        say "${FG_MUTED}$(repeat_char "$BOX_H" 2) ${label} $(repeat_char "$BOX_H" "$ll")${RESET}"
    else
        say "${FG_MUTED}$(repeat_char "$BOX_H" "$width")${RESET}"
    fi
}

section() { [ "$QUIET" -eq 1 ] && return 0; say ""; divider "$1"; }

status_token() {
    case "$1" in
        ready|healthy|online|running|ok|pass) printf '%b%s%b' "$FG_OK"   "$OK"   "$RESET" ;;
        warn|degraded|advisory)               printf '%b%s%b' "$FG_WARN" "$WARN" "$RESET" ;;
        fail|offline|critical|error|failed)   printf '%b%s%b' "$FG_ERR"  "$FAIL" "$RESET" ;;
        skip|optional|off|waiting)            printf '%b%s%b' "$FG_MUTED" "$SKIP" "$RESET" ;;
        starting)                             printf '%b%s%b' "$FG_INFO"  "$RUN"  "$RESET" ;;
        *)                                    printf '%b%s%b' "$FG_INFO"  "$RUN"  "$RESET" ;;
    esac
}

status_row() {
    local name="$1" state="$2" detail="${3:-}"
    [ "$QUIET" -eq 1 ] && return 0
    printf '  %b %-22s %-12s %s\n' "$(status_token "$state")" "$name" "$state" "$detail"
}

clear_line() { [ -t 1 ] && printf '\r\033[K'; return 0; }

typewrite_center() {
    local text="$1" color="${2:-}" width="${3:-$TERM_WIDTH}"
    [ "$QUIET" -eq 1 ] && return 0
    local len="${#text}" pad=0 i char
    [ "$width" -gt "$len" ] && pad=$(( (width - len) / 2 ))
    printf '%*s%b' "$pad" "" "$color"
    if [ "$ANIMATION_ENABLED" -eq 1 ] && [ "$UI_MODE" = "full" ]; then
        for (( i=0; i<len; i++ )); do
            char="${text:i:1}"; printf '%s' "$char"; sleep 0.012
        done
    else
        printf '%s' "$text"
    fi
    printf '%b\n' "$RESET"
}

# ─────────────────────────────────────────────────────────────────────
# LIVE DASHBOARD  (new in dev.sh — service-registry driven)
# ─────────────────────────────────────────────────────────────────────
healthy_count() {
    local count=0
    for svc in "${DECLARE_ORDER[@]}"; do
        [[ "${SERVICE_STATE[$svc]:-waiting}" == "ready" ]] && (( count+=1 )) || true
    done
    echo "$count"
}

active_service_count() {
    local count=0
    for svc in "${DECLARE_ORDER[@]}"; do
        [[ "${SERVICE_STATE[$svc]:-waiting}" != "optional" ]] && (( count+=1 )) || true
    done
    echo "$count"
}

service_state_icon() {
    case "$1" in
        ready)    printf '%b%s%b' "$FG_OK"    "$OK"   "$RESET" ;;
        starting) printf '%b%s%b' "$FG_INFO"  "$RUN"  "$RESET" ;;
        failed)   printf '%b%s%b' "$FG_ERR"   "$FAIL" "$RESET" ;;
        waiting)  printf '%b%s%b' "$FG_MUTED" "$SKIP" "$RESET" ;;
        degraded) printf '%b%s%b' "$FG_WARN"  "$WARN" "$RESET" ;;
        optional) printf '%b%s%b' "$FG_MUTED" "$SKIP" "$RESET" ;;
        *)        printf '%b%s%b' "$FG_MUTED" "$SKIP" "$RESET" ;;
    esac
}

render_live_header() {
    local width="$TERM_WIDTH"
    [ "$width" -gt 100 ] && width=100
    printf '%b%s%b\n' "$FG_ACCENT$BOLD" "$(repeat_char "$BOX_H" "$width")" "$RESET"
    printf '%b %-20s %b%s%b uptime: %s  services: %s/%s healthy%b\n' \
        "$BOLD$FG_PRIMARY" "BIJMANTRA" \
        "$RESET$FG_MUTED" "runtime: $(mode_label)" \
        "$RESET" "$(runtime_clock)" \
        "$(healthy_count)" "$(active_service_count)" "$RESET"
    printf '%b%s%b\n' "$FG_ACCENT" "$(repeat_char "$BOX_H" "$width")" "$RESET"
}

render_live_services() {
    printf '\n%b SERVICES%b\n\n' "$BOLD$FG_PRIMARY" "$RESET"
    for svc in "${DECLARE_ORDER[@]}"; do
        local state="${SERVICE_STATE[$svc]:-waiting}"
        local icon dur="${SERVICE_DURATION[$svc]:--}" port="${SERVICE_PORT[$svc]:-}"
        icon="$(service_state_icon "$state")"
        printf ' %-20s %b %-12s %b%8s%b %b%s%b\n' \
            "${SERVICE_LABEL[$svc]:-$svc}" \
            "$icon" "${state^^}" \
            "$FG_MUTED" "$dur" "$RESET" \
            "$FG_MUTED" "${port:+:${port}}" "$RESET"
    done
}

render_live_graph() {
    printf '\n%b SYSTEM GRAPH%b\n\n' "$BOLD$FG_PRIMARY" "$RESET"
    printf ' PostgreSQL\n'
    printf '   └─ Backend API\n'
    printf '       ├─ Auth (Keycloak)\n'
    printf '       ├─ Search (Meilisearch)\n'
    printf '       ├─ Cache (Redis)\n'
    printf '       ├─ Storage (MinIO)\n'
    printf '       ├─ Optional product infra\n'
    printf '       └─ WebSocket Gateway\n'
    printf '            └─ Frontend\n'
    printf '   Experimental autonomy sidecars (explicit only)\n'
}

render_live_events() {
    printf '\n%b LIVE EVENTS%b\n\n' "$BOLD$FG_PRIMARY" "$RESET"
    tail -n 8 "$EVENT_LOG" 2>/dev/null || true
}

render_live_dashboard() {
    [ "$QUIET" -eq 1 ] && return 0
    [ -t 1 ] || return 0
    clear 2>/dev/null || true
    render_live_header
    render_live_services
    render_live_graph
    render_live_events
    printf '\n%bPress Ctrl+C to disconnect orchestration. Infra containers stay up.%b\n' "$FG_MUTED" "$RESET"
    return 0
}

# State machine helpers — update registry and refresh dashboard
set_service_state() {
    local svc="$1" state="$2"
    SERVICE_STATE[$svc]="$state"
}

mark_starting() {
    local svc="$1"
    SERVICE_START[$svc]="$(now_ms)"
    emit_event INFO "${SERVICE_LABEL[$svc]:-$svc} starting"
    set_service_state "$svc" "starting"
    render_live_dashboard
}

mark_ready() {
    local svc="$1" end start delta
    end="$(now_ms)"
    start="${SERVICE_START[$svc]:-$end}"
    delta=$(( end - start ))
    SERVICE_DURATION[$svc]="${delta}ms"
    emit_event READY "${SERVICE_LABEL[$svc]:-$svc} healthy (${delta}ms)"
    set_service_state "$svc" "ready"
    render_live_dashboard
}

mark_failed() {
    local svc="$1"
    emit_event ERROR "${SERVICE_LABEL[$svc]:-$svc} failed"
    set_service_state "$svc" "failed"
    render_live_dashboard
}

mark_degraded() {
    local svc="$1" detail="${2:-degraded}"
    emit_event WARN "${SERVICE_LABEL[$svc]:-$svc} ${detail}"
    set_service_state "$svc" "degraded"
    render_live_dashboard
}

mark_optional() {
    local svc="$1"
    emit_event SKIP "${SERVICE_LABEL[$svc]:-$svc} optional / not started in this mode"
    SERVICE_STATE[$svc]="optional"
}

# ─────────────────────────────────────────────────────────────────────
# STEP RUNNERS  (spinner + log capture, from dev-original.sh)
# ─────────────────────────────────────────────────────────────────────
print_command_debug() {
    local quoted="" part
    for part in "$@"; do printf -v part '%q' "$part"; quoted="${quoted}${quoted:+ }${part}"; done
    say "${FG_MUTED}$ ${quoted}${RESET}"
    log_note "$ $quoted"
}

spin_wait() {
    local pid="$1" label="$2" started="$3"
    local frames_ascii='-\|/' frames_unicode='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    local index=0 frames="$frames_ascii" frame_count=4
    [ "$UNICODE_ENABLED" -eq 1 ] && frames="$frames_unicode" && frame_count=10
    while kill -0 "$pid" >/dev/null 2>&1; do
        local frame="${frames:index:1}" elapsed
        elapsed="$(elapsed_seconds "$started")"
        printf '\r  %b%s%b %-54s %s' "$FG_SECONDARY" "$frame" "$RESET" "$label" "${FG_MUTED}${elapsed}s${RESET}"
        sleep 0.1
        index=$(( (index+1) % frame_count ))
    done
}

finish_step_line() {
    local label="$1" state="$2" started="$3"
    local dur; dur="$(format_duration "$(elapsed_seconds "$started")")"
    clear_line
    case "$state" in
        ok)   say "  $(status_token "ok")   ${label} ${FG_MUTED}(${dur})${RESET}" ;;
        warn) say "  $(status_token "warn") ${label} ${FG_MUTED}(${dur})${RESET}" ;;
        *)    say "  $(status_token "fail") ${label} ${FG_MUTED}(${dur})${RESET}" ;;
    esac
}

run_step() {
    local label="$1"; shift
    local started status pid
    started="$(date +%s)"
    log_note "STEP: $label"
    if [ "$DEBUG" -eq 1 ]; then
        say "  $(status_token "starting") ${label}"
        print_command_debug "$@"
        set +e; "$@" 2>&1 | tee -a "$STARTUP_LOG"; status=${PIPESTATUS[0]}; set -e
    else
        "$@" >> "$STARTUP_LOG" 2>&1 & pid=$!
        [ "$ANIMATION_ENABLED" -eq 1 ] && [ "$QUIET" -eq 0 ] && spin_wait "$pid" "$label" "$started"
        set +e; wait "$pid"; status=$?; set -e
    fi
    if [ "$status" -eq 0 ]; then finish_step_line "$label" "ok" "$started"; return 0; fi
    finish_step_line "$label" "fail" "$started"
    if has_cmd tail; then
        say "${FG_MUTED}Last startup log lines:${RESET}"
        tail -20 "$STARTUP_LOG" | sed 's/^/    /'
    fi
    return "$status"
}

run_soft_step() {
    local label="$1"; shift
    run_step "$label" "$@" && return 0
    warn "$label returned non-zero; readiness probes will confirm actual state."
    return 0
}

run_advisory_step() {
    local label="$1"; shift
    local started status pid
    started="$(date +%s)"
    log_note "ADVISORY: $label"
    if [ "$DEBUG" -eq 1 ]; then
        say "  $(status_token "starting") ${label}"
        print_command_debug "$@"
        set +e; "$@" 2>&1 | tee -a "$STARTUP_LOG"; status=${PIPESTATUS[0]}; set -e
    else
        "$@" >> "$STARTUP_LOG" 2>&1 & pid=$!
        [ "$ANIMATION_ENABLED" -eq 1 ] && [ "$QUIET" -eq 0 ] && spin_wait "$pid" "$label" "$started"
        set +e; wait "$pid"; status=$?; set -e
    fi
    if [ "$status" -eq 0 ]; then finish_step_line "$label" "ok" "$started"; return 0; fi
    finish_step_line "$label" "warn" "$started"
    return "$status"
}

# ─────────────────────────────────────────────────────────────────────
# HEALTH PROBES
# ─────────────────────────────────────────────────────────────────────
tcp_probe() {
    local host="$1" port="$2"
    if has_cmd nc; then nc -z "$host" "$port" >/dev/null 2>&1; return $?; fi
    (echo >/dev/tcp/"$host"/"$port") >/dev/null 2>&1
}

http_probe() {
    local url="$1"
    if has_cmd curl; then curl -fsS --max-time 2 "$url" >/dev/null 2>&1; return $?; fi
    case "$url" in
        http://localhost:*)
            local rest port
            rest="${url#http://localhost:}"
            port="${rest%%/*}"
            tcp_probe "127.0.0.1" "$port"
            ;;
        http://127.0.0.1:*)
            local rest port
            rest="${url#http://127.0.0.1:}"
            port="${rest%%/*}"
            tcp_probe "127.0.0.1" "$port"
            ;;
        *) return 1 ;;
    esac
}

fetch_url() {
    has_cmd curl && curl -fsS --max-time 2 "$1" 2>/dev/null || true
}

# postgres_ready: run a real query, not just pg_isready.
# pg_isready passes while Postgres is still initializing extensions
# (TimescaleDB, pgvector, PostGIS) — causing Alembic to get a dropped
# connection mid-handshake.
postgres_ready() {
    tcp_probe "127.0.0.1" "$POSTGRES_PORT" || return 1
    "$RUNTIME" exec bijmantra-postgres \
        psql -h 127.0.0.1 -p 5432 -U bijmantra_user -d bijmantra_db -c "SELECT 1" >/dev/null 2>&1
}

postgres_stable_ready() {
    local attempt
    for attempt in 1 2 3; do
        postgres_ready || return 1
        [ "$attempt" -lt 3 ] && sleep 1
    done
    return 0
}

redis_ready()          { "$RUNTIME" exec bijmantra-redis redis-cli ping >/dev/null 2>&1; }
minio_ready()          { http_probe "http://127.0.0.1:${MINIO_PORT}/minio/health/live"; }
meilisearch_ready()    { http_probe "http://127.0.0.1:${MEILISEARCH_PORT}/health"; }
beingbijmantra_ready() { http_probe "http://127.0.0.1:${BEINGBIJMANTRA_SURREAL_PORT}/health" || tcp_probe "127.0.0.1" "$BEINGBIJMANTRA_SURREAL_PORT"; }
keycloak_ready()       { http_probe "http://127.0.0.1:${KEYCLOAK_PORT:-8084}/realms/bijmantra"; }
backend_ready()        { http_probe "http://127.0.0.1:${BACKEND_PORT}/health"; }
api_docs_ready()       { http_probe "http://127.0.0.1:${BACKEND_PORT}/docs"; }
frontend_ready()       { http_probe "http://127.0.0.1:${FRONTEND_PORT}/"; }
chloe_ready()          { http_probe "http://127.0.0.1:${OPENCLAW_GATEWAY_PORT}/healthz"; }

configure_auth_environment() {
    if [ "$WITH_AUTH" -ne 1 ]; then
        return 0
    fi

    export KEYCLOAK_ENABLED="true"
    export KEYCLOAK_ISSUER="${KEYCLOAK_ISSUER:-http://localhost:${KEYCLOAK_PORT}/realms/bijmantra}"
    export KEYCLOAK_AUDIENCE="${KEYCLOAK_AUDIENCE:-bijmantra-api}"
    export KEYCLOAK_JWKS_URL="${KEYCLOAK_JWKS_URL:-http://localhost:${KEYCLOAK_PORT}/realms/bijmantra/protocol/openid-connect/certs}"
    export KEYCLOAK_BOOTSTRAP_ADMIN_SUBJECT="${KEYCLOAK_BOOTSTRAP_ADMIN_SUBJECT:-00000000-0000-4000-8000-000000000001}"

    export VITE_AUTH_PROVIDER="keycloak"
    export VITE_KEYCLOAK_URL="${VITE_KEYCLOAK_URL:-http://localhost:${KEYCLOAK_PORT}}"
    export VITE_KEYCLOAK_REALM="${VITE_KEYCLOAK_REALM:-bijmantra}"
    export VITE_KEYCLOAK_CLIENT_ID="${VITE_KEYCLOAK_CLIENT_ID:-bijmantra-web}"
}

container_running() {
    "$RUNTIME" ps --filter "name=${1}" --format "{{.Names}}" 2>/dev/null | grep -qx "$1"
}

container_health() {
    local h
    h="$("$RUNTIME" inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$1" 2>/dev/null || true)"
    [ -n "$h" ] && printf '%s' "$h" || { container_running "$1" && printf 'running' || printf 'offline'; }
}

wait_for_service() {
    local label="$1" timeout="$2"; shift 2
    local started now elapsed index=0 frame
    local frames_ascii='-\|/' frames_unicode='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    local frames="$frames_ascii" frame_count=4
    started="$(date +%s)"
    [ "$UNICODE_ENABLED" -eq 1 ] && frames="$frames_unicode" && frame_count=10
    while true; do
        if "$@" >/dev/null 2>&1; then finish_step_line "$label" "ok" "$started"; return 0; fi
        now="$(date +%s)"; elapsed=$(( now - started ))
        if [ "$elapsed" -ge "$timeout" ]; then finish_step_line "$label" "fail" "$started"; return 1; fi
        if [ "$ANIMATION_ENABLED" -eq 1 ] && [ "$QUIET" -eq 0 ]; then
            frame="${frames:index:1}"
            printf '\r  %b%s%b %-54s %s/%ss' "$FG_SECONDARY" "$frame" "$RESET" "$label" "$elapsed" "$timeout"
            index=$(( (index+1) % frame_count ))
        fi
        sleep 1
    done
}

service_probe_state()   { "$1" >/dev/null 2>&1 && printf 'ready'    || printf 'offline'; }
optional_probe_state()  { "$1" >/dev/null 2>&1 && printf 'ready'    || printf 'optional'; }

port_preflight() {
    case "$MODE" in dev|all|chloe) ;; *) return 0 ;; esac
    tcp_probe "127.0.0.1" "$BACKEND_PORT"  && warn "Port ${BACKEND_PORT} already in use. Backend may attach to an existing service."
    tcp_probe "127.0.0.1" "$FRONTEND_PORT" && warn "Port ${FRONTEND_PORT} already in use. Vite may choose another port."
    return 0
}

restart_existing_backend_for_auth() {
    local pids attempt

    pids="$(pgrep -f "uvicorn app.main:app.*--port ${BACKEND_PORT}" 2>/dev/null || true)"
    if [ -z "$pids" ]; then
        fatal "Backend is already responding on port ${BACKEND_PORT}, but --auth requires a backend started with KEYCLOAK_ENABLED=true. Stop the existing backend or free port ${BACKEND_PORT}, then rerun dev.sh --auth."
    fi

    warn "Auth mode requested; restarting existing FastAPI backend so Keycloak settings are applied."
    for pid in $pids; do
        kill "$pid" >/dev/null 2>&1 || true
    done

    for attempt in {1..20}; do
        backend_ready >/dev/null 2>&1 || return 0
        sleep 0.5
    done

    fatal "Existing backend on port ${BACKEND_PORT} did not stop cleanly. Stop it manually, then rerun dev.sh --auth."
}

sql_escape_literal() {
    printf '%s' "$1" | sed "s/'/''/g"
}

keycloak_admin_login() {
    container_running "bijmantra-keycloak" || return 1
    "$RUNTIME" exec bijmantra-keycloak /opt/keycloak/bin/kcadm.sh config credentials \
        --server "http://localhost:8080" \
        --realm master \
        --user "${KEYCLOAK_ADMIN_USERNAME:-admin}" \
        --password "${KEYCLOAK_ADMIN_PASSWORD:-admin}" >/dev/null 2>&1
}

keycloak_web_client_contract_ready() {
    local realm web_client api_audience clients_json client_id client_json scopes_json

    has_cmd python3 || return 1
    realm="${VITE_KEYCLOAK_REALM:-bijmantra}"
    web_client="${VITE_KEYCLOAK_CLIENT_ID:-bijmantra-web}"
    api_audience="${KEYCLOAK_AUDIENCE:-bijmantra-api}"

    keycloak_admin_login || return 1

    clients_json="$("$RUNTIME" exec bijmantra-keycloak /opt/keycloak/bin/kcadm.sh \
        get clients -r "$realm" -q "clientId=${web_client}" 2>/dev/null || true)"
    [ -n "$clients_json" ] || return 1

    client_id="$(printf '%s' "$clients_json" | python3 -c 'import json,sys; data=json.load(sys.stdin); print(data[0].get("id", "") if data else "")' 2>/dev/null || true)"
    [ -n "$client_id" ] || return 1

    client_json="$("$RUNTIME" exec bijmantra-keycloak /opt/keycloak/bin/kcadm.sh \
        get "clients/${client_id}" -r "$realm" 2>/dev/null || true)"
    scopes_json="$("$RUNTIME" exec bijmantra-keycloak /opt/keycloak/bin/kcadm.sh \
        get client-scopes -r "$realm" 2>/dev/null || true)"
    [ -n "$client_json" ] && [ -n "$scopes_json" ] || return 1

    CLIENT_JSON="$client_json" SCOPES_JSON="$scopes_json" API_AUDIENCE="$api_audience" python3 - <<'PY'
import json
import os
import sys

client = json.loads(os.environ["CLIENT_JSON"])
scopes = json.loads(os.environ["SCOPES_JSON"])
api_audience = os.environ["API_AUDIENCE"]

subject_mapper_ready = any(
    mapper.get("protocolMapper") == "oidc-sub-mapper"
    and mapper.get("config", {}).get("access.token.claim") == "true"
    for mapper in client.get("protocolMappers", [])
)
if not subject_mapper_ready:
    sys.exit(10)

if "bijmantra-api-audience" not in client.get("defaultClientScopes", []):
    sys.exit(11)

audience_scope = next(
    (scope for scope in scopes if scope.get("name") == "bijmantra-api-audience"),
    None,
)
if not audience_scope:
    sys.exit(12)

audience_mapper_ready = any(
    mapper.get("protocolMapper") == "oidc-audience-mapper"
    and mapper.get("config", {}).get("included.client.audience") == api_audience
    and mapper.get("config", {}).get("access.token.claim") == "true"
    for mapper in audience_scope.get("protocolMappers", [])
)
if not audience_mapper_ready:
    sys.exit(13)
PY
}

keycloak_admin_identity_ready() {
    local issuer subject issuer_sql subject_sql result

    issuer="${KEYCLOAK_ISSUER:-http://localhost:${KEYCLOAK_PORT}/realms/bijmantra}"
    subject="${KEYCLOAK_BOOTSTRAP_ADMIN_SUBJECT:-}"
    [ -n "$subject" ] || return 1

    issuer_sql="$(sql_escape_literal "$issuer")"
    subject_sql="$(sql_escape_literal "$subject")"
    result="$("$RUNTIME" exec bijmantra-postgres psql \
        -h 127.0.0.1 \
        -p 5432 \
        -U "${POSTGRES_USER:-bijmantra_user}" \
        -d "${POSTGRES_DB:-bijmantra_db}" \
        -tAc "SELECT 1 FROM auth_identities WHERE provider = 'keycloak' AND issuer = '${issuer_sql}' AND subject = '${subject_sql}' LIMIT 1;" \
        2>/dev/null | tr -d '[:space:]' || true)"

    [ "$result" = "1" ]
}

auth_runtime_preflight() {
    [ "$WITH_AUTH" -ne 1 ] && return 0

    section "Auth Preflight"
    status_row "backend auth env" "ready" "KEYCLOAK_ENABLED=${KEYCLOAK_ENABLED:-false}"

    keycloak_ready \
        || fatal "Keycloak is not reachable at http://localhost:${KEYCLOAK_PORT}/realms/bijmantra. Check ${RUNTIME_NAME} containers and rerun dev.sh --auth."
    status_row "Keycloak realm" "ready" "http://localhost:${KEYCLOAK_PORT}/realms/bijmantra"

    keycloak_web_client_contract_ready \
        || fatal "Keycloak realm contract is not ready. The bijmantra-web access token must carry a stable sub claim and the ${KEYCLOAK_AUDIENCE:-bijmantra-api} audience. See infra/keycloak/README.md for recovery."
    status_row "token contract" "ready" "sub + ${KEYCLOAK_AUDIENCE:-bijmantra-api} audience"

    keycloak_admin_identity_ready \
        || fatal "Bootstrap admin Keycloak identity is missing in auth_identities for subject ${KEYCLOAK_BOOTSTRAP_ADMIN_SUBJECT:-unset}. Rerun the admin seeder or see infra/keycloak/README.md."
    status_row "admin identity" "ready" "${KEYCLOAK_BOOTSTRAP_ADMIN_SUBJECT}"
}

# ─────────────────────────────────────────────────────────────────────
# RUNTIME DETECTION
# ─────────────────────────────────────────────────────────────────────
detect_runtime() {
    if [ -n "${CONTAINER_RUNTIME:-}" ] && has_cmd "$CONTAINER_RUNTIME"; then
        RUNTIME="$CONTAINER_RUNTIME"
    elif [ -x "/opt/homebrew/bin/podman" ]; then
        RUNTIME="/opt/homebrew/bin/podman"
    elif has_cmd podman; then
        RUNTIME="$(command -v podman)"
    elif has_cmd docker; then
        RUNTIME="$(command -v docker)"
    else
        fatal "Neither Podman nor Docker found. BijMantra expects Podman at /opt/homebrew/bin/podman."
    fi
    RUNTIME_NAME="$(basename "$RUNTIME")"
    COMPOSE=("$RUNTIME" compose)
}

# ─────────────────────────────────────────────────────────────────────
# PODMAN MACHINE HEALTH + AUTO-RECOVER
# ─────────────────────────────────────────────────────────────────────
ensure_podman_machine() {
    [ "$RUNTIME_NAME" != "podman" ] && return 0

    # Fast path — socket already works
    if "${COMPOSE[@]}" version >/dev/null 2>&1; then return 0; fi

    info "Podman socket unavailable — checking machine state..."

    _podman_machine_cycle() {
        info "Cycling machine: stopping, killing orphans, restarting..."
        "$RUNTIME" machine stop podman-machine-default >/dev/null 2>&1 || true
        sleep 2
        pgrep -x vfkit   | xargs kill -9 2>/dev/null || true
        pgrep -x gvproxy | xargs kill -9 2>/dev/null || true
        sleep 2
        "$RUNTIME" machine start podman-machine-default >/dev/null 2>&1 || true
    }

    _podman_machine_reinit() {
        warn "Reinitializing machine from scratch (~2 min)..."
        pgrep -x vfkit   | xargs kill -9 2>/dev/null || true
        pgrep -x gvproxy | xargs kill -9 2>/dev/null || true
        "$RUNTIME" machine rm --force podman-machine-default >/dev/null 2>&1 || true
        sleep 2
        "$RUNTIME" machine init \
            --cpus 5 --memory 6144 --disk-size 100 \
            --volume /Users:/Users \
            --volume /private:/private \
            --volume /var/folders:/var/folders \
            --now \
            podman-machine-default \
            || fatal "Podman machine init failed. Check network and disk space."
    }

    _wait_for_socket() {
        local secs="${1:-60}" i
        for i in $(seq 1 "$secs"); do
            sleep 1
            if "${COMPOSE[@]}" version >/dev/null 2>&1; then return 0; fi
        done
        return 1
    }

    # Get machine state via inspect — reliable across all Podman 5.x
    local machine_state
    machine_state="$("$RUNTIME" machine inspect podman-machine-default 2>/dev/null \
        | python3 -c 'import json,sys; print(json.load(sys.stdin)[0]["State"])' 2>/dev/null \
        || echo "missing")"

    case "$machine_state" in
        running)
            # Running but socket dead — cycle it
            warn "Machine running but socket unresponsive. Cycling..."
            _podman_machine_cycle
            ;;
        stopped)
            info "Starting podman-machine-default..."
            "$RUNTIME" machine start podman-machine-default >/dev/null 2>&1 || true
            ;;
        missing)
            info "No machine found — initializing podman-machine-default..."
            _podman_machine_reinit
            ;;
        *)
            warn "Machine state '${machine_state}' — attempting start..."
            "$RUNTIME" machine start podman-machine-default >/dev/null 2>&1 || true
            ;;
    esac

    if _wait_for_socket 60; then
        success "Podman machine is ready."
        return 0
    fi

    # Still not up — full reinit as last resort
    warn "Socket unresponsive after 60s — reinitializing..."
    _podman_machine_reinit
    if _wait_for_socket 90; then
        success "Podman machine reinitialized and ready."
        return 0
    fi

    fatal "Podman machine unresponsive after reinit. Run: podman machine inspect podman-machine-default"
}

# ─────────────────────────────────────────────────────────────────────
# PREFLIGHT
# ─────────────────────────────────────────────────────────────────────
preflight_required_tools() {
    section "Preflight"
    status_row "container runtime" "ready" "$RUNTIME"
    [ "$RUNTIME_NAME" != "podman" ] && warn "Using ${RUNTIME_NAME}; BijMantra prefers Podman-oriented workflows."
    ensure_podman_machine
    "${COMPOSE[@]}" version >/dev/null 2>&1 \
        || fatal "Compose unavailable for ${RUNTIME}. Check Podman machine/compose installation."
    status_row "compose" "ready" "$("${COMPOSE[@]}" version 2>/dev/null | head -1)"
    case "$MODE" in
        dev|all|chloe|setup)
            has_cmd uv  || fatal "Missing 'uv'. Install backend deps with the repo's uv workflow."
            status_row "uv"  "ready" "$(command -v uv)"
            has_cmd bun || fatal "Missing 'bun'. BijMantra frontend uses Bun only."
            status_row "bun" "ready" "$(command -v bun)"
            ;;
    esac
    has_cmd gum \
        && status_row "optional gum" "ready"    "$(command -v gum)" \
        || status_row "optional gum" "optional" "not installed; built-in fallback active"
    port_preflight
}

# ─────────────────────────────────────────────────────────────────────
# MODE HELPERS
# ─────────────────────────────────────────────────────────────────────
mode_label() {
    case "$MODE" in
        all)     printf 'product infra + app runtime' ;;
        chloe)   printf 'experimental autonomy sidecars' ;;
        minimal) printf 'PostgreSQL-only minimal infra' ;;
        setup)   printf 'first-time setup' ;;
        status)  printf 'status inspection' ;;
        stop)    printf 'shutdown' ;;
        *)       printf 'core app runtime' ;;
    esac
}

choose_mode() {
    [ "$MENU" -eq 0 ] && return 0
    local choice=""
    if has_cmd gum; then
        choice="$(gum choose \
            "core app runtime" \
            "product infra + app runtime" \
            "experimental autonomy sidecars" \
            "PostgreSQL-only minimal infra" \
            "first-time setup" \
            "status inspection" \
            "shutdown")"
    elif [ -t 0 ]; then
        plain "Choose BijMantra startup mode:"
        plain "  1. core app runtime"
        plain "  2. product infra + app runtime"
        plain "  3. experimental autonomy sidecars"
        plain "  4. PostgreSQL-only minimal infra"
        plain "  5. first-time setup"
        plain "  6. status inspection"
        plain "  7. shutdown"
        printf 'Selection [1]: '; read -r choice
        case "${choice:-1}" in
            2) choice="product infra + app runtime" ;;
            3) choice="experimental autonomy sidecars" ;;
            4) choice="PostgreSQL-only minimal infra" ;;
            5) choice="first-time setup" ;;
            6) choice="status inspection" ;;
            7) choice="shutdown" ;;
            *) choice="core app runtime" ;;
        esac
    else
        warn "--menu requested but stdin is not interactive."
        return 0
    fi
    case "$choice" in
        "product infra + app runtime")      MODE="all" ;;
        "experimental autonomy sidecars")   MODE="chloe" ;;
        "PostgreSQL-only minimal infra")    MODE="minimal" ;;
        "first-time setup")                 MODE="setup" ;;
        "status inspection")                MODE="status" ;;
        "shutdown")                         MODE="stop" ;;
        *)                                  MODE="dev" ;;
    esac
}

# ─────────────────────────────────────────────────────────────────────
# BANNER + BOOT SEQUENCE DISPLAY
# ─────────────────────────────────────────────────────────────────────
render_banner() {
    [ "$QUIET" -eq 1 ] && return 0
    [ "$UI_MODE" = "compact" ] && {
        say "${FG_PRIMARY}${BOLD}BijMantra${RESET} ${FG_MUTED}runtime engine · $(mode_label)${RESET}"
        return 0
    }
    local width="$TERM_WIDTH"
    [ "$width" -gt 96 ] && width=96
    [ "$width" -lt 64 ] && width=64
    say ""
    center_text "${BOX_TL}$(repeat_char "$BOX_H" 46)${BOX_TR}" "$width"
    center_text "${BOX_V}              BIJMANTRA RUNTIME ENGINE              ${BOX_V}" "$width"
    center_text "${BOX_V}        BrAPI · REEVU · Compute · Field Ops         ${BOX_V}" "$width"
    center_text "${BOX_BL}$(repeat_char "$BOX_H" 46)${BOX_BR}" "$width"
    say ""
    typewrite_center "Orchestration Boot Sequence: $(mode_label)" "$FG_SECONDARY" "$width"
    say ""
}

boot_stage() {
    [ "$QUIET" -eq 1 ] && return 0
    [ "$UI_MODE" = "compact" ] && return 0
    printf '  %b %-24s%b %s\n' "$(status_token "starting")" "$1" "$RESET" "${FG_MUTED}${2}${RESET}"
    [ "$ANIMATION_ENABLED" -eq 1 ] && sleep 0.08
    return 0
}

render_boot_sequence() {
    boot_stage "workspace"       "$ROOT_DIR"
    boot_stage "runtime profile" "$(mode_label)"
    boot_stage "container engine" "$RUNTIME_NAME"
    boot_stage "startup log"     "$STARTUP_LOG"
}

# ─────────────────────────────────────────────────────────────────────
# HELP
# ─────────────────────────────────────────────────────────────────────
render_help() {
    plain "${BOLD}BijMantra Development Runtime${RESET}"
    plain ""
    plain "Usage: ./dev.sh [option] [ux flags]"
    plain ""
    plain "Runtime options:"
    plain "  (none)        Start PostgreSQL + backend + frontend"
    plain "  --all         Start product infra (+ Redis, MinIO, Meilisearch)"
    plain "  --chloe       Start experimental autonomy sidecars (+ BeingBijmantra, Chloe)"
    plain "  --minimal     Start PostgreSQL only"
    plain "  --auth        Include Keycloak authentication (combine with other modes)"
    plain "  --stop        Stop all BijMantra containers"
    plain "  --setup       First-time setup (build, migrate, seed, install)"
    plain "  --status      Show running containers and runtime probes"
    plain ""
    plain "UX flags:"
    plain "  --compact       Shorter sections and dashboard"
    plain "  --full          Cinematic banner and staged boot output"
    plain "  --quiet         Suppress non-essential output"
    plain "  --debug         Stream command logs to terminal as well as log files"
    plain "  --no-color      Disable ANSI colors"
    plain "  --no-animation  Disable spinners/typewriter effects"
    plain "  --menu          Choose startup mode interactively"
    plain ""
    plain "Services:"
    plain "  Frontend       http://localhost:${FRONTEND_PORT}"
    plain "  Backend        http://localhost:${BACKEND_PORT}"
    plain "  API Docs       http://localhost:${BACKEND_PORT}/docs"
    plain "  PostgreSQL     localhost:${POSTGRES_PORT}"
    plain "  Redis          localhost:${REDIS_PORT}          (--all, --chloe)"
    plain "  MinIO          http://localhost:${MINIO_CONSOLE_PORT}   (--all, --chloe)"
    plain "  Meilisearch    http://localhost:${MEILISEARCH_PORT}     (--all, --chloe)"
    plain "  BeingBijmantra http://localhost:${BEINGBIJMANTRA_SURREAL_PORT}  (--chloe or make dev-beingbijmantra)"
    plain "  Keycloak       http://localhost:${KEYCLOAK_PORT}        (--auth)"
    plain "  Chloe Gateway  http://127.0.0.1:${OPENCLAW_GATEWAY_PORT}  (--chloe)"
    plain ""
    plain "Examples:"
    plain "  ./dev.sh                    # Core app (PostgreSQL + backend + frontend)"
    plain "  ./dev.sh --auth             # Core app + Keycloak"
    plain "  ./dev.sh --all --auth       # Product infra + Keycloak"
    plain "  ./dev.sh --chloe --auth     # Experimental autonomy sidecars + Keycloak"
    plain "  ./dev.sh --all              # Product-development stack"
}

# ─────────────────────────────────────────────────────────────────────
# INFRASTRUCTURE STARTUP
# ─────────────────────────────────────────────────────────────────────
start_infra() {
    section "Infrastructure"

    # Mark services not started in this mode as optional upfront
    if [ "$MODE" != "all" ] && [ "$MODE" != "chloe" ]; then
        for svc in redis minio meilisearch; do mark_optional "$svc"; done
    fi
    [ "$MODE" != "chloe" ] && mark_optional beingbijmantra
    [ "$WITH_AUTH" -ne 1 ] && mark_optional keycloak
    [ "$MODE" != "chloe" ] && mark_optional chloe

    case "$MODE" in
        all)
            info "Starting PostgreSQL + Redis + MinIO + Meilisearch"
            if [ "$WITH_AUTH" -eq 1 ]; then
                run_soft_step "Compose infra + auth profiles" \
                    "${COMPOSE[@]}" --profile infra --profile auth up -d
            else
                run_soft_step "Compose infra profile" \
                    "${COMPOSE[@]}" --profile infra up -d
            fi
            ;;
        chloe)
            info "Starting product infra + experimental autonomy sidecars"
            if [ "$WITH_AUTH" -eq 1 ]; then
                run_soft_step "Compose infra + chloe + auth profiles" \
                    "${COMPOSE[@]}" --profile infra --profile beingbijmantra --profile chloe --profile auth up -d
            else
                run_soft_step "Compose infra + chloe profiles" \
                    "${COMPOSE[@]}" --profile infra --profile beingbijmantra --profile chloe up -d
            fi
            ;;
        *)
            info "Starting PostgreSQL"
            if [ "$WITH_AUTH" -eq 1 ]; then
                run_soft_step "Compose PostgreSQL + Keycloak" \
                    "${COMPOSE[@]}" --profile auth up -d postgres keycloak-postgres keycloak
            else
                run_soft_step "Compose PostgreSQL service" \
                    "${COMPOSE[@]}" up -d postgres
            fi
            ;;
    esac

    mark_starting postgres
    wait_for_service "PostgreSQL stable TCP probe" 60 postgres_stable_ready \
        && mark_ready postgres \
        || { mark_failed postgres; fatal "PostgreSQL did not become ready. Run 'make startup-doctor' for diagnosis."; }

    if [ "$WITH_AUTH" -eq 1 ]; then
        mark_starting keycloak
        wait_for_service "Keycloak readiness probe" 60 keycloak_ready \
            && mark_ready keycloak \
            || { warn "Keycloak is not ready yet."; mark_degraded keycloak "readiness probe did not pass"; }
    fi

    if [ "$MODE" = "all" ] || [ "$MODE" = "chloe" ]; then
        mark_starting redis
        wait_for_service "Redis cache probe" 35 redis_ready \
            && mark_ready redis \
            || { warn "Redis is not ready yet; backend will use its configured fallback."; mark_degraded redis "readiness probe did not pass"; }

        mark_starting minio
        wait_for_service "MinIO object-store probe" 45 minio_ready \
            && mark_ready minio \
            || { warn "MinIO is not ready yet."; mark_degraded minio "readiness probe did not pass"; }

        mark_starting meilisearch
        wait_for_service "Meilisearch probe" 45 meilisearch_ready \
            && mark_ready meilisearch \
            || { warn "Meilisearch is not ready yet; search may be degraded."; mark_degraded meilisearch "readiness probe did not pass"; }

        if [ "$MODE" = "chloe" ]; then
            mark_starting beingbijmantra
            wait_for_service "BeingBijmantra sidecar probe" 45 beingbijmantra_ready \
                && mark_ready beingbijmantra \
                || { warn "BeingBijmantra sidecar is not ready yet."; mark_degraded beingbijmantra "readiness probe did not pass"; }
        fi
    fi

    if [ "$MODE" = "chloe" ]; then
        mark_starting chloe
        wait_for_service "Chloe gateway probe" 70 chloe_ready \
            && mark_ready chloe \
            || { warn "Chloe gateway is not ready yet. Check compose logs for bijmantra-chloe-gateway."; mark_degraded chloe "readiness probe did not pass"; }
    fi
}

# ─────────────────────────────────────────────────────────────────────
# SETUP / MIGRATIONS / BACKEND / FRONTEND
# ─────────────────────────────────────────────────────────────────────
verify_postgres_extensions() {
    local required_extensions="timescaledb vector postgis pg_trgm uuid-ossp pgcrypto pgaudit ltree"
    local ext result missing=""
    section "PostgreSQL Extensions"
    for ext in $required_extensions; do
        result="$("$RUNTIME" exec bijmantra-postgres psql -U bijmantra_user -d bijmantra_db \
            -tAc "SELECT extname FROM pg_extension WHERE extname = '$ext';" 2>/dev/null || true)"
        if [ -n "$result" ]; then
            status_row "$ext" "ready" "loaded"
        else
            status_row "$ext" "warn" "missing"
            missing="${missing} ${ext}"
        fi
    done
    if [ -n "$missing" ]; then
        warn "Missing extensions:${missing}. Rebuild with: ${COMPOSE[*]} build --no-cache postgres"
    else
        success "All required PostgreSQL extensions are loaded."
    fi
}

setup_stack() {
    section "First-Time Setup"
    run_step "Build PostgreSQL image (PostGIS + pgvector)" "${COMPOSE[@]}" build postgres
    run_soft_step "Start PostgreSQL service" "${COMPOSE[@]}" up -d postgres
    wait_for_service "PostgreSQL stable TCP probe" 60 postgres_stable_ready \
        || fatal "PostgreSQL did not become ready during setup."

    section "Backend Setup"
    run_step "Install backend dependencies" bash -lc "cd backend && uv sync --extra dev --extra analytics --extra geo"
    run_step "Apply Alembic migrations"     bash -lc "cd backend && uv run alembic upgrade head"
    verify_postgres_extensions
    run_step "Seed bootstrap admin" bash -lc "cd backend && uv run python -m app.db.seed --env=dev --scope=system --only=admin_user"
    run_step "Seed reference data" bash -lc "cd backend && uv run python -m app.db.seed --env=dev --scope=system --only=reference_data"
    run_step "Seed deterministic development data" bash -lc "cd backend && SEED_DEMO_DATA=true uv run python -m app.db.seed --env=dev"

    section "Frontend Setup"
    run_step "Install frontend dependencies" bash -lc "cd frontend && bun install"

    render_setup_summary
}

run_migrations() {
    section "Database"
    run_step "Apply Alembic migrations" bash -lc "cd backend && uv run alembic upgrade head"
}

seed_system_data() {
    section "System Seed"
    run_step "Seed bootstrap admin" bash -lc "cd backend && uv run python -m app.db.seed --env=dev --scope=system --only=admin_user"
    run_step "Seed reference data" bash -lc "cd backend && uv run python -m app.db.seed --env=dev --scope=system --only=reference_data"
}

start_backend() {
    section "Backend"
    export POSTGRES_SERVER="${POSTGRES_SERVER:-localhost}"
    export POSTGRES_PORT="${POSTGRES_PORT:-5432}"
    export POSTGRES_USER="${POSTGRES_USER:-bijmantra_user}"
    export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-changeme_in_production}"
    export POSTGRES_DB="${POSTGRES_DB:-bijmantra_db}"
    export SECRET_KEY="${SECRET_KEY:-dev_secret_key_for_local_development_only_do_not_use_in_production}"
    export DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/lib:${DYLD_FALLBACK_LIBRARY_PATH:-}"

    : > "$BACKEND_LOG"
    status_row "database authority" "ready" "${POSTGRES_SERVER}:${POSTGRES_PORT}/${POSTGRES_DB}"

    if backend_ready >/dev/null 2>&1; then
        if [ "$WITH_AUTH" -eq 1 ]; then
            restart_existing_backend_for_auth
        else
            emit_event INFO "Backend API already responding on port ${BACKEND_PORT}"
            mark_ready backend
            status_row "FastAPI backend" "ready" "existing service on port ${BACKEND_PORT}"
            return 0
        fi
    fi

    mark_starting backend
    if [ "$DEBUG" -eq 1 ]; then
        (cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port "$BACKEND_PORT") \
            > >(tee -a "$BACKEND_LOG") 2>&1 &
    else
        (cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port "$BACKEND_PORT") \
            >> "$BACKEND_LOG" 2>&1 &
    fi
    BACKEND_PID=$!
    SERVICE_PID[backend]="$BACKEND_PID"
    status_row "FastAPI backend" "starting" "pid ${BACKEND_PID}; log ${BACKEND_LOG}"

    wait_for_service "Backend health endpoint" 70 backend_ready \
        && mark_ready backend \
        || { warn "Backend health did not become ready on port ${BACKEND_PORT}. See ${BACKEND_LOG}."; mark_degraded backend "health endpoint did not pass"; }
}

check_wasm_sync() {
    if has_cmd make; then
        if ! run_advisory_step "Check Rust/WASM genomics bundle" make check-wasm-sync; then
            warn "WASM binary is stale or missing. Run 'make wasm' to rebuild the genomics engine."
        fi
    else
        status_row "WASM freshness" "skip" "make not available"
    fi
}

start_frontend() {
    : > "$FRONTEND_LOG"
    if frontend_ready >/dev/null 2>&1; then
        emit_event INFO "Frontend already responding on port ${FRONTEND_PORT}"
        mark_ready frontend
        status_row "Vite frontend" "ready" "existing service on port ${FRONTEND_PORT}"
        return 0
    fi

    mark_starting frontend
    if [ "$DEBUG" -eq 1 ]; then
        (cd frontend && bun run dev) > >(tee -a "$FRONTEND_LOG") 2>&1 &
    else
        (cd frontend && bun run dev) >> "$FRONTEND_LOG" 2>&1 &
    fi
    FRONTEND_PID=$!
    SERVICE_PID[frontend]="$FRONTEND_PID"
    status_row "Vite frontend" "starting" "pid ${FRONTEND_PID}; log ${FRONTEND_LOG}"

    wait_for_service "Frontend dev server" 45 frontend_ready \
        && mark_ready frontend \
        || { warn "Frontend did not become ready on port ${FRONTEND_PORT}. See ${FRONTEND_LOG}."; mark_degraded frontend "readiness probe did not pass"; }
}

# ─────────────────────────────────────────────────────────────────────
# SELF-HEALING WATCHER  (new in dev.sh)
# ─────────────────────────────────────────────────────────────────────
recover_service() {
    local svc="$1"
    emit_event WARN "${SERVICE_LABEL[$svc]:-$svc} crashed — attempting recovery"
    set_service_state "$svc" "degraded"
    render_live_dashboard
    sleep 2
    case "$svc" in
        backend)  start_backend ;;
        frontend) start_frontend ;;
        *) warn "No recovery handler for ${svc}." ;;
    esac
}

child_active() {
    local pid="$1" stat
    [ -n "$pid" ] || return 1
    kill -0 "$pid" >/dev/null 2>&1 || return 1
    stat="$(ps -p "$pid" -o stat= 2>/dev/null || true)"
    [[ "$stat" == *Z* ]] && return 1
    return 0
}

supervise_services() {
    while true; do
        if [ -n "$BACKEND_PID" ] && ! child_active "$BACKEND_PID"; then
            wait "$BACKEND_PID" 2>/dev/null || true
            recover_service backend
        fi
        if [ -n "$FRONTEND_PID" ] && ! child_active "$FRONTEND_PID"; then
            wait "$FRONTEND_PID" 2>/dev/null || true
            recover_service frontend
        fi
        sleep 2
    done
}

# ─────────────────────────────────────────────────────────────────────
# HEALTH PAYLOAD PARSERS  (from dev-original.sh)
# ─────────────────────────────────────────────────────────────────────
json_dependency_summary() {
    local payload="$1" dep="$2"
    [ -z "$payload" ] || ! has_cmd python3 && { printf 'unknown|health payload unavailable'; return 0; }
    printf '%s' "$payload" | python3 -c '
import json, sys
dep = sys.argv[1]
try:    data = json.load(sys.stdin)
except: print("unknown|health payload unreadable"); raise SystemExit(0)
value = data.get("dependencies", {}).get(dep, {})
status = value.get("status", "unknown")
detail = value.get("detail") or value.get("error") or ""
stats = value.get("stats") or {}
if stats:
    parts = [f"{k}={stats[k]}" for k in ("queue_size","running","pending","max_concurrent") if k in stats]
    detail = ", ".join(parts)
print(f"{status}|{detail}")
' "$dep"
}

json_root_status() {
    local payload="$1"
    [ -z "$payload" ] || ! has_cmd python3 && { printf 'unknown'; return 0; }
    printf '%s' "$payload" | python3 -c '
import json, sys
try:    print(json.load(sys.stdin).get("status","unknown"))
except: print("unknown")
'
}

worker_health_summary() {
    local payload="$1"
    [ -z "$payload" ] || ! has_cmd python3 && { printf 'unknown|external worker endpoint unavailable'; return 0; }
    printf '%s' "$payload" | python3 -c '
import json, sys
try:    data = json.load(sys.stdin)
except: print("unknown|external worker payload unreadable"); raise SystemExit(0)
total = data.get("total_workers", 0); healthy = data.get("healthy_workers", 0)
if total: print(f"healthy|{healthy}/{total} external workers registered")
else:     print("optional|no external compute workers registered")
'
}

# ─────────────────────────────────────────────────────────────────────
# FINAL DASHBOARD  (rich status panel after boot, from dev-original.sh)
# ─────────────────────────────────────────────────────────────────────
render_dashboard() {
    [ "$QUIET" -eq 1 ] && return 0
    local duration backend_payload backend_state dep_state dep_detail worker_payload worker_state worker_detail
    duration="$(format_duration "$(elapsed_seconds "$START_SECONDS")")"
    backend_payload="$(fetch_url "http://127.0.0.1:${BACKEND_PORT}/health")"
    backend_state="$(json_root_status "$backend_payload")"
    [ "$backend_state" = "unknown" ] && backend_state="$(service_probe_state backend_ready)"

    section "Runtime Control Panel"
    status_row "mode"              "ready" "$(mode_label)"
    status_row "environment"       "ready" "${ENVIRONMENT:-development}"
    if [ "$WITH_AUTH" -eq 1 ]; then
        status_row "auth provider" "ready" "Keycloak ${KEYCLOAK_ISSUER}"
    else
        status_row "auth provider" "optional" "local token mode; use --auth for Keycloak"
    fi
    status_row "container runtime" "ready" "$RUNTIME"
    status_row "startup duration"  "ready" "$duration"
    status_row "startup log"       "ready" "$STARTUP_LOG"

    divider "Services"
    status_row "PostgreSQL" "$(service_probe_state postgres_ready)" \
        "localhost:${POSTGRES_PORT} · $(container_health bijmantra-postgres)"

    IFS='|' read -r dep_state dep_detail <<< "$(json_dependency_summary "$backend_payload" "redis")"
    if [ "$MODE" = "all" ] || [ "$MODE" = "chloe" ] || redis_ready >/dev/null 2>&1; then
        status_row "Redis cache" "${dep_state:-$(service_probe_state redis_ready)}" \
            "localhost:${REDIS_PORT} ${dep_detail:+· ${dep_detail}}"
    else
        status_row "Redis cache" "optional" "off in this mode; backend can fall back in-memory"
    fi

    if [ "$MODE" = "all" ] || [ "$MODE" = "chloe" ] || minio_ready >/dev/null 2>&1; then
        status_row "MinIO object store" "$(optional_probe_state minio_ready)" \
            "api :${MINIO_PORT}, console :${MINIO_CONSOLE_PORT}"
    else
        status_row "MinIO object store" "optional" "off in this mode"
    fi

    IFS='|' read -r dep_state dep_detail <<< "$(json_dependency_summary "$backend_payload" "meilisearch")"
    if [ "$MODE" = "all" ] || [ "$MODE" = "chloe" ] || meilisearch_ready >/dev/null 2>&1; then
        status_row "Meilisearch" "${dep_state:-$(service_probe_state meilisearch_ready)}" \
            "http://localhost:${MEILISEARCH_PORT} ${dep_detail:+· ${dep_detail}}"
    else
        status_row "Meilisearch" "optional" "off in this mode; search may run degraded"
    fi

    if [ "$MODE" = "chloe" ] || beingbijmantra_ready >/dev/null 2>&1; then
        status_row "BeingBijmantra" "$(optional_probe_state beingbijmantra_ready)" \
            "http://localhost:${BEINGBIJMANTRA_SURREAL_PORT}"
    else
        status_row "BeingBijmantra" "optional" "off in this mode"
    fi

    if [ "$WITH_AUTH" -eq 1 ] || keycloak_ready >/dev/null 2>&1; then
        status_row "Keycloak" "$(optional_probe_state keycloak_ready)" "http://localhost:${KEYCLOAK_PORT}"
    else
        status_row "Keycloak" "optional" "off unless --auth is selected"
    fi

    status_row "Backend API" "$backend_state" "http://localhost:${BACKEND_PORT}"
    status_row "API Docs"    "$(service_probe_state api_docs_ready)" "http://localhost:${BACKEND_PORT}/docs"
    status_row "Frontend"    "$(service_probe_state frontend_ready)" "http://localhost:${FRONTEND_PORT}"

    IFS='|' read -r dep_state dep_detail <<< "$(json_dependency_summary "$backend_payload" "task_queue")"
    status_row "Task queue" "${dep_state:-unknown}" "${dep_detail:-in-process backend workers}"

    worker_payload="$(fetch_url "http://127.0.0.1:${BACKEND_PORT}/api/v2/workers/health")"
    IFS='|' read -r worker_state worker_detail <<< "$(worker_health_summary "$worker_payload")"
    status_row "Compute workers" "$worker_state" "$worker_detail"

    if [ "$MODE" = "chloe" ] || chloe_ready >/dev/null 2>&1; then
        status_row "Chloe gateway" "$(optional_probe_state chloe_ready)" \
            "http://127.0.0.1:${OPENCLAW_GATEWAY_PORT}"
    else
        status_row "Chloe gateway" "optional" "off unless --chloe is selected"
    fi

    status_row "REEVU AI surface" "$backend_state" "backend-managed; provider status is auth-protected"

    divider "Logs"
    status_row "backend log"  "ready" "$BACKEND_LOG"
    status_row "frontend log" "ready" "$FRONTEND_LOG"

    divider "Live Events"
    tail -n 6 "$EVENT_LOG" 2>/dev/null | sed 's/^/  /' || true

    say ""
    say "${FG_PRIMARY}${BOLD}BijMantra is running.${RESET} ${FG_MUTED}Press Ctrl+C to stop backend/frontend. Infra containers stay up.${RESET}"
}

# ─────────────────────────────────────────────────────────────────────
# TELEMETRY LOOP  (new in dev.sh — live 1s refresh)
# ─────────────────────────────────────────────────────────────────────
telemetry_loop() {
    [ "$QUIET" -eq 1 ] && return 0
    while true; do
        render_live_dashboard
        sleep 1
    done
}

# ─────────────────────────────────────────────────────────────────────
# SUMMARY SCREENS
# ─────────────────────────────────────────────────────────────────────
render_minimal_summary() {
    section "Runtime Control Panel"
    status_row "mode"           "ready" "$(mode_label)"
    status_row "PostgreSQL"     "$(service_probe_state postgres_ready)" "localhost:${POSTGRES_PORT}"
    status_row "manual backend" "skip"  "cd backend && bash ./start_dev.sh"
    status_row "manual frontend" "skip" "cd frontend && bun run dev"
    status_row "startup log"    "ready" "$STARTUP_LOG"
}

render_setup_summary() {
    section "Setup Complete"
    status_row "PostgreSQL image" "ready" "PostGIS + pgvector stack built"
    status_row "backend deps"     "ready" "uv sync complete"
    status_row "migrations"       "ready" "alembic head applied"
    status_row "frontend deps"    "ready" "bun install complete"
    status_row "next command"     "ready" "./dev.sh"
}

# ─────────────────────────────────────────────────────────────────────
# STATUS / STOP
# ─────────────────────────────────────────────────────────────────────
show_status() {
    section "Container Status"
    "$RUNTIME" ps --filter "name=bijmantra" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null \
        || "$RUNTIME" ps --filter "name=bijmantra" 2>/dev/null || true

    section "Runtime Probes"
    status_row "PostgreSQL"     "$(service_probe_state postgres_ready)"      "localhost:${POSTGRES_PORT}"
    status_row "Redis cache"    "$(optional_probe_state redis_ready)"         "localhost:${REDIS_PORT}"
    status_row "MinIO"          "$(optional_probe_state minio_ready)"         "http://localhost:${MINIO_CONSOLE_PORT}"
    status_row "Meilisearch"    "$(optional_probe_state meilisearch_ready)"   "http://localhost:${MEILISEARCH_PORT}"
    status_row "BeingBijmantra" "$(optional_probe_state beingbijmantra_ready)" "http://localhost:${BEINGBIJMANTRA_SURREAL_PORT}"
    status_row "Keycloak"       "$(optional_probe_state keycloak_ready)"       "http://localhost:${KEYCLOAK_PORT}"
    status_row "Backend API"    "$(service_probe_state backend_ready)"        "http://localhost:${BACKEND_PORT}"
    status_row "Frontend"       "$(service_probe_state frontend_ready)"       "http://localhost:${FRONTEND_PORT}"
    status_row "Chloe gateway"  "$(optional_probe_state chloe_ready)"         "http://127.0.0.1:${OPENCLAW_GATEWAY_PORT}"
}

stop_stack() {
    section "Shutdown"
    run_soft_step "Stop profiled compose services" \
        "${COMPOSE[@]}" --profile infra --profile auth --profile tools --profile beingbijmantra --profile chloe down
    run_soft_step "Stop core compose services" "${COMPOSE[@]}" down
    if [ "$RUNTIME_NAME" = "podman" ]; then
        run_soft_step "Stop Podman machine" \
            "$RUNTIME" machine stop podman-machine-default
    fi
    success "All BijMantra services stopped cleanly."
}

# ─────────────────────────────────────────────────────────────────────
# CLEANUP / SIGNAL HANDLERS
# ─────────────────────────────────────────────────────────────────────
stop_child() {
    local label="$1" pid="$2"
    if [ -n "$pid" ] && kill -0 "$pid" >/dev/null 2>&1; then
        kill "$pid" >/dev/null 2>&1 || true
        wait "$pid" 2>/dev/null || true
        status_row "$label" "ok" "stopped pid ${pid}"
    else
        status_row "$label" "skip" "not running"
    fi
}

cleanup() {
    [ "$SHUTTING_DOWN" -eq 1 ] && return 0
    SHUTTING_DOWN=1
    show_cursor
    section "Disconnect"
    if [ -n "$TELEMETRY_PID" ]; then
        kill "$TELEMETRY_PID" >/dev/null 2>&1 || true
        wait "$TELEMETRY_PID" 2>/dev/null || true
    fi
    stop_child "backend"  "$BACKEND_PID"
    stop_child "frontend" "$FRONTEND_PID"

    # Always stop the Podman machine cleanly so the VM disk is never
    # left in a dirty state — safe to call even if machine is already
    # stopped, and takes only a few seconds.
    if [ "$RUNTIME_NAME" = "podman" ]; then
        info "Stopping Podman machine cleanly..."
        "$RUNTIME" machine stop podman-machine-default >/dev/null 2>&1 || true
        success "Podman machine stopped."
    fi

    success "All services stopped cleanly."
}

# ─────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────
main() {
    parse_args "$@"
    init_terminal
    trap show_cursor EXIT
    trap refresh_terminal_size WINCH

    if [ "$MODE" = "help" ]; then
        render_help
        exit 0
    fi

    choose_mode
    detect_runtime
    mkdir -p "$LOG_DIR"
    : > "$STARTUP_LOG"
    : > "$EVENT_LOG"
    log_note "BijMantra dev.sh mode=$(mode_label)"
    log_note "Root: $ROOT_DIR"
    log_note "Runtime: $RUNTIME"
    emit_event SYSTEM "Initializing runtime orchestration"

    render_banner
    render_boot_sequence
    preflight_required_tools
    configure_auth_environment

    case "$MODE" in
        stop)
            stop_stack
            exit 0
            ;;
        status)
            show_status
            exit 0
            ;;
        setup)
            setup_stack
            exit 0
            ;;
        *)
            ;;
    esac

    trap 'cleanup; exit 130' INT
    trap 'cleanup; exit 143' TERM
    trap 'cleanup; exit 129' HUP

    hide_cursor
    start_infra

    if [ "$MODE" = "minimal" ]; then
        show_cursor
        render_minimal_summary
        exit 0
    fi

    run_migrations
    seed_system_data
    auth_runtime_preflight
    start_backend
    check_wasm_sync
    start_frontend

    emit_event READY "All services started"

    render_dashboard

    if [ "$QUIET" -eq 0 ]; then
        telemetry_loop &
        TELEMETRY_PID=$!
    fi

    supervise_services

    cleanup
}

main "$@"
