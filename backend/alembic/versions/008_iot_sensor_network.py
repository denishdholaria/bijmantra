"""IoT Sensor Network Tables

BrAPI IoT Extension - Devices, Sensors, Telemetry, Alerts, Aggregates
Implements: docs/confidential/SensorIOT/sensor-iot.md specification

Revision ID: 008
Revises: 007_schema_per_division
Create Date: 2025-12-20
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON
from geoalchemy2 import Geometry

# revision identifiers
revision = '008'
down_revision = '007_schema_per_division'
branch_labels = None
depends_on = None


def upgrade():
    # ===========================================
    # IoT Devices Table
    # ===========================================
    op.create_table(
        'iot_devices',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        
        # Core identifiers
        sa.Column('device_db_id', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        
        # Device classification
        sa.Column('device_type', sa.String(50), nullable=False, index=True),
        sa.Column('connectivity', sa.String(50)),
        sa.Column('protocol', sa.String(50)),
        
        # Status
        sa.Column('status', sa.String(20), server_default='offline', index=True),
        sa.Column('battery_level', sa.Integer()),
        sa.Column('signal_strength', sa.Integer()),
        sa.Column('firmware_version', sa.String(50)),
        sa.Column('last_seen', sa.DateTime(timezone=True)),
        
        # Location (PostGIS)
        sa.Column('coordinates', Geometry('POINT', srid=4326)),
        sa.Column('location_description', sa.String(255)),
        sa.Column('elevation', sa.Float()),
        
        # BrAPI Integration
        sa.Column('field_id', sa.Integer(), sa.ForeignKey('locations.id')),
        sa.Column('environment_id', sa.String(255), index=True),
        sa.Column('study_id', sa.Integer(), sa.ForeignKey('studies.id')),
        
        # Organization (multi-tenant)
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id'), nullable=False, index=True),
        
        # Metadata
        sa.Column('manufacturer', sa.String(100)),
        sa.Column('model', sa.String(100)),
        sa.Column('serial_number', sa.String(100)),
        sa.Column('installation_date', sa.DateTime()),
        sa.Column('calibration_date', sa.DateTime()),
        sa.Column('additional_info', JSON),
    )
    
    # ===========================================
    # IoT Sensors Table
    # ===========================================
    op.create_table(
        'iot_sensors',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        
        # Core identifiers
        sa.Column('sensor_db_id', sa.String(100), nullable=False, index=True),
        sa.Column('device_id', sa.Integer(), sa.ForeignKey('iot_devices.id', ondelete='CASCADE'), nullable=False, index=True),
        
        # Sensor classification
        sa.Column('sensor_type', sa.String(50), nullable=False, index=True),
        sa.Column('name', sa.String(255)),
        sa.Column('description', sa.Text()),
        
        # Measurement specs
        sa.Column('unit', sa.String(30), nullable=False),
        sa.Column('accuracy', sa.String(50)),
        sa.Column('precision', sa.Integer()),
        sa.Column('min_value', sa.Float()),
        sa.Column('max_value', sa.Float()),
        
        # Calibration
        sa.Column('calibration_date', sa.DateTime()),
        sa.Column('calibration_offset', sa.Float(), server_default='0'),
        sa.Column('calibration_factor', sa.Float(), server_default='1'),
        
        # Status
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        
        # Metadata
        sa.Column('additional_info', JSON),
        
        # Constraints
        sa.UniqueConstraint('device_id', 'sensor_db_id', name='uq_device_sensor'),
    )
    op.create_index('ix_iot_sensors_type_device', 'iot_sensors', ['sensor_type', 'device_id'])

    
    # ===========================================
    # IoT Telemetry Table (Time-Series)
    # ===========================================
    op.create_table(
        'iot_telemetry',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        
        # Time-series key
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, index=True),
        
        # Foreign keys
        sa.Column('device_id', sa.Integer(), sa.ForeignKey('iot_devices.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('sensor_id', sa.Integer(), sa.ForeignKey('iot_sensors.id', ondelete='CASCADE'), nullable=False, index=True),
        
        # Measurement
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('raw_value', sa.Float()),
        
        # Quality
        sa.Column('quality', sa.String(20), server_default='good'),
        sa.Column('quality_code', sa.Integer()),
        
        # Metadata
        sa.Column('additional_info', JSON),
    )
    op.create_index('ix_telemetry_device_sensor_time', 'iot_telemetry', ['device_id', 'sensor_id', 'timestamp'])
    op.create_index('ix_telemetry_time_desc', 'iot_telemetry', ['timestamp'])
    
    # ===========================================
    # IoT Alert Rules Table
    # ===========================================
    op.create_table(
        'iot_alert_rules',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        
        # Core identifiers
        sa.Column('rule_db_id', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        
        # Target
        sa.Column('sensor_type', sa.String(50), nullable=False, index=True),
        sa.Column('device_id', sa.Integer(), sa.ForeignKey('iot_devices.id'), index=True),
        
        # Condition
        sa.Column('condition', sa.String(20), nullable=False),
        sa.Column('threshold', sa.Float()),
        sa.Column('threshold_min', sa.Float()),
        sa.Column('threshold_max', sa.Float()),
        sa.Column('threshold_unit', sa.String(30)),
        
        # Timing
        sa.Column('duration_minutes', sa.Integer(), server_default='0'),
        sa.Column('cooldown_minutes', sa.Integer(), server_default='60'),
        
        # Severity
        sa.Column('severity', sa.String(20), server_default='warning', index=True),
        
        # Status
        sa.Column('enabled', sa.Boolean(), server_default='true', index=True),
        
        # Notifications
        sa.Column('notify_email', sa.Boolean(), server_default='true'),
        sa.Column('notify_sms', sa.Boolean(), server_default='false'),
        sa.Column('notify_push', sa.Boolean(), server_default='true'),
        sa.Column('notify_webhook', sa.String(500)),
        sa.Column('notify_users', JSON),
        
        # Organization (multi-tenant)
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id'), nullable=False, index=True),
        
        # Metadata
        sa.Column('additional_info', JSON),
    )
    
    # ===========================================
    # IoT Alert Events Table
    # ===========================================
    op.create_table(
        'iot_alert_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        
        # Core identifiers
        sa.Column('event_db_id', sa.String(100), unique=True, nullable=False, index=True),
        
        # References
        sa.Column('rule_id', sa.Integer(), sa.ForeignKey('iot_alert_rules.id', ondelete='SET NULL'), index=True),
        sa.Column('device_id', sa.Integer(), sa.ForeignKey('iot_devices.id', ondelete='SET NULL'), index=True),
        sa.Column('sensor_id', sa.Integer(), sa.ForeignKey('iot_sensors.id', ondelete='SET NULL'), index=True),
        
        # Alert details
        sa.Column('alert_type', sa.String(50), nullable=False, index=True),
        sa.Column('severity', sa.String(20), nullable=False, index=True),
        sa.Column('message', sa.Text(), nullable=False),
        
        # Trigger data
        sa.Column('trigger_value', sa.Float()),
        sa.Column('trigger_threshold', sa.Float()),
        sa.Column('trigger_condition', sa.String(20)),
        
        # Timing
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('end_time', sa.DateTime(timezone=True)),
        sa.Column('duration_seconds', sa.Integer()),
        
        # Status
        sa.Column('status', sa.String(20), server_default='active', index=True),
        sa.Column('acknowledged', sa.Boolean(), server_default='false', index=True),
        sa.Column('acknowledged_by', sa.String(255)),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True)),
        sa.Column('acknowledged_note', sa.Text()),
        
        # Resolution
        sa.Column('resolved_at', sa.DateTime(timezone=True)),
        sa.Column('resolved_by', sa.String(255)),
        sa.Column('resolution_note', sa.Text()),
        
        # Notifications sent
        sa.Column('notifications_sent', JSON),
        
        # Metadata
        sa.Column('additional_info', JSON),
    )
    op.create_index('ix_alert_events_status_severity', 'iot_alert_events', ['status', 'severity'])
    op.create_index('ix_alert_events_device_time', 'iot_alert_events', ['device_id', 'start_time'])
    
    # ===========================================
    # IoT Aggregates Table (BrAPI Bridge)
    # ===========================================
    op.create_table(
        'iot_aggregates',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        
        # BrAPI Integration (PRIMARY KEY for bridge)
        sa.Column('environment_db_id', sa.String(255), nullable=False, index=True),
        sa.Column('study_id', sa.Integer(), sa.ForeignKey('studies.id'), index=True),
        
        # Environmental parameter
        sa.Column('parameter', sa.String(100), nullable=False, index=True),
        sa.Column('parameter_category', sa.String(50)),
        
        # Value
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(30), nullable=False),
        
        # Aggregation period
        sa.Column('period', sa.String(20), nullable=False, index=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        
        # Statistics
        sa.Column('min_value', sa.Float()),
        sa.Column('max_value', sa.Float()),
        sa.Column('std_dev', sa.Float()),
        sa.Column('sample_count', sa.Integer()),
        
        # Source tracking
        sa.Column('source_device_ids', JSON),
        sa.Column('source_sensor_ids', JSON),
        
        # Quality
        sa.Column('quality_score', sa.Float()),
        sa.Column('missing_data_percent', sa.Float()),
        
        # Metadata
        sa.Column('calculation_method', sa.String(100)),
        sa.Column('additional_info', JSON),
        
        # Constraints
        sa.UniqueConstraint('environment_db_id', 'parameter', 'period', 'start_time', 
                          name='uq_aggregate_env_param_period_time'),
    )
    op.create_index('ix_aggregates_env_period', 'iot_aggregates', ['environment_db_id', 'period'])
    op.create_index('ix_aggregates_param_time', 'iot_aggregates', ['parameter', 'start_time'])
    
    # ===========================================
    # IoT Environment Links Table
    # ===========================================
    op.create_table(
        'iot_environment_links',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        
        # BrAPI references
        sa.Column('environment_db_id', sa.String(255), nullable=False, index=True),
        sa.Column('study_id', sa.Integer(), sa.ForeignKey('studies.id'), index=True),
        sa.Column('trial_id', sa.Integer(), sa.ForeignKey('trials.id'), index=True),
        sa.Column('location_id', sa.Integer(), sa.ForeignKey('locations.id'), index=True),
        
        # IoT references
        sa.Column('device_id', sa.Integer(), sa.ForeignKey('iot_devices.id', ondelete='CASCADE'), nullable=False, index=True),
        
        # Link configuration
        sa.Column('is_primary', sa.Boolean(), server_default='false'),
        sa.Column('weight', sa.Float(), server_default='1.0'),
        
        # Active period
        sa.Column('start_date', sa.DateTime(timezone=True)),
        sa.Column('end_date', sa.DateTime(timezone=True)),
        sa.Column('is_active', sa.Boolean(), server_default='true', index=True),
        
        # Metadata
        sa.Column('notes', sa.Text()),
        sa.Column('additional_info', JSON),
        
        # Constraints
        sa.UniqueConstraint('environment_db_id', 'device_id', name='uq_env_device_link'),
    )
    op.create_index('ix_env_links_active', 'iot_environment_links', ['environment_db_id', 'is_active'])
    
    print("✅ IoT Sensor Network tables created successfully!")


def downgrade():
    op.drop_table('iot_environment_links')
    op.drop_table('iot_aggregates')
    op.drop_table('iot_alert_events')
    op.drop_table('iot_alert_rules')
    op.drop_table('iot_telemetry')
    op.drop_table('iot_sensors')
    op.drop_table('iot_devices')
    print("✅ IoT Sensor Network tables dropped successfully!")
