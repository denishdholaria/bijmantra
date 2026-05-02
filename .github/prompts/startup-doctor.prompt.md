---
name: "Startup Doctor"
description: "Use when BijMantra fails to start locally or the dev stack only partially boots. Diagnoses startup, dependency, Podman, backend, frontend, and env issues."
argument-hint: "Observed error, failing command, or blocked service"
agent: "agent"
---
Diagnose and, when safe, fix a local BijMantra startup failure.

- Start with [operator quickstart](../docs/ai/2026-03-30-ai-operator-quickstart.md), [copilot instructions](../copilot-instructions.md), and [AGENTS.md](../../AGENTS.md).
- Inspect the actual failing command, `start-bijmantra-app.sh`, `Makefile`, backend and frontend startup paths, Podman services, migrations, and environment assumptions before proposing a fix.
- Prefer minimal repo fixes over local-only workarounds when the repo is clearly wrong.
- Avoid destructive actions such as deleting databases, wiping migration history, or resetting unrelated local state unless the user explicitly asks.
- If the issue is environment-only, identify the exact missing prerequisite or local configuration gap.
- When code or script changes are needed, keep them additive and targeted.

Return:

1. Root cause.
2. Fix applied or exact blocker.
3. Verification performed.
4. Any safe next step still required.
