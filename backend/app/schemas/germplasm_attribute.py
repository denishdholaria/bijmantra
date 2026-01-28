from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.brapi import ExternalReference, AdditionalInfo

class GermplasmAttributeDefinitionBase(BaseModel):
    attributeName: str = Field(..., description="The name of the attribute")
    attributePUI: Optional[str] = Field(None, description="The Permanent Unique Identifier for the attribute")
    attributeDescription: Optional[str] = Field(None, description="The description of the attribute")
    attributeCategory: Optional[str] = Field(None, description="The category of the attribute")
    commonCropName: Optional[str] = Field(None, description="The common name of the crop")
    contextOfUse: Optional[List[str]] = Field(None, description="The context in which the attribute is used")
    defaultValue: Optional[str] = Field(None, description="The default value of the attribute")
    documentationURL: Optional[str] = Field(None, description="URL to documentation")
    growthStage: Optional[str] = Field(None, description="The growth stage when the attribute is measured")
    institution: Optional[str] = Field(None, description="The institution responsible for the attribute")
    language: Optional[str] = Field(None, description="The language of the attribute")
    scientist: Optional[str] = Field(None, description="The scientist responsible for the attribute")
    status: Optional[str] = Field(None, description="The status of the attribute")
    submissionTimestamp: Optional[str] = Field(None, description="The timestamp when the attribute was submitted")
    synonyms: Optional[List[str]] = Field(None, description="Synonyms for the attribute")
    traitDbId: Optional[str] = Field(None, description="The DbId of the trait")
    traitName: Optional[str] = Field(None, description="The name of the trait")
    traitDescription: Optional[str] = Field(None, description="The description of the trait")
    traitClass: Optional[str] = Field(None, description="The class of the trait")
    methodDbId: Optional[str] = Field(None, description="The DbId of the method")
    methodName: Optional[str] = Field(None, description="The name of the method")
    methodDescription: Optional[str] = Field(None, description="The description of the method")
    methodClass: Optional[str] = Field(None, description="The class of the method")
    scaleDbId: Optional[str] = Field(None, description="The DbId of the scale")
    scaleName: Optional[str] = Field(None, description="The name of the scale")
    dataType: Optional[str] = Field(None, description="The data type of the attribute")
    additionalInfo: Optional[Dict[str, Any]] = Field(None, description="Additional arbitrary information")
    externalReferences: Optional[List[ExternalReference]] = Field(None, description="External references")

    model_config = ConfigDict(populate_by_name=True)

class GermplasmAttributeDefinitionNewRequest(GermplasmAttributeDefinitionBase):
    attributeDbId: Optional[str] = Field(None, description="The DbId of the attribute (optional for creation)")

class GermplasmAttributeDefinition(GermplasmAttributeDefinitionBase):
    attributeDbId: str = Field(..., description="The DbId of the attribute")

class GermplasmAttributeDefinitionResponse(BaseModel):
    data: List[GermplasmAttributeDefinition]
