# Canonical Feature Mapping v0.1

**Context:** This document serves as the initial contract for the "Common Language" of environmental and biological features in BijMantra. It maps the Canonical Feature List v0.1 to the current codebase, identifying semantic drift, gaps, and duplication.

**Workflow Scope:** Yield Prediction & Abiotic Stress Analysis

---

## Summary of Findings

The codebase contains robust implementations for many underlying physical and biological processes (GDD, Solar Radiation, Spatial Analysis), but they are often:
1.  **Fragmented:** Spread across multiple services (`gdd_calculator_service`, `field_gdd_service`).
2.  **Semantically Drifted:** Named differently (e.g., `estimated_radiation` vs `radiation_opportunity_score`).
3.  **Missing "Index" Logic:** Raw data exists (e.g., Water Balance), but the canonical "Score" or "Index" (0-100 or categorical) is not calculated.

---

## Detailed Mapping

### CATEGORY A — Environmental Opportunity

| Canonical Feature | Current Implementation | Status | Semantic Drift / Notes |
| :--- | :--- | :--- | :--- |
| **A1. thermal_opportunity_index** | `GDDCalculatorService.calculate_cumulative_gdd` in `backend/app/services/gdd_calculator_service.py` | **Implemented** | Named `cumulative_gdd`. The canonical feature implies a relative index (relative to crop requirement), whereas the current implementation is absolute GDD units. Needs normalization logic. |
| **A2. radiation_opportunity_score** | `SolarService.calculate_solar_radiation` in `backend/app/services/solar.py` | **Implemented** | Named `estimated_radiation` or `par_estimate`. Canonical feature implies a score. The service provides raw MJ/m²/day. |

### CATEGORY B — Stress Exposure

| Canonical Feature | Current Implementation | Status | Semantic Drift / Notes |
| :--- | :--- | :--- | :--- |
| **B1. heat_stress_flowering** | `AbioticStressService` (generic "Heat" category) & `GDDCalculatorService` (modified method) | **Partial** | "Heat" stress exists as a category. `GDDCalculatorService` handles "modified" GDD capping at 30°C. **Missing:** Explicit logic connecting heat events specifically to the *flowering* window defined in `PhenologyService`. |
| **B2. drought_timing_class** | `WaterBalanceService` (raw data) | **Missing** | `WaterBalance` records exist (`precipitation`, `irrigation`, `et`), but the classification logic (early/mid/late/intermittent) is missing. |
| **B3. water_availability_index** | `WaterBalanceService` (raw data) | **Partial** | Raw `WaterBalance` data exists. **Missing:** A scalar index integrating sufficiency over the season. |

### CATEGORY C — Phenological Realization

| Canonical Feature | Current Implementation | Status | Semantic Drift / Notes |
| :--- | :--- | :--- | :--- |
| **C1. days_to_emergence** | `PhenologyService` & `GDDCalculatorService.predict_growth_stages` | **Implemented** | `GDDCalculatorService` predicts this based on GDD (e.g., 125 GDD for Corn). `PhenologyService` tracks observations. |
| **C2. days_to_flowering** | `PhenologyService` & `GDDCalculatorService` | **Implemented** | Maps to `Silking`/`Heading`/`Flowering` stages in `GDDCalculatorService`. |
| **C3. grain_filling_duration** | `PhenologyService` & `GDDCalculatorService` | **Implemented** | Calculated as difference between Maturity and Flowering GDD thresholds. |

### CATEGORY D — Spatial & Trial Quality

| Canonical Feature | Current Implementation | Status | Semantic Drift / Notes |
| :--- | :--- | :--- | :--- |
| **D1. within_trial_variability_index** | `SpatialAnalysisService.spatial_autocorrelation` in `backend/app/services/spatial_analysis.py` | **Implemented** | Implemented as `morans_i`. Also has `moving_average_adjustment`. |
| **D2. environment_representativeness_score** | None | **Missing** | No current logic to compare an environment to program history. |

### CATEGORY E — Genotype × Environment Response

| Canonical Feature | Current Implementation | Status | Semantic Drift / Notes |
| :--- | :--- | :--- | :--- |
| **E1. gxe_sensitivity_score** | `AbioticStressService.calculate_stress_indices` | **Implemented** | Calculates SSI (Stress Susceptibility Index), STI (Stress Tolerance Index), etc. `STI` is a strong candidate for this. |
| **E2. stress_response_type** | `AbioticStressService._rate_tolerance` | **Implemented** | Outputs ratings like "Highly Tolerant", "Susceptible". Maps well to canonical enums. |

### CATEGORY F — Risk & Uncertainty

| Canonical Feature | Current Implementation | Status | Semantic Drift / Notes |
| :--- | :--- | :--- | :--- |
| **F1. yield_variance_estimate** | `MLPredictor` (implicit) | **Partial** | `MLPredictor` in `yield_prediction/ml.py` uses ensemble (RandomForest + XGBoost), which could provide variance, but currently averages them. |
| **F2. downside_risk_score** | None | **Missing** | No explicit downside risk calculation. |

---

## Action Plan (Next Steps)

1.  **Unify GDD Services:** Merge `field_gdd_service.py` logic into `gdd_calculator_service.py` to prevent logic drift.
2.  **Formalize L1 Features:** Create a wrapper service (e.g., `EnvironmentalFeatureService`) that consumes `SolarService`, `GDDCalculatorService`, and `WaterBalanceService` to output the canonical *Indices* and *Scores* (normalized 0-1 or categorical) rather than raw physical units.
3.  **Implement Temporal Stress Logic:** Update `AbioticStressService` to consume `PhenologyService` data, allowing detection of stress *specifically during flowering* (B1).
4.  **Add Variability Index:** Expose `SpatialAnalysisService.morans_i` as `within_trial_variability_index` in the trial summary API.
