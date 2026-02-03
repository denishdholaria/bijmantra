from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.brapi import ExternalReference, Metadata, BrAPIResponse

class OntologyReference(BaseModel):
    ontology_db_id: Optional[str] = Field(None, alias="ontologyDbId")
    ontology_name: Optional[str] = Field(None, alias="ontologyName")
    version: Optional[str] = Field(None, alias="version")

    model_config = ConfigDict(populate_by_name=True)

class Category(BaseModel):
    label: str
    value: str

class ValidValues(BaseModel):
    min: Optional[int] = None
    max: Optional[int] = None
    categories: Optional[List[Category]] = None

class ScaleBase(BaseModel):
    scale_name: str = Field(..., alias="scaleName")
    scale_pui: Optional[str] = Field(None, alias="scalePUI")
    data_type: Optional[str] = Field(None, alias="dataType")  # Numerical, Ordinal, Nominal, Date, Text, Code, Duration
    decimal_places: Optional[int] = Field(None, alias="decimalPlaces")
    valid_values: Optional[ValidValues] = Field(None, alias="validValues")
    ontology_reference: Optional[OntologyReference] = Field(None, alias="ontologyReference")
    external_references: Optional[List[ExternalReference]] = Field(None, alias="externalReferences")
    additional_info: Optional[Dict[str, Any]] = Field(None, alias="additionalInfo")

    model_config = ConfigDict(populate_by_name=True)

class ScaleCreate(ScaleBase):
    scale_db_id: Optional[str] = Field(None, alias="scaleDbId")

class ScaleUpdate(ScaleBase):
    pass

class Scale(ScaleBase):
    scale_db_id: str = Field(..., alias="scaleDbId")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class ScaleList(BaseModel):
    data: List[Scale]

class ScaleListResponse(BrAPIResponse[ScaleList]):
    pass

class ScaleSingleResponse(BrAPIResponse[Scale]):
    pass

class ScaleDeleteResponse(BrAPIResponse[Union[Scale, None]]):
    pass
