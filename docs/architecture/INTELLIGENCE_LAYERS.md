# Intelligence Layers Architecture

This document defines the architectural strategy for organizing intelligence, AI, and domain logic within BijMantra. It reframes the system's complexity as "idea capture at scale" rather than architectural failure and establishes a layered approach to intelligence.

## 1. Core Philosophy

The system currently holds three distinct inventories in one space:
1.  **Idea Inventory** ("I don't want to forget this")
2.  **Capability Inventory** ("The system can do this")
3.  **User Workflow** ("A human will do this")

Confusion arises when these are mixed. The solution is **indexing**, not deletion.

## 2. Orthogonal Dimensions

BijMantra operates on four orthogonal dimensions. Grouping by pages/gateways often fails because it ignores these other axes.

| Dimension | Scope | Examples |
| :--- | :--- | :--- |
| **1. Domain** | The subject matter | Biology, Soil, Seed, Economics |
| **2. Function** | The action type | Observe, Decide, Act |
| **3. Scale** | The physical scope | Plot → Trial → Program → Market |
| **4. Intelligence** | The cognitive depth | Rule → Model → AI |

**Key Insight:** Gateways only represent *Domain*. AI is not a gateway; it is a **lens** applied across gateways, living mostly in *Function + Intelligence*.

## 3. The Intelligence Layers (L0–L3)

To organize the system without killing cross-domain creativity, we define four explicit Intelligence Layers.

### 🟦 L0 — Raw Data & Capture
*The foundation. Passive, unopinionated, and domain-specific.*

*   **Role:** Capture and storage of raw observations and facts.
*   **Characteristics:** Not "smart". Source of truth for *what happened*.
*   **Examples:**
    *   Weather logs
    *   Soil sensor readings
    *   Plot observations (height, count)
    *   Raw images (drone, phone)
    *   Genotypes (VCFs)
    *   Pedigree records
    *   Lab test results

### 🟩 L1 — Derived Features
*Where order begins. Domain-aware but usage-agnostic.*

*   **Role:** Transforming raw data into standardized, meaningful metrics. This is the **shared language** of the system.
*   **Characteristics:** Deterministic, computed, reusable.
*   **Examples:**
    *   GDD (Growing Degree Days) accumulation
    *   Heat stress duration during flowering
    *   Drought timing classification
    *   Spatial heterogeneity index
    *   Phenology phase durations
    *   Trait heritability per environment

### 🟨 L2 — Models & Reasoning
*Where AI truly lives. Analytical and causal.*

*   **Role:** simulating processes, predicting outcomes, and explaining "why".
*   **Characteristics:** Probabilistic, complex, explanatory. **Not chatbots.**
*   **Examples:**
    *   Fortran crop simulation models
    *   G×E (Genotype by Environment) interaction models
    *   Selection index engines
    *   Yield prediction models
    *   Disease risk forecasting
    *   Process-based environmental models

### 🟥 L3 — Decisions & Guidance
*Where humans feel value. Synthesized and actionable.*

*   **Role:** translating model outputs into human-centric advice.
*   **Characteristics:** Suggestive, context-aware, prioritizing actions.
*   **Examples:**
    *   "Advance this breeding line"
    *   "Drop this test environment"
    *   "Genotype X is stable but has a low yield ceiling"
    *   "Trial Y is not representative due to spatial noise"
    *   "High risk of failure under late heat stress"

## 4. The Role of Veena (AI)

**Veena is a navigator, not an oracle.**

*   **Source of Truth:** Veena is **never** the source of truth. The underlying data (L0) and models (L2) are.
*   **Function:** Veena acts as a UI/UX layer over L1–L3.
*   **Responsibilities:**
    *   Translate human natural language questions into specific feature queries.
    *   Summarize outputs from L2 models.
    *   Explain the reasoning behind an L3 suggestion.
    *   Compare across domains (e.g., "Synthesize genetics + environment + economics").
*   **Restrictions:**
    *   Does not invent conclusions.
    *   Does not replace deterministic models.
    *   Does not bypass established architecture.

## 5. Architectural Rules

### Rule 1: Separation of UI and Intelligence
*   **Pages** can be domain-specific (e.g., `/drought`, `/yield-predictor`).
*   **Intelligence** must be domain-agnostic or shared.
*   Different views (pages) must draw from the **same** L1 derived features and **same** L2 models.

### Rule 2: Cross-Domain Logic lives below the UI
*   Do not encode intelligence in routes.
*   Centralize feature computation (L1).
*   Centralize reasoning (L2).
*   "UI mess is survivable. Semantic mess is not."

## 6. Feature Ownership Strategy

When defining a new capability (e.g., "Drought Resistance"), do not ask "Where is the page?". Instead, ask:

**"What are the canonical features for this?"**

Define the L1 features first. The UI (Page) is merely a view into these features.
