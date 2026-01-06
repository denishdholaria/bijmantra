"""
IoT Sensor Network Models

BrAPI IoT Extension - Devices, Sensors, Telemetry, Alerts, Aggregates
Implements: docs/confidential/SensorIOT/sensor-iot.md specification
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, 
    ForeignKey, JSON, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.models.base import BaseModel


class IoTDevice(BaseModel):
    """
    IoT Device - Physical or virtual unit that produces sensor data
    
    Examples: Weather station, soil probe, gateway, plant sensor
    """
    
    __tablename__ = "iot_devices"
    
    # Core identifiers
    device_db_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Device classification
    device_type = Column(String(50), nullable=False, index=True)  # weather, soil, plant, water, gateway
    connectivity = Column(String(50))  # mqtt, lora, wifi, cellular, zigbee
    protocol = Column(String(50))  # json, binary, modbus, custom
    
    # Status
    status = Column(String(20), default="offline", index=True)  # online, offline, warning, error
    battery_level = Column(Integer)  # 0-100%
    signal_strength = Column(Integer)  # 0-100%
    firmware_version = Column(String(50))
    last_seen = Column(DateTime(timezone=True))
    
    # Location (PostGIS)
    coordinates = Column(Geometry('POINT', srid=4326))
    location_description = Column(String(255))
    elevation = Column(Float)  # meters
    
    # BrAPI Integration
    field_id = Column(Integer, ForeignKey("locations.id"), index=True)
    environment_id = Column(String(255), index=True)  # Links to BrAPI environment
    study_id = Column(Integer, ForeignKey("studies.id"), index=True)
    
    # Organization (multi-tenant)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Metadata
    manufacturer = Column(String(100))
    model = Column(String(100))
    serial_number = Column(String(100))
    installation_date = Column(DateTime)
    calibration_date = Column(DateTime)
    additional_info = Column(JSON)
    
    # Relationships
    organization = relationship("Organization")
    field = relationship("Location")
    study = relationship("Study")
    sensors = relationship("IoTSensor", back_populates="device", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<IoTDevice {self.device_db_id}: {self.name}>"


class IoTSensor(BaseModel):
    """
    IoT Sensor - Logical measurement unit associated with a device
    
    Examples: temperature, soil_moisture, humidity, par, leaf_wetness
    """
    
    __tablename__ = "iot_sensors"
    
    # Core identifiers
    sensor_db_id = Column(String(100), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("iot_devices.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Sensor classification
    sensor_type = Column(String(50), nullable=False, index=True)  # temperature, humidity, soil_moisture, etc.
    name = Column(String(255))
    description = Column(Text)
    
    # Measurement specs
    unit = Column(String(30), nullable=False)  # °C, %, hPa, mm, etc.
    accuracy = Column(String(50))  # ±0.5°C
    precision = Column(Integer)  # decimal places
    min_value = Column(Float)  # valid range min
    max_value = Column(Float)  # valid range max
    
    # Calibration
    calibration_date = Column(DateTime)
    calibration_offset = Column(Float, default=0)
    calibration_factor = Column(Float, default=1)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    additional_info = Column(JSON)
    
    # Relationships
    device = relationship("IoTDevice", back_populates="sensors")
    
    __table_args__ = (
        UniqueConstraint('device_id', 'sensor_db_id', name='uq_device_sensor'),
        Index('ix_iot_sensors_type_device', 'sensor_type', 'device_id'),
    )
    
    def __repr__(self):
        return f"<IoTSensor {self.sensor_db_id}: {self.sensor_type}>"



class IoTTelemetry(BaseModel):
    """
    IoT Telemetry - High-frequency time-series sensor data
    
    Note: In production, consider using TimescaleDB hypertable for this table
    """
    
    __tablename__ = "iot_telemetry"
    
    # Time-series key
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Foreign keys
    device_id = Column(Integer, ForeignKey("iot_devices.id", ondelete="CASCADE"), nullable=False, index=True)
    sensor_id = Column(Integer, ForeignKey("iot_sensors.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Measurement
    value = Column(Float, nullable=False)
    raw_value = Column(Float)  # Before calibration
    
    # Quality
    quality = Column(String(20), default="good")  # good, suspect, bad, missing
    quality_code = Column(Integer)  # Numeric quality code
    
    # Metadata
    additional_info = Column(JSON)
    
    __table_args__ = (
        Index('ix_telemetry_device_sensor_time', 'device_id', 'sensor_id', 'timestamp'),
        Index('ix_telemetry_time_desc', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<IoTTelemetry {self.timestamp}: {self.value}>"


class IoTAlertRule(BaseModel):
    """
    IoT Alert Rule - Threshold-based alert configuration
    
    Triggers alerts when sensor values exceed defined thresholds
    """
    
    __tablename__ = "iot_alert_rules"
    
    # Core identifiers
    rule_db_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Target
    sensor_type = Column(String(50), nullable=False, index=True)  # Which sensor type to monitor
    device_id = Column(Integer, ForeignKey("iot_devices.id"), index=True)  # Optional: specific device
    
    # Condition
    condition = Column(String(20), nullable=False)  # above, below, equals, range, rate_of_change
    threshold = Column(Float)  # For above/below/equals
    threshold_min = Column(Float)  # For range
    threshold_max = Column(Float)  # For range
    threshold_unit = Column(String(30))
    
    # Timing
    duration_minutes = Column(Integer, default=0)  # How long condition must persist
    cooldown_minutes = Column(Integer, default=60)  # Min time between alerts
    
    # Severity
    severity = Column(String(20), default="warning", index=True)  # info, warning, critical, emergency
    
    # Status
    enabled = Column(Boolean, default=True, index=True)
    
    # Notifications
    notify_email = Column(Boolean, default=True)
    notify_sms = Column(Boolean, default=False)
    notify_push = Column(Boolean, default=True)
    notify_webhook = Column(String(500))  # Webhook URL
    notify_users = Column(JSON)  # List of user IDs
    
    # Organization (multi-tenant)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Metadata
    additional_info = Column(JSON)
    
    # Relationships
    organization = relationship("Organization")
    device = relationship("IoTDevice")
    events = relationship("IoTAlertEvent", back_populates="rule", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<IoTAlertRule {self.rule_db_id}: {self.name}>"


class IoTAlertEvent(BaseModel):
    """
    IoT Alert Event - Triggered alert instance
    
    Created when an alert rule condition is met
    """
    
    __tablename__ = "iot_alert_events"
    
    # Core identifiers
    event_db_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # References
    rule_id = Column(Integer, ForeignKey("iot_alert_rules.id", ondelete="SET NULL"), index=True)
    device_id = Column(Integer, ForeignKey("iot_devices.id", ondelete="SET NULL"), index=True)
    sensor_id = Column(Integer, ForeignKey("iot_sensors.id", ondelete="SET NULL"), index=True)
    
    # Alert details
    alert_type = Column(String(50), nullable=False, index=True)  # threshold, anomaly, offline, battery_low
    severity = Column(String(20), nullable=False, index=True)  # info, warning, critical, emergency
    message = Column(Text, nullable=False)
    
    # Trigger data
    trigger_value = Column(Float)
    trigger_threshold = Column(Float)
    trigger_condition = Column(String(20))
    
    # Timing
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True))  # When condition ended
    duration_seconds = Column(Integer)
    
    # Status
    status = Column(String(20), default="active", index=True)  # active, resolved, acknowledged, dismissed
    acknowledged = Column(Boolean, default=False, index=True)
    acknowledged_by = Column(String(255))
    acknowledged_at = Column(DateTime(timezone=True))
    acknowledged_note = Column(Text)
    
    # Resolution
    resolved_at = Column(DateTime(timezone=True))
    resolved_by = Column(String(255))
    resolution_note = Column(Text)
    
    # Notifications sent
    notifications_sent = Column(JSON)  # {email: true, sms: false, push: true}
    
    # Metadata
    additional_info = Column(JSON)
    
    # Relationships
    rule = relationship("IoTAlertRule", back_populates="events")
    device = relationship("IoTDevice")
    sensor = relationship("IoTSensor")
    
    __table_args__ = (
        Index('ix_alert_events_status_severity', 'status', 'severity'),
        Index('ix_alert_events_device_time', 'device_id', 'start_time'),
    )
    
    def __repr__(self):
        return f"<IoTAlertEvent {self.event_db_id}: {self.severity}>"


class IoTAggregate(BaseModel):
    """
    IoT Aggregate - Derived environmental summaries for BrAPI integration
    
    This is the PRIMARY BRIDGE between IoT telemetry and BrAPI environments.
    Aggregates are suitable as environmental covariates for G×E analysis.
    """
    
    __tablename__ = "iot_aggregates"
    
    # BrAPI Integration (PRIMARY KEY for bridge)
    environment_db_id = Column(String(255), nullable=False, index=True)  # Links to BrAPI environment
    study_id = Column(Integer, ForeignKey("studies.id"), index=True)
    
    # Environmental parameter
    parameter = Column(String(100), nullable=False, index=True)  # air_temperature_mean, rainfall_total, gdd
    parameter_category = Column(String(50))  # temperature, precipitation, radiation, soil, stress
    
    # Value
    value = Column(Float, nullable=False)
    unit = Column(String(30), nullable=False)
    
    # Aggregation period
    period = Column(String(20), nullable=False, index=True)  # hourly, daily, weekly, monthly, seasonal
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False)
    
    # Statistics (optional, for richer aggregates)
    min_value = Column(Float)
    max_value = Column(Float)
    std_dev = Column(Float)
    sample_count = Column(Integer)
    
    # Source tracking
    source_device_ids = Column(JSON)  # List of device IDs that contributed
    source_sensor_ids = Column(JSON)  # List of sensor IDs that contributed
    
    # Quality
    quality_score = Column(Float)  # 0-1, based on data completeness
    missing_data_percent = Column(Float)
    
    # Metadata
    calculation_method = Column(String(100))  # mean, sum, max, gdd_single_sine, etc.
    additional_info = Column(JSON)
    
    # Relationships
    study = relationship("Study")
    
    __table_args__ = (
        UniqueConstraint('environment_db_id', 'parameter', 'period', 'start_time', 
                        name='uq_aggregate_env_param_period_time'),
        Index('ix_aggregates_env_period', 'environment_db_id', 'period'),
        Index('ix_aggregates_param_time', 'parameter', 'start_time'),
    )
    
    def __repr__(self):
        return f"<IoTAggregate {self.environment_db_id}: {self.parameter}={self.value}>"


class IoTEnvironmentLink(BaseModel):
    """
    IoT Environment Link - Maps devices/sensors to BrAPI environments
    
    Enables automatic aggregation of sensor data for specific environments
    """
    
    __tablename__ = "iot_environment_links"
    
    # BrAPI references
    environment_db_id = Column(String(255), nullable=False, index=True)
    study_id = Column(Integer, ForeignKey("studies.id"), index=True)
    trial_id = Column(Integer, ForeignKey("trials.id"), index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), index=True)
    
    # IoT references
    device_id = Column(Integer, ForeignKey("iot_devices.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Link configuration
    is_primary = Column(Boolean, default=False)  # Primary device for this environment
    weight = Column(Float, default=1.0)  # Weight for averaging multiple devices
    
    # Active period
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True, index=True)
    
    # Metadata
    notes = Column(Text)
    additional_info = Column(JSON)
    
    # Relationships
    device = relationship("IoTDevice")
    study = relationship("Study")
    trial = relationship("Trial")
    location = relationship("Location")
    
    __table_args__ = (
        UniqueConstraint('environment_db_id', 'device_id', name='uq_env_device_link'),
        Index('ix_env_links_active', 'environment_db_id', 'is_active'),
    )
    
    def __repr__(self):
        return f"<IoTEnvironmentLink {self.environment_db_id} -> Device {self.device_id}>"
