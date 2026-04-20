from typing import Any, Union

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.brapi import BrAPIResponse, ExternalReference


class OntologyReference(BaseModel):
    ontology_db_id: str | None = Field(None, alias="ontologyDbId")
    ontology_name: str | None = Field(None, alias="ontologyName")
    version: str | None = Field(None, alias="version")

    model_config = ConfigDict(populate_by_name=True)

class Category(BaseModel):
    label: str
    value: str

class ValidValues(BaseModel):
    min: int | None = None
    max: int | None = None
    categories: list[Category] | None = None

class ScaleBase(BaseModel):
    scale_name: str = Field(..., alias="scaleName")
    scale_pui: str | None = Field(None, alias="scalePUI")
    data_type: str | None = Field(None, alias="dataType")  # Numerical, Ordinal, Nominal, Date, Text, Code, Duration
    decimal_places: int | None = Field(None, alias="decimalPlaces")
    valid_values: ValidValues | None = Field(None, alias="validValues")
    ontology_reference: OntologyReference | None = Field(None, alias="ontologyReference")
    external_references: list[ExternalReference] | None = Field(None, alias="externalReferences")
    additional_info: dict[str, Any] | None = Field(None, alias="additionalInfo")

    model_config = ConfigDict(populate_by_name=True)

class ScaleCreate(ScaleBase):
    scale_db_id: str | None = Field(None, alias="scaleDbId")

class ScaleUpdate(ScaleBase):
    pass

class Scale(ScaleBase):
    scale_db_id: str = Field(..., alias="scaleDbId")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class ScaleList(BaseModel):
    data: list[Scale]

class ScaleListResponse(BrAPIResponse[ScaleList]):
    pass

class ScaleSingleResponse(BrAPIResponse[Scale]):
    pass

class ScaleDeleteResponse(BrAPIResponse[Union[Scale, None]]):
    pass
