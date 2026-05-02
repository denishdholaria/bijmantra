---
name: "Migration Doctor"
description: "Use when Alembic revisions, schema drift, or migration ordering break BijMantra startup, tests, or deployment workflows."
argument-hint: "Revision error, schema drift, or failing migration command"
agent: "agent"
---
Diagnose and, when safe, fix a BijMantra migration or schema-drift problem.

- Start with [operator quickstart](../docs/ai/2026-03-30-ai-operator-quickstart.md), [copilot instructions](../copilot-instructions.md), and the matching instruction under [../instructions](../instructions/).
- Inspect `backend/alembic/versions/`, the current revision chain, heads, startup callers, model metadata, and any failing migration or test output before editing anything.
- Fix root cause with additive, reviewable changes. Preserve migration history unless the user explicitly asks for a reset strategy.
- Do not delete revisions, rewrite unrelated history, or recommend destructive database resets as the default response.
- Keep tenant boundaries, enum handling, indexes, and row-level-security expectations intact when touching persistence.

Return:

1. Root cause.
2. Fix applied or exact blocker.
3. Verification performed.
4. Any residual migration risk.
