"""
Latent State Encoder — REEVU Expansion

Encodes high-dimensional sensorimotor input streams (e.g., from robotics, IoT)
into low-dimensional latent state representations for REEVU's reasoning engine.

This module provides the `LatentStateEncoder` class and associated Pydantic models.
It is designed to be a standalone component that can be integrated into the
REEVU pipeline.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ── Schemas ──────────────────────────────────────────────────────────

class SensorStreamConfig(BaseModel):
    """Configuration for a specific sensor input stream."""

    stream_id: str = Field(..., description="Unique identifier for the sensor stream")
    sensor_type: str = Field(..., description="Type of sensor, e.g., 'camera', 'lidar', 'gnss', 'imu'")
    frequency_hz: float = Field(..., gt=0, description="Sampling frequency in Hz")
    resolution: Optional[List[int]] = Field(None, description="Resolution [H, W] for grid-based sensors")
    channels: int = Field(1, ge=1, description="Number of data channels (e.g., 3 for RGB)")

    model_config = ConfigDict(frozen=True)


class SensorObservation(BaseModel):
    """A single observation from a sensor stream."""

    observation_id: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
        description="Unique identifier for this observation"
    )
    stream_id: str = Field(..., description="ID of the source sensor stream")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the observation"
    )
    data: Any = Field(..., description="Raw sensor data (e.g., numpy array, list of floats)")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (e.g., sensor health, calibration info)"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("timestamp")
    @classmethod
    def ensure_timezone(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware (UTC)."""
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


class LatentState(BaseModel):
    """Compressed latent representation of the sensorimotor state."""

    state_id: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
        description="Unique identifier for this latent state"
    )
    vector: List[float] = Field(..., description="The low-dimensional latent vector")
    dimension: int = Field(..., description="Dimension of the latent vector")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Confidence score of the encoding")
    source_observations: List[str] = Field(
        default_factory=list,
        description="List of observation IDs used to generate this state"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the state generation"
    )

    model_config = ConfigDict(frozen=True)


# ── Encoder Logic ────────────────────────────────────────────────────

class LatentStateEncoder:
    """
    Encodes sensorimotor data into latent states.

    This class serves as the perception frontend for REEVU. Ideally, it wraps
    a machine learning model (e.g., VAE, Autoencoder). For this implementation,
    it uses a mock dimensionality reduction technique (random projection) to
    simulate the interface.
    """

    def __init__(self, latent_dim: int = 64, random_seed: Optional[int] = None):
        """
        Initialize the encoder.

        Args:
            latent_dim: Target dimension for the latent vector.
            random_seed: Seed for the random number generator (for reproducibility).
        """
        self.latent_dim = latent_dim
        self._rng = np.random.default_rng(random_seed)

        # Mock projection matrix cache (lazy initialization based on input dim)
        self._projection_matrix: Optional[np.ndarray] = None
        self._input_dim: Optional[int] = None

    def _get_projection_matrix(self, input_dim: int) -> np.ndarray:
        """Get or create a random projection matrix for dimensionality reduction."""
        if self._projection_matrix is None or self._input_dim != input_dim:
            # Create a random Gaussian matrix for projection: (input_dim, latent_dim)
            # Normalize by sqrt(latent_dim) to maintain scale roughly
            self._projection_matrix = self._rng.standard_normal((input_dim, self.latent_dim)) / np.sqrt(self.latent_dim)
            self._input_dim = input_dim
        return self._projection_matrix

    def _preprocess(self, data: Any) -> np.ndarray:
        """
        Convert input data to a flattened numpy array.

        Handles:
        - Lists
        - Numpy arrays (flattens them)
        """
        if isinstance(data, list):
            arr = np.array(data, dtype=np.float32)
        elif isinstance(data, np.ndarray):
            arr = data.astype(np.float32)
        else:
            raise ValueError(f"Unsupported data type: {type(data)}. Expected list or numpy array.")

        flat_arr = arr.flatten()

        if not np.all(np.isfinite(flat_arr)):
            raise ValueError(
                "Input data contains non-finite values (NaN or Inf); "
                "please impute or drop invalid sensor readings before encoding."
            )

        return flat_arr

    def encode(self, observation: SensorObservation) -> LatentState:
        """
        Encode a single sensor observation into a latent state.

        Args:
            observation: The sensor observation to encode.

        Returns:
            LatentState object containing the encoded vector.
        """
        try:
            # 1. Preprocess
            flat_data = self._preprocess(observation.data)
            input_dim = flat_data.shape[0]

            if input_dim == 0:
                raise ValueError("Input data is empty.")

            # 2. Encode (Mock: Random Projection)
            proj_matrix = self._get_projection_matrix(input_dim)
            latent_vector = np.dot(flat_data, proj_matrix)

            # 3. Post-process (e.g., activation function - using tanh for -1 to 1 range, or just raw)
            # Let's use tanh to bound it, simulating a neural net layer
            latent_vector = np.tanh(latent_vector)

            return LatentState(
                vector=latent_vector.tolist(),
                dimension=self.latent_dim,
                confidence=0.95,  # Mock confidence
                source_observations=[observation.observation_id],
                timestamp=datetime.now(timezone.utc)
            )

        except Exception as e:
            # In a real system, we might log this or return a fallback state
            # For now, re-raise with context
            raise RuntimeError(f"Encoding failed for observation {observation.observation_id}: {str(e)}") from e

    def batch_encode(self, observations: List[SensorObservation]) -> List[LatentState]:
        """
        Encode a batch of sensor observations.

        Args:
            observations: List of sensor observations.

        Returns:
            List of LatentState objects.
        """
        results = []
        for obs in observations:
            try:
                state = self.encode(obs)
                results.append(state)
            except RuntimeError as e:
                # Handle individual failures in batch?
                # For now, let's skip failed ones or we could insert None/Error state
                # The requirement implies robust processing.
                # Let's log (print for now) and continue to avoid crashing the whole batch
                print(f"Warning: Skipping observation {obs.observation_id} due to error: {e}")
                continue

        return results
