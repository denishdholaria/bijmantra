# Environmental Models Architecture

**Status**: Draft (Proposed Architecture)
**Domain**: Environmental Intelligence
**Related**: `DOMAIN_ENGINES.md`, `ARCHITECTURE.md`, `MODULE_ACCEPTANCE_CRITERIA.md`, `INTEROPERABILITY_CONTRACT.md`, `SCHEMA_GOVERNANCE.md`, `AI_AGENT_GOVERNANCE.md`

---

## 1. Definition: "Environmental Models" in BijMantra

In the context of BijMantra, an **Environmental Model** is a computational construct that transforms raw environmental data (weather, soil, topography) into biologically relevant indices through **mechanistic or process-based logic**.

### What It Is
*   **Process-Based**: Simulates physical or physiological processes (e.g., "water infiltration", "thermal time accumulation").
*   **Spatio-Temporal**: Explicitly accounts for time (growth stages) and space (field topography).
*   **Stress-Aware**: Quantifies the intensity, duration, and timing of abiotic stresses.

### What It Is NOT (Explicitly Excluded)
*   **Pure Statistical Regressions**: `Yield = a * Rainfall + b` is *not* an environmental model in this architecture. It is a statistical outcome.
*   **Black-Box ML**: Neural networks predicting stress without causal structure are excluded from this definition.
*   **Raw Data Aggregation**: A simple "average temperature" is a statistic, not a model.

---

## 2. Classification of Environmental Model Types

We classify environmental models into five distinct categories based on the biological subsystem they simulate.

### 2.1 Crop Phenology & Thermal Time
*   **Models**: Development stage progression based on thermal units (GDD), photoperiod sensitivity, and vernalization requirements.
*   **Answers**: "When did flowering actually occur vs. predicted?" "Was the trial exposed to heat stress *during* meiosis?"
*   **Value**: Synchronizing stress events with sensitive crop stages is critical for correct phenotyping.

### 2.2 Soil-Water Balance
*   **Models**: Dynamic simulation of soil water content across layers, accounting for infiltration, runoff, evaporation, and transpiration (e.g., tipping bucket models).
*   **Answers**: "Is the low yield due to terminal drought or poor root penetration?" "What was the plant-available water at grain filling?"
*   **Value**: Distinguishes between **drought escape** (early maturity) and true **drought tolerance**.

### 2.3 Micro-Climate & Spatial Heterogeneity
*   **Models**: Solar radiation interception based on slope/aspect; cold air drainage; spatial interpolation of weather station data to plot level.
*   **Answers**: "Did the south end of the field receive significantly more radiation?" "Is the yield variation due to genotype or a frost pocket?"
*   **Value**: Reduces residual error in spatial analysis by treating micro-environment as a covariate.

### 2.4 Stress Interaction Indices
*   **Models**: Compound events such as "Heat × Drought" or "High Humidity × Warmth" (disease pressure).
*   **Answers**: "Which locations provide the best screening pressure for Spot Blotch?"
*   **Value**: Moves beyond single-factor analysis to capture complex G×E drivers.

### 2.5 Climate Variability & Risk Envelopes
*   **Models**: Frequency analysis of historical weather patterns to define target population of environments (TPE).
*   **Answers**: "How often does this specific drought pattern occur in our target market?"
*   **Value**: Weights trial results by their representativeness of the target production environment.

---

## 3. BijMantra Use-Case Mapping

| Model Category | Breeding Decision | G×E & Trial Analysis | Genetic Gain |
| :--- | :--- | :--- | :--- |
| **Phenology** | **Crossing Planning**: Syncing flowering times of parents. | **Covariate**: Correcting yield for maturity differences. | **Selection**: Penalizing "escape" strategies if long-duration is the target. |
| **Water Balance** | **Site Selection**: Choosing managed drought trial sites. | **Enviro-typing**: Clustering environments by drought intensity/timing. | **Forecast**: Predicting performance in future drier climates. |
| **Micro-Climate** | **Plot Layout**: Avoiding frost/heat pockets. | **Spatial Error**: Removing field-trend noise (Spatial Analysis). | **Accuracy**: Higher heritability ($h^2$) due to reduced environmental noise. |
| **Stress Indices** | **Screening**: verifying if a "stress trial" actually applied stress. | **Reaction Norms**: Modeling genotype sensitivity to specific stresses. | **Stability**: Selecting stable lines across variable stress intensities. |

---

## 4. Architectural Integration Plan

### a) Compute Engine: **Rust / WASM**

**Choice**: Rust compiled to WebAssembly.

**Justification**:
1.  **Offline-First PWA**: Breeders in the field need to run "what-if" scenarios (e.g., "If I plant today, when will it flower?") without server connectivity.
2.  **Performance**: Process-based models (especially daily loops over years) require speed that Python lacks, but don't need the dense linear algebra support of Fortran.
3.  **Safety**: Rust's type safety prevents common numerical bugs in stateful simulations.

### b) Data Dependencies

*   **Weather Data**: Daily resolution (Min/Max Temp, Precip, Solar Rad). stored in time-series format.
*   **Soil Data**: Profile properties (Texture, Depth, WHC) stored in PostGIS/PostgreSQL.
*   **Trial Metadata**: Geo-coordinates, Sowing Date, Irrigation events.
*   **Crop Constants**: Species-specific base temperatures and coefficients (stored in config/DB).

### c) Output Format

The output is **derived environmental features**, not raw simulation dumps.

*   **Format**: JSON/Struct (consumable by Python APIs and Frontend).
*   **Example**:
    ```json
    {
      "trial_id": "TR-2024-001",
      "stress_indices": {
        "drought_intensity_flowering": 0.45,
        "heat_days_grain_filling": 3,
        "cumulative_radiation": 1250.5
      },
      "phenology": {
        "predicted_flowering_date": "2024-08-15",
        "thermal_time_accumulation": 1450.0
      }
    }
    ```

---

## 5. Environmental Feature Layer (EFL)

The **Environmental Feature Layer** is a conceptual architectural boundary.

```ascii
[Raw Weather/Soil Data]
       ⬇
[ ENVIRONMENTAL FEATURE LAYER (Rust/WASM) ]
   Logic: Phenology, Water Balance, Stress Logic
       ⬇
[ Derived Features (Covariates) ]
       ⬇
   FEED INTO:
   ├── G×E Analysis (Factorial Regression)
   ├── Spatial Analysis (Field Trends)
   ├── Selection Indices (Weighting)
   └── Veena AI (Contextual Explanation)
```

**Role**:
*   It decouples the *complexity of the physics* from the *application of the statistics*.
*   The Breeding Engine (Fortran) receives "Drought Index" as a simple number, unaware of the complex tipping-bucket model that produced it.

---

## 6. User Abstraction Rules

We separate **Implementation Complexity** from **User Insight**.

| User Persona | What They SEE | What They NEVER See |
| :--- | :--- | :--- |
| **Breeder** | "Severe Terminal Drought Stress detected." | Richards equation partial differential parameters. |
| **Trial Manager** | "Sow between Oct 15-20 to avoid frost." | Probability density functions of minimum temperature. |
| **Data Analyst** | "covariate: `water_deficit_period_3`" | Raw daily soil moisture arrays. |

**Rule**: The UI displays **Actionable Intelligence**, not **Physics Debugging**.

---

## 7. What NOT To Build

1.  **No Monolithic "Environment Service"**: Do not build a standalone microservice that requires network calls for every calculation. Embed the logic as a library (crate) used by the API and the Client.
2.  **No DSSAT/APSIM Clones**: We are not building a full physiological crop model. We are building *indices* relevant to breeding.
3.  **No Real-Time Global Climate Sim**: Use processed weather provider data; do not run GCMs (Global Climate Models) on our servers.
4.  **No ML-First Physics Replacements**: Do not train a neural network to predict soil moisture if a simple water balance model works. Causal understanding is required for G×E.

---

## 8. Phased Adoption Strategy

This strategy allows immediate value while respecting the solo-developer constraint.

### Phase 1: Feature Extraction (The "Easy" Wins)
*   **Goal**: Calculate simple thermal and stress indices from existing weather data.
*   **Action**: Implement `GDD`, `Photothermal Units`, and simple `Precipitation Deficit` in Rust.
*   **Integration**: Expose as standard covariates for G×E analysis.
*   **Value**: Immediate improvement in trial interpretation.

### Phase 2: Deterministic Process Models
*   **Goal**: Implement stateful simulation.
*   **Action**: Build a simple 2-layer soil water balance model and phenology predictor.
*   **Integration**: Link with "Trial Management" to predict optimal sowing/harvest windows.
*   **Value**: "What-if" capability for offline users.

### Phase 3: Risk Envelopes & TPE
*   **Goal**: Characterize the Target Population of Environments.
*   **Action**: Run Phase 2 models over 30 years of historical weather data.
*   **Integration**: Weight selection indices based on environmental frequency.
*   **Value**: Genetic gain directed specifically at target environments (e.g., "Drought Prone").
