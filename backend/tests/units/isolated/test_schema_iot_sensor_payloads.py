"""
Isolated tests for IoT Sensor Payload Schemas
"""
import unittest
from datetime import datetime, timezone
from pydantic import ValidationError
from app.schemas.schema_iot_sensor_payloads import (
    GenericIngestionPayload,
    SensorReading,
    TTNUplinkPayload
)

class TestIoTSensorPayloads(unittest.TestCase):
    def test_sensor_reading_validation(self):
        """Test SensorReading validation."""
        # Valid
        reading = SensorReading(sensor_type="temp", value=25.5, unit="C")
        self.assertEqual(reading.sensor_type, "temp")
        self.assertEqual(reading.value, 25.5)

        # Invalid (missing value)
        with self.assertRaises(ValidationError):
            SensorReading(sensor_type="temp")

    def test_generic_payload_validation(self):
        """Test GenericIngestionPayload validation."""
        payload_data = {
            "device_id": "dev-123",
            "readings": [
                {"sensor_type": "temp", "value": 22.0},
                {"sensor_type": "humidity", "value": 60.0}
            ]
        }
        payload = GenericIngestionPayload(**payload_data)
        self.assertEqual(payload.device_id, "dev-123")
        self.assertEqual(len(payload.readings), 2)
        self.assertIsInstance(payload.timestamp, datetime)

        # Empty readings check
        with self.assertRaises(ValidationError) as cm:
            GenericIngestionPayload(device_id="dev-123", readings=[])
        self.assertIn("readings list cannot be empty", str(cm.exception))

    def test_ttn_uplink_payload(self):
        """Test TTNUplinkPayload validation."""
        ttn_json = {
            "end_device_ids": {
                "device_id": "eui-1234567890abcdef",
                "application_ids": {"application_id": "my-app"}
            },
            "correlation_ids": ["as:up:123"],
            "received_at": "2023-10-27T10:00:00Z",
            "uplink_message": {
                "f_port": 1,
                "f_cnt": 10,
                "frm_payload": "AwAAAA==",
                "received_at": "2023-10-27T10:00:00Z"
            }
        }
        payload = TTNUplinkPayload(**ttn_json)
        self.assertEqual(payload.end_device_ids.device_id, "eui-1234567890abcdef")
        self.assertEqual(payload.uplink_message.f_cnt, 10)

    def test_ttn_uplink_payload_extra_fields(self):
        """Test that extra fields in TTN payload are ignored."""
        ttn_json = {
            "end_device_ids": {
                "device_id": "eui-1234567890abcdef",
                "application_ids": {"application_id": "my-app"}
            },
            "correlation_ids": ["as:up:123"],
            "received_at": "2023-10-27T10:00:00Z",
            "uplink_message": {
                "f_port": 1,
                "f_cnt": 10,
                "received_at": "2023-10-27T10:00:00Z"
            },
            "simulated": True  # Extra field
        }
        payload = TTNUplinkPayload(**ttn_json)
        self.assertEqual(payload.end_device_ids.device_id, "eui-1234567890abcdef")

if __name__ == "__main__":
    unittest.main()
