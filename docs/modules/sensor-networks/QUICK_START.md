# BrAPI IoT Extension - Quick Start Guide

> **Get Started in 30 Minutes**: Set up your development environment and run Phase 1
> 
> **Prerequisites**: PostgreSQL, Python 3.11+, Node.js 18+

---

## 🚀 Phase 1: Database Setup (30 minutes)

### Step 1: Create Database Schema (10 min)

```bash
# Navigate to backend
cd backend

# Create migration file
alembic revision -m "add_iot_tables"
```

**Edit**: `backend/alembic/versions/008_add_iot_tables.py`

```python
"""add_iot_tables

Revision ID: 008
Revises: 007
Create Date: 2025-12-20
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

def upgrade():
    # Devices
    op.create_table(
        'iot_devices',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('device_id', sa.String(100), unique=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('device_type', sa.String(50), nullable=False),
        sa.Column('connectivity', sa.String(50)),
        sa.Column('status', sa.String(20), server_default='offline'),
        sa.Column('location', JSONB),
        sa.Column('field_id', UUID, sa.ForeignKey('fields.id')),
        sa.Column('environment_id', UUID),
        sa.Column('metadata', JSONB),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Sensors
    op.create_table(
        'iot_sensors',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('device_id', UUID, sa.ForeignKey('iot_devices.id', ondelete='CASCADE')),
        sa.Column('sensor_id', sa.String(100), nullable=False),
        sa.Column('sensor_type', sa.String(50), nullable=False),
        sa.Column('unit', sa.String(20)),
        sa.Column('accuracy', sa.String(50)),
        sa.Column('calibration_date', sa.Date),
        sa.Column('metadata', JSONB),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('device_id', 'sensor_id')
    )
    
    # Telemetry
    op.create_table(
        'iot_telemetry',
        sa.Column('time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('device_id', UUID, nullable=False),
        sa.Column('sensor_id', UUID, nullable=False),
        sa.Column('value', sa.Float, nullable=False),
        sa.Column('quality', sa.String(20), server_default='good'),
        sa.Column('metadata', JSONB)
    )
    
    # Indexes
    op.create_index('idx_telemetry_device_sensor_time', 'iot_telemetry', ['device_id', 'sensor_id', 'time'])
    op.create_index('idx_telemetry_time', 'iot_telemetry', ['time'])
    
    # Alert Rules
    op.create_table(
        'iot_alert_rules',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('sensor_type', sa.String(50), nullable=False),
        sa.Column('condition', sa.String(20), nullable=False),
        sa.Column('threshold', sa.Float),
        sa.Column('threshold_min', sa.Float),
        sa.Column('threshold_max', sa.Float),
        sa.Column('severity', sa.String(20), server_default='warning'),
        sa.Column('enabled', sa.Boolean, server_default='true'),
        sa.Column('notify_channels', JSONB),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )
    
    # Alert Events
    op.create_table(
        'iot_alert_events',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('rule_id', UUID, sa.ForeignKey('iot_alert_rules.id')),
        sa.Column('device_id', UUID, sa.ForeignKey('iot_devices.id')),
        sa.Column('sensor_id', UUID, sa.ForeignKey('iot_sensors.id')),
        sa.Column('value', sa.Float),
        sa.Column('severity', sa.String(20)),
        sa.Column('acknowledged', sa.Boolean, server_default='false'),
        sa.Column('acknowledged_by', sa.String(255)),
        sa.Column('acknowledged_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )
    
    # Aggregates
    op.create_table(
        'iot_aggregates',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('environment_id', UUID),
        sa.Column('parameter', sa.String(100), nullable=False),
        sa.Column('value', sa.Float, nullable=False),
        sa.Column('unit', sa.String(20)),
        sa.Column('period', sa.String(20), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metadata', JSONB),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('environment_id', 'parameter', 'period', 'start_time')
    )

def downgrade():
    op.drop_table('iot_aggregates')
    op.drop_table('iot_alert_events')
    op.drop_table('iot_alert_rules')
    op.drop_table('iot_telemetry')
    op.drop_table('iot_sensors')
    op.drop_table('iot_devices')
```

**Run Migration**:

```bash
alembic upgrade head
```

---

### Step 2: Create SQLAlchemy Models (10 min)

**Create**: `backend/app/models/iot.py`

```python
"""IoT Models"""

from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class IoTDevice(Base):
    __tablename__ = "iot_devices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(String(100), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    device_type = Column(String(50), nullable=False)
    connectivity = Column(String(50))
    status = Column(String(20), default="offline")
    location = Column(JSONB)
    field_id = Column(UUID(as_uuid=True), ForeignKey("fields.id"))
    environment_id = Column(UUID(as_uuid=True))
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    sensors = relationship("IoTSensor", back_populates="device", cascade="all, delete-orphan")

class IoTSensor(Base):
    __tablename__ = "iot_sensors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("iot_devices.id", ondelete="CASCADE"))
    sensor_id = Column(String(100), nullable=False)
    sensor_type = Column(String(50), nullable=False)
    unit = Column(String(20))
    accuracy = Column(String(50))
    calibration_date = Column(DateTime)
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    device = relationship("IoTDevice", back_populates="sensors")
    
    __table_args__ = (UniqueConstraint('device_id', 'sensor_id'),)

class IoTTelemetry(Base):
    __tablename__ = "iot_telemetry"
    
    time = Column(DateTime(timezone=True), nullable=False, primary_key=True)
    device_id = Column(UUID(as_uuid=True), nullable=False, primary_key=True)
    sensor_id = Column(UUID(as_uuid=True), nullable=False, primary_key=True)
    value = Column(Float, nullable=False)
    quality = Column(String(20), default="good")
    metadata = Column(JSONB)

class IoTAlertRule(Base):
    __tablename__ = "iot_alert_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    sensor_type = Column(String(50), nullable=False)
    condition = Column(String(20), nullable=False)
    threshold = Column(Float)
    threshold_min = Column(Float)
    threshold_max = Column(Float)
    severity = Column(String(20), default="warning")
    enabled = Column(Boolean, default=True)
    notify_channels = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class IoTAlertEvent(Base):
    __tablename__ = "iot_alert_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("iot_alert_rules.id"))
    device_id = Column(UUID(as_uuid=True), ForeignKey("iot_devices.id"))
    sensor_id = Column(UUID(as_uuid=True), ForeignKey("iot_sensors.id"))
    value = Column(Float)
    severity = Column(String(20))
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(255))
    acknowledged_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class IoTAggregate(Base):
    __tablename__ = "iot_aggregates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    environment_id = Column(UUID(as_uuid=True))
    parameter = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(20))
    period = Column(String(20), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (UniqueConstraint('environment_id', 'parameter', 'period', 'start_time'),)
```

---

### Step 3: Update Service Layer (10 min)

**Update**: `backend/app/services/sensor_network.py`

Add database operations:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.iot import IoTDevice, IoTSensor, IoTTelemetry
from app.core.database import get_db

class SensorNetworkService:
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def register_device(self, device_id: str, name: str, device_type: str, ...):
        """Register device in database."""
        device = IoTDevice(
            device_id=device_id,
            name=name,
            device_type=device_type,
            # ... other fields
        )
        self.db.add(device)
        await self.db.commit()
        await self.db.refresh(device)
        return device
    
    async def record_reading(self, device_id: str, sensor_id: str, value: float, ...):
        """Record telemetry in database."""
        reading = IoTTelemetry(
            time=datetime.utcnow(),
            device_id=device_id,
            sensor_id=sensor_id,
            value=value,
            # ... other fields
        )
        self.db.add(reading)
        await self.db.commit()
        return reading
```

---

## ✅ Verify Installation

```bash
# Check tables created
psql -d bijmantra -c "\dt iot_*"

# Should see:
# iot_devices
# iot_sensors
# iot_telemetry
# iot_alert_rules
# iot_alert_events
# iot_aggregates
```

---

## 🎯 Next Steps

**Phase 1 Complete!** ✅

Now move to **Phase 2: BrAPI Endpoints**

See `IMPLEMENTATION_PLAN.md` for details.

---

**Jay Shree Ganeshay Namo Namah!** 🙏
