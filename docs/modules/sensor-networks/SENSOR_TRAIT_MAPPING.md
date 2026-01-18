# Sensor → Trait / Covariate Mapping

> **Reference Guide**: How sensor data becomes breeding-relevant information
> 
> **Purpose**: Bridge IoT telemetry to BrAPI observations and environmental covariates

---

## 🌡️ Temperature Sensors

### Raw Sensor Data
- **Sensor Type**: `temperature`
- **Unit**: °C
- **Frequency**: Every 5-15 minutes
- **Typical Range**: -10°C to 50°C

### Derived Environmental Parameters

| Parameter | Formula | Unit | Period | Use Case |
|-----------|---------|------|--------|----------|
| **air_temperature_mean** | AVG(temp) | °C | Daily | General climate |
| **air_temperature_max** | MAX(temp) | °C | Daily | Heat stress |
| **air_temperature_min** | MIN(temp) | °C | Daily | Frost risk |
| **growing_degree_days** | Σ(GDD) | °C·day | Seasonal | Phenology |
| **heat_stress_days** | COUNT(temp > 35) | days | Seasonal | Stress tolerance |
| **frost_days** | COUNT(temp < 2) | days | Seasonal | Cold tolerance |

### BrAPI Trait Mapping

```json
{
  "observationVariableDbId": "env-temp-mean",
  "observationVariableName": "Daily Mean Temperature",
  "trait": {
    "traitDbId": "env-temp",
    "traitName": "Air Temperature"
  },
  "method": {
    "methodDbId": "sensor-avg",
    "methodName": "Sensor Average"
  },
  "scale": {
    "scaleDbId": "celsius",
    "scaleName": "Degrees Celsius",
    "dataType": "Numerical"
  }
}
```

### G×E Covariate Example

```json
{
  "environmentDbId": "env-kharif-2025-01",
  "covariates": [
    {
      "covariateName": "mean_temperature",
      "covariateValue": "28.5",
      "covariateUnit": "°C"
    },
    {
      "covariateName": "gdd_accumulated",
      "covariateValue": "1850",
      "covariateUnit": "°C·day"
    }
  ]
}
```

---

## 💧 Soil Moisture Sensors

### Raw Sensor Data
- **Sensor Type**: `soil_moisture`
- **Unit**: % (volumetric water content)
- **Frequency**: Every 15-30 minutes
- **Typical Range**: 10% to 60%

### Derived Environmental Parameters

| Parameter | Formula | Unit | Period | Use Case |
|-----------|---------|------|--------|----------|
| **soil_moisture_mean** | AVG(moisture) | % | Daily | Irrigation |
| **soil_moisture_min** | MIN(moisture) | % | Daily | Drought stress |
| **drought_stress_days** | COUNT(moisture < 30) | days | Seasonal | Stress tolerance |
| **irrigation_events** | COUNT(Δmoisture > 10) | events | Seasonal | Water use |
| **water_deficit_integral** | Σ(30 - moisture) | %·day | Seasonal | Cumulative stress |

### BrAPI Observation Example

```json
{
  "observationDbId": "obs-soil-moisture-001",
  "observationUnitDbId": "plot-A-01",
  "observationVariableDbId": "env-soil-moisture",
  "value": "42.5",
  "observationTimeStamp": "2025-01-15T10:30:00Z",
  "collector": "IoT-Sensor-DEV-002"
}
```

---

## 🌧️ Rainfall Sensors

### Raw Sensor Data
- **Sensor Type**: `rainfall`
- **Unit**: mm
- **Frequency**: Event-based or hourly
- **Typical Range**: 0 to 200 mm/day

### Derived Environmental Parameters

| Parameter | Formula | Unit | Period | Use Case |
|-----------|---------|------|--------|----------|
| **precipitation_total** | SUM(rain) | mm | Daily/Seasonal | Water availability |
| **precipitation_days** | COUNT(rain > 1) | days | Seasonal | Rainfall pattern |
| **max_dry_spell** | MAX(consecutive days rain = 0) | days | Seasonal | Drought |
| **rainfall_intensity** | MAX(rain/hour) | mm/h | Event | Erosion risk |

---

## ☀️ Solar Radiation (PAR) Sensors

### Raw Sensor Data
- **Sensor Type**: `par` (Photosynthetically Active Radiation)
- **Unit**: µmol/m²/s
- **Frequency**: Every 1-5 minutes
- **Typical Range**: 0 to 2000 µmol/m²/s

### Derived Environmental Parameters

| Parameter | Formula | Unit | Period | Use Case |
|-----------|---------|------|--------|----------|
| **solar_radiation_total** | Σ(PAR × time) | MJ/m² | Daily | Photosynthesis |
| **light_hours** | COUNT(PAR > 50) | hours | Daily | Photoperiod |
| **peak_radiation** | MAX(PAR) | µmol/m²/s | Daily | Light stress |

---

## 🌿 Leaf Wetness Sensors

### Raw Sensor Data
- **Sensor Type**: `leaf_wetness`
- **Unit**: % (0-100)
- **Frequency**: Every 5-15 minutes
- **Typical Range**: 0% to 100%

### Derived Environmental Parameters

| Parameter | Formula | Unit | Period | Use Case |
|-----------|---------|------|--------|----------|
| **leaf_wetness_hours** | SUM(wetness > 80) / 12 | hours | Daily | Disease risk |
| **dew_duration** | Consecutive hours wetness > 80 | hours | Event | Fungal infection |

---

## 🔗 Complete Workflow: Sensor → BrAPI

### Step 1: Telemetry Ingestion

```python
# Raw sensor reading
{
  "device_id": "DEV-001",
  "sensor": "temperature",
  "value": 32.5,
  "unit": "°C",
  "timestamp": "2025-01-15T14:30:00Z"
}
```

### Step 2: Aggregation (Daily)

```python
# Aggregated environmental parameter
{
  "environment_id": "env-kharif-2025-01",
  "parameter": "air_temperature_mean",
  "value": 28.5,
  "unit": "°C",
  "period": "daily",
  "start_time": "2025-01-15T00:00:00Z",
  "end_time": "2025-01-15T23:59:59Z"
}
```

### Step 3: BrAPI Aggregate Exposure

```http
GET /brapi/v2/extensions/iot/aggregates?environmentDbId=env-kharif-2025-01
```

```json
{
  "metadata": {...},
  "result": {
    "data": [
      {
        "environmentDbId": "env-kharif-2025-01",
        "environmentalParameter": "air_temperature_mean",
        "value": 28.5,
        "unit": "°C",
        "period": "daily",
        "startDate": "2025-01-15",
        "endDate": "2025-01-15"
      }
    ]
  }
}
```

### Step 4: G×E Analysis

```python
# Use in breeding analysis
environment_data = {
    "environment_id": "env-kharif-2025-01",
    "location": "Field A",
    "season": "Kharif 2025",
    "covariates": {
        "mean_temp": 28.5,
        "gdd": 1850,
        "rainfall": 450,
        "drought_days": 12
    }
}

# Genotype × Environment interaction
gxe_model = fit_gxe(
    genotypes=germplasm_data,
    environments=[environment_data],
    trait="yield"
)
```

---

## 📊 Example G×E Workflow

### Scenario: Multi-Environment Trial (MET)

**Trial Setup**:
- 3 locations (Field A, B, C)
- 50 genotypes
- 2 seasons (Kharif, Rabi)
- Total: 6 environments

**Sensor Deployment**:
- 1 weather station per location
- 3 soil probes per location
- Continuous monitoring

**Data Flow**:

1. **Telemetry Collection** (Real-time)
   - 10,000+ readings/day per location
   - Stored in `iot_telemetry` hypertable

2. **Daily Aggregation** (Midnight)
   - Calculate daily means, totals
   - Store in `iot_aggregates` table
   - Link to `environment_id`

3. **BrAPI Exposure** (On-demand)
   - Query via `/brapi/v2/extensions/iot/aggregates`
   - Filter by environment, date range
   - Use in analysis tools

4. **G×E Analysis** (End of season)
   - Extract environmental covariates
   - Fit AMMI/GGE biplot models
   - Identify stable genotypes
   - Recommend varieties per environment

---

## 🎯 Key Environmental Covariates for Breeding

### Critical for Yield Prediction

| Covariate | Importance | Typical Range | Optimal Value |
|-----------|------------|---------------|---------------|
| **GDD (Growing Degree Days)** | ⭐⭐⭐⭐⭐ | 1500-2500 °C·day | Crop-specific |
| **Total Rainfall** | ⭐⭐⭐⭐⭐ | 300-800 mm | 500-600 mm |
| **Mean Temperature** | ⭐⭐⭐⭐ | 20-35 °C | 25-30 °C |
| **Drought Stress Days** | ⭐⭐⭐⭐ | 0-30 days | <10 days |
| **Heat Stress Days** | ⭐⭐⭐ | 0-20 days | <5 days |
| **Solar Radiation** | ⭐⭐⭐ | 15-25 MJ/m²/day | 18-22 MJ/m²/day |

### Critical for Disease Resistance

| Covariate | Importance | Typical Range | Risk Threshold |
|-----------|------------|---------------|----------------|
| **Leaf Wetness Hours** | ⭐⭐⭐⭐⭐ | 0-12 hours/day | >6 hours |
| **Relative Humidity** | ⭐⭐⭐⭐ | 40-90% | >80% |
| **Temperature Range** | ⭐⭐⭐ | 10-30 °C | 20-25 °C |

---

## 🔧 Implementation Example

### Python Service: Aggregation

```python
# backend/app/services/iot_aggregation.py

from datetime import datetime, timedelta
from sqlalchemy import func
from app.models.iot import Telemetry, Aggregate

class IoTAggregationService:
    
    async def aggregate_daily(self, environment_id: str, date: datetime):
        """Calculate daily aggregates for an environment."""
        
        start = date.replace(hour=0, minute=0, second=0)
        end = start + timedelta(days=1)
        
        # Temperature aggregates
        temp_data = await self.db.query(
            func.avg(Telemetry.value).label('mean'),
            func.max(Telemetry.value).label('max'),
            func.min(Telemetry.value).label('min')
        ).filter(
            Telemetry.sensor_type == 'temperature',
            Telemetry.time >= start,
            Telemetry.time < end
        ).first()
        
        # Store aggregates
        aggregates = [
            Aggregate(
                environment_id=environment_id,
                parameter='air_temperature_mean',
                value=temp_data.mean,
                unit='°C',
                period='daily',
                start_time=start,
                end_time=end
            ),
            # ... more aggregates
        ]
        
        await self.db.bulk_save_objects(aggregates)
        await self.db.commit()
```

---

## ✅ Validation Checklist

### For Each Sensor Type:
- [ ] Raw telemetry stored correctly
- [ ] Aggregation formulas validated
- [ ] BrAPI parameter exposed
- [ ] Units consistent
- [ ] Typical ranges documented
- [ ] G×E use case defined

### For Each Environment:
- [ ] Sensors linked to environment
- [ ] Aggregates calculated daily
- [ ] BrAPI endpoint returns data
- [ ] Covariates available for analysis
- [ ] Data quality validated

---

**Status**: Reference guide complete. Use this for implementation.

**Jay Shree Ganeshay Namo Namah!** 🙏
