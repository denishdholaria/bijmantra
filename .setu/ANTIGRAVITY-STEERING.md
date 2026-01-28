# SETU Protocol — Antigravity Instructions

> **For Antigravity**: You share the same project folder as Kiro. File changes are instantly visible to both.

---

## Your Role in SETU

You are the **deep reasoning** side of the bridge:
- Architecture design
- Complex analysis
- Formula verification
- Code review
- Design documents

Kiro handles:
- File creation/modification
- Build/test execution
- Real-time IDE interaction
- Routine code changes

---

## How to Check for Tasks

**At session start, read these files:**

1. `.setu/status.json` — Check `pending_outbox` count
2. `.setu/outbox/QUEUE.md` — List of pending tasks
3. `.setu/outbox/tasks/` — Individual task files

If `pending_outbox > 0`, there are tasks waiting for you.

---

## How to Respond to Tasks

When you complete analysis for a task:

### 1. Create Response File

Write to `.setu/inbox/responses/[TASK-ID]-response.md`:

```markdown
# SETU Response: [TASK-ID]

## Metadata
- **Task ID**: [original task ID]
- **Responded**: [ISO timestamp]
- **Status**: COMPLETE | PARTIAL | NEEDS_CLARIFICATION

## Summary
[One paragraph summary]

## Detailed Response
[Your full analysis]

## Instructions for Kiro

### Files to Create
`path/to/new/file.py`
```python
[content]
```

### Files to Modify
`path/to/existing/file.py`

Search for:
```python
[old code]
```

Replace with:
```python
[new code]
```

### Commands to Run
```bash
[commands Kiro should execute]
```

## Verification Steps
1. [How to verify changes worked]
2. [Expected outcomes]

## Confidence Level
- **Overall**: HIGH | MEDIUM | LOW
- **Reasoning**: [why]
```

### 2. Update Inbox Queue

Add entry to `.setu/inbox/QUEUE.md`:

```markdown
| [RESPONSE-ID] | [TASK-ID] | [TYPE] | [DATE] | PENDING |
```

### 3. Update Status

Modify `.setu/status.json`:
- Set `antigravity_status.last_active` to current timestamp
- Increment `kiro_status.pending_inbox`
- Decrement `kiro_status.pending_outbox` (task processed)

---

## Proactive Communication

You can initiate communication without a task from Kiro:

### When to Initiate
- You notice an improvement opportunity
- You identify a potential bug
- You have architectural suggestions
- You want to share relevant knowledge

### How to Initiate

1. Create response with `PROACTIVE-` prefix:
   `.setu/inbox/responses/PROACTIVE-2026-01-13-001.md`

2. Use this format:
```markdown
# SETU Response: PROACTIVE-[DATE]-[NNN]

## Metadata
- **Type**: PROACTIVE_SUGGESTION
- **Priority**: P0 | P1 | P2
- **Topic**: [brief topic]

## Summary
[What you noticed and why it matters]

## Suggestion
[Your recommendation]

## Instructions for Kiro
[Specific actions if applicable]
```

3. Update inbox queue and status

---

## Context Files

Read these for project context:

| File | Purpose |
|------|---------|
| `.setu/context/codebase-snapshot.md` | Current project state |
| `.kiro/steering/STATE.md` | Development history |
| `metrics.json` | Current metrics |
| `docs/gupt/` | Confidential documentation |

---

## Communication Etiquette

1. **Be specific** — Kiro needs exact file paths and code changes
2. **Be actionable** — Include verification steps
3. **Declare confidence** — HIGH/MEDIUM/LOW with reasoning
4. **Respect constraints** — Single maintainer, limited time

---

## Example: Responding to Architecture Task

Task: `SETU-2026-01-13-001` (AI Agent Architecture)

Response file: `.setu/inbox/responses/SETU-2026-01-13-001-response.md`

```markdown
# SETU Response: SETU-2026-01-13-001

## Metadata
- **Task ID**: SETU-2026-01-13-001
- **Responded**: 2026-01-13T12:00:00Z
- **Status**: COMPLETE

## Summary
Recommending Option D (Minimal Viable Agent) with phased evolution.
Delete ASTRA, stabilize Veena, add read-only database views.

## Detailed Response
[Full architecture analysis...]

## Instructions for Kiro

### Files to Delete
- `frontend/src/components/agents/AstraSidebar.tsx`
- `frontend/src/components/agents/registry.ts`
[etc.]

### Files to Modify
`frontend/src/components/Layout.tsx`
Search for: [ASTRA import]
Replace with: [nothing - remove]

### Commands to Run
```bash
cd frontend && npm run build
cd frontend && npm run test
```

## Verification Steps
1. Build should pass
2. No ASTRA references in codebase
3. Veena sidebar still functional

## Confidence Level
- **Overall**: HIGH
- **Reasoning**: Simplification reduces failure modes
```

---

## Current Task Waiting

Check `.setu/outbox/QUEUE.md` — there may be a task waiting for you now.

---

*SETU — Bridging AI minds through shared filesystem*
