from __future__ import annotations

from pydantic import BaseModel, Field


CROSS_DOMAIN_QUERY_CONTRACT_VERSION = "cross_domain_query.response.v1"
CROSS_DOMAIN_QUERY_TRUST_SURFACE = "cross_domain_query"


class CrossDomainQueryContractMetadata(BaseModel):
    response_contract_version: str = Field(default=CROSS_DOMAIN_QUERY_CONTRACT_VERSION)
    trust_surface: str = Field(default=CROSS_DOMAIN_QUERY_TRUST_SURFACE)
    data_source: str = Field(default="database_and_weather_service")
    schema_version: str = Field(default="1")
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    calculation_method_refs: list[str] = Field(default_factory=list)
