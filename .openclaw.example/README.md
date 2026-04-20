# OpenClaw Example Runtime Home
> Warning: Always use NemoClaw Layer on OpenClaw

Use these files as bootstrap inputs for an operator-managed runtime home such as:

- `~/.bijmantra/runtime/claw`

Safe to publish from this directory:

1. `agents.yaml`
2. `bridge-config.yaml`
3. `openclaw.json`
4. this README

Never place live auth stores, device identity, paired-device state, sessions, cron run output, watchdog output, closeout receipts, or provider secrets in this example directory.

Suggested bootstrap flow:

1. Create the runtime home: `mkdir -p ~/.bijmantra/runtime/claw`
2. Copy the example files into that runtime home.
3. Replace the placeholder gateway token in `openclaw.json` and `bridge-config.yaml` with a locally generated operator token.
4. Build the sandbox image before starting the runtime: `podman build -f Dockerfile.bijmantra-sandbox -t bijmantra-sandbox:latest .`
5. Build the local OpenClaw wrapper image with a Docker CLI before starting the runtime: `podman build -f ops-private/claw-runtime/Dockerfile.openclaw -t bijmantra-openclaw:latest ops-private/claw-runtime`
6. Seed credentials separately with `OPENCLAW_STATE_DIR=~/.bijmantra/runtime/claw openclaw channels add ...` or `openclaw channels login`, then bind the existing default agent with `OPENCLAW_STATE_DIR=~/.bijmantra/runtime/claw openclaw agents bind --agent main --bind <channel[:account]>`.
7. Copy the provider auth store into the BijMantra runtime agent after seeding `main`: `mkdir -p ~/.bijmantra/runtime/claw/agents/bijmantra-dev/agent && cp ~/.bijmantra/runtime/claw/agents/main/agent/auth-profiles.json ~/.bijmantra/runtime/claw/agents/bijmantra-dev/agent/auth-profiles.json`
8. Export `OPENCLAW_CONFIG_DIR=~/.bijmantra/runtime/claw` before running the private operator stack. For containerized Podman runs on macOS Podman Machine, also export `OPENCLAW_DOCKER_SOCKET="$(podman info --format '{{.Host.RemoteSocket.Path}}' | sed 's#^unix://##')"` or use `ops-private/claw-runtime/scripts/bjm-start.sh`, which resolves it automatically.
9. Approve fresh device pairing from the external runtime home; do not copy old `identity/`, `devices/`, `agents/*/sessions/`, or `cron/` state from a removed repo-local runtime.

Configuration note:

- `openclaw.json` is the canonical OpenClaw runtime configuration for agent registration and sandbox behavior.
- `agents.yaml` is the BijMantra bridge-side model contract used to resolve the reviewed queue's canonical model defaults.

The product repo only keeps the contract examples. Live execution state must stay outside the repo.