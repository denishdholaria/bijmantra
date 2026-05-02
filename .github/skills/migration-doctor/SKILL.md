---
name: migration-doctor
description: 'Diagnose BijMantra Alembic revision failures, missing revision ids, schema drift, and startup errors such as Cannot locate revision or database not up to date. Use when migrations, startup, or tests fail around Alembic state.'
argument-hint: 'Revision error, schema drift, or failing migration command'
---

# Migration Doctor

## When To Use

- Alembic reports `Can't locate revision identified by ...`.
- Startup fails during the migration phase.
- Tests or local runtime report schema drift or an out-of-date database.
- You need a safe diagnosis of local revision-chain integrity before editing migrations.

## Procedure

1. Read `.github/copilot-instructions.md` and `.github/instructions/backend-migrations.instructions.md`.
2. Run `make migration-doctor`.
3. Separate local graph failures from database-state failures.
4. Fix root cause with additive, reversible migration changes.
5. Rerun `make migration-doctor`, then rerun the blocked startup or test command.

## Guardrails

- Do not delete or rewrite migration history as the default response.
- Treat `backend/alembic/versions/` as the canonical local revision chain.
- Preserve tenant boundaries, enum handling, indexes, and reversible rollout patterns.
- Prefer targeted fixes over destructive database resets.

## References

- [repo anchors](./references/repo-anchors.md)
