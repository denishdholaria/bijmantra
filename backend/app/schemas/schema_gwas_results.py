"""
GWAS Results Schema
Marker Association results following BrAPI v2.1 standards
"""
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GWASResultBase(BaseModel):
    """Base schema for GWAS Marker Association Result"""
    marker_db_id: str | None = Field(None, alias="markerDbId", description="The unique identifier for the marker")
    marker_name: str | None = Field(None, alias="markerName", description="The name of the marker")
    variant_db_id: str | None = Field(None, alias="variantDbId", description="The unique identifier for the variant")
    linkage_group_name: str | None = Field(None, alias="linkageGroupName", description="The chromosome or linkage group name")
    position: int | None = Field(None, description="The position of the marker")
    p_value: float | None = Field(None, alias="pValue", description="The p-value of the association")
    log10_p_value: float | None = Field(None, alias="log10PValue", description="The -log10 p-value of the association")
    effect_size: float | None = Field(None, alias="effectSize", description="The effect size of the association")
    standard_error: float | None = Field(None, alias="standardError", description="The standard error of the effect size")
    trait_db_id: str | None = Field(None, alias="traitDbId", description="The unique identifier for the trait")
    trait_name: str | None = Field(None, alias="traitName", description="The name of the trait")
    study_db_id: str | None = Field(None, alias="studyDbId", description="The unique identifier for the study")
    model_db_id: str | None = Field(None, alias="modelDbId", description="The unique identifier for the analysis model")
    n_samples: int | None = Field(None, alias="nSamples", description="The number of samples used in the analysis")
    additional_info: dict[str, Any] | None = Field(None, alias="additionalInfo", description="Additional arbitrary info")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator('p_value')
    @classmethod
    def validate_p_value(cls, v: float | None) -> float | None:
        if v is not None and (v < 0 or v > 1):
            raise ValueError('p_value must be between 0 and 1')
        return v

    @field_validator('position')
    @classmethod
    def validate_position(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError('position must be non-negative')
        return v


class GWASResultCreate(GWASResultBase):
    """Schema for creating a GWAS result"""
    marker_name: str = Field(..., alias="markerName")
    linkage_group_name: str = Field(..., alias="linkageGroupName")
    position: int = Field(...)
    p_value: float = Field(..., alias="pValue")
    trait_name: str = Field(..., alias="traitName")


class GWASResultUpdate(GWASResultBase):
    """Schema for updating a GWAS result"""
    pass


class GWASResult(GWASResultBase):
    """GWAS Result response schema"""
    result_db_id: str = Field(..., alias="resultDbId", description="The unique identifier for this result")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class GWASResultListResponse(BaseModel):
    """List response for GWAS results"""
    metadata: dict[str, Any]
    result: dict[str, list[GWASResult]]

    model_config = ConfigDict(from_attributes=True)
