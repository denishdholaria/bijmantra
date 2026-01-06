"""
Vault Sensor Integration Service

Links IoT sensors to Seed Bank vaults for environmental monitoring.
Tracks temperature, humidity, and other conditions critical for seed preservation.
"""

from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional
from uuid import uuid4
import random


def _utcnow() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(UTC)


class VaultSensorService:
    """Service for managing vault environmental sensors."""
    
    def __init__(self):
        self.vault_sensors: Dict[str, Dict] = {}
        self.readings: List[Dict] = []
        self.alerts: List[Dict] = []
        self.thresholds: Dict[str, Dict] = {}
        self._init_demo_data()
    
    def _init_demo_data(self):
        """Initialize demo vault sensors."""
        # Default thresholds for different vault types
        self.default_thresholds = {
            "base": {
                "temperature": {"min": -20, "max": -15, "unit": "°C"},
                "humidity": {"min": 3, "max": 7, "unit": "%"},
            },
            "active": {
                "temperature": {"min": 2, "max": 8, "unit": "°C"},
                "humidity": {"min": 20, "max": 40, "unit": "%"},
            },
            "cryo": {
                "temperature": {"min": -200, "max": -180, "unit": "°C"},
                "humidity": {"min": 0, "max": 5, "unit": "%"},
            },
        }
        
        # Demo vault sensors
        demo_sensors = [
            {
                "id": str(uuid4()),
                "sensor_id": "VS-001",
                "vault_id": "vault-base-1",
                "vault_name": "Base Collection Vault A",
                "vault_type": "base",
                "status": "online",
                "battery": 95,
                "signal": 98,
                "sensors": ["temperature", "humidity", "door_status", "power_status"],
                "current_readings": {
                    "temperature": -18.2,
                    "humidity": 5.1,
                    "door_status": "closed",
                    "power_status": "main",
                },
                "last_reading": _utcnow().isoformat(),
                "installed_date": "2024-01-15",
                "calibration_date": "2024-11-01",
                "alerts_enabled": True,
            },
            {
                "id": str(uuid4()),
                "sensor_id": "VS-002",
                "vault_id": "vault-base-2",
                "vault_name": "Base Collection Vault B",
                "vault_type": "base",
                "status": "online",
                "battery": 88,
                "signal": 95,
                "sensors": ["temperature", "humidity", "door_status", "power_status"],
                "current_readings": {
                    "temperature": -17.8,
                    "humidity": 4.8,
                    "door_status": "closed",
                    "power_status": "main",
                },
                "last_reading": _utcnow().isoformat(),
                "installed_date": "2024-01-15",
                "calibration_date": "2024-11-01",
                "alerts_enabled": True,
            },
            {
                "id": str(uuid4()),
                "sensor_id": "VS-003",
                "vault_id": "vault-active-1",
                "vault_name": "Active Collection Room",
                "vault_type": "active",
                "status": "warning",
                "battery": 72,
                "signal": 85,
                "sensors": ["temperature", "humidity", "door_status"],
                "current_readings": {
                    "temperature": 6.5,
                    "humidity": 35.2,
                    "door_status": "closed",
                },
                "last_reading": _utcnow().isoformat(),
                "installed_date": "2024-03-10",
                "calibration_date": "2024-10-15",
                "alerts_enabled": True,
            },
            {
                "id": str(uuid4()),
                "sensor_id": "VS-004",
                "vault_id": "vault-cryo-1",
                "vault_name": "Cryopreservation Unit",
                "vault_type": "cryo",
                "status": "online",
                "battery": 100,
                "signal": 99,
                "sensors": ["temperature", "humidity", "nitrogen_level", "power_status"],
                "current_readings": {
                    "temperature": -196.0,
                    "humidity": 2.1,
                    "nitrogen_level": 85,
                    "power_status": "main",
                },
                "last_reading": _utcnow().isoformat(),
                "installed_date": "2024-02-20",
                "calibration_date": "2024-11-10",
                "alerts_enabled": True,
            },
        ]
        
        for sensor in demo_sensors:
            self.vault_sensors[sensor["id"]] = sensor
            self.thresholds[sensor["vault_id"]] = self.default_thresholds.get(
                sensor["vault_type"], self.default_thresholds["active"]
            )
        
        # Generate historical readings
        self._generate_historical_readings()
        
        # Generate some demo alerts
        self._generate_demo_alerts()
    
    def _generate_historical_readings(self):
        """Generate 24 hours of historical readings."""
        now = _utcnow()
        
        for sensor in self.vault_sensors.values():
            vault_type = sensor["vault_type"]
            thresholds = self.default_thresholds.get(vault_type, self.default_thresholds["active"])
            
            # Generate readings every 15 minutes for 24 hours
            for i in range(96):  # 96 readings = 24 hours
                timestamp = now - timedelta(minutes=15 * i)
                
                # Temperature reading with slight variation
                temp_base = (thresholds["temperature"]["min"] + thresholds["temperature"]["max"]) / 2
                temp_variance = (thresholds["temperature"]["max"] - thresholds["temperature"]["min"]) / 4
                temp_value = temp_base + (random.random() - 0.5) * temp_variance
                
                self.readings.append({
                    "id": str(uuid4()),
                    "sensor_id": sensor["id"],
                    "vault_id": sensor["vault_id"],
                    "sensor_type": "temperature",
                    "value": round(temp_value, 1),
                    "unit": "°C",
                    "timestamp": timestamp.isoformat(),
                })
                
                # Humidity reading
                hum_base = (thresholds["humidity"]["min"] + thresholds["humidity"]["max"]) / 2
                hum_variance = (thresholds["humidity"]["max"] - thresholds["humidity"]["min"]) / 4
                hum_value = hum_base + (random.random() - 0.5) * hum_variance
                
                self.readings.append({
                    "id": str(uuid4()),
                    "sensor_id": sensor["id"],
                    "vault_id": sensor["vault_id"],
                    "sensor_type": "humidity",
                    "value": round(hum_value, 1),
                    "unit": "%",
                    "timestamp": timestamp.isoformat(),
                })
    
    def _generate_demo_alerts(self):
        """Generate some demo alerts."""
        demo_alerts = [
            {
                "id": str(uuid4()),
                "vault_id": "vault-active-1",
                "vault_name": "Active Collection Room",
                "sensor_type": "temperature",
                "severity": "warning",
                "message": "Temperature approaching upper threshold",
                "value": 7.8,
                "threshold": 8.0,
                "condition": "approaching_max",
                "timestamp": (_utcnow() - timedelta(hours=2)).isoformat(),
                "acknowledged": False,
            },
            {
                "id": str(uuid4()),
                "vault_id": "vault-base-1",
                "vault_name": "Base Collection Vault A",
                "sensor_type": "door_status",
                "severity": "info",
                "message": "Door opened for scheduled access",
                "value": "open",
                "threshold": None,
                "condition": "door_opened",
                "timestamp": (_utcnow() - timedelta(hours=6)).isoformat(),
                "acknowledged": True,
                "acknowledged_by": "admin",
                "acknowledged_at": (_utcnow() - timedelta(hours=5, minutes=45)).isoformat(),
            },
            {
                "id": str(uuid4()),
                "vault_id": "vault-cryo-1",
                "vault_name": "Cryopreservation Unit",
                "sensor_type": "nitrogen_level",
                "severity": "warning",
                "message": "Nitrogen level below 90%",
                "value": 85,
                "threshold": 90,
                "condition": "below_threshold",
                "timestamp": (_utcnow() - timedelta(hours=1)).isoformat(),
                "acknowledged": False,
            },
        ]
        
        self.alerts = demo_alerts
    
    # Vault-Sensor Linking
    def link_sensor_to_vault(
        self,
        vault_id: str,
        vault_name: str,
        vault_type: str,
        sensor_id: str,
        sensors: List[str],
    ) -> Dict:
        """Link a sensor device to a vault."""
        sensor_record = {
            "id": str(uuid4()),
            "sensor_id": sensor_id,
            "vault_id": vault_id,
            "vault_name": vault_name,
            "vault_type": vault_type,
            "status": "online",
            "battery": 100,
            "signal": 100,
            "sensors": sensors,
            "current_readings": {},
            "last_reading": None,
            "installed_date": _utcnow().strftime("%Y-%m-%d"),
            "calibration_date": None,
            "alerts_enabled": True,
        }
        
        self.vault_sensors[sensor_record["id"]] = sensor_record
        self.thresholds[vault_id] = self.default_thresholds.get(
            vault_type, self.default_thresholds["active"]
        )
        
        return sensor_record
    
    def unlink_sensor(self, sensor_id: str) -> bool:
        """Remove sensor from vault."""
        for key, sensor in list(self.vault_sensors.items()):
            if sensor["sensor_id"] == sensor_id:
                del self.vault_sensors[key]
                return True
        return False
    
    def get_vault_sensors(self, vault_id: Optional[str] = None) -> List[Dict]:
        """Get all sensors or sensors for a specific vault."""
        sensors = list(self.vault_sensors.values())
        
        if vault_id:
            sensors = [s for s in sensors if s["vault_id"] == vault_id]
        
        return sensors
    
    def get_sensor_by_id(self, sensor_id: str) -> Optional[Dict]:
        """Get sensor by its ID."""
        return self.vault_sensors.get(sensor_id)
    
    # Readings
    def record_reading(
        self,
        sensor_id: str,
        sensor_type: str,
        value: float,
        unit: str,
    ) -> Optional[Dict]:
        """Record a new sensor reading."""
        sensor = self.vault_sensors.get(sensor_id)
        if not sensor:
            return None
        
        reading = {
            "id": str(uuid4()),
            "sensor_id": sensor_id,
            "vault_id": sensor["vault_id"],
            "sensor_type": sensor_type,
            "value": value,
            "unit": unit,
            "timestamp": _utcnow().isoformat(),
        }
        
        self.readings.append(reading)
        
        # Update current readings
        sensor["current_readings"][sensor_type] = value
        sensor["last_reading"] = reading["timestamp"]
        sensor["status"] = "online"
        
        # Check thresholds
        self._check_thresholds(sensor, sensor_type, value)
        
        return reading
    
    def get_sensor_readings(
        self,
        sensor_id: Optional[str] = None,
        vault_id: Optional[str] = None,
        sensor_type: Optional[str] = None,
        hours: int = 24,
        limit: int = 500,
    ) -> List[Dict]:
        """Get sensor readings with filters."""
        cutoff = _utcnow() - timedelta(hours=hours)
        cutoff_str = cutoff.isoformat()
        
        readings = [r for r in self.readings if r["timestamp"] >= cutoff_str]
        
        if sensor_id:
            readings = [r for r in readings if r["sensor_id"] == sensor_id]
        if vault_id:
            readings = [r for r in readings if r["vault_id"] == vault_id]
        if sensor_type:
            readings = [r for r in readings if r["sensor_type"] == sensor_type]
        
        readings.sort(key=lambda x: x["timestamp"], reverse=True)
        return readings[:limit]
    
    def get_vault_conditions(self, vault_id: str) -> Optional[Dict]:
        """Get current conditions for a vault."""
        sensors = [s for s in self.vault_sensors.values() if s["vault_id"] == vault_id]
        
        if not sensors:
            return None
        
        sensor = sensors[0]
        thresholds = self.thresholds.get(vault_id, {})
        
        conditions = {
            "vault_id": vault_id,
            "vault_name": sensor["vault_name"],
            "vault_type": sensor["vault_type"],
            "sensor_status": sensor["status"],
            "last_reading": sensor["last_reading"],
            "current_readings": sensor["current_readings"],
            "thresholds": thresholds,
            "status": "normal",
            "alerts_count": len([a for a in self.alerts if a["vault_id"] == vault_id and not a.get("acknowledged", False)]),
        }
        
        # Check if any readings are out of range
        for sensor_type, value in sensor["current_readings"].items():
            if sensor_type in thresholds:
                thresh = thresholds[sensor_type]
                if value < thresh["min"] or value > thresh["max"]:
                    conditions["status"] = "critical"
                    break
                elif value < thresh["min"] * 1.1 or value > thresh["max"] * 0.9:
                    conditions["status"] = "warning"
        
        return conditions
    
    def get_all_vault_conditions(self) -> List[Dict]:
        """Get conditions for all vaults."""
        vault_ids = set(s["vault_id"] for s in self.vault_sensors.values())
        return [self.get_vault_conditions(vid) for vid in vault_ids if self.get_vault_conditions(vid)]
    
    # Threshold Management
    def _check_thresholds(self, sensor: Dict, sensor_type: str, value: float):
        """Check if reading exceeds thresholds and create alert if needed."""
        vault_id = sensor["vault_id"]
        thresholds = self.thresholds.get(vault_id, {})
        
        if sensor_type not in thresholds:
            return
        
        thresh = thresholds[sensor_type]
        
        # Check critical thresholds
        if value < thresh["min"]:
            self._create_alert(
                sensor, sensor_type, value, thresh["min"],
                "below_threshold", "critical",
                f"{sensor_type.title()} below minimum threshold"
            )
        elif value > thresh["max"]:
            self._create_alert(
                sensor, sensor_type, value, thresh["max"],
                "above_threshold", "critical",
                f"{sensor_type.title()} above maximum threshold"
            )
        # Check warning thresholds (within 10% of limits)
        elif value < thresh["min"] * 1.1:
            self._create_alert(
                sensor, sensor_type, value, thresh["min"],
                "approaching_min", "warning",
                f"{sensor_type.title()} approaching minimum threshold"
            )
        elif value > thresh["max"] * 0.9:
            self._create_alert(
                sensor, sensor_type, value, thresh["max"],
                "approaching_max", "warning",
                f"{sensor_type.title()} approaching maximum threshold"
            )
    
    def _create_alert(
        self,
        sensor: Dict,
        sensor_type: str,
        value: float,
        threshold: float,
        condition: str,
        severity: str,
        message: str,
    ):
        """Create a new alert."""
        alert = {
            "id": str(uuid4()),
            "vault_id": sensor["vault_id"],
            "vault_name": sensor["vault_name"],
            "sensor_id": sensor["id"],
            "sensor_type": sensor_type,
            "severity": severity,
            "message": message,
            "value": value,
            "threshold": threshold,
            "condition": condition,
            "timestamp": _utcnow().isoformat(),
            "acknowledged": False,
        }
        self.alerts.append(alert)
    
    def set_thresholds(
        self,
        vault_id: str,
        sensor_type: str,
        min_value: float,
        max_value: float,
        unit: str,
    ) -> Dict:
        """Set custom thresholds for a vault."""
        if vault_id not in self.thresholds:
            self.thresholds[vault_id] = {}
        
        self.thresholds[vault_id][sensor_type] = {
            "min": min_value,
            "max": max_value,
            "unit": unit,
        }
        
        return self.thresholds[vault_id]
    
    def get_thresholds(self, vault_id: str) -> Dict:
        """Get thresholds for a vault."""
        return self.thresholds.get(vault_id, {})
    
    # Alert Management
    def get_alerts(
        self,
        vault_id: Optional[str] = None,
        severity: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """Get alerts with filters."""
        alerts = self.alerts.copy()
        
        if vault_id:
            alerts = [a for a in alerts if a["vault_id"] == vault_id]
        if severity:
            alerts = [a for a in alerts if a["severity"] == severity]
        if acknowledged is not None:
            alerts = [a for a in alerts if a.get("acknowledged", False) == acknowledged]
        
        alerts.sort(key=lambda x: x["timestamp"], reverse=True)
        return alerts[:limit]
    
    def acknowledge_alert(self, alert_id: str, user: str) -> Optional[Dict]:
        """Acknowledge an alert."""
        for alert in self.alerts:
            if alert["id"] == alert_id:
                alert["acknowledged"] = True
                alert["acknowledged_by"] = user
                alert["acknowledged_at"] = _utcnow().isoformat()
                return alert
        return None
    
    def get_alert_by_id(self, alert_id: str) -> Optional[Dict]:
        """Get alert by ID."""
        for alert in self.alerts:
            if alert["id"] == alert_id:
                return alert
        return None
    
    # Statistics
    def get_statistics(self) -> Dict:
        """Get vault sensor statistics."""
        sensors = list(self.vault_sensors.values())
        
        return {
            "total_sensors": len(sensors),
            "online": len([s for s in sensors if s["status"] == "online"]),
            "warning": len([s for s in sensors if s["status"] == "warning"]),
            "offline": len([s for s in sensors if s["status"] == "offline"]),
            "by_vault_type": {
                "base": len([s for s in sensors if s["vault_type"] == "base"]),
                "active": len([s for s in sensors if s["vault_type"] == "active"]),
                "cryo": len([s for s in sensors if s["vault_type"] == "cryo"]),
            },
            "total_readings_24h": len([r for r in self.readings if r["timestamp"] >= (_utcnow() - timedelta(hours=24)).isoformat()]),
            "active_alerts": len([a for a in self.alerts if not a.get("acknowledged", False)]),
            "critical_alerts": len([a for a in self.alerts if a["severity"] == "critical" and not a.get("acknowledged", False)]),
        }
    
    def get_vault_types(self) -> List[Dict]:
        """Get available vault types with their default thresholds."""
        return [
            {
                "value": "base",
                "label": "Base Collection",
                "description": "Long-term storage at -18°C to -20°C",
                "thresholds": self.default_thresholds["base"],
            },
            {
                "value": "active",
                "label": "Active Collection",
                "description": "Working collection at 2°C to 8°C",
                "thresholds": self.default_thresholds["active"],
            },
            {
                "value": "cryo",
                "label": "Cryopreservation",
                "description": "Ultra-cold storage in liquid nitrogen",
                "thresholds": self.default_thresholds["cryo"],
            },
        ]


# Global service instance
vault_sensor_service = VaultSensorService()