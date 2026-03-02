"""
BrAPI Genotyping Schemas
Genome Maps, Linkage Groups, Marker Positions, Calls, Variants
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# --- Reference Schemas ---

# --- Reference Set ---

class ReferenceSetBase(BaseModel):
    referenceSetName: str | None = None
    description: str | None = None
    assemblyPUI: str | None = None
    sourceURI: str | None = None
    species: dict[str, Any] | None = None
    isDerived: bool | None = False
    md5checksum: str | None = None
    additionalInfo: dict[str, Any] | None = None

class ReferenceSetCreate(ReferenceSetBase):
    referenceSetName: str

class ReferenceSetUpdate(ReferenceSetBase):
    pass

class ReferenceSet(ReferenceSetBase):
    referenceSetDbId: str

    model_config = ConfigDict(from_attributes=True)

# --- Reference ---

class ReferenceBase(BaseModel):
    referenceName: str | None = None
    referenceSetDbId: str | None = None
    length: int | None = None
    md5checksum: str | None = None
    sourceURI: str | None = None
    species: dict[str, Any] | None = None
    isDerived: bool | None = False
    additionalInfo: dict[str, Any] | None = None

class ReferenceCreate(ReferenceBase):
    referenceName: str
    referenceSetDbId: str | None = None

class ReferenceUpdate(ReferenceBase):
    pass

class Reference(ReferenceBase):
    referenceDbId: str

    model_config = ConfigDict(from_attributes=True)

# --- VariantSet Schemas ---

class VariantSetBase(BaseModel):
    variantSetName: str | None = None
    studyDbId: str | None = None
    referenceSetDbId: str | None = None
    analysis: list[dict[str, Any]] | None = None
    availableFormats: list[dict[str, Any]] | None = None
    additionalInfo: dict[str, Any] | None = None

class VariantSetCreate(VariantSetBase):
    variantSetName: str

class VariantSetUpdate(VariantSetBase):
    pass

class VariantSetResponse(VariantSetBase):
    variantSetDbId: str
    callSetCount: int | None = 0
    variantCount: int | None = 0

    model_config = ConfigDict(from_attributes=True)

# --- Variant Schemas ---

class VariantBase(BaseModel):
    variantName: str | None = None
    variantType: str | None = None
    referenceBases: str | None = None
    alternateBases: list[str] | None = None
    start: int | None = None
    end: int | None = None
    cipos: list[int] | None = None
    ciend: list[int] | None = None
    svlen: int | None = None
    filtersApplied: bool | None = True
    filtersPassed: bool | None = None
    additionalInfo: dict[str, Any] | None = None

    variantSetDbId: str | None = None # For linkage
    referenceDbId: str | None = None   # For linkage

class VariantCreate(VariantBase):
    variantSetDbId: str
    referenceDbId: str | None = None
    start: int | None = None

class VariantUpdate(VariantBase):
    pass

class VariantResponse(VariantBase):
    variantDbId: str
    variantSetDbId: list[str] = [] # BrAPI specifies list
    referenceName: str | None = None
    created: datetime | None = None
    updated: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

# --- CallSet Schemas ---

class CallSetBase(BaseModel):
    callSetName: str | None = None
    sampleDbId: str | None = None
    variantSetDbIds: list[str] | None = None
    additionalInfo: dict[str, Any] | None = None

class CallSetCreate(CallSetBase):
    callSetName: str
    variantSetDbIds: list[str]

class CallSetUpdate(CallSetBase):
    pass

class CallSetResponse(CallSetBase):
    callSetDbId: str
    created: str | None = None
    updated: str | None = None

    model_config = ConfigDict(from_attributes=True)

# --- Call Schemas ---

class CallBase(BaseModel):
    genotype: dict[str, Any] | None = None
    genotypeValue: str | None = None
    genotypeLikelihood: list[float] | None = None
    phaseSet: str | None = None
    additionalInfo: dict[str, Any] | None = None

class CallCreate(CallBase):
    callSetDbId: str
    variantDbId: str

class CallUpdate(CallBase):
    pass

class CallResponse(CallBase):
    callDbId: str | None = None
# --- Responses ---

class CallListResponse(BaseModel):
    metadata: dict[str, Any]
    result: dict[str, list[CallResponse]]

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# Genome Map Schemas
# ==========================================

class GenomeMapBase(BaseModel):
    map_name: str = Field(..., alias="mapName", description="The human readable name of this map")
    map_pui: str | None = Field(None, alias="mapPUI", description="The DOI or other permanent identifier for this map")
    common_crop_name: str | None = Field(None, alias="commonCropName", description="The common name of the crop")
    type: str | None = Field(None, description="Type of map (e.g., Genetic, Physical)")
    unit: str | None = Field(None, description="The unit used for positions on this map (e.g., cM, bp)")
    scientific_name: str | None = Field(None, alias="scientificName", description="The scientific name of the organism")
    published_date: str | None = Field(None, alias="publishedDate", description="The date this map was published")
    comments: str | None = Field(None, description="Additional comments")
    documentation_url: str | None = Field(None, alias="documentationURL", description="A URL to the documentation of this map")
    additional_info: dict[str, Any] | None = Field(None, alias="additionalInfo", description="Additional arbitrary info")

    model_config = ConfigDict(populate_by_name=True)

class GenomeMapCreate(GenomeMapBase):
    pass

class GenomeMapUpdate(BaseModel):
    map_name: str | None = Field(None, alias="mapName")
    map_pui: str | None = Field(None, alias="mapPUI")
    common_crop_name: str | None = Field(None, alias="commonCropName")
    type: str | None = Field(None)
    unit: str | None = Field(None)
    scientific_name: str | None = Field(None, alias="scientificName")
    published_date: str | None = Field(None, alias="publishedDate")
    comments: str | None = Field(None)
    documentation_url: str | None = Field(None, alias="documentationURL")
    additional_info: dict[str, Any] | None = Field(None, alias="additionalInfo")

    model_config = ConfigDict(populate_by_name=True)

class GenomeMap(GenomeMapBase):
    map_db_id: str = Field(..., alias="mapDbId", description="The unique identifier for this map")
    linkage_group_count: int | None = Field(0, alias="linkageGroupCount", description="The number of linkage groups in this map")
    marker_count: int | None = Field(0, alias="markerCount", description="The number of markers in this map")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# ==========================================
# Linkage Group Schemas
# ==========================================

class LinkageGroupBase(BaseModel):
    linkage_group_name: str = Field(..., alias="linkageGroupName", description="The name of the linkage group")
    max_position: float | None = Field(None, alias="maxPosition", description="The maximum position on this linkage group")
    marker_count: int | None = Field(0, alias="markerCount", description="The number of markers on this linkage group")
    additional_info: dict[str, Any] | None = Field(None, alias="additionalInfo")

    model_config = ConfigDict(populate_by_name=True)

class LinkageGroupCreate(LinkageGroupBase):
    map_db_id: str = Field(..., alias="mapDbId", description="The map this linkage group belongs to")

class LinkageGroup(LinkageGroupBase):
    map_db_id: str = Field(..., alias="mapDbId", description="The map this linkage group belongs to")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# ==========================================
# Marker Position Schemas
# ==========================================

class MarkerPositionBase(BaseModel):
    marker_db_id: str | None = Field(None, alias="markerDbId")
    marker_name: str | None = Field(None, alias="markerName")
    variant_db_id: str | None = Field(None, alias="variantDbId")
    variant_name: str | None = Field(None, alias="variantName")
    linkage_group_name: str = Field(..., alias="linkageGroupName")
    position: float
    map_db_id: str = Field(..., alias="mapDbId")
    additional_info: dict[str, Any] | None = Field(None, alias="additionalInfo")

    model_config = ConfigDict(populate_by_name=True)

class MarkerPositionCreate(MarkerPositionBase):
    pass

class MarkerPosition(MarkerPositionBase):
    marker_position_db_id: str = Field(..., alias="markerPositionDbId")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# ==========================================
# Vendor Order Schemas
# ==========================================

class VendorOrderBase(BaseModel):
    client_id: str | None = Field(None, alias="clientId", description="A unique identifier for the client submitting the order")
    number_of_samples: int | None = Field(None, alias="numberOfSamples", description="The number of samples in the order")
    required_service_info: dict[str, Any] | None = Field(None, alias="requiredServiceInfo", description="Additional information required by the requested service")
    service_ids: list[str] | None = Field(None, alias="serviceIds", description="List of service identifiers requested")

    model_config = ConfigDict(populate_by_name=True)

class VendorOrderCreate(VendorOrderBase):
    client_id: str = Field(..., alias="clientId")
    number_of_samples: int = Field(..., alias="numberOfSamples")
    service_ids: list[str] = Field(..., alias="serviceIds")

class VendorOrderStatusUpdate(BaseModel):
    status: str = Field(..., description="The new status of the order")

class VendorOrder(VendorOrderBase):
    order_db_id: str = Field(..., alias="vendorOrderDbId", description="The unique identifier for this order")
    order_id: str | None = Field(None, alias="orderId", description="Human readable order ID")
    status: str | None = Field(None, description="The current status of the order")
    status_time_stamp: str | None = Field(None, alias="statusTimeStamp", description="Timestamp of the last status update")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
