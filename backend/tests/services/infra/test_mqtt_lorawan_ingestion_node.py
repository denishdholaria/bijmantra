import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# We need to mock 'mqtt' import if paho-mqtt is missing, but here we installed it.
# However, for pure unit testing without relying on external deps availability, we can use sys.modules patching or just rely on the installed package.
from app.services.infra.mqtt_lorawan_ingestion_node import MqttLorawanIngestionNode


@pytest.fixture
def mock_telemetry_service():
    with patch("app.services.infra.mqtt_lorawan_ingestion_node.telemetry_service") as mock:
        mock.record_reading = AsyncMock()
        yield mock

@pytest.fixture
def mock_db_session():
    mock_db = AsyncMock()
    # Mock context manager
    mock_session_cls = MagicMock()
    mock_session_cls.__aenter__.return_value = mock_db
    mock_session_cls.__aexit__.return_value = None

    with patch("app.services.infra.mqtt_lorawan_ingestion_node.AsyncSessionLocal", return_value=mock_session_cls):
        yield mock_db

@pytest.fixture
def mock_mqtt_client():
    with patch("app.services.infra.mqtt_lorawan_ingestion_node.mqtt.Client") as mock_cls:
        client_instance = MagicMock()
        mock_cls.return_value = client_instance
        yield client_instance

@pytest.mark.asyncio
async def test_process_uplink_success(mock_telemetry_service, mock_db_session, mock_mqtt_client):
    node = MqttLorawanIngestionNode(
        broker_url="localhost",
        broker_port=1883,
        topic="v3/+/devices/+/up"
    )

    payload = {
        "end_device_ids": {
            "device_id": "sensor-001",
            "application_ids": {"application_id": "app-1"},
            "dev_eui": "0004A30B001A2B3C"
        },
        "uplink_message": {
            "f_port": 1,
            "f_cnt": 42,
            "decoded_payload": {
                "temperature": 25.5,
                "humidity": 60.0
            },
            "rx_metadata": [{"rssi": -50, "snr": 10}]
        }
    }

    payload_str = json.dumps(payload)

    await node.process_uplink(payload_str)

    assert mock_telemetry_service.record_reading.call_count == 2

    calls = mock_telemetry_service.record_reading.call_args_list
    # The order depends on dict iteration, but usually consistent
    sensors_found = []
    for call in calls:
        telemetry_in = call[0][1] # second arg
        assert telemetry_in.device_db_id == "sensor-001"
        sensors_found.append(telemetry_in.sensor_code)
        assert telemetry_in.additional_info["lora_f_cnt"] == 42

    assert "temperature" in sensors_found
    assert "humidity" in sensors_found

@pytest.mark.asyncio
async def test_process_uplink_invalid_json(mock_telemetry_service, mock_db_session, mock_mqtt_client):
    node = MqttLorawanIngestionNode("localhost", 1883, "topic")
    await node.process_uplink("not json")
    mock_telemetry_service.record_reading.assert_not_called()

@pytest.mark.asyncio
async def test_process_uplink_validation_error(mock_telemetry_service, mock_db_session, mock_mqtt_client):
    node = MqttLorawanIngestionNode("localhost", 1883, "topic")
    # Missing required field 'end_device_ids'
    payload = {"uplink_message": {}}
    await node.process_uplink(json.dumps(payload))
    mock_telemetry_service.record_reading.assert_not_called()
