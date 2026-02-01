# BijMantra BrAPI IoT Extension - Implementation Plan

> **Strategic Plan**: Transform sensor-iot.md spec into production-ready implementation
> 
> **Created**: December 20, 2025  
> **Status**: Ready to Execute  
> **Timeline**: 4-6 weeks

---

## 📊 Current State Analysis

### ✅ What We Have (Already Built)

**Backend** (`backend/app/api/v2/sensors.py`):
- 18 API endpoints for device/sensor management
- Device CRUD operations
- Reading recording and retrieval
- Alert rules and events
- Live readings generation
- Network statistics

**Service Layer** (`backend/app/services/sensor_network.py`):
- In-memory device management
- Demo data with 6 devices
- Alert rule engine
- Reading storage and retrieval
- Network statistics

**Frontend** (`frontend/src/divisions/sensor-networks/pages/`):
- Dashboard with live readings
- Device management UI
- Alert management UI
- Live data visualization

### ❌ What's Missing (From BrAPI IoT Spec)

1. **BrAPI Extension Endpoints** (`/brapi/v2/extensions/iot/`)
2. **Environmental Aggregates** (bridge to BrAPI environments)
3. **Telemetry Time-Series Storage** (PostgreSQL/TimescaleDB)
4. **BrAPI Environment Integration** (link sensors to studies/trials)
5. **G×E Analysis Support** (environmental covariates)
6. **Vendor-Neutral Device Registry**
7. **MQTT/LoRaWAN Gateway Integration**
8. **Database Persistence** (currently in-memory)

---

## 🎯 Implementation Strategy

### Phase 1: Database Foundation (Week 1-2)

**Goal**: Persist sensor data to PostgreSQL with TimescaleDB for time-series

#### Tasks:
1. **Database Schema Design**
   - `iot_devices` table
   - `iot_sensors` table
   - `iot_telemetry` hypertable (TimescaleDB)
   - `iot_alert_rules` table
   - `iot_alert_events` table
   - `iot_aggregates` table (for BrAPI bridge)

2. **Alembic Migration**
   - Create migration `008_iot_tables.py`
   - Add TimescaleDB extension
   - Create hypertable for telemetry
   - Add indexes for performance

3. **SQLAlchemy Models**
   - `backend/app/models/iot.py`
   - Device, Sensor, Telemetry, AlertRule, AlertEvent, Aggregate models
   - Relationships and constraints

4. **Update Service Layer**
   - Replace in-memory storage with database
   - Add async database operations
   - Maintain backward compatibility

**Deliverables**:
- ✅ Database schema
- ✅ Migration script
- ✅ SQLAlchemy models
- ✅ Updated service with persistence

**Estimated Time**: 1-2 weeks

---

### Phase 2: BrAPI Extension Endpoints (Week 2-3)

**Goal**: Implement `/brapi/v2/extensions/iot/` endpoints per spec

#### Tasks:
1. **Create BrAPI IoT Router**
   - `backend/app/api/brapi/extensions/iot.py`
   - Follow BrAPI v2.x response format
   - Add pagination, filtering, sorting

2. **Implement Core Endpoints**:
   - `GET /iot/devices` - Device metadata
   - `GET /iot/sensors` - Sensor catalog
   - `GET /iot/telemetry` - Time-series data (with mandatory time range)
   - `GET /iot/aggregates` - Environmental summaries (PRIMARY BRIDGE)
   - `GET /iot/alerts` - Alert events

3. **BrAPI Response Format**:

   ```json
   {
     "metadata": {
       "pagination": {"pageSize": 100, "currentPage": 0, "totalCount": 1234},
       "status": [],
       "datafiles": []
     },
     "result": {
       "data": [...]
     }
   }
   ```

4. **Telemetry Endpoint Rules**:
   - Mandatory time range (start_time, end_time)
   - Mandatory pagination
   - Optional downsampling (1min, 5min, 1hour, 1day)
   - Max 10,000 points per request

5. **Aggregates Endpoint** (Most Important):
   - Link to `environmentDbId` from BrAPI
   - Daily/weekly/seasonal summaries
   - Parameters: temp_mean, temp_max, rainfall_total, etc.
   - Used for G×E analysis

**Deliverables**:
- ✅ BrAPI IoT router with 5 endpoints
- ✅ BrAPI-compliant response format
- ✅ Pagination and filtering
- ✅ Telemetry downsampling
- ✅ Environmental aggregates

**Estimated Time**: 1 week

---

### Phase 3: BrAPI Environment Integration (Week 3-4)

**Goal**: Bridge IoT data to BrAPI core objects (Environments, Studies, Trials)

#### Tasks:
1. **Environment Linking**:
   - Add `environment_id` to devices/sensors
   - Link aggregates to BrAPI environments
   - Support multiple environments per device

2. **Environmental Parameters**:
   - Extend `/brapi/v2/environmentalParameters` endpoint
   - Add sensor-derived parameters
   - Map sensor types to environmental parameters

3. **Study/Trial Covariates**:
   - Add environmental covariates to studies
   - Link sensor data to observation units
   - Support G×E analysis workflows

4. **Observation Integration**:
   - Create "environmental observations" from sensor data
   - Use BrAPI observation schema
   - Link to observation units

**Deliverables**:
- ✅ Environment linking
- ✅ Environmental parameters
- ✅ Study covariates
- ✅ Observation integration

**Estimated Time**: 1 week

---

### Phase 4: Telemetry Aggregation Engine (Week 4-5)

**Goal**: Generate breeding-relevant environmental summaries

#### Tasks:
1. **Aggregation Service**:
   - `backend/app/services/iot_aggregation.py`
   - Daily, weekly, seasonal aggregations
   - Growing Degree Days (GDD)
   - Stress indices (heat, drought, frost)

2. **Aggregation Types**:
   - **Temperature**: mean, min, max, GDD
   - **Rainfall**: total, days, intensity
   - **Humidity**: mean, min, max
   - **Soil Moisture**: mean, stress days
   - **Solar Radiation**: total, mean PAR
   - **Wind**: mean speed, max gust

3. **Scheduled Jobs**:
   - Hourly aggregation (last hour)
   - Daily aggregation (midnight)
   - Weekly aggregation (Sunday)
   - Seasonal aggregation (end of season)

4. **Caching**:
   - Cache aggregates in `iot_aggregates` table
   - Invalidate on new data
   - Redis cache for frequently accessed

**Deliverables**:
- ✅ Aggregation service
- ✅ 6 aggregation types
- ✅ Scheduled jobs
- ✅ Caching layer

**Estimated Time**: 1 week

---

### Phase 5: IoT Gateway Integration (Week 5-6)

**Goal**: Connect real IoT devices via MQTT/LoRaWAN

#### Tasks:
1. **MQTT Broker Integration**:
   - Connect to Mosquitto/RabbitMQ
   - Subscribe to device topics
   - Parse telemetry messages
   - Store in database

2. **LoRaWAN Gateway**:
   - ChirpStack integration
   - Device registration
   - Uplink message parsing
   - Downlink commands

3. **Device Protocols**:
   - JSON payload format
   - Binary payload decoding
   - Vendor-specific adapters

4. **Real-Time Processing**:
   - WebSocket for live data
   - Alert evaluation on ingestion
   - Anomaly detection

**Deliverables**:
- ✅ MQTT integration
- ✅ LoRaWAN integration
- ✅ Device protocol adapters
- ✅ Real-time processing

**Estimated Time**: 1-2 weeks

---

### Phase 6: Frontend Enhancement (Week 6)

**Goal**: Update UI to use BrAPI IoT endpoints

#### Tasks:
1. **Update API Client**:
   - Add BrAPI IoT methods
   - Use `/brapi/v2/extensions/iot/` endpoints
   - Handle pagination

2. **New Pages**:
   - Environmental Aggregates page
   - Telemetry Viewer (time-series charts)
   - Environment Linking page
   - G×E Analysis Dashboard

3. **Enhanced Visualizations**:
   - Time-series charts (Recharts/ECharts)
   - Heatmaps for spatial data
   - Correlation matrices
   - GDD accumulation curves

4. **Real-Time Updates**:
   - WebSocket connection
   - Live telemetry streaming
   - Alert notifications

**Deliverables**:
- ✅ Updated API client
- ✅ 4 new pages
- ✅ Enhanced visualizations
- ✅ Real-time updates

**Estimated Time**: 1 week

---

## 📋 Detailed Task Breakdown

### Phase 1: Database Schema

```sql
-- Devices
CREATE TABLE iot_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    device_type VARCHAR(50) NOT NULL,
    connectivity VARCHAR(50), -- mqtt, lora, wifi, cellular
    status VARCHAR(20) DEFAULT 'offline',
    location JSONB, -- {lat, lon, elevation}
    field_id UUID REFERENCES fields(id),
    environment_id UUID REFERENCES environments(id),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Sensors
CREATE TABLE iot_sensors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID REFERENCES iot_devices(id) ON DELETE CASCADE,
    sensor_id VARCHAR(100) NOT NULL,
    sensor_type VARCHAR(50) NOT NULL,
    unit VARCHAR(20),
    accuracy VARCHAR(50),
    calibration_date DATE,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(device_id, sensor_id)
);

-- Telemetry (TimescaleDB Hypertable)
CREATE TABLE iot_telemetry (
    time TIMESTAMPTZ NOT NULL,
    device_id UUID NOT NULL,
    sensor_id UUID NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    quality VARCHAR(20) DEFAULT 'good', -- good, suspect, bad
    metadata JSONB
);

SELECT create_hypertable('iot_telemetry', 'time');
CREATE INDEX ON iot_telemetry (device_id, sensor_id, time DESC);

-- Alert Rules
CREATE TABLE iot_alert_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    sensor_type VARCHAR(50) NOT NULL,
    condition VARCHAR(20) NOT NULL, -- above, below, equals, range
    threshold DOUBLE PRECISION,
    threshold_min DOUBLE PRECISION,
    threshold_max DOUBLE PRECISION,
    severity VARCHAR(20) DEFAULT 'warning',
    enabled BOOLEAN DEFAULT TRUE,
    notify_channels JSONB, -- {email: true, sms: false, push: true}
    created_at TIMESTAMP DEFAULT NOW()
);

-- Alert Events
CREATE TABLE iot_alert_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id UUID REFERENCES iot_alert_rules(id),
    device_id UUID REFERENCES iot_devices(id),
    sensor_id UUID REFERENCES iot_sensors(id),
    value DOUBLE PRECISION,
    severity VARCHAR(20),
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(255),
    acknowledged_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Environmental Aggregates (BrAPI Bridge)
CREATE TABLE iot_aggregates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    environment_id UUID REFERENCES environments(id),
    parameter VARCHAR(100) NOT NULL, -- air_temperature_mean, rainfall_total
    value DOUBLE PRECISION NOT NULL,
    unit VARCHAR(20),
    period VARCHAR(20) NOT NULL, -- hourly, daily, weekly, seasonal
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(environment_id, parameter, period, start_time)
);
```

---

### Phase 2: BrAPI IoT Endpoints

**File**: `backend/app/api/brapi/extensions/iot.py`

```python
from fastapi import APIRouter, Query
from typing import Optional
from app.schemas.brapi import BrAPIResponse, Metadata, Pagination

router = APIRouter(prefix="/extensions/iot", tags=["BrAPI IoT Extension"])

@router.get("/devices")
async def get_iot_devices(
    page: int = Query(0, ge=0),
    pageSize: int = Query(100, ge=1, le=1000),
    deviceType: Optional[str] = None,
    status: Optional[str] = None,
):
    """Get IoT device metadata (BrAPI Extension)."""
    # Implementation
    pass

@router.get("/sensors")
async def get_iot_sensors(
    page: int = Query(0, ge=0),
    pageSize: int = Query(100, ge=1, le=1000),
    sensorType: Optional[str] = None,
):
    """Get sensor catalog (BrAPI Extension)."""
    pass

@router.get("/telemetry")
async def get_iot_telemetry(
    deviceDbId: str = Query(..., description="Device ID (required)"),
    sensorDbId: Optional[str] = None,
    startTime: str = Query(..., description="ISO 8601 start time (required)"),
    endTime: str = Query(..., description="ISO 8601 end time (required)"),
    downsample: Optional[str] = Query(None, description="1min, 5min, 1hour, 1day"),
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
):
    """Get time-series telemetry data (BrAPI Extension)."""
    pass

@router.get("/aggregates")
async def get_iot_aggregates(
    environmentDbId: str = Query(..., description="Environment ID (required)"),
    parameter: Optional[str] = None,
    period: Optional[str] = Query(None, description="hourly, daily, weekly, seasonal"),
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(100, ge=1, le=1000),
):
    """Get environmental aggregates for BrAPI environments (PRIMARY BRIDGE)."""
    pass

@router.get("/alerts")
async def get_iot_alerts(
    severity: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    startTime: Optional[str] = None,
    endTime: Optional[str] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(100, ge=1, le=1000),
):
    """Get alert events (BrAPI Extension)."""
    pass
```

---

### Phase 3: Environmental Parameters Mapping

**Sensor Type → Environmental Parameter**:

| Sensor Type | Environmental Parameter | Unit | Aggregation |
|-------------|------------------------|------|-------------|
| temperature | air_temperature_mean | °C | mean |
| temperature | air_temperature_max | °C | max |
| temperature | air_temperature_min | °C | min |
| temperature | growing_degree_days | °C·day | sum |
| humidity | relative_humidity_mean | % | mean |
| pressure | atmospheric_pressure_mean | hPa | mean |
| rainfall | precipitation_total | mm | sum |
| rainfall | precipitation_days | days | count |
| soil_moisture | soil_moisture_mean | % | mean |
| soil_temp | soil_temperature_mean | °C | mean |
| wind_speed | wind_speed_mean | km/h | mean |
| wind_speed | wind_speed_max | km/h | max |
| par | solar_radiation_total | MJ/m² | sum |
| leaf_wetness | leaf_wetness_hours | hours | sum |

---

### Phase 4: Aggregation Formulas

**Growing Degree Days (GDD)**:
```python
def calculate_gdd(temp_min, temp_max, base_temp=10, max_temp=30):
    """Calculate GDD using single sine method."""
    temp_avg = (temp_min + temp_max) / 2
    if temp_avg < base_temp:
        return 0
    if temp_avg > max_temp:
        return max_temp - base_temp
    return temp_avg - base_temp
```

**Heat Stress Index**:
```python
def calculate_heat_stress(temp_max, threshold=35):
    """Count days above threshold."""
    return 1 if temp_max > threshold else 0
```

**Drought Stress Index**:
```python
def calculate_drought_stress(soil_moisture, threshold=30):
    """Count days below threshold."""
    return 1 if soil_moisture < threshold else 0
```

---

## 🗂️ File Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── brapi/
│   │   │   └── extensions/
│   │   │       └── iot.py          # NEW: BrAPI IoT endpoints
│   │   └── v2/
│   │       └── sensors.py          # EXISTING: Keep for backward compat
│   ├── models/
│   │   └── iot.py                  # NEW: SQLAlchemy models
│   ├── services/
│   │   ├── sensor_network.py       # UPDATE: Add database persistence
│   │   └── iot_aggregation.py     # NEW: Aggregation engine
│   └── schemas/
│       └── iot.py                  # NEW: Pydantic schemas
├── alembic/
│   └── versions/
│       └── 008_iot_tables.py       # NEW: Database migration
└── integrations/
    ├── mqtt_client.py              # NEW: MQTT integration
    └── lorawan_client.py           # NEW: LoRaWAN integration

frontend/
└── src/
    └── divisions/
        └── sensor-networks/
            └── pages/
                ├── Dashboard.tsx           # UPDATE: Use BrAPI endpoints
                ├── Devices.tsx             # EXISTING
                ├── LiveData.tsx            # EXISTING
                ├── Alerts.tsx              # EXISTING
                ├── Telemetry.tsx           # NEW: Time-series viewer
                ├── Aggregates.tsx          # NEW: Environmental summaries
                └── EnvironmentLink.tsx     # NEW: Link to BrAPI environments
```

---

## 📊 Success Metrics

### Phase 1 Success:
- ✅ Database schema created
- ✅ Migration runs successfully
- ✅ Models tested with sample data
- ✅ Service layer persists to database

### Phase 2 Success:
- ✅ 5 BrAPI IoT endpoints implemented
- ✅ BrAPI response format validated
- ✅ Pagination works correctly
- ✅ Telemetry downsampling functional

### Phase 3 Success:
- ✅ Devices linked to environments
- ✅ Environmental parameters exposed
- ✅ Study covariates available
- ✅ G×E analysis possible

### Phase 4 Success:
- ✅ Aggregations calculated correctly
- ✅ GDD formula validated
- ✅ Scheduled jobs running
- ✅ Cache improves performance

### Phase 5 Success:
- ✅ MQTT broker connected
- ✅ Real device data ingested
- ✅ Alerts triggered in real-time
- ✅ WebSocket streaming works

### Phase 6 Success:
- ✅ UI uses BrAPI endpoints
- ✅ Time-series charts render
- ✅ Real-time updates work
- ✅ User can link environments

---

## 🚧 Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **TimescaleDB complexity** | Medium | High | Use PostgreSQL first, add TimescaleDB later |
| **MQTT broker setup** | Medium | Medium | Use managed service (CloudMQTT) |
| **Performance issues** | High | High | Add indexes, caching, downsampling |
| **BrAPI compliance** | Low | High | Follow spec strictly, validate responses |
| **Real device integration** | High | Medium | Start with simulated data, add real later |

---

## 🎯 Recommended Approach

### Option A: Full Implementation (4-6 weeks)
**Pros**: Complete BrAPI IoT Extension, production-ready
**Cons**: Time-intensive, requires TimescaleDB

### Option B: MVP First (2-3 weeks)
**Pros**: Faster delivery, validates concept
**Cons**: Missing real-time features

### Option C: Phased Rollout (Recommended)
**Week 1-2**: Phase 1 (Database)
**Week 3**: Phase 2 (BrAPI Endpoints)
**Week 4**: Phase 3 (Environment Integration)
**Week 5**: Phase 4 (Aggregation)
**Week 6**: Phase 6 (Frontend)
**Later**: Phase 5 (Real IoT Integration)

---

## ✅ Next Steps

### Immediate (This Week):
1. Review this plan
2. Decide on approach (A, B, or C)
3. Set up TimescaleDB (or use PostgreSQL)
4. Create database schema

### Week 1:
1. Write Alembic migration
2. Create SQLAlchemy models
3. Update service layer
4. Test with sample data

### Week 2:
1. Implement BrAPI IoT endpoints
2. Add pagination and filtering
3. Test with Postman
4. Validate BrAPI compliance

---

**Status**: Ready to execute! Say "SWAYAM IoT" to begin autonomous implementation.

**Jay Shree Ganeshay Namo Namah!** 🙏
