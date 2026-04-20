# BijMantra Agent Workflow

This repository already contains agent guidance, but some of it is easy to miss because it lives in dotfolders.

This file makes the active workflow visible at the repo root.

For the shortest route from operator intent to the correct control surface, use `.github/docs/ai/2026-03-30-ai-operator-quickstart.md` after reading this file once.

## Canonical Instruction Sources

Use these in order:

1. `.github/copilot-instructions.md`
   - primary repo-wide coding and workflow rules
2. `metrics.json`
   - single source of truth for repo metrics and milestone metadata
3. `.ai/README.md` and `.ai/AGENT_COORDINATION_PROTOCOL.md`
   - multi-agent planning and coordination flow
4. `.ai/proposals/`, `.ai/reviews/`, `.ai/decisions/`, and `.ai/tasks/`
   - active repository-local architecture and execution trail

## Current Repo Reality

- Repo-wide Copilot instructions exist and are active.
- The repo has an `.ai/` coordination area for proposals, reviews, decisions, and tasks.
- Some older guidance still refers to `.kiro/steering/*`, but missing steering files should not outrank current workspace evidence or the active `.ai/` trail.
- The repo has an `.agent/jobs/` folder with a canonical JSON overnight queue for OmShriMaatreNamaha; use it as a queue surface, not as a second architecture trail.
- The app now has a hidden internal developer master board at `/admin/developer/master-board`; use it as the in-app master-plan and sub-plan surface for BijMantra app-development coordination, not as a public workspace page.
- The visible project-memory surface lives in the sibling docs workspace at `confidential-docs/ai/2026-03-18-project-memory-surface.md`; use it to record durable architecture intent that humans and agents should both be able to inspect without relying on hidden Copilot memory.
- The repo now has a repo-local `.github/instructions/` library for shared path-scoped guidance and a `.github/prompts/` library for repeatable operator kickoffs.
- The repo now also has a repo-local `.github/skills/` library for repeatable specialist workflows.
- The first-wave REEVU authority surface is currently locked by `.github/docs/architecture/2026-03-29-reevu-trusted-surface-map.md`; agents may harden code inside that surface, but must not silently expand or reclassify trusted versus partial REEVU surfaces without a fresh repo-grounded re-audit and matching doc updates.

## Project Memory Surface

Use two layers on purpose:

1. Visible repo memory:
   - `.github/docs/ai/2026-03-18-project-memory-surface.md`
   - Holds durable project intent, sovereignty rules, interoperability posture, and other guidance that should remain legible to humans and agents.
2. Copilot memory:
   - `/memories/` and `/memories/repo/`
   - Holds compact operational recall for agent continuity, but should not be treated as the only durable surface for important project rules.

Default rule:

- if a rule matters to long-term architecture or product identity, mirror it in the visible repo memory surface
- if a note is just short-lived or agent-operational, keep it in Copilot memory only

## Active Agent System

The current accepted custom-agent set is the Phase-1 seven-agent role system recorded in `.ai/decisions/ADR-009-phase1-seven-agent-role-system.md`.

The practical usage guide lives in `.github/agents/2026-03-13-phase1-agent-operator-guide.md`.

The reusable prompt templates live in `.github/agents/2026-03-13-phase1-agent-prompt-cookbook.md`.

Repo-wide repeatable operator kickoffs and specialist workflows now live in `.github/prompts/` and `.github/skills/`.

Use it when you need:

1. the right agent for a task
2. prompt shapes for single-agent work
3. coordinated prompting through the orchestrator
4. guardrails to avoid overlapping roles

Default rule:

- start with `OmShriMaatreNamaha` for multi-agent coordination
- use the specialist agents directly when the task has one clear owner
- `OmShreemMahalakshmiyeiNamaha` and `OmKlimKalikayeiNamah` are support roles and are typically routed indirectly rather than used as default picker choices

## Recommended Default Workflow

For normal implementation work:

1. Read `.github/copilot-instructions.md`.
2. Identify the affected domain and current architecture boundary.
3. Check whether the touched file is already a hot file or carries an agent index; if so, prefer extraction-first slices and track deferred splits in `.ai/tasks/` instead of growing the file further.
4. Make the smallest valid change that respects the domain model.
5. Update `metrics.json` when project-state metadata should change.
6. Verify the touched files or commands before closing work.

For unattended overnight orchestration:

1. Put eligible job cards in `.agent/jobs/overnight-queue.json`.
2. Build the dispatch plan with `make overnight-plan`.
3. Let `OmShriMaatreNamaha` own routing and closure from one control plane.
4. Run `make update-state` after the overnight slice changes tracked state.

For architecture or cross-domain planning:

1. Draft a proposal in `.ai/proposals/`.
2. Add review notes in `.ai/reviews/` when critique is needed.
3. Record accepted decisions in `.ai/decisions/`.
4. Drive implementation tasks from `.ai/tasks/` or the active architecture docs.

## Non-Negotiable Rules

- No mock data in production paths.
- Use Podman-oriented workflows, not Docker-first assumptions.
- Keep Python as orchestration, Rust as acceleration or WASM, and Fortran as validated numerical compute unless architecture decisions explicitly change that.
- Keep scientific provenance, assumptions, uncertainty, and validation visible.
- Do not introduce new runtimes or engines without registry, validation, and ownership clarity.
- For canonical REEVU work, treat `.github/docs/architecture/2026-03-29-reevu-trusted-surface-map.md` and `.github/instructions/reevu-trusted-surfaces.instructions.md` as the control surfaces that govern which first-wave trust surfaces are locked, partial, or out of scope.

## Further Expansion Rules

The repo already has active `.github/instructions/`, `.github/prompts/`, and `.github/skills/` libraries.

Only expand them when the new surface removes real repeated ambiguity:

1. expand `.github/instructions/*.instructions.md`
   - only where a real high-friction path still lacks targeted guidance
2. add `.github/prompts/*.prompt.md` or `.github/skills/<skill>/SKILL.md`
   - only for repeatable workflows with clear reuse evidence
3. add additional agent workflow templates under `.ai/`
   - only when current packaging still leaves a proven planning or review gap

These surfaces are useful only when they reduce ambiguity.

They should not become a second codebase made of process files.
