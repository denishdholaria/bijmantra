"""Shared deterministic interpretation contract for database-backed phenotyping outputs."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PhenotypeInterpretationSummary(BaseModel):
    entity_count: int = Field(..., ge=0)
    trait_count: int = Field(..., ge=0)
    observation_count: int = Field(..., ge=0)


class PhenotypeInterpretationBaseline(BaseModel):
    entity_db_id: str
    entity_name: str
    selection_method: str


class PhenotypeInterpretationEntityMetric(BaseModel):
    trait_key: str
    trait_name: str
    unit: str | None = None
    mean: float
    observation_count: int = Field(..., ge=0)
    delta_percent_vs_baseline: float | None = None


class PhenotypeInterpretationEntity(BaseModel):
    entity_db_id: str
    entity_name: str
    role: str
    metric_count: int = Field(..., ge=0)
    metrics: list[PhenotypeInterpretationEntityMetric] = Field(default_factory=list)


class PhenotypeInterpretationTrait(BaseModel):
    trait_key: str
    trait_name: str
    unit: str | None = None
    subject_count: int = Field(..., ge=0)
    observation_count: int = Field(..., ge=0)
    min: float
    max: float
    mean: float
    std: float
    cv: float | None = None


class PhenotypeInterpretationRankingItem(BaseModel):
    rank: int = Field(..., ge=1)
    entity_db_id: str
    entity_name: str
    role: str
    score_trait_key: str | None = None
    score_trait_name: str | None = None
    score: float | None = None
    delta_percent_vs_baseline: float | None = None
    rationale: str = ""
    evidence_refs: list[str] = Field(default_factory=list)


class PhenotypeInterpretation(BaseModel):
    contract_version: str = "phenotyping.interpretation.v1"
    scope: str
    source: str = "database"
    methodology: str
    primary_trait_key: str | None = None
    primary_trait_name: str | None = None
    summary: PhenotypeInterpretationSummary
    baseline: PhenotypeInterpretationBaseline | None = None
    entities: list[PhenotypeInterpretationEntity] = Field(default_factory=list)
    traits: list[PhenotypeInterpretationTrait] = Field(default_factory=list)
    ranking: list[PhenotypeInterpretationRankingItem] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    calculation_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)