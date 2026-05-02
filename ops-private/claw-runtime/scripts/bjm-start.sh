#!/bin/bash
# BijMantra Autonomous System - Start Script
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
CANONICAL_COMPOSE="$REPO_ROOT/ops-private/claw-runtime/compose/docker-compose.bijmantra.yml"
SCRIPT_DIR="$REPO_ROOT/ops-private/claw-runtime/scripts"
GATEWAY_CONTAINER_NAME="bijmantra-openclaw-gateway"

resolve_podman_socket() {
	local discovered_socket=""
	local linux_default_socket="/run/user/$(id -u)/podman/podman.sock"

	if [[ -n "${OPENCLAW_DOCKER_SOCKET:-}" ]]; then
		printf '%s\n' "$OPENCLAW_DOCKER_SOCKET"
		return 0
	fi

	discovered_socket="$(podman info --format '{{.Host.RemoteSocket.Path}}' 2>/dev/null || true)"
	discovered_socket="${discovered_socket#unix://}"
	if [[ -n "$discovered_socket" ]]; then
		printf '%s\n' "$discovered_socket"
		return 0
	fi

	if [[ -n "$linux_default_socket" ]]; then
		printf '%s\n' "$linux_default_socket"
		return 0
	fi

	echo "Unable to determine a Podman socket path. Set OPENCLAW_DOCKER_SOCKET explicitly." >&2
	return 1
}

wait_for_gateway_health() {
	local max_attempts="${1:-60}"
	local attempt="1"
	local gateway_status=""

	while [[ "$attempt" -le "$max_attempts" ]]; do
		gateway_status="$(podman inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$GATEWAY_CONTAINER_NAME" 2>/dev/null || true)"
		if [[ "$gateway_status" == "healthy" ]]; then
			echo "OpenClaw gateway is healthy."
			return 0
		fi
		if [[ "$gateway_status" == "unhealthy" || "$gateway_status" == "exited" ]]; then
			echo "OpenClaw gateway failed to become healthy (status: $gateway_status)." >&2
			podman logs --tail 100 "$GATEWAY_CONTAINER_NAME" >&2 || true
			return 1
		fi
		sleep 2
		attempt="$((attempt + 1))"
	done

	echo "Timed out waiting for OpenClaw gateway health." >&2
	podman logs --tail 100 "$GATEWAY_CONTAINER_NAME" >&2 || true
	return 1
}

echo "🚀 Starting BijMantra Autonomous System..."

# 1. Start Podman VM
echo "--- Starting Podman Machine ---"
podman_machine_start_output=""
if ! podman_machine_start_output="$(podman machine start 2>&1)"; then
	if [[ "$podman_machine_start_output" == *"already running"* ]]; then
		echo "Podman machine already running."
	else
		printf '%s\n' "$podman_machine_start_output" >&2
		exit 1
	fi
elif [[ -n "$podman_machine_start_output" ]]; then
	printf '%s\n' "$podman_machine_start_output"
fi

# 2. Start Project Containers (Gateway, Postgres, Redis)
echo "--- Starting Project Stack ---"
cd "$REPO_ROOT"
RUNTIME_HOME="${BIJMANTRA_CLAW_RUNTIME_HOME:-${OPENCLAW_CONFIG_DIR:-$HOME/.bijmantra/runtime/claw}}"
export BIJMANTRA_CLAW_RUNTIME_HOME="$RUNTIME_HOME"
export OPENCLAW_CONFIG_DIR="${OPENCLAW_CONFIG_DIR:-$RUNTIME_HOME}"
export OPENCLAW_WORKSPACE_DIR="${OPENCLAW_WORKSPACE_DIR:-$REPO_ROOT}"
export OPENCLAW_DOCKER_SOCKET="$(resolve_podman_socket)"
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-bijmantra-private-runtime}"
if [[ -z "${OPENCLAW_GATEWAY_TOKEN:-}" ]]; then
	echo "OPENCLAW_GATEWAY_TOKEN must be set before starting the private runtime stack." >&2
	echo "Use a local operator token that matches $OPENCLAW_CONFIG_DIR/openclaw.json." >&2
	exit 1
fi
mkdir -p "$OPENCLAW_CONFIG_DIR"
podman-compose -p "$COMPOSE_PROJECT_NAME" -f "$CANONICAL_COMPOSE" up -d

echo "--- Waiting for OpenClaw Gateway ---"
wait_for_gateway_health

# 3. Sync Jobs (OpenClaw Bridge)
echo "--- Syncing Jobs to OpenClaw ---"
# Note: Active model comes from $OPENCLAW_CONFIG_DIR/agents.yaml.
# Seed provider auth by linking a channel, then bind the existing `main` agent.
# Example:
#   OPENCLAW_STATE_DIR="$OPENCLAW_CONFIG_DIR" openclaw channels add ...
#   OPENCLAW_STATE_DIR="$OPENCLAW_CONFIG_DIR" openclaw agents bind --agent main --bind <channel[:account]>
python3 "$SCRIPT_DIR/bijmantra_cron_bridge.py" --apply

# 4. Start Watchdog (Monitoring)
echo "--- Starting Watchdog (Background) ---"
nohup python3 "$SCRIPT_DIR/bijmantra_watchdog.py" > "$OPENCLAW_CONFIG_DIR/watchdog.log" 2>&1 &

echo "✨ System started! Check $OPENCLAW_CONFIG_DIR/watchdog.log for monitoring details."
