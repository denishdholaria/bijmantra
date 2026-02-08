# SETU (सेतु) — Kiro ⟷ Antigravity Bridge

> **सेतु** — The bridge that connects two realms.

This folder enables **automatic bidirectional communication** between Kiro and Antigravity.

**Key Insight**: Both AIs share the same project folder. File writes are instantly visible to both.

## How It Works

```
┌─────────────────┐     .setu/ folder      ┌─────────────────┐
│      KIRO       │ ◄──────────────────────► │  ANTIGRAVITY   │
│  (writes here)  │    (shared filesystem)   │  (reads here)  │
└─────────────────┘                          └─────────────────┘
```

**No manual copying required!** When Kiro writes a task, Antigravity can read it immediately. When Antigravity writes a response, Kiro can process it immediately.

## Quick Start

### For Kiro
1. Write tasks to `outbox/tasks/`
2. Update `outbox/QUEUE.md` and `status.json`
3. Poll `inbox/QUEUE.md` for new responses
4. Process responses from `inbox/responses/`

### For Antigravity
1. Poll `outbox/QUEUE.md` for new tasks
2. Read task files from `outbox/tasks/`
3. Write responses to `inbox/responses/`
4. Update `inbox/QUEUE.md` and `status.json`

## Structure

```
.setu/
├── status.json          # Communication state (both update)
├── outbox/              # Kiro → Antigravity
│   ├── QUEUE.md         # Pending tasks
│   └── tasks/           # Task files
├── inbox/               # Antigravity → Kiro
│   ├── QUEUE.md         # Pending responses
│   └── responses/       # Response files
├── context/             # Shared context
└── archive/             # Completed communications
```

## Proactive Communication

Either AI can initiate:
- **Kiro**: "I found an issue that needs deep analysis" → creates task
- **Antigravity**: "I have a suggestion for improvement" → creates response

## Protocol Documentation

See `docs/gupt/SETU-COMMUNICATION-SYSTEM.md` for full specification.

---

*Last Updated: January 13, 2026*
