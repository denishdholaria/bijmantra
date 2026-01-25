"""
Sensor Network Service

IoT device management, sensor data collection, and alert handling.
"""

from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional, Any
from uuid import uuid4
import random


def _utcnow() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(UTC)


class SensorNetworkService:
    """Service for managing IoT sensor networks."""
    
    def __init__(self):
        self.devices: Dict[str, Dict] = {}
        self.readings: List[Dict] = []
        self.alert_rules: Dict[str, Dict] = {}
        self.alert_events: List[Dict] = []
        self._init_demo_data()
    
    def _init_demo_data(self):
        """Initialize demo devices and data."""
        # Demo devices
        demo_devices = [
            {
                "id": "DEV-001",
                "name": "Weather Station Alpha",
                "type": "weather",
                "status": "online",
                "battery": 85,
                "signal": 92,
                "location": "Field A - North",
                "field_id": "field-1",
                "firmware": "v2.1.0",
                "sensors": ["temperature", "humidity", "pressure", "wind_speed", "rain"],
                "last_seen": _utcnow().isoformat(),
            },
            {
                "id": "DEV-002",
                "name": "Soil Probe B1",
                "type": "soil",
                "status": "online",
                "battery": 72,
                "signal": 78,
                "location": "Field B - Block 1",
                "field_id": "field-2",
                "firmware": "v1.8.2",
                "sensors": ["soil_moisture", "soil_temp", "ec", "ph"],
                "last_seen": _utcnow().isoformat(),
            },
            {
                "id": "DEV-003",
                "name": "Soil Probe B2",
                "type": "soil",
                "status": "warning",
                "battery": 15,
                "signal": 65,
                "location": "Field B - Block 2",
                "field_id": "field-2",
                "firmware": "v1.8.2",
                "sensors": ["soil_moisture", "soil_temp", "ec"],
                "last_seen": (_utcnow() - timedelta(minutes=10)).isoformat(),
            },
            {
                "id": "DEV-004",
                "name": "Plant Sensor P1",
                "type": "plant",
                "status": "online",
                "battery": 90,
                "signal": 88,
                "location": "Greenhouse 1",
                "firmware": "v3.0.1",
                "sensors": ["leaf_wetness", "canopy_temp", "par"],
                "last_seen": _utcnow().isoformat(),
            },
            {
                "id": "DEV-005",
                "name": "Water Level Sensor",
                "type": "water",
                "status": "online",
                "battery": 95,
                "signal": 90,
                "location": "Irrigation Tank",
                "firmware": "v1.2.0",
                "sensors": ["water_level", "water_temp", "flow_rate"],
                "last_seen": _utcnow().isoformat(),
            },
            {
                "id": "GW-001",
                "name": "LoRa Gateway Main",
                "type": "gateway",
                "status": "online",
                "battery": 100,
                "signal": 100,
                "location": "Central Building",
                "firmware": "v4.2.0",
                "sensors": [],
                "last_seen": _utcnow().isoformat(),
            },
        ]
        
        for device in demo_devices:
            self.devices[device["id"]] = device
        
        # Demo alert rules
        demo_rules = [
            {
                "id": "rule-1",
                "name": "High Temperature Alert",
                "sensor": "temperature",
                "condition": "above",
                "threshold": 35,
                "unit": "°C",
                "severity": "critical",
                "enabled": True,
                "notify_email": True,
                "notify_sms": True,
                "notify_push": True,
            },
            {
                "id": "rule-2",
                "name": "Low Soil Moisture",
                "sensor": "soil_moisture",
                "condition": "below",
                "threshold": 30,
                "unit": "%",
                "severity": "warning",
                "enabled": True,
                "notify_email": True,
                "notify_sms": False,
                "notify_push": True,
            },
            {
                "id": "rule-3",
                "name": "Frost Warning",
                "sensor": "temperature",
                "condition": "below",
                "threshold": 2,
                "unit": "°C",
                "severity": "critical",
                "enabled": True,
                "notify_email": True,
                "notify_sms": True,
                "notify_push": True,
            },
        ]
        
        for rule in demo_rules:
            self.alert_rules[rule["id"]] = rule
    
    # Device Management
    def register_device(
        self,
        device_id: str,
        name: str,
        device_type: str,
        location: str,
        sensors: List[str],
        field_id: Optional[str] = None,
    ) -> Dict:
        """Register a new sensor device."""
        device = {
            "id": device_id,
            "name": name,
            "type": device_type,
            "status": "offline",
            "battery": 100,
            "signal": 0,
            "location": location,
            "field_id": field_id,
            "firmware": "unknown",
            "sensors": sensors,
            "last_seen": None,
            "registered_at": _utcnow().isoformat(),
        }
        self.devices[device_id] = device
        return device
    
    def get_device(self, device_id: str) -> Optional[Dict]:
        """Get device by ID."""
        return self.devices.get(device_id)
    
    def list_devices(
        self,
        device_type: Optional[str] = None,
        status: Optional[str] = None,
        field_id: Optional[str] = None,
    ) -> List[Dict]:
        """List all devices with optional filters."""
        devices = list(self.devices.values())
        
        if device_type:
            devices = [d for d in devices if d["type"] == device_type]
        if status:
            devices = [d for d in devices if d["status"] == status]
        if field_id:
            devices = [d for d in devices if d.get("field_id") == field_id]
        
        return devices
    
    def update_device_status(
        self,
        device_id: str,
        status: str,
        battery: Optional[int] = None,
        signal: Optional[int] = None,
    ) -> Optional[Dict]:
        """Update device status."""
        device = self.devices.get(device_id)
        if not device:
            return None
        
        device["status"] = status
        device["last_seen"] = _utcnow().isoformat()
        
        if battery is not None:
            device["battery"] = battery
        if signal is not None:
            device["signal"] = signal
        
        return device
    
    def delete_device(self, device_id: str) -> bool:
        """Remove a device."""
        if device_id in self.devices:
            del self.devices[device_id]
            return True
        return False
    
    # Sensor Readings
    def record_reading(
        self,
        device_id: str,
        sensor: str,
        value: float,
        unit: str,
        timestamp: Optional[str] = None,
    ) -> Dict:
        """Record a sensor reading."""
        reading = {
            "id": str(uuid4()),
            "device_id": device_id,
            "sensor": sensor,
            "value": value,
            "unit": unit,
            "timestamp": timestamp or _utcnow().isoformat(),
        }
        self.readings.append(reading)
        
        # Update device last seen
        if device_id in self.devices:
            self.devices[device_id]["last_seen"] = reading["timestamp"]
            self.devices[device_id]["status"] = "online"
        
        # Check alert rules
        self._check_alerts(device_id, sensor, value)
        
        return reading
    
    def get_readings(
        self,
        device_id: Optional[str] = None,
        sensor: Optional[str] = None,
        since: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """Get sensor readings with filters."""
        readings = self.readings.copy()
        
        if device_id:
            readings = [r for r in readings if r["device_id"] == device_id]
        if sensor:
            readings = [r for r in readings if r["sensor"] == sensor]
        if since:
            readings = [r for r in readings if r["timestamp"] >= since]
        
        # Sort by timestamp descending
        readings.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return readings[:limit]
    
    def get_latest_readings(self, device_id: str) -> Dict[str, Dict]:
        """Get latest reading for each sensor on a device."""
        device = self.devices.get(device_id)
        if not device:
            return {}
        
        latest = {}
        for sensor in device.get("sensors", []):
            readings = [r for r in self.readings if r["device_id"] == device_id and r["sensor"] == sensor]
            if readings:
                readings.sort(key=lambda x: x["timestamp"], reverse=True)
                latest[sensor] = readings[0]
        
        return latest
    
    def generate_live_readings(self) -> List[Dict]:
        """Generate simulated live readings for demo."""
        readings = []
        
        sensor_configs = {
            "temperature": {"base": 24, "variance": 2, "unit": "°C"},
            "humidity": {"base": 65, "variance": 10, "unit": "%"},
            "pressure": {"base": 1013, "variance": 5, "unit": "hPa"},
            "wind_speed": {"base": 12, "variance": 8, "unit": "km/h"},
            "soil_moisture": {"base": 42, "variance": 5, "unit": "%"},
            "soil_temp": {"base": 18, "variance": 2, "unit": "°C"},
            "ec": {"base": 1.2, "variance": 0.3, "unit": "dS/m"},
            "ph": {"base": 6.5, "variance": 0.5, "unit": ""},
            "leaf_wetness": {"base": 50, "variance": 50, "unit": "%"},
            "par": {"base": 800, "variance": 400, "unit": "µmol/m²/s"},
            "water_level": {"base": 75, "variance": 5, "unit": "%"},
            "flow_rate": {"base": 2.5, "variance": 1.5, "unit": "L/min"},
        }
        
        for device_id, device in self.devices.items():
            if device["status"] == "offline":
                continue
            
            for sensor in device.get("sensors", []):
                config = sensor_configs.get(sensor, {"base": 50, "variance": 10, "unit": ""})
                value = config["base"] + (random.random() - 0.5) * 2 * config["variance"]
                
                readings.append({
                    "id": str(uuid4()),
                    "device_id": device_id,
                    "device_name": device["name"],
                    "sensor": sensor,
                    "value": round(value, 2),
                    "unit": config["unit"],
                    "timestamp": _utcnow().isoformat(),
                    "trend": random.choice(["up", "down", "stable"]),
                })
        
        return readings
    
    # Alert Management
    def create_alert_rule(
        self,
        name: str,
        sensor: str,
        condition: str,
        threshold: float,
        unit: str,
        severity: str = "warning",
        notify_email: bool = True,
        notify_sms: bool = False,
        notify_push: bool = True,
    ) -> Dict:
        """Create a new alert rule."""
        rule_id = f"rule-{uuid4().hex[:8]}"
        rule = {
            "id": rule_id,
            "name": name,
            "sensor": sensor,
            "condition": condition,
            "threshold": threshold,
            "unit": unit,
            "severity": severity,
            "enabled": True,
            "notify_email": notify_email,
            "notify_sms": notify_sms,
            "notify_push": notify_push,
            "created_at": _utcnow().isoformat(),
        }
        self.alert_rules[rule_id] = rule
        return rule
    
    def list_alert_rules(self, enabled_only: bool = False) -> List[Dict]:
        """List all alert rules."""
        rules = list(self.alert_rules.values())
        if enabled_only:
            rules = [r for r in rules if r.get("enabled", True)]
        return rules
    
    def update_alert_rule(self, rule_id: str, updates: Dict) -> Optional[Dict]:
        """Update an alert rule."""
        rule = self.alert_rules.get(rule_id)
        if not rule:
            return None
        
        rule.update(updates)
        return rule
    
    def delete_alert_rule(self, rule_id: str) -> bool:
        """Delete an alert rule."""
        if rule_id in self.alert_rules:
            del self.alert_rules[rule_id]
            return True
        return False
    
    def _check_alerts(self, device_id: str, sensor: str, value: float):
        """Check if a reading triggers any alerts."""
        device = self.devices.get(device_id)
        if not device:
            return
        
        for rule in self.alert_rules.values():
            if not rule.get("enabled", True):
                continue
            if rule["sensor"] != sensor:
                continue
            
            triggered = False
            if rule["condition"] == "above" and value > rule["threshold"]:
                triggered = True
            elif rule["condition"] == "below" and value < rule["threshold"]:
                triggered = True
            elif rule["condition"] == "equals" and abs(value - rule["threshold"]) < 0.01:
                triggered = True
            
            if triggered:
                self._create_alert_event(rule, device, sensor, value)
    
    def _create_alert_event(self, rule: Dict, device: Dict, sensor: str, value: float):
        """Create an alert event."""
        event = {
            "id": f"event-{uuid4().hex[:8]}",
            "rule_id": rule["id"],
            "rule_name": rule["name"],
            "device_id": device["id"],
            "device_name": device["name"],
            "sensor": sensor,
            "value": value,
            "threshold": rule["threshold"],
            "condition": rule["condition"],
            "severity": rule["severity"],
            "timestamp": _utcnow().isoformat(),
            "acknowledged": False,
        }
        self.alert_events.append(event)
    
    def list_alert_events(
        self,
        acknowledged: Optional[bool] = None,
        severity: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """List alert events."""
        events = self.alert_events.copy()
        
        if acknowledged is not None:
            events = [e for e in events if e["acknowledged"] == acknowledged]
        if severity:
            events = [e for e in events if e["severity"] == severity]
        
        events.sort(key=lambda x: x["timestamp"], reverse=True)
        return events[:limit]
    
    def acknowledge_alert(self, event_id: str, user: str) -> Optional[Dict]:
        """Acknowledge an alert event."""
        for event in self.alert_events:
            if event["id"] == event_id:
                event["acknowledged"] = True
                event["acknowledged_by"] = user
                event["acknowledged_at"] = _utcnow().isoformat()
                return event
        return None
    
    # Statistics
    def get_network_stats(self) -> Dict:
        """Get overall network statistics."""
        devices = list(self.devices.values())
        
        return {
            "total_devices": len(devices),
            "online": len([d for d in devices if d["status"] == "online"]),
            "offline": len([d for d in devices if d["status"] == "offline"]),
            "warning": len([d for d in devices if d["status"] == "warning"]),
            "by_type": {
                "weather": len([d for d in devices if d["type"] == "weather"]),
                "soil": len([d for d in devices if d["type"] == "soil"]),
                "plant": len([d for d in devices if d["type"] == "plant"]),
                "water": len([d for d in devices if d["type"] == "water"]),
                "gateway": len([d for d in devices if d["type"] == "gateway"]),
            },
            "active_alerts": len([e for e in self.alert_events if not e["acknowledged"]]),
            "total_readings": len(self.readings),
            "alert_rules": len(self.alert_rules),
        }
    
    def get_device_types(self) -> List[Dict]:
        """Get available device types."""
        return [
            {"value": "weather", "label": "Weather Station", "icon": "🌤️"},
            {"value": "soil", "label": "Soil Sensor", "icon": "🌱"},
            {"value": "plant", "label": "Plant Sensor", "icon": "🌿"},
            {"value": "water", "label": "Water Sensor", "icon": "💧"},
            {"value": "gateway", "label": "Gateway", "icon": "📡"},
        ]
    
    def get_sensor_types(self) -> List[Dict]:
        """Get available sensor types."""
        return [
            {"value": "temperature", "label": "Temperature", "unit": "°C"},
            {"value": "humidity", "label": "Humidity", "unit": "%"},
            {"value": "pressure", "label": "Pressure", "unit": "hPa"},
            {"value": "wind_speed", "label": "Wind Speed", "unit": "km/h"},
            {"value": "soil_moisture", "label": "Soil Moisture", "unit": "%"},
            {"value": "soil_temp", "label": "Soil Temperature", "unit": "°C"},
            {"value": "ec", "label": "Electrical Conductivity", "unit": "dS/m"},
            {"value": "ph", "label": "pH Level", "unit": ""},
            {"value": "leaf_wetness", "label": "Leaf Wetness", "unit": "%"},
            {"value": "par", "label": "PAR (Light)", "unit": "µmol/m²/s"},
            {"value": "water_level", "label": "Water Level", "unit": "%"},
            {"value": "flow_rate", "label": "Flow Rate", "unit": "L/min"},
        ]


# Global service instance
sensor_network_service = SensorNetworkService()
