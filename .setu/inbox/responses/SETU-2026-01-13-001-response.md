# SETU Response: SETU-2026-01-13-001

## Metadata

- **Task ID**: SETU-2026-01-13-001
- **Responded**: 2026-01-13T14:15:00+05:30
- **Status**: COMPLETE
- **Responder**: Antigravity (Claude)

---

## Summary

**Recommendation: Option D (Minimal Viable Agent) with Phased Evolution**

Delete ASTRA, consolidate to Veena-only, add read-only database views for safety. The architecture is over-engineered for a single maintainer. Strip down to working essentials, then rebuild incrementally.

---

## Detailed Response

### Architecture Decision: Single Agent (Veena Only)

After analyzing the codebase, I recommend **Option D (Minimal Viable Agent)** with evolution path to Option A:

```
┌─────────────────────────────────────────────────────────────┐
│                     CURRENT STATE (BROKEN)                  │
├─────────────────────────────────────────────────────────────┤
│  VeenaSidebar.tsx ──┐                                       │
│                     ├──► Conflict: Who owns right sidebar?  │
│  AstraSidebar.tsx ──┘                                       │
│                                                             │
│  ASTRA Registry: 5 agents                                   │
│    - Veena (working)                                        │
│    - REEVA (experimental, separate endpoint)                │
│    - Prithvi, Vayu, Artha (placeholders)                    │
│                                                             │
│  function_executor.py: Only search_germplasm uses real DB   │
│  Everything else returns demo=True                          │
└─────────────────────────────────────────────────────────────┘

                           ↓ MIGRATE TO ↓

┌─────────────────────────────────────────────────────────────┐
│                     TARGET STATE (STABLE)                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐     ┌──────────────────────────────────┐  │
│  │   VEENA      │────►│   Read-Only Data Access Layer    │  │
│  │  (Primary)   │     │   (PostgreSQL Views + Audit)     │  │
│  └──────────────┘     └──────────────────────────────────┘  │
│       │                                                     │
│       ├── Chat (General Q&A)                                │
│       ├── Search (Germplasm, Trials, etc.)                  │
│       ├── Navigate (Go to pages)                            │
│       └── Analyze (Read-only queries)                       │
│                                                             │
│  NO ASTRA. NO MULTIPLE AGENTS. JUST VEENA.                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Rationale

| Factor          | ASTRA (Multiple Agents)             | Veena-Only                 |
| --------------- | ----------------------------------- | -------------------------- |
| Maintainability | ❌ 5 agents to maintain             | ✅ 1 agent                 |
| UI Clarity      | ❌ User confusion about which agent | ✅ Clear single interface  |
| Data Flow       | ❌ Complex routing                  | ✅ Simple request/response |
| Testing         | ❌ 5x test surface                  | ✅ Focused testing         |
| Current Reality | ❌ Only Veena works anyway          | ✅ Matches reality         |

**Key Insight**: ASTRA's agent registry is aspirational architecture for a future that hasn't arrived. Currently:

- Veena: Partially working
- REEVA: Experimental, separate endpoint (localhost:8081)
- Prithvi, Vayu, Artha: **Placeholders with no backend**

Building infrastructure for 5 agents when you only have 1 working is premature optimization.

---

## Data Safety Model

### Critical Tables (AI Must Never Modify)

| Category         | Tables                                                       | Reason                    |
| ---------------- | ------------------------------------------------------------ | ------------------------- |
| **Germplasm**    | `germplasm`, `germplasm_attributes`, `pedigrees`             | Core genetic data         |
| **Observations** | `observations`, `observation_units`, `observation_variables` | Research data integrity   |
| **Trials**       | `trials`, `studies`, `treatments`, `experimental_designs`    | Scientific validity       |
| **Genomics**     | `samples`, `variants`, `marker_data`, `call_sets`            | Expensive sequencing data |
| **Breeding**     | `crosses`, `crossing_blocks`, `selections`                   | Breeding decisions        |

### Safe to Modify via AI

| Category             | Tables                                      | Why Safe                   |
| -------------------- | ------------------------------------------- | -------------------------- |
| **User Preferences** | `user_preferences`, `saved_filters`         | User-specific, recoverable |
| **Activity Logs**    | `activity_logs`, `audit_logs`               | AI viewing logs is fine    |
| **Notifications**    | `notifications`, `notification_preferences` | Low impact                 |
| **AI Internal**      | `conversations`, `messages`                 | Veena's own data           |

### Enforcement Strategy

**Option A: PostgreSQL Views (Recommended for Single Maintainer)**

```sql
-- Create read-only views for AI access
CREATE SCHEMA ai_readonly;

-- Germplasm view (AI can read, not write)
CREATE VIEW ai_readonly.germplasm AS
SELECT
  g.id, g.germplasm_name, g.default_display_name,
  g.species, g.subtaxa, g.pedigree_string,
  g.seed_source, g.acquisition_date, g.breeding_method_id,
  g.country_of_origin_code
FROM public.germplasm g
WHERE g.organization_id = current_setting('app.current_org_id')::int;

-- Create AI user with only SELECT on ai_readonly schema
CREATE ROLE veena_ai WITH LOGIN PASSWORD 'xxx';
GRANT USAGE ON SCHEMA ai_readonly TO veena_ai;
GRANT SELECT ON ALL TABLES IN SCHEMA ai_readonly TO veena_ai;
REVOKE ALL ON SCHEMA public FROM veena_ai;
```

**Option B: Application-Level Enforcement**

```python
# In function_executor.py - already partially implemented
class FunctionExecutor:
    """
    Veena's function executor.
    CRITICAL: Only read operations allowed on research data.
    """

    READONLY_PREFIXES = ["search_", "get_", "compare_", "analyze_", "calculate_"]
    WRITE_PREFIXES = ["create_", "record_", "update_"]  # Disabled for safety

    async def execute(self, function_name: str, parameters: Dict) -> Dict:
        # SAFETY: Reject write operations on critical data
        if any(function_name.startswith(p) for p in self.WRITE_PREFIXES):
            # Only allow writes to safe tables
            if not self._is_safe_write_operation(function_name, parameters):
                return {"success": False, "error": "Write operations disabled for data safety"}
        # ... rest of execution
```

**Recommendation**: Start with Option B (application-level) because it requires no database changes. Add Option A (views) when you have time.

---

## UI Integration Pattern

### Current Problem

```
Layout.tsx line 52-54:
  const VeenaSidebar = lazy(() => ...)  // Imported but NOT rendered

Layout.tsx line 56-58:
  const AstraSidebar = lazy(() => ...)  // Imported and rendered

Layout.tsx line 299-304:
  <AstraSidebar />  // ASTRA owns the right sidebar
```

VeenaSidebar exists but isn't rendered because AstraSidebar contains Veena. This is confusing architecture.

### Target State

```
┌─────────────────────────────────────────────────────────────┐
│                    SIMPLIFIED UI                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌──────────────────────┐  ┌────────────┐  │
│  │ Mahasarthi  │  │    Main Content      │  │   VEENA    │  │
│  │   (Left)    │  │                      │  │ (Right)    │  │
│  │             │  │                      │  │            │  │
│  │  Navigation │  │  Pages / Data        │  │  Chat      │  │
│  │             │  │                      │  │  Search    │  │
│  │             │  │                      │  │  Analyze   │  │
│  └─────────────┘  └──────────────────────┘  └────────────┘  │
│                                                             │
│  NO agent switcher. NO arsenal. JUST VEENA.                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Key Changes**:

1. Delete `AstraSidebar.tsx` (580 lines of complexity removed)
2. Delete `frontend/src/components/agents/` directory entirely
3. Use `VeenaSidebar.tsx` directly in Layout
4. Simplify to single AI interface

---

## Migration Plan

### Phase 1: Delete ASTRA (2 hours)

**Files to Delete:**

```
frontend/src/components/agents/AstraSidebar.tsx     (580 lines)
frontend/src/components/agents/registry.ts         (142 lines)
frontend/src/components/agents/types.ts
frontend/src/components/agents/useAgentArsenal.ts
```

**Files to Modify:**

`frontend/src/components/Layout.tsx`:

Search for:

```tsx
// ASTRA Agent Arsenal - unified agent sidebar (replaces individual agent sidebars)
const AstraSidebar = lazy(() => import("@/components/agents/AstraSidebar"));
```

Replace with:

```tsx
// DELETED: ASTRA Agent Arsenal - consolidated to VeenaSidebar
```

Search for:

```tsx
{
  /* ASTRA Agent Arsenal (Right side) */
}
<Suspense fallback={null}>
  <ComponentErrorBoundary>
    <AstraSidebar />
  </ComponentErrorBoundary>
</Suspense>;
```

Replace with:

```tsx
{
  /* Veena AI Assistant (Right side) */
}
<Suspense fallback={null}>
  <ComponentErrorBoundary>
    <VeenaSidebar />
  </ComponentErrorBoundary>
</Suspense>;
```

### Phase 2: Stabilize Veena Backend (4 hours)

**Current State of `function_executor.py`:**

- `search_germplasm`: ✅ Real database query
- Everything else: ❌ Returns `demo: True`

**Priority Order for Implementation:**

| Priority | Function                | Effort  | Impact                       |
| -------- | ----------------------- | ------- | ---------------------------- |
| P0       | `search_germplasm`      | ✅ Done | High                         |
| P1       | `get_germplasm_details` | 1 hour  | High - complete the flow     |
| P1       | `search_trials`         | 2 hours | High - researchers need this |
| P2       | `get_trial_results`     | 2 hours | Medium                       |
| P2       | `search_crosses`        | 1 hour  | Medium                       |
| P3       | Others                  | Defer   | Low - not requested          |

**Implementation Pattern** (copy search_germplasm pattern):

```python
# Example: Implementing get_germplasm_details
async def _handle_get(self, function_name: str, params: Dict) -> Dict:
    if function_name == "get_germplasm_details":
        germplasm_id = params.get("germplasm_id")
        if not germplasm_id:
            return {"success": False, "error": "germplasm_id required"}

        # Use existing germplasm service
        from app.api.v2.germplasm import get_germplasm_by_id
        try:
            result = await get_germplasm_by_id(self.db, germplasm_id)
            return {
                "success": True,
                "function": function_name,
                "result_type": "germplasm_details",
                "data": result.model_dump() if result else None,
                "demo": False  # Real data!
            }
        except Exception as e:
            logger.error(f"Get germplasm failed: {e}")
            return {"success": False, "error": str(e)}
```

### Phase 3: Add Read-Only Enforcement (2 hours)

1. Add `READONLY_MODE = True` flag to `function_executor.py`
2. Block all `create_*`, `update_*`, `record_*` functions
3. Log all AI data access for audit
4. Later: Add PostgreSQL views when needed

### Phase 4: Document and Test (2 hours)

1. Update README with simplified agent architecture
2. Write basic integration test for Veena chat flow
3. Manual testing: Can Veena search germplasm? ✓
4. Manual testing: Does sidebar open/close? ✓

---

## Verification Steps

### After Phase 1 (Delete ASTRA):

```bash
cd frontend && npm run build
# Should succeed with no imports from @/components/agents/

cd frontend && npm run test
# Should pass (no agent-related test failures)
```

**Manual Check:**

1. Open BijMantra in browser
2. Right sidebar should show Veena (not ASTRA arsenal)
3. Chat should still work

### After Phase 2 (Stabilize Veena):

```bash
cd backend && python -m pytest tests/test_function_executor.py -v
# (Create this test file if it doesn't exist)
```

**Manual Check:**

1. Ask Veena: "Search for drought-tolerant wheat"
2. Verify results come from actual database
3. Ask: "Show details for [germplasm_id]"
4. Verify actual record is returned

### After Phase 3 (Read-Only):

**Manual Check:**

1. Try to create a cross via Veena
2. Should get "Write operations disabled for safety" error
3. Check audit logs for the attempt

---

## Confidence Level

| Aspect               | Level  | Reasoning                                                 |
| -------------------- | ------ | --------------------------------------------------------- |
| **Delete ASTRA**     | HIGH   | Clear path, no dependencies, reduces complexity           |
| **Stabilize Veena**  | HIGH   | Pattern exists (search_germplasm), just needs replication |
| **Read-Only Safety** | MEDIUM | Need to verify all code paths block writes correctly      |
| **Overall**          | HIGH   | Simplification is the safest architectural choice         |

---

## Complexity Budget

For a single maintainer, I recommend:

| Metric                        | Budget   | Current       | Target                    |
| ----------------------------- | -------- | ------------- | ------------------------- |
| **Agent Count**               | 1-2 max  | 5 (ASTRA)     | 1 (Veena)                 |
| **Lines of Agent Code**       | <1000    | 2500+         | ~500                      |
| **Database Connection Pools** | 1        | 1             | 1 (+ readonly view later) |
| **External Dependencies**     | Minimize | LLM providers | Keep same                 |
| **Test Surface**              | Focused  | Scattered     | Clear paths               |

**Rule of Thumb**: If you can't explain the entire AI architecture in 2 minutes, it's too complex for a single maintainer.

---

## Future Evolution Path

Once Veena is stable and you have more time:

```
Phase 1: Veena Only (NOW)
    ↓
Phase 2: Veena + Workspace Awareness (Q2)
    - Veena changes prompts based on active workspace
    - No new agents, just context switching
    ↓
Phase 3: Veena + Specialists (Q3+)
    - Add domain specialists ONLY when needed
    - Each specialist must prove value before inclusion
```

**Critical Principle**: Don't add agents until Veena is rock solid. One working agent beats five broken ones.

---

## Summary of Actions for Kiro

### Immediate (Do Today):

1. Delete `frontend/src/components/agents/` directory
2. Update `Layout.tsx` to use VeenaSidebar instead of AstraSidebar
3. Run `npm run build` to verify no broken imports
4. Test that Veena chat still works

### This Week:

1. Implement `get_germplasm_details` in `function_executor.py`
2. Implement `search_trials` in `function_executor.py`
3. Add `READONLY_MODE` flag to block write operations

### This Month:

1. Create `ai_readonly` PostgreSQL schema
2. Set up AI audit logging
3. Document simplified architecture

---

_SETU Response — Bridging insight from Antigravity to Kiro for implementation_
