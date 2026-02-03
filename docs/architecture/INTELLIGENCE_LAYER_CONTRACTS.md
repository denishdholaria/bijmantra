# Intelligence Layer Contracts

**For BijMantra – Cross-Domain, AI-Augmented System**

This document defines the architecture for the "Intelligence Layer" of BijMantra. It establishes strict semantic boundaries ("Contracts") between the different stages of data processing, reasoning, and presentation.

## What "Contracts" Means Here

A contract is **NOT** an API spec and **NOT** a UI decision.

A contract is a **stable semantic agreement** between layers about:
1.  **What is produced**
2.  **What it means**
3.  **Who can consume it**

**Why Contracts?**
*   **Decoupling:** Domains (Breeding, Seed Ops, Research) stay independent.
*   **Grounding:** AI stays grounded in fact, preventing hallucinations.
*   **Flexibility:** Pages (UI) can change messily without breaking the underlying intelligence.

---

## The 4 Intelligence Layers

We define four distinct layers of intelligence processing:

| Layer | Name | Description | Role |
| :--- | :--- | :--- | :--- |
| **L0** | **Raw Signals** | Fragmented, domain-specific data (tables, logs, sensors). | **Input** |
| **L1** | **Canonical Features** | Standardized, derived environmental & biological language. | **Translation** |
| **L2** | **Models & Reasoning** | Mathematical models, simulations, and predictions. | **Analysis** |
| **L3** | **Decisions & Guidance** | Narrative interpretation, context, and suggestions. | **Synthesis** |

Each layer has strict ownership, inputs, outputs, and rules.

---

## CONTRACT A: L0 → L1
**Raw Signals → Canonical Features**

**Purpose:** Turn fragmented, domain-specific data into a shared environmental + biological language. This is the "dictionary" that all intelligence in the system speaks.

### L0 Inputs (Raw Signals)
*   **Atmosphere:** Weather time series, satellite imagery.
*   **Lithosphere:** Soil profiles, nutrient logs.
*   **Sensors:** IoT stream data.
*   **Phenotyping:** Raw field observations, notes.
*   **Genotyping:** Raw sequence data, pedigree records.
*   **Operations:** Management events (sowing dates, irrigation logs).
*   **Characteristics:** Noisy, high-resolution, incomplete, domain-owned.

### L1 Outputs (Canonical Features)
*   **Environmental:** `thermal_opportunity_index`, `heat_stress_flowering`, `drought_timing_class`, `soil_water_availability_score`, `environment_class (E1-E5)`.
*   **Phenology:** `days_to_emergence`, `flowering_window_length`, `grain_filling_duration`.
*   **Trial / Spatial:** `within_trial_variability_index`, `edge_effect_risk`, `microclimate_variance`.
*   **Genetic / Statistical:** `trait_heritability_env_adjusted`, `gxe_sensitivity_score`.

### Contract Rules (Non-Negotiable)
1.  **No UI Logic:** L1 features do not know about screens or users.
2.  **No Decisions:** L1 does not say "good" or "bad", only "high" or "low".
3.  **No ML Hallucinations:** Calculation must be deterministic or statistically robust feature extraction.
4.  **Defined:** Every feature has a strict definition.
5.  **Versioning:** Features are versioned entities.

---

## CONTRACT B: L1 → L2
**Canonical Features → Models & Reasoning**

**Purpose:** The domain of AI and Math. Controlled power.

### L2 Inputs
*   **Source:** **Only** Canonical Features (L1).
*   **Supplementary:** Genetics matrices, trial design matrices.
*   **Restriction:** L2 **must not** access raw L0 data directly (e.g., no parsing raw weather CSVs).

### L2 Responsibilities
*   Combine features.
*   Run deterministic or probabilistic models.
*   Perform simulations, predictions, and rankings.
*   Produce interpretable numerical outputs.

### L2 Outputs (Model Results)
*   `predicted_yield_mean`
*   `yield_variance`
*   `stability_rank`
*   `stress_response_curve`
*   `risk_envelope`
*   **Characteristics:** Numerical, comparable, explainable. Not advice.

### Contract Rules
1.  **Consumption:** Models consume Features (L1), not Raw Data (L0).
2.  **Blindness:** Models do not know who the user is or their business goals.
3.  **Neutrality:** Models do not recommend actions; they quantify states.
4.  **Uncertainty:** Models must expose confidence intervals or uncertainty metrics.

---

## CONTRACT C: L2 → L3
**Model Outputs → Decisions & Guidance**

**Purpose:** Human meaning. Where context, business logic, and narrative enter.

### L3 Responsibilities
*   Interpret L2 outputs in the context of the user's goals.
*   Combine insights across domains (Genetics + Environment + Economics).
*   Generate natural language explanations.
*   Suggest actions (Guidance, never Force).
*   **Home of:** Dashboards, Reports, and Veena (AI Assistant).

### L3 Outputs (Human-Facing)
*   "Genotype A is stable but has a low yield ceiling."
*   "Trial X is environmentally unrepresentative of the target population."
*   "This line performs well due to drought escape, not tolerance."
*   "High downside risk identified under late heat stress conditions."

### Contract Rules
1.  **Aggregation:** L3 may combine multiple L2 outputs.
2.  **Business Logic:** L3 may apply business rules (e.g., "Discard if stability < X").
3.  **LLM Usage:** L3 is where Large Language Models live and generate text.
4.  **Grounding:** L3 **must never** fabricate numbers. Every claim must trace back to an L2 or L1 artifact.

---

## AI Roles by Layer

| Layer | AI Role | Permitted Actions |
| :--- | :--- | :--- |
| **L0** | ❌ **None** | Raw data storage only. |
| **L1** | ⚠️ **Helper** | Feature extraction helpers only (e.g., cleaning noise). |
| **L2** | ✅ **Analytical** | ML, Statistical Models, Simulation. |
| **L3** | ✅ **Narrative** | NLP, Explanations, Comparisons, Veena. |

---

## Example Implementation: Drought

This template demonstrates how a specific concept flows through the Intelligence Layers.

### 1. L1 Features (Canonical Dictionary)
*   `precipitation_deficit_mm`: Cumulative difference between rainfall and evapotranspiration.
*   `drought_stress_days`: Count of days where soil moisture < wilting point during critical growth stages.
*   `water_use_efficiency_score`: Derived metric from biomass vs water input.
*   `terminal_drought_flag`: Boolean, true if drought occurs during grain filling.

### 2. L2 Models (Reasoning)
*   **Yield Loss Model:** Predicts `yield_loss_percentage` based on `drought_stress_days`.
*   **Stability Analysis:** Calculates `drought_stability_index` comparing performance in drought vs. non-drought environments.
*   **Recovery Probability:** Monte Carlo simulation outputting `recovery_chance` if irrigation is applied.

### 3. L3 Narratives (Guidance)
*   **Dashboard View:** "Drought Alert: 3 trials in Zone B are experiencing terminal drought."
*   **Veena:** "Genotype G-123 shows high resilience (`drought_stability_index: 0.85`) but suffers significant yield penalty in well-watered conditions. It is recommended for rain-fed marginal zones."
*   **Report:** "The current season exhibits a `Severe` drought classification. Expect a 15-20% yield reduction across the program compared to the 5-year average."
