---
name: startup-doctor
description: 'Diagnose BijMantra local startup failures, partially booted dev stacks, missing prerequisites, Podman issues, and unhealthy backend or frontend services. Use when start-bijmantra-app.sh, make dev, make dev-backend, or make dev-frontend is blocked.'
argument-hint: 'Observed startup failure or failing command'
---

# Startup Doctor

## When To Use

- `bash ./start-bijmantra-app.sh` fails or only partially boots.
- `make dev`, `make dev-backend`, or `make dev-frontend` does not produce a usable local stack.
- You need a quick diagnosis of prerequisites, services, backend health, or frontend availability.

## Procedure

1. Read the active operator surfaces first:
   - `AGENTS.md`
   - `.github/copilot-instructions.md`
   - `.github/docs/ai/2026-03-30-ai-operator-quickstart.md`
2. Run `make startup-doctor`.
3. Use the output to separate failures from warnings.
4. If startup reaches the migration phase and fails there, run `make migration-doctor` next.
5. Apply the smallest safe fix, then rerun `make startup-doctor`.

## Expected Focus

- Prefer repo fixes over one-off local workarounds when the repo is clearly wrong.
- Keep Podman-oriented assumptions.
- Do not delete containers, volumes, or databases as the default response.
- Avoid masking migration-chain problems under generic setup advice.

## References

- [repo anchors](./references/repo-anchors.md)
