# Ralph Wiggum Technique (RWT) — Complete Standard

**Version:** 1.0  
**Applies to:** All UI, API, AI, workflow, data model, and integration design  
**Status:** Mandatory

---

## 1. Purpose

The **Ralph Wiggum Technique (RWT)** enforces **extreme clarity, explicitness, and defensive design** by assuming that:

- Users may be confused
- Data may be missing or wrong
- AI may hallucinate or misinterpret
- Developers may misunderstand intent
- Workflows may be followed incorrectly

The system **must still behave safely and correctly under these conditions**.

---

## 2. Core Principle (Non-Negotiable)

> **Design as if the user, the AI, and the future developer understand nothing and will misinterpret anything ambiguous.**

No feature may rely on:
- "Common sense"
- "User will know"
- "AI will infer"
- "This is obvious"

---

## 3. Scope

RWT applies to:
- UI / UX flows
- API design
- Data models & schemas
- AI prompts & agent logic
- Workflow orchestration
- Cross-module integration
- Error handling
- Validation logic
- Documentation

---

# Part I: Design Rules

## 4. Zero-Assumption Rule

Nothing is assumed. Everything required must be:
- Explicitly requested
- Explicitly validated
- Explicitly explained

❌ **Forbidden**
> "User will know to select crop first."

✅ **Required**
> "Select Crop (Required) — Tooltip: 'Used to determine nutrient and disease models'"

---

## 5. Missing Data Survival Rule

Every feature must define behavior for:
- Missing data
- Partial data
- Conflicting data
- Low-confidence data

❌ **Forbidden**
```python
yield = calculate_yield(crop, soil_type, rainfall)
```

✅ **Required**
```python
if not crop:
    return "CROP_REQUIRED"
if not soil_type:
    return "SOIL_TYPE_REQUIRED"
```

---

## 6. AI Non-Guessing Rule

AI must **never guess or assume** in scientific, agronomic, financial, or regulatory contexts.

AI behavior must be:
- Constrained
- Stepwise
- Validated
- Data-aware

❌ **Forbidden Prompt**
> "Analyze and recommend fertilizer."

✅ **Required Prompt**
> "If crop type is missing, ask.
> If growth stage is missing, ask.
> If soil data is missing, say 'INSUFFICIENT DATA'.
> Do NOT guess. Do NOT generalize."

---

## 7. Literal Workflow Rule

Workflows must be safe even if followed:
- Out of order
- Partially
- Incorrectly

System must:
- Block unsafe actions
- Explain why
- Provide recovery path

❌ **Forbidden**
> "Prediction failed."

✅ **Required**
> "Prediction blocked: Planting date missing. Click here to add."

---

## 8. Explain-While-Acting Rule

Every non-trivial action must explain:
- **What** is happening
- **Why** it is needed
- **What happens next**

This applies to buttons, AI actions, background processes, and automated decisions.

---

# Part II: Layer-Specific Rules

## 9. UI / UX Layer

Each screen must define:
- Required inputs
- Optional inputs
- Dependencies
- Error states
- Empty states

**Checklist:**
- [ ] Are all terms explained?
- [ ] Are all required fields clearly marked?
- [ ] Is there an example for complex input?
- [ ] Is failure explained in plain language?

---

## 10. Data Model Layer

All schemas must support:
- Unknown values
- Source attribution
- Confidence scoring

✅ **Required Pattern**
```json
{
  "soil_type": {
    "value": "Loamy",
    "source": "user_input | sensor | lab_report",
    "confidence": 0.75
  }
}
```

❌ **Forbidden**
```json
{
  "soil_type": "Loamy"
}
```

---

## 11. API Layer

APIs must:
- Reject incomplete requests
- Return explicit error codes
- Never silently default

✅ **Required**
```json
{
  "error": "MISSING_FIELD",
  "field": "crop_type",
  "message": "Crop type is required for this operation."
}
```

---

## 12. AI Agent Layer

All AI agents must follow:
1. Check required inputs
2. If missing → ask
3. If conflicting → flag
4. If insufficient → stop
5. Only then → reason

**Mandatory States:**
- `INSUFFICIENT_DATA`
- `CONFLICTING_DATA`
- `LOW_CONFIDENCE_DATA`
- `READY_FOR_ANALYSIS`

---

## 13. Workflow / Orchestration Layer

Workflows must be modeled as **state machines**, not assumptions.

Each step must declare:
- Prerequisites
- Inputs
- Outputs
- Failure handling

```
STATE: SoilAnalysis
REQUIRES: crop, field_location
ON_MISSING: prompt_user
ON_CONFLICT: block_and_explain
```

---

# Part III: Module-Specific Standards

## 14. Breeding Module

**User Reality:** May not understand terminology, mix generations, upload incomplete data.

| Mandatory Input | Required |
|-----------------|----------|
| Crop species | ✅ BLOCK if missing |
| Breeding objective | ✅ BLOCK if missing |
| Generation | Recommended |
| Parent lines | Optional |

**Workflow Guards:**
| Action | Prerequisite | On Missing |
|--------|--------------|------------|
| Create Cross | Parent lines selected | Block + explain |
| Run Selection | Phenotype data | Ask + link |
| Advance Generation | Current generation | Ask |

**AI Constraints:**
- Verify crop species, objective, generation context
- If any missing → ask
- If conflicting → stop

❌ Forbidden: "Based on typical breeding practices…"  
✅ Required: "Generation information missing. Cannot recommend selection strategy."

---

## 15. Seed Bank / Germplasm Module

**User Reality:** May not know accession codes, confuse varieties, upload partial records.

| Mandatory Input | Required |
|-----------------|----------|
| Accession ID or variety name | ✅ |
| Source (institution/farm) | ✅ |

**AI Constraints:**
- Never assume genetic purity
- Never assume trait stability
- State confidence: "Trait stability unknown. Source data incomplete."

---

## 16. Field Trials Module

**User Reality:** May not design trials correctly, skip randomization, upload incomplete layouts.

| Mandatory Input | Required |
|-----------------|----------|
| Crop | ✅ |
| Location | ✅ |
| Trial design | ✅ |

**AI Constraints:**
- Check replication, randomization, sample size
- If invalid: "Trial design insufficient for statistical analysis."

---

## 17. IoT & Sensor Module

**User Reality:** May connect wrong sensor, mislabel units, provide intermittent data.

| Mandatory Input | Required |
|-----------------|----------|
| Device ID | ✅ |
| Sensor type | ✅ |
| Unit | ✅ |

**AI Constraints:**
- Validate unit and range
- Detect anomalies: "Sensor reading out of expected range. Verify device."

---

## 18. Soil & Environment Module

**User Reality:** May not know soil classification, upload partial reports.

| Mandatory Input | Required |
|-----------------|----------|
| Location | ✅ |
| Sample date | ✅ |

**AI Constraints:**
- Never assume fertility or texture
- If missing: "Soil texture unknown. Cannot recommend fertilizer."

---

## 19. Crop Health & Pathology Module

**User Reality:** May upload unclear images, misidentify symptoms.

| Mandatory Input | Required |
|-----------------|----------|
| Crop | ✅ |
| Growth stage | ✅ |
| Symptom description or image | ✅ |

**AI Constraints:**
- Report confidence, list alternatives
- If unclear: "Image quality insufficient for diagnosis."

---

## 20. Advisory & Recommendation Engine

**User Reality:** May expect instant answers, provide vague input.

| Mandatory Input | Required |
|-----------------|----------|
| Crop | ✅ |
| Region | ✅ |
| Season | ✅ |

**AI Constraints:**
- Never generalize across regions
- Never ignore season
- If missing: "Region not provided. Recommendation unsafe."

---

## 21. Analytics & AI Insights Module

**User Reality:** May misinterpret graphs, expect causation from correlation.

| Mandatory Input | Required |
|-----------------|----------|
| Dataset | ✅ |
| Time range | ✅ |

**AI Constraints:**
- Label assumptions and uncertainty
- If low confidence: "Pattern detected but confidence low. Do not act."

---

## 22. Cross-Domain Integration Layer

**User Reality:** May not understand domain interactions, combine incompatible data.

| Mandatory Input | Required |
|-----------------|----------|
| Source domain | ✅ |
| Target domain | ✅ |

**AI Constraints:**
- Validate compatibility
- Refuse unsafe merges: "Domains not compatible. Integration blocked."

---

## 23. Compliance & Audit Module

**User Reality:** May not know regulations, upload partial records.

| Mandatory Input | Required |
|-----------------|----------|
| Record type | ✅ |
| Timestamp | ✅ |

**AI Constraints:**
- Never fabricate compliance
- Flag gaps: "Compliance record incomplete. Audit failed."

---

# Part IV: Enforcement

## 24. Universal RWT Enforcement Rules

Every module must implement:
1. **INSUFFICIENT_DATA state**
2. **CONFLICTING_DATA state**
3. **LOW_CONFIDENCE state**
4. **BLOCK + EXPLAIN behavior**
5. **RECOVERY PATH**

---

## 25. Design Review Checklist (Mandatory)

Every PR / feature design must answer:

1. What if the user does not understand this?
2. What if the user skips this step?
3. What if the data is missing?
4. What if the data is wrong?
5. What if the AI misinterprets?
6. What if this is used out of order?
7. What if a junior developer maintains this?

If any answer is "they will figure it out" → **REJECT DESIGN**

---

## 26. Anti-Patterns (Explicitly Banned)

These phrases indicate RWT violation:
- "User will know…"
- "It's obvious…"
- "Normally this happens…"
- "AI should infer…"
- "Assume that…"
- "Typically user would…"

Replace with **explicit logic and handling**.

---

## 27. Enforcement Policy

- Any design violating RWT may be **rejected without further review**
- Any AI prompt violating RWT must be **rewritten**
- Any workflow assuming user knowledge must be **redesigned**

RWT compliance is **not optional**.

---

# Part V: Philosophy

## 28. Why RWT Exists

BijMantra is:
- Cross-domain
- Scientific
- AI-driven
- Safety-relevant
- Long-lived

Therefore:
> **Clarity beats cleverness.**  
> **Explicit beats implicit.**  
> **Boring beats broken.**

---

## 29. The RWT Rule

> **If a confused user, a hallucinating AI, and a tired developer cannot use this module safely — it is not complete.**

---

*Ralph Wiggum Technique — because assuming competence is a design flaw.*
