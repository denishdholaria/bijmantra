"""
Demo IoT Sensor Network Data Seeder

Seeds IoT devices, sensors, telemetry, alerts, and aggregates
into the Demo Organization for development and testing.
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.db.seeders.base import BaseSeeder, register_seeder
from app.models.iot import (
    IoTDevice, IoTSensor, IoTTelemetry, IoTAlertRule,
    IoTAlertEvent, IoTAggregate, IoTEnvironmentLink
)
from app.core.config import settings
import uuid
import random
import logging

logger = logging.getLogger(__name__)


@register_seeder
class DemoIoTSeeder(BaseSeeder):
    """Seeds IoT sensor network data into Demo Organization"""

    name = "demo_iot"
    priority = 30  # After core seeders

    def seed(self) -> int:
        """Seed demo IoT data"""
        from app.models.core import Organization

        count = 0

        # Get Demo Organization
        demo_org = self.db.query(Organization).filter(
            Organization.name == settings.DEMO_ORG_NAME
        ).first()
        if not demo_org:
            logger.warning("Demo Organization not found, skipping IoT seeder")
            return 0

        org_id = demo_org.id
        now = datetime.now(timezone.utc)

        # Check if already seeded
        existing = self.db.query(IoTDevice).filter(IoTDevice.organization_id == org_id).first()
        if existing:
            logger.info("IoT data already seeded")
            return 0

        # ===========================================
        # Seed IoT Devices
        # ===========================================
        devices_data = [
            {
                "device_db_id": "DEV-WS-001",
                "name": "Weather Station Alpha",
                "description": "Primary weather station for Field A",
                "device_type": "weather_station",
                "connectivity": "lora",
                "protocol": "json",
                "status": "online",
                "battery_level": 85,
                "signal_strength": 92,
                "firmware_version": "v2.1.0",
                "last_seen": now,
                "location_description": "Field A - North Corner",
                "elevation": 15.0,
                "environment_id": "env-kharif-2025-field-a",
                "manufacturer": "AgriSense",
                "model": "WS-Pro-500",
                "serial_number": "WS2024001",
            },
            {
                "device_db_id": "DEV-SP-001",
                "name": "Soil Probe Block A",
                "description": "Soil moisture and temperature probe",
                "device_type": "soil_probe",
                "connectivity": "lora",
                "protocol": "json",
                "status": "online",
                "battery_level": 72,
                "signal_strength": 88,
                "firmware_version": "v1.8.2",
                "last_seen": now,
                "location_description": "Field A - Block A Center",
                "elevation": 14.0,
                "environment_id": "env-kharif-2025-field-a",
                "manufacturer": "SoilTech",
                "model": "SP-200",
                "serial_number": "SP2024001",
            },
            {
                "device_db_id": "DEV-SP-002",
                "name": "Soil Probe Block B",
                "description": "Soil moisture and temperature probe",
                "device_type": "soil_probe",
                "connectivity": "lora",
                "protocol": "json",
                "status": "warning",
                "battery_level": 15,
                "signal_strength": 75,
                "firmware_version": "v1.8.2",
                "last_seen": now - timedelta(minutes=30),
                "location_description": "Field A - Block B Center",
                "elevation": 14.0,
                "environment_id": "env-kharif-2025-field-b",
                "manufacturer": "SoilTech",
                "model": "SP-200",
                "serial_number": "SP2024002",
            },
            {
                "device_db_id": "DEV-PS-001",
                "name": "Plant Sensor Greenhouse 1",
                "description": "Canopy temperature and leaf wetness sensor",
                "device_type": "plant_sensor",
                "connectivity": "wifi",
                "protocol": "mqtt",
                "status": "online",
                "battery_level": 90,
                "signal_strength": 95,
                "firmware_version": "v3.0.1",
                "last_seen": now,
                "location_description": "Greenhouse 1 - Center",
                "elevation": 16.0,
                "environment_id": "env-rabi-2025-greenhouse",
                "manufacturer": "PlantVision",
                "model": "PV-100",
                "serial_number": "PV2024001",
            },
            {
                "device_db_id": "DEV-WL-001",
                "name": "Water Level Sensor Tank 1",
                "description": "Water tank level and flow monitoring",
                "device_type": "water_sensor",
                "connectivity": "mqtt",
                "protocol": "json",
                "status": "online",
                "battery_level": 95,
                "signal_strength": 98,
                "firmware_version": "v1.2.0",
                "last_seen": now,
                "location_description": "Irrigation Tank 1",
                "elevation": 12.0,
                "manufacturer": "AquaMonitor",
                "model": "WL-50",
                "serial_number": "WL2024001",
            },
        ]

        device_map = {}  # Map device_db_id to database id
        for data in devices_data:
            existing = self.db.query(IoTDevice).filter(
                IoTDevice.device_db_id == data["device_db_id"]
            ).first()
            if not existing:
                device = IoTDevice(organization_id=org_id, **data)
                self.db.add(device)
                self.db.flush()
                device_map[data["device_db_id"]] = device.id
                count += 1
            else:
                device_map[data["device_db_id"]] = existing.id

        self.db.commit()

        # ===========================================
        # Seed IoT Sensors
        # ===========================================
        sensors_data = [
            # Weather Station sensors
            {"sensor_db_id": "SEN-001-TEMP", "device_db_id": "DEV-WS-001", "sensor_type": "air_temperature", "name": "Air Temperature", "unit": "°C", "accuracy": "±0.5°C", "min_value": -40, "max_value": 60},
            {"sensor_db_id": "SEN-001-HUM", "device_db_id": "DEV-WS-001", "sensor_type": "relative_humidity", "name": "Relative Humidity", "unit": "%", "accuracy": "±3%", "min_value": 0, "max_value": 100},
            {"sensor_db_id": "SEN-001-PRES", "device_db_id": "DEV-WS-001", "sensor_type": "atmospheric_pressure", "name": "Atmospheric Pressure", "unit": "hPa", "accuracy": "±1 hPa", "min_value": 800, "max_value": 1200},
            {"sensor_db_id": "SEN-001-WIND", "device_db_id": "DEV-WS-001", "sensor_type": "wind_speed", "name": "Wind Speed", "unit": "km/h", "accuracy": "±5%", "min_value": 0, "max_value": 200},
            {"sensor_db_id": "SEN-001-RAIN", "device_db_id": "DEV-WS-001", "sensor_type": "rainfall", "name": "Rainfall", "unit": "mm", "accuracy": "±0.2mm", "min_value": 0, "max_value": 500},
            # Soil Probe A sensors
            {"sensor_db_id": "SEN-002-SM", "device_db_id": "DEV-SP-001", "sensor_type": "soil_moisture", "name": "Soil Moisture", "unit": "%", "accuracy": "±2%", "min_value": 0, "max_value": 100},
            {"sensor_db_id": "SEN-002-ST", "device_db_id": "DEV-SP-001", "sensor_type": "soil_temperature", "name": "Soil Temperature", "unit": "°C", "accuracy": "±0.5°C", "min_value": -10, "max_value": 50},
            {"sensor_db_id": "SEN-002-EC", "device_db_id": "DEV-SP-001", "sensor_type": "electrical_conductivity", "name": "Electrical Conductivity", "unit": "dS/m", "accuracy": "±5%", "min_value": 0, "max_value": 20},
            {"sensor_db_id": "SEN-002-PH", "device_db_id": "DEV-SP-001", "sensor_type": "soil_ph", "name": "Soil pH", "unit": "pH", "accuracy": "±0.1", "min_value": 0, "max_value": 14},
            # Soil Probe B sensors
            {"sensor_db_id": "SEN-003-SM", "device_db_id": "DEV-SP-002", "sensor_type": "soil_moisture", "name": "Soil Moisture", "unit": "%", "accuracy": "±2%", "min_value": 0, "max_value": 100},
            {"sensor_db_id": "SEN-003-ST", "device_db_id": "DEV-SP-002", "sensor_type": "soil_temperature", "name": "Soil Temperature", "unit": "°C", "accuracy": "±0.5°C", "min_value": -10, "max_value": 50},
            # Plant Sensor
            {"sensor_db_id": "SEN-004-LW", "device_db_id": "DEV-PS-001", "sensor_type": "leaf_wetness", "name": "Leaf Wetness", "unit": "%", "accuracy": "±5%", "min_value": 0, "max_value": 100},
            {"sensor_db_id": "SEN-004-CT", "device_db_id": "DEV-PS-001", "sensor_type": "canopy_temperature", "name": "Canopy Temperature", "unit": "°C", "accuracy": "±1°C", "min_value": -10, "max_value": 60},
            {"sensor_db_id": "SEN-004-PAR", "device_db_id": "DEV-PS-001", "sensor_type": "par", "name": "PAR", "unit": "µmol/m²/s", "accuracy": "±5%", "min_value": 0, "max_value": 2500},
            # Water Sensor
            {"sensor_db_id": "SEN-005-WL", "device_db_id": "DEV-WL-001", "sensor_type": "water_level", "name": "Water Level", "unit": "%", "accuracy": "±1%", "min_value": 0, "max_value": 100},
            {"sensor_db_id": "SEN-005-WT", "device_db_id": "DEV-WL-001", "sensor_type": "water_temperature", "name": "Water Temperature", "unit": "°C", "accuracy": "±0.5°C", "min_value": 0, "max_value": 50},
            {"sensor_db_id": "SEN-005-FR", "device_db_id": "DEV-WL-001", "sensor_type": "flow_rate", "name": "Flow Rate", "unit": "L/min", "accuracy": "±2%", "min_value": 0, "max_value": 1000},
        ]

        sensor_map = {}  # Map sensor_db_id to database id
        for data in sensors_data:
            device_id = device_map.get(data.pop("device_db_id"))
            if not device_id:
                continue

            existing = self.db.query(IoTSensor).filter(
                IoTSensor.sensor_db_id == data["sensor_db_id"],
                IoTSensor.device_id == device_id
            ).first()
            if not existing:
                sensor = IoTSensor(device_id=device_id, **data)
                self.db.add(sensor)
                self.db.flush()
                sensor_map[data["sensor_db_id"]] = sensor.id
                count += 1
            else:
                sensor_map[data["sensor_db_id"]] = existing.id

        self.db.commit()

        # ===========================================
        # Seed Alert Rules
        # ===========================================
        rules_data = [
            {
                "rule_db_id": f"RULE-{uuid.uuid4().hex[:8].upper()}",
                "name": "High Temperature Alert",
                "description": "Alert when air temperature exceeds 35°C",
                "sensor_type": "air_temperature",
                "condition": "above",
                "threshold": 35.0,
                "threshold_unit": "°C",
                "duration_minutes": 30,
                "cooldown_minutes": 60,
                "severity": "warning",
                "enabled": True,
            },
            {
                "rule_db_id": f"RULE-{uuid.uuid4().hex[:8].upper()}",
                "name": "Low Soil Moisture Alert",
                "description": "Alert when soil moisture drops below 30%",
                "sensor_type": "soil_moisture",
                "condition": "below",
                "threshold": 30.0,
                "threshold_unit": "%",
                "duration_minutes": 60,
                "cooldown_minutes": 120,
                "severity": "warning",
                "enabled": True,
            },
            {
                "rule_db_id": f"RULE-{uuid.uuid4().hex[:8].upper()}",
                "name": "Critical Temperature Alert",
                "description": "Alert when air temperature exceeds 40°C",
                "sensor_type": "air_temperature",
                "condition": "above",
                "threshold": 40.0,
                "threshold_unit": "°C",
                "duration_minutes": 15,
                "cooldown_minutes": 30,
                "severity": "critical",
                "enabled": True,
            },
            {
                "rule_db_id": f"RULE-{uuid.uuid4().hex[:8].upper()}",
                "name": "Frost Warning",
                "description": "Alert when temperature drops below 2°C",
                "sensor_type": "air_temperature",
                "condition": "below",
                "threshold": 2.0,
                "threshold_unit": "°C",
                "duration_minutes": 15,
                "cooldown_minutes": 60,
                "severity": "critical",
                "enabled": True,
            },
        ]

        for data in rules_data:
            existing = self.db.query(IoTAlertRule).filter(
                IoTAlertRule.name == data["name"],
                IoTAlertRule.organization_id == org_id
            ).first()
            if not existing:
                rule = IoTAlertRule(organization_id=org_id, **data)
                self.db.add(rule)
                count += 1

        self.db.commit()

        # ===========================================
        # Seed Alert Events
        # ===========================================
        events_data = [
            {
                "event_db_id": f"ALERT-{uuid.uuid4().hex[:8].upper()}",
                "alert_type": "battery_low",
                "severity": "warning",
                "message": "Low battery warning on Soil Probe Block B (15%)",
                "device_id": device_map.get("DEV-SP-002"),
                "trigger_value": 15,
                "start_time": now - timedelta(hours=2),
                "status": "active",
                "acknowledged": False,
            },
            {
                "event_db_id": f"ALERT-{uuid.uuid4().hex[:8].upper()}",
                "alert_type": "threshold",
                "severity": "critical",
                "message": "High temperature alert: 38.5°C exceeds threshold of 35°C",
                "device_id": device_map.get("DEV-WS-001"),
                "sensor_id": sensor_map.get("SEN-001-TEMP"),
                "trigger_value": 38.5,
                "trigger_threshold": 35.0,
                "trigger_condition": "above",
                "start_time": now - timedelta(hours=5),
                "end_time": now - timedelta(hours=3),
                "duration_seconds": 7200,
                "status": "resolved",
                "acknowledged": True,
                "acknowledged_by": "demo@bijmantra.org",
                "acknowledged_at": now - timedelta(hours=4),
            },
            {
                "event_db_id": f"ALERT-{uuid.uuid4().hex[:8].upper()}",
                "alert_type": "threshold",
                "severity": "warning",
                "message": "Low soil moisture: 28% below threshold of 30%",
                "device_id": device_map.get("DEV-SP-001"),
                "sensor_id": sensor_map.get("SEN-002-SM"),
                "trigger_value": 28,
                "trigger_threshold": 30.0,
                "trigger_condition": "below",
                "start_time": now - timedelta(days=1),
                "end_time": now - timedelta(hours=18),
                "duration_seconds": 21600,
                "status": "resolved",
                "acknowledged": True,
                "acknowledged_by": "demo@bijmantra.org",
                "acknowledged_at": now - timedelta(hours=20),
            },
        ]

        for data in events_data:
            if data.get("device_id") is None:
                continue
            existing = self.db.query(IoTAlertEvent).filter(
                IoTAlertEvent.message == data["message"]
            ).first()
            if not existing:
                event = IoTAlertEvent(**data)
                self.db.add(event)
                count += 1

        self.db.commit()

        # ===========================================
        # Seed Aggregates (7 days of daily data)
        # ===========================================
        base_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        environment_ids = ["env-kharif-2025-field-a", "env-kharif-2025-field-b"]

        for env_id in environment_ids:
            for day_offset in range(7):
                date = base_date - timedelta(days=day_offset)
                date_str = date.strftime("%Y-%m-%d")

                # Temperature aggregates
                temp_mean = 25 + random.uniform(-3, 5)
                aggregates = [
                    {
                        "environment_db_id": env_id,
                        "parameter": "air_temperature_mean",
                        "parameter_category": "temperature",
                        "value": round(temp_mean, 1),
                        "unit": "°C",
                        "period": "daily",
                        "start_time": date,
                        "end_time": date + timedelta(days=1),
                        "min_value": round(temp_mean - 5, 1),
                        "max_value": round(temp_mean + 8, 1),
                        "sample_count": 288,
                        "quality_score": 0.98,
                    },
                    {
                        "environment_db_id": env_id,
                        "parameter": "growing_degree_days",
                        "parameter_category": "temperature",
                        "value": round(max(0, temp_mean - 10), 1),
                        "unit": "°C·day",
                        "period": "daily",
                        "start_time": date,
                        "end_time": date + timedelta(days=1),
                        "calculation_method": "gdd_single_sine",
                    },
                    {
                        "environment_db_id": env_id,
                        "parameter": "precipitation_total",
                        "parameter_category": "precipitation",
                        "value": round(random.choice([0, 0, 0, 0, 2.5, 5.0, 12.0, 25.0]), 1),
                        "unit": "mm",
                        "period": "daily",
                        "start_time": date,
                        "end_time": date + timedelta(days=1),
                    },
                    {
                        "environment_db_id": env_id,
                        "parameter": "soil_moisture_mean",
                        "parameter_category": "soil",
                        "value": round(40 + random.uniform(-10, 15), 1),
                        "unit": "%",
                        "period": "daily",
                        "start_time": date,
                        "end_time": date + timedelta(days=1),
                        "sample_count": 288,
                    },
                    {
                        "environment_db_id": env_id,
                        "parameter": "relative_humidity_mean",
                        "parameter_category": "humidity",
                        "value": round(65 + random.uniform(-15, 20), 1),
                        "unit": "%",
                        "period": "daily",
                        "start_time": date,
                        "end_time": date + timedelta(days=1),
                    },
                    {
                        "environment_db_id": env_id,
                        "parameter": "solar_radiation_total",
                        "parameter_category": "radiation",
                        "value": round(18 + random.uniform(-5, 7), 1),
                        "unit": "MJ/m²",
                        "period": "daily",
                        "start_time": date,
                        "end_time": date + timedelta(days=1),
                    },
                ]

                for agg_data in aggregates:
                    existing = self.db.query(IoTAggregate).filter(
                        IoTAggregate.environment_db_id == agg_data["environment_db_id"],
                        IoTAggregate.parameter == agg_data["parameter"],
                        IoTAggregate.start_time == agg_data["start_time"]
                    ).first()
                    if not existing:
                        agg = IoTAggregate(**agg_data)
                        self.db.add(agg)
                        count += 1

        self.db.commit()

        logger.info(f"Seeded {count} IoT records")
        return count

    def clear(self) -> int:
        """Clear demo IoT data"""
        from app.models.core import Organization

        count = 0
        demo_org = self.db.query(Organization).filter(
            Organization.name == settings.DEMO_ORG_NAME
        ).first()
        if not demo_org:
            return 0

        # Delete in reverse order of dependencies
        count += self.db.query(IoTAggregate).delete()
        count += self.db.query(IoTEnvironmentLink).delete()
        count += self.db.query(IoTAlertEvent).delete()
        count += self.db.query(IoTAlertRule).filter(
            IoTAlertRule.organization_id == demo_org.id
        ).delete()
        count += self.db.query(IoTTelemetry).delete()
        count += self.db.query(IoTSensor).delete()
        count += self.db.query(IoTDevice).filter(
            IoTDevice.organization_id == demo_org.id
        ).delete()

        self.db.commit()
        logger.info(f"Cleared {count} IoT records")
        return count
