"""
Unit tests for Latent State Encoder (REEVU Expansion).
"""

import sys
import os
import pytest
import numpy as np
from datetime import datetime, timezone

# Adjust path to allow imports from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../")))

from app.modules.ai.services.reevu.expansions.latent_state_encoder import (
    LatentStateEncoder,
    SensorObservation,
    LatentState,
    SensorStreamConfig
)

def test_sensor_stream_config():
    """Test SensorStreamConfig validation."""
    config = SensorStreamConfig(
        stream_id="cam_01",
        sensor_type="camera",
        frequency_hz=30.0,
        resolution=[1920, 1080],
        channels=3
    )
    assert config.stream_id == "cam_01"
    assert config.frequency_hz == 30.0

    with pytest.raises(Exception): # Pydantic validation error
        SensorStreamConfig(
            stream_id="bad",
            sensor_type="test",
            frequency_hz=-1.0 # Invalid
        )

def test_sensor_observation_defaults():
    """Test SensorObservation default values."""
    obs = SensorObservation(
        stream_id="gnss_01",
        data=[12.34, 56.78]
    )
    assert obs.observation_id is not None
    assert obs.timestamp is not None
    assert obs.timestamp.tzinfo == timezone.utc
    assert obs.data == [12.34, 56.78]

def test_encoder_initialization():
    """Test encoder initialization."""
    encoder = LatentStateEncoder(latent_dim=32, random_seed=42)
    assert encoder.latent_dim == 32
    # Private attributes check
    assert encoder._rng is not None

def test_encode_single_vector():
    """Test encoding a single vector input."""
    encoder = LatentStateEncoder(latent_dim=16, random_seed=42)

    data = np.random.rand(100).tolist()
    obs = SensorObservation(
        stream_id="test_stream",
        data=data
    )

    state = encoder.encode(obs)

    assert isinstance(state, LatentState)
    assert len(state.vector) == 16
    assert state.dimension == 16
    assert state.source_observations == [obs.observation_id]
    # Check if values are in [-1, 1] due to tanh
    assert all(-1.0 <= v <= 1.0 for v in state.vector)

def test_encode_numpy_array():
    """Test encoding a numpy array input."""
    encoder = LatentStateEncoder(latent_dim=8, random_seed=123)

    # Simulate an image 10x10x3
    data = np.zeros((10, 10, 3))
    obs = SensorObservation(
        stream_id="cam_stream",
        data=data
    )

    state = encoder.encode(obs)

    assert len(state.vector) == 8
    assert state.dimension == 8

def test_batch_encode():
    """Test batch encoding."""
    encoder = LatentStateEncoder(latent_dim=4, random_seed=1)

    observations = [
        SensorObservation(stream_id="s1", data=[1.0, 2.0]),
        SensorObservation(stream_id="s1", data=[3.0, 4.0]),
        SensorObservation(stream_id="s1", data=[5.0, 6.0]),
    ]

    results = encoder.batch_encode(observations)

    assert len(results) == 3
    for res in results:
        assert isinstance(res, LatentState)
        assert res.dimension == 4

def test_error_handling_invalid_data():
    """Test error handling for invalid data types."""
    encoder = LatentStateEncoder()

    obs = SensorObservation(
        stream_id="bad_stream",
        data="invalid_string_data" # String not supported by _preprocess
    )

    with pytest.raises(RuntimeError) as excinfo:
        encoder.encode(obs)

    assert "Encoding failed" in str(excinfo.value)

def test_error_handling_empty_data():
    """Test error handling for empty data."""
    encoder = LatentStateEncoder()

    obs = SensorObservation(
        stream_id="empty_stream",
        data=[]
    )

    with pytest.raises(RuntimeError) as excinfo:
        encoder.encode(obs)

    assert "Input data is empty" in str(excinfo.value)


def test_error_handling_nan_data():
    """Test encoder rejects NaN sensor values."""
    encoder = LatentStateEncoder()

    obs = SensorObservation(
        stream_id="nan_stream",
        data=[1.0, float("nan"), 2.0]
    )

    with pytest.raises(RuntimeError) as excinfo:
        encoder.encode(obs)

    assert "non-finite values" in str(excinfo.value)


def test_error_handling_infinite_data():
    """Test encoder rejects infinite sensor values."""
    encoder = LatentStateEncoder()

    obs = SensorObservation(
        stream_id="inf_stream",
        data=np.array([1.0, np.inf, 2.0], dtype=np.float32)
    )

    with pytest.raises(RuntimeError) as excinfo:
        encoder.encode(obs)

    assert "non-finite values" in str(excinfo.value)


def test_batch_encode_partial_failure():
    """Test batch encoding with some failing inputs."""
    encoder = LatentStateEncoder()

    observations = [
        SensorObservation(stream_id="s1", data=[1.0, 2.0]), # Valid
        SensorObservation(stream_id="s2", data=[]),         # Invalid (empty)
        SensorObservation(stream_id="s3", data=[3.0, 4.0]), # Valid
    ]

    # Capture stdout to verify warning?
    # Or just check result count. Implementation logs and skips.
    results = encoder.batch_encode(observations)

    assert len(results) == 2
    assert results[0].source_observations[0] == observations[0].observation_id
    assert results[1].source_observations[0] == observations[2].observation_id
