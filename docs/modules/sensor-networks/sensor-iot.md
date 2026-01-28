# BijMantra BrAPI IoT Extension – Sensor & Environment Data

**File:** `sensor-iot.md`  
**Version:** 1.0 (Draft)  
**Status:** Proposed Extension  
**Compatibility:** BrAPI v2.x  
**Owner:** BijMantra Project  

---

## 1. Purpose

This document defines the **BijMantra BrAPI IoT Extension** for integrating
**sensor- and IoT-derived environmental data** into BrAPI-compliant
plant breeding workflows.

The goal is to **bridge real-world environmental sensing with breeding data**
while fully respecting BrAPI’s scope and design philosophy.

> BrAPI describes *experiments and observations*.  
> BijMantra IoT describes *the environment in which they occur*.

---

## 2. Scope

### This extension:
- ✅ Provides access to **environmental sensor metadata**
- ✅ Exposes **derived environmental summaries** usable by BrAPI clients
- ✅ Enables **G×E (Genotype × Environment)** analysis
- ✅ Preserves full BrAPI compatibility

### This extension does NOT:
- ❌ Standardize hardware or sensors
- ❌ Define firmware or device protocols
- ❌ Replace core BrAPI endpoints
- ❌ Push raw telemetry into BrAPI objects

---

## 3. Design Principles

1. **BrAPI-First Compatibility**  
   Core BrAPI schemas and endpoints remain unchanged.

2. **Separation of Concerns**  
   - Raw telemetry → BijMantra IoT Core  
   - Aggregated context → BrAPI-compatible exposure

3. **Vendor Neutrality**  
   No assumptions about brands, networks, or device vendors.

4. **Optional Adoption**  
   BrAPI clients may ignore this extension without breaking.

---

## 4. Architectural Overview

```

Physical Sensors
↓
IoT Devices / Gateways
↓
BijMantra IoT Core

* Devices
* Sensors
* Telemetry (time-series)
* Alerts
  ↓
  Aggregation / Derivation
  ↓
  BrAPI IoT Extension Endpoints

```

Only **derived, breeding-relevant data** is exposed to BrAPI consumers.

---

## 5. Namespace & Versioning

All endpoints are exposed under:

```

/brapi/v2/extensions/iot/

````

- Backward-compatible additions are allowed
- Breaking changes require a new extension version

---

## 6. Core Concepts

### 6.1 Device (Non-BrAPI Object)

A **Device** is a physical or virtual unit that produces data
(e.g., weather station, soil probe, gateway).

Devices:
- Exist only in the IoT layer
- Are **not** core BrAPI entities
- Are referenced indirectly via environments

---

### 6.2 Sensor

A **Sensor** is a logical measurement unit associated with a device.

Examples:
- air_temperature
- soil_moisture
- rainfall
- relative_humidity
- leaf_wetness

Sensors define:
- Measurement type
- Unit
- Accuracy / metadata

---

### 6.3 Telemetry (Non-BrAPI Data)

Telemetry is **high-frequency, time-series sensor data**.

Characteristics:
- Continuous or near-continuous
- High volume
- Stored outside BrAPI core schemas

Telemetry is accessed **only via extension endpoints**.

---

### 6.4 Environmental Aggregates (BrAPI-Aligned)

Environmental aggregates are **derived summaries** mapped to:
- Environments
- Studies
- Trials

These aggregates are suitable as:
- Environmental covariates
- Contextual observations
- G×E inputs

---

## 7. Extension Endpoints

### 7.1 `/iot/devices`

**Purpose:**  
Expose device metadata for traceability and audit.

**Example**
```json
{
  "deviceDbId": "device-001",
  "deviceType": "weather_station",
  "connectivity": "lora",
  "status": "active",
  "location": {
    "lat": 21.12,
    "lon": 72.34
  }
}
````

---

### 7.2 `/iot/sensors`

**Purpose:**
Describe sensors available within the system.

```json
{
  "sensorDbId": "sensor-101",
  "sensorType": "soil_moisture",
  "unit": "%",
  "accuracy": "±2%"
}
```

---

### 7.3 `/iot/telemetry`

**Purpose:**
Provide controlled access to time-series sensor data.

**Rules:**

* Time range is mandatory
* Pagination is mandatory
* Downsampling is recommended for long ranges

```json
{
  "sensorDbId": "sensor-101",
  "readings": [
    {
      "timestamp": "2025-01-10T06:30:00Z",
      "value": 23.4
    }
  ]
}
```

---

### 7.4 `/iot/aggregates` (Primary BrAPI Bridge)

**Purpose:**
Expose BrAPI-aligned environmental summaries.

```json
{
  "environmentDbId": "env-kharif-2025-01",
  "aggregates": [
    {
      "environmentalParameter": "air_temperature_mean",
      "value": 31.2,
      "unit": "C",
      "period": "daily"
    },
    {
      "environmentalParameter": "rainfall_total",
      "value": 124,
      "unit": "mm",
      "period": "seasonal"
    }
  ]
}
```

These parameters align with:

* `/environmentalParameters`
* Study-level covariates
* G×E modeling pipelines

---

### 7.5 `/iot/alerts`

**Purpose:**
Expose environment-driven stress or anomaly events.

```json
{
  "alertDbId": "alert-heat-2025-01",
  "type": "heat_stress",
  "severity": "high",
  "startTime": "2025-01-09T11:00:00Z",
  "endTime": "2025-01-09T16:00:00Z"
}
```

Alerts may be used as:

* Trial annotations
* Stress covariates
* Decision triggers

---

## 8. Mapping to Core BrAPI Objects

| BrAPI Object | IoT Contribution           |
| ------------ | -------------------------- |
| Environment  | Aggregated sensor context  |
| Study        | Environmental covariates   |
| Observation  | Derived environment traits |
| Trait        | Sensor-derived parameters  |

---

## 9. Compliance Requirements

An implementation is **BijMantra BrAPI IoT compliant** if:

* ✅ Core BrAPI endpoints remain unchanged
* ✅ IoT endpoints live under `/extensions/iot/`
* ✅ Raw telemetry is not injected into core BrAPI schemas
* ✅ Aggregates reference valid `environmentDbId` values

---

## 10. Explicit Non-Goals

This specification explicitly avoids:

* Hardware certification
* Firmware enforcement
* Network protocol mandates
* Real-time control systems

---

## 11. Rationale

Environmental conditions are a **primary driver of phenotypic expression**.
BrAPI standardizes experimental data; this extension standardizes
how **environmental reality is connected to those experiments**.

Together, they enable:

* Robust G×E analysis
* Climate-resilient breeding
* Reproducible, data-rich trials

---

## 12. Summary

> **BrAPI standardizes breeding data interoperability.**
> **BijMantra IoT standardizes environmental context ingestion.**

This extension allows both to coexist cleanly, without scope conflict.

---

```

---

### What you now have
- 📘 A **clean, standards-grade markdown spec**
- 🤖 AI-prototyper-friendly (clear boundaries & intent)
- 🔌 Drop-in ready for your repo
- 🌍 Strong enough to share with the BrAPI community later

---

### Recommended next steps (in order)
1. 🧬 Sensor → trait / covariate mapping table  
2. 📊 Example G×E workflow using this extension  
3. ⚙️ Reference implementation notes (API + DB)  

Just say **“Next: \<step\>”** and we continue.
```
