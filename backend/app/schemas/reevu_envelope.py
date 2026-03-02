"""
REEVU Evidence Envelope Schema — Stage B

Defines the structured evidence envelope emitted alongside every
REEVU response.  Field names align with reevu-agent-contract.md §2.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EvidenceRef(BaseModel):
    """A single traceable reference to a data source."""

    source_type: str = Field(
        ...,
        description="Domain of the evidence: 'rag', 'function', 'database', 'external'",
    )
    entity_id: str = Field(..., description="Stable identifier for the source entity")
    retrieved_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 timestamp when the evidence was retrieved",
    )
    query_or_method: str = Field(
        "",
        description="Search query or function name used to retrieve this evidence",
    )
    freshness_seconds: float | None = Field(
        None,
        description="Age of the evidence in seconds at retrieval time (None = unknown)",
    )

    model_config = ConfigDict(frozen=True)


class CalculationStep(BaseModel):
    """One step in a reproducible calculation chain."""

    step_id: str = Field(..., description="Unique identifier, e.g. 'fn:calculate_gdd'")
    formula: str | None = Field(None, description="Human-readable formula string")
    inputs: dict[str, Any] | None = Field(None, description="Key input values")

    model_config = ConfigDict(frozen=True)


class UncertaintyInfo(BaseModel):
    """Confidence and data-gap metadata."""

    confidence: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Overall confidence score (0.0–1.0)",
    )
    missing_data: list[str] = Field(
        default_factory=list,
        description="List of data gaps identified during response generation",
    )


class ReevuEnvelope(BaseModel):
    """
    The complete evidence envelope attached to every REEVU response.

    Designed for:
    - Frontend trace-card rendering
    - Audit logging
    - Anti-hallucination validation
    """

    claims: list[str] = Field(
        default_factory=list,
        description="Natural-language claim statements extracted from the response",
    )
    evidence_refs: list[EvidenceRef] = Field(
        default_factory=list,
        description="Traceable references backing the claims",
    )
    calculation_steps: list[CalculationStep] = Field(
        default_factory=list,
        description="Reproducible calculation chain (if any)",
    )
    uncertainty: UncertaintyInfo = Field(
        default_factory=UncertaintyInfo,
        description="Confidence and data-gap metadata",
    )
    policy_flags: list[str] = Field(
        default_factory=list,
        description="Flags raised by provenance or policy checks, e.g. 'stale_evidence'",
    )
