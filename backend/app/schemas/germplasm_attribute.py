from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.brapi import ExternalReference


class GermplasmAttributeDefinitionBase(BaseModel):
    attributeName: str = Field(..., description="The name of the attribute")
    attributePUI: str | None = Field(None, description="The Permanent Unique Identifier for the attribute")
    attributeDescription: str | None = Field(None, description="The description of the attribute")
    attributeCategory: str | None = Field(None, description="The category of the attribute")
    commonCropName: str | None = Field(None, description="The common name of the crop")
    contextOfUse: list[str] | None = Field(None, description="The context in which the attribute is used")
    defaultValue: str | None = Field(None, description="The default value of the attribute")
    documentationURL: str | None = Field(None, description="URL to documentation")
    growthStage: str | None = Field(None, description="The growth stage when the attribute is measured")
    institution: str | None = Field(None, description="The institution responsible for the attribute")
    language: str | None = Field(None, description="The language of the attribute")
    scientist: str | None = Field(None, description="The scientist responsible for the attribute")
    status: str | None = Field(None, description="The status of the attribute")
    submissionTimestamp: str | None = Field(None, description="The timestamp when the attribute was submitted")
    synonyms: list[str] | None = Field(None, description="Synonyms for the attribute")
    traitDbId: str | None = Field(None, description="The DbId of the trait")
    traitName: str | None = Field(None, description="The name of the trait")
    traitDescription: str | None = Field(None, description="The description of the trait")
    traitClass: str | None = Field(None, description="The class of the trait")
    methodDbId: str | None = Field(None, description="The DbId of the method")
    methodName: str | None = Field(None, description="The name of the method")
    methodDescription: str | None = Field(None, description="The description of the method")
    methodClass: str | None = Field(None, description="The class of the method")
    scaleDbId: str | None = Field(None, description="The DbId of the scale")
    scaleName: str | None = Field(None, description="The name of the scale")
    dataType: str | None = Field(None, description="The data type of the attribute")
    additionalInfo: dict[str, Any] | None = Field(None, description="Additional arbitrary information")
    externalReferences: list[ExternalReference] | None = Field(None, description="External references")

    model_config = ConfigDict(populate_by_name=True)

class GermplasmAttributeDefinitionNewRequest(GermplasmAttributeDefinitionBase):
    attributeDbId: str | None = Field(None, description="The DbId of the attribute (optional for creation)")

class GermplasmAttributeDefinition(GermplasmAttributeDefinitionBase):
    attributeDbId: str = Field(..., description="The DbId of the attribute")

class GermplasmAttributeDefinitionResponse(BaseModel):
    data: list[GermplasmAttributeDefinition]
