"""
MQTT LoRaWAN Ingestion Node

This service connects to an MQTT broker (e.g., The Things Network, ChirpStack)
to ingest LoRaWAN uplink messages and store them as IoT Telemetry.

It acts as an infrastructure bridge between external LoRaWAN networks and the internal REEVU domain.
"""

import asyncio
import json
import logging
from typing import Any


try:
    import paho.mqtt.client as mqtt
    from paho.mqtt.enums import CallbackAPIVersion
except ImportError:
    # Fallback for environments without paho-mqtt (mocking or just logging error)
    mqtt = None
    CallbackAPIVersion = None

from pydantic import BaseModel

from app.core.database import AsyncSessionLocal
from app.schemas.iot.telemetry import TelemetryCreate
from app.modules.environment.services.iot.telemetry_service import telemetry_service


logger = logging.getLogger(__name__)


# --- LoRaWAN Payload Schemas (TTN v3 / ChirpStack compatible) ---

class EndDeviceIds(BaseModel):
    """Device identifiers"""
    device_id: str
    application_ids: dict[str, Any] | None = None
    dev_eui: str | None = None
    join_eui: str | None = None
    dev_addr: str | None = None


class UplinkMessage(BaseModel):
    """Uplink message details"""
    session_key_id: str | None = None
    f_port: int | None = None
    f_cnt: int | None = None
    frm_payload: str | None = None  # Base64 encoded payload
    decoded_payload: dict[str, Any] | None = None  # Decoded payload from network server
    rx_metadata: list[dict[str, Any]] | None = None
    settings: dict[str, Any] | None = None


class LorawanUplinkPayload(BaseModel):
    """Root payload structure for LoRaWAN uplink"""
    end_device_ids: EndDeviceIds
    correlation_ids: list[str] | None = None
    received_at: str | None = None
    uplink_message: UplinkMessage
    simulated: bool = False


# --- Ingestion Node Service ---

class MqttLorawanIngestionNode:
    """
    Connects to MQTT broker and ingests LoRaWAN data.
    """

    def __init__(
        self,
        broker_url: str,
        broker_port: int,
        topic: str,
        client_id: str | None = None,
        username: str | None = None,
        password: str | None = None,
        loop: asyncio.AbstractEventLoop | None = None
    ):
        if not mqtt:
            logger.error("paho-mqtt library is not installed.")
            raise ImportError("paho-mqtt is required for MqttLorawanIngestionNode")

        self.broker_url = broker_url
        self.broker_port = broker_port
        self.topic = topic
        self.client_id = client_id or "bijmantra_lorawan_ingest"
        self.username = username
        self.password = password
        self.loop = loop or asyncio.get_event_loop()

        # Initialize MQTT Client with Version 2 callbacks
        self.client = mqtt.Client(
            callback_api_version=CallbackAPIVersion.VERSION2,
            client_id=self.client_id
        )

        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def start(self):
        """Connects to the broker and starts the loop."""
        logger.info(f"Connecting to MQTT broker at {self.broker_url}:{self.broker_port}")
        try:
            self.client.connect(self.broker_url, self.broker_port, 60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise

    def stop(self):
        """Stops the loop and disconnects."""
        self.client.loop_stop()
        self.client.disconnect()

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """Callback for when the client receives a CONNACK response from the server."""
        if rc == 0:
            logger.info("Connected to MQTT Broker!")
            client.subscribe(self.topic)
            logger.info(f"Subscribed to topic: {self.topic}")
        else:
            logger.error(f"Failed to connect, return code {rc}")

    def _on_message(self, client, userdata, msg):
        """Callback for when a PUBLISH message is received from the server."""
        try:
            payload = msg.payload.decode()
            logger.debug(f"Received message on {msg.topic}: {payload[:100]}...")

            # Bridge to async world
            asyncio.run_coroutine_threadsafe(self.process_uplink(payload), self.loop)
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    def _on_disconnect(self, client, userdata, flags, rc, properties=None): # pylint: disable=unused-argument
        """Callback for when the client disconnects from the server."""
        logger.warning(f"Disconnected from MQTT broker with code {rc}")

    async def process_uplink(self, payload_str: str):
        """
        Async method to process the uplink payload and save telemetry.
        """
        try:
            data = json.loads(payload_str)
            # Validate against schema
            uplink = LorawanUplinkPayload(**data)

            # Identify device
            device_id = uplink.end_device_ids.device_id
            # Optionally fallback to DevEUI if device_id is not the DB ID
            if uplink.end_device_ids.dev_eui:
                # In strict implementation, we might need to map DevEUI to device_db_id via DB query.
                # For now, we assume device_id in payload matches device_db_id in our DB,
                # or the caller uses DevEUI as the ID.
                pass

            # Extract sensor data
            sensor_data: dict[str, Any] = {}

            # 1. Try decoded payload (from Network Server codec)
            if uplink.uplink_message.decoded_payload:
                sensor_data = uplink.uplink_message.decoded_payload

            # 2. If no decoded payload, but frm_payload exists, we could try generic decoding?
            #    (Skipping generic binary decoding as it's device-specific)

            if not sensor_data:
                logger.warning(f"No decoded payload found for device {device_id}. Skipping.")
                return

            # Save to DB
            async with AsyncSessionLocal() as db:
                for sensor_key, value in sensor_data.items():
                    # Basic filtering for numeric values
                    if isinstance(value, (int, float)):
                        telemetry_in = TelemetryCreate(
                            device_db_id=device_id,
                            sensor_code=sensor_key,
                            value=float(value),
                            timestamp=None, # will use server timestamp
                            additional_info={
                                "lora_f_cnt": uplink.uplink_message.f_cnt,
                                "lora_f_port": uplink.uplink_message.f_port,
                                "rssi": uplink.uplink_message.rx_metadata[0].get("rssi") if uplink.uplink_message.rx_metadata else None,
                                "snr": uplink.uplink_message.rx_metadata[0].get("snr") if uplink.uplink_message.rx_metadata else None
                            }
                        )
                        try:
                            await telemetry_service.record_reading(db, telemetry_in)
                            logger.info(f"Recorded telemetry for {device_id}: {sensor_key}={value}")
                        except ValueError as ve:
                            logger.error(f"Validation error for {device_id}: {ve}")
                        except Exception as e:
                            logger.error(f"DB error recording telemetry for {device_id}: {e}")
                    else:
                        logger.debug(f"Skipping non-numeric value for {sensor_key}: {value}")

        except json.JSONDecodeError:
            logger.error("Failed to decode JSON payload")
        except Exception as e:
            logger.error(f"Error processing uplink: {e}", exc_info=True)
