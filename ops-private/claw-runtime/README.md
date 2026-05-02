# KRABI Staged Private-Ops Boundary

This directory is the staged private-ops ownership boundary for the claw execution fabric.

Canonical private-ops surfaces currently staged here:

1. `compose/docker-compose.bijmantra.yml`
2. `ops-private/claw-runtime/scripts/bjm-start.sh`
3. `ops-private/claw-runtime/scripts/bijmantra_cron_bridge.py`
4. `ops-private/claw-runtime/scripts/bijmantra_watchdog.py`
5. `ops-private/claw-runtime/scripts/bijmantra_ctl.py`
6. `ops-private/claw-runtime/scripts/sandbox_policy_manager.py`
7. `policies/bijmantra-sandbox.yaml`
8. `policies/bijmantra-bca-observe.yaml`
9. `policies/bijmantra-bca-edit.yaml`
10. `policies/bijmantra-bca-local-verify.yaml`

Boundary rules:

1. This tree is operator-only and excluded from public sync.
2. The product repo contract remains the reviewed queue, normalized runtime reads, and sanitized examples.
3. Live runtime state stays outside the repo in `~/.bijmantra/runtime/claw`.
4. Canonical operator entrypoints now live only under `ops-private/claw-runtime/`; the former root compatibility mirror and shim files have been removed.
5. The reviewed queue is immutable after export; runtime lifecycle is tracked in watchdog state and mission-evidence receipts, not by rewriting `.agent/jobs/overnight-queue.json`.
6. The canonical compose stack defaults to loopback-only token-authenticated gateway access; operators must set `OPENCLAW_GATEWAY_TOKEN` explicitly before startup.
7. Policy profiles in this repo are operator-only staged sources, not public product contract and not end-user selectable runtime modes.
8. `sandbox_policy_manager.py` validates and inspects policy declarations, but static validation is not proof of runtime enforcement by itself.
9. Live runtime state, auth, session material, and mutable receipts remain external to the repo even when policy source is versioned here.

Post-rotation expectations:

1. Repo-local `.openclaw` runtime state is invalid and should remain absent.
2. Bootstrap only from `.openclaw.example/` into `~/.bijmantra/runtime/claw`.
3. Seed provider auth locally by linking a provider channel with `OPENCLAW_STATE_DIR=~/.bijmantra/runtime/claw openclaw channels add ...` or `openclaw channels login`, then bind the existing default agent with `OPENCLAW_STATE_DIR=~/.bijmantra/runtime/claw openclaw agents bind --agent main --bind <channel[:account]>` before runtime start.
4. Approve fresh device pairing from the external runtime home; do not restore old `identity/`, `devices/`, `agents/*/sessions/`, or `cron/` state.
5. Always mount the BijMantra repo root into `/home/node/.openclaw/workspace`; `ops-private/claw-runtime/scripts/bjm-start.sh` now exports `OPENCLAW_WORKSPACE_DIR` automatically, and manual compose starts must set it explicitly.
6. Always expose a Docker-compatible container-runtime socket to the gateway for tool sandboxing; `ops-private/claw-runtime/scripts/bjm-start.sh` now resolves and exports `OPENCLAW_DOCKER_SOCKET` from Podman's VM-side remote socket path, and manual compose starts should derive it from `podman info --format '{{.Host.RemoteSocket.Path}}'` and strip any leading `unix://` prefix.
7. Treat `openclaw.json` as the canonical OpenClaw runtime config surface for agent registration and sandbox mode. The repo's `agents.yaml` remains the BijMantra bridge-side model contract and must stay aligned, but it is not the gateway's authoritative multi-agent config by itself.
8. The private runtime now builds a thin local `bijmantra-openclaw:latest` image from `ops-private/claw-runtime/Dockerfile.openclaw` so the gateway and CLI include a Docker client binary required by OpenClaw's docker-backed sandbox launcher.
9. On Podman Machine hosts, the gateway runs as `root` with `label=disable` because the VM-side Podman socket is otherwise unreadable from inside the container even when the Docker CLI is present.

Next extraction step after this cutover:

1. keep future operator runtime resets and credential rotations constrained to the external runtime home.

Current BCA profile foundation:

1. `bijmantra-bca-observe.yaml` is the bounded read-only inspection profile.
2. `bijmantra-bca-edit.yaml` is the bounded local edit profile with no public egress and no package installation.
3. `bijmantra-bca-local-verify.yaml` is the bounded local verification profile with local-service-only network allowances.
4. Active profile selection remains operator-managed; profile-selection automation is intentionally out of scope for this slice.
