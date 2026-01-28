"""
BrAPI Genotyping Schemas
Genome Maps, Linkage Groups, Marker Positions, Calls, Variants
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
# --- Reference Schemas ---

# --- Reference Set ---

class ReferenceSetBase(BaseModel):
    referenceSetName: Optional[str] = None
    description: Optional[str] = None
    assemblyPUI: Optional[str] = None
    sourceURI: Optional[str] = None
    species: Optional[Dict[str, Any]] = None
    isDerived: Optional[bool] = False
    md5checksum: Optional[str] = None
    additionalInfo: Optional[Dict[str, Any]] = None

class ReferenceSetCreate(ReferenceSetBase):
    referenceSetName: str

class ReferenceSetUpdate(ReferenceSetBase):
    pass

class ReferenceSet(ReferenceSetBase):
    referenceSetDbId: str

    class Config:
        from_attributes = True

# --- Reference ---

class ReferenceBase(BaseModel):
    referenceName: Optional[str] = None
    referenceSetDbId: Optional[str] = None
    length: Optional[int] = None
    md5checksum: Optional[str] = None
    sourceURI: Optional[str] = None
    species: Optional[Dict[str, Any]] = None
    isDerived: Optional[bool] = False
    additionalInfo: Optional[Dict[str, Any]] = None

class ReferenceCreate(ReferenceBase):
    referenceName: str
    referenceSetDbId: Optional[str] = None

class ReferenceUpdate(ReferenceBase):
    pass

class Reference(ReferenceBase):
    referenceDbId: str

    class Config:
        from_attributes = True

# --- VariantSet Schemas ---

class VariantSetBase(BaseModel):
    variantSetName: Optional[str] = None
    studyDbId: Optional[str] = None
    referenceSetDbId: Optional[str] = None
    analysis: Optional[List[Dict[str, Any]]] = None
    availableFormats: Optional[List[Dict[str, Any]]] = None
    additionalInfo: Optional[Dict[str, Any]] = None

class VariantSetCreate(VariantSetBase):
    variantSetName: str

class VariantSetUpdate(VariantSetBase):
    pass

class VariantSetResponse(VariantSetBase):
    variantSetDbId: str
    callSetCount: Optional[int] = 0
    variantCount: Optional[int] = 0

    class Config:
        from_attributes = True

# --- Variant Schemas ---

class VariantBase(BaseModel):
    variantName: Optional[str] = None
    variantType: Optional[str] = None
    referenceBases: Optional[str] = None
    alternateBases: Optional[List[str]] = None
    start: Optional[int] = None
    end: Optional[int] = None
    cipos: Optional[List[int]] = None
    ciend: Optional[List[int]] = None
    svlen: Optional[int] = None
    filtersApplied: Optional[bool] = True
    filtersPassed: Optional[bool] = None
    additionalInfo: Optional[Dict[str, Any]] = None

    variantSetDbId: Optional[str] = None # For linkage
    referenceDbId: Optional[str] = None   # For linkage

class VariantCreate(VariantBase):
    variantSetDbId: str
    referenceDbId: Optional[str] = None
    start: Optional[int] = None

class VariantUpdate(VariantBase):
    pass

class VariantResponse(VariantBase):
    variantDbId: str
    variantSetDbId: List[str] = [] # BrAPI specifies list
    referenceName: Optional[str] = None
    created: Optional[datetime] = None
    updated: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- CallSet Schemas ---

class CallSetBase(BaseModel):
    callSetName: Optional[str] = None
    sampleDbId: Optional[str] = None
    variantSetDbIds: Optional[List[str]] = None
    additionalInfo: Optional[Dict[str, Any]] = None

class CallSetCreate(CallSetBase):
    callSetName: str
    variantSetDbIds: List[str]

class CallSetUpdate(CallSetBase):
    pass

class CallSetResponse(CallSetBase):
    callSetDbId: str
    created: Optional[str] = None
    updated: Optional[str] = None

    class Config:
        from_attributes = True

# --- Call Schemas ---

class CallBase(BaseModel):
    genotype: Optional[Dict[str, Any]] = None
    genotypeValue: Optional[str] = None
    genotypeLikelihood: Optional[List[float]] = None
    phaseSet: Optional[str] = None
    additionalInfo: Optional[Dict[str, Any]] = None

class CallCreate(CallBase):
    callSetDbId: str
    variantDbId: str

class CallUpdate(CallBase):
    pass

class CallResponse(CallBase):
    callDbId: Optional[str] = None
# --- Responses ---

class CallListResponse(BaseModel):
    metadata: Dict[str, Any]
    result: Dict[str, List[CallResponse]]

    class Config:
         from_attributes = True

# ==========================================
# Genome Map Schemas
# ==========================================

class GenomeMapBase(BaseModel):
    map_name: str = Field(..., alias="mapName", description="The human readable name of this map")
    map_pui: Optional[str] = Field(None, alias="mapPUI", description="The DOI or other permanent identifier for this map")
    common_crop_name: Optional[str] = Field(None, alias="commonCropName", description="The common name of the crop")
    type: Optional[str] = Field(None, description="Type of map (e.g., Genetic, Physical)")
    unit: Optional[str] = Field(None, description="The unit used for positions on this map (e.g., cM, bp)")
    scientific_name: Optional[str] = Field(None, alias="scientificName", description="The scientific name of the organism")
    published_date: Optional[str] = Field(None, alias="publishedDate", description="The date this map was published")
    comments: Optional[str] = Field(None, description="Additional comments")
    documentation_url: Optional[str] = Field(None, alias="documentationURL", description="A URL to the documentation of this map")
    additional_info: Optional[Dict[str, Any]] = Field(None, alias="additionalInfo", description="Additional arbitrary info")

    model_config = ConfigDict(populate_by_name=True)

class GenomeMapCreate(GenomeMapBase):
    pass

class GenomeMapUpdate(BaseModel):
    map_name: Optional[str] = Field(None, alias="mapName")
    map_pui: Optional[str] = Field(None, alias="mapPUI")
    common_crop_name: Optional[str] = Field(None, alias="commonCropName")
    type: Optional[str] = Field(None)
    unit: Optional[str] = Field(None)
    scientific_name: Optional[str] = Field(None, alias="scientificName")
    published_date: Optional[str] = Field(None, alias="publishedDate")
    comments: Optional[str] = Field(None)
    documentation_url: Optional[str] = Field(None, alias="documentationURL")
    additional_info: Optional[Dict[str, Any]] = Field(None, alias="additionalInfo")

    model_config = ConfigDict(populate_by_name=True)

class GenomeMap(GenomeMapBase):
    map_db_id: str = Field(..., alias="mapDbId", description="The unique identifier for this map")
    linkage_group_count: Optional[int] = Field(0, alias="linkageGroupCount", description="The number of linkage groups in this map")
    marker_count: Optional[int] = Field(0, alias="markerCount", description="The number of markers in this map")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# ==========================================
# Linkage Group Schemas
# ==========================================

class LinkageGroupBase(BaseModel):
    linkage_group_name: str = Field(..., alias="linkageGroupName", description="The name of the linkage group")
    max_position: Optional[float] = Field(None, alias="maxPosition", description="The maximum position on this linkage group")
    marker_count: Optional[int] = Field(0, alias="markerCount", description="The number of markers on this linkage group")
    additional_info: Optional[Dict[str, Any]] = Field(None, alias="additionalInfo")

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
    marker_db_id: Optional[str] = Field(None, alias="markerDbId")
    marker_name: Optional[str] = Field(None, alias="markerName")
    variant_db_id: Optional[str] = Field(None, alias="variantDbId")
    variant_name: Optional[str] = Field(None, alias="variantName")
    linkage_group_name: str = Field(..., alias="linkageGroupName")
    position: float
    map_db_id: str = Field(..., alias="mapDbId")
    additional_info: Optional[Dict[str, Any]] = Field(None, alias="additionalInfo")

    model_config = ConfigDict(populate_by_name=True)

class MarkerPositionCreate(MarkerPositionBase):
    pass

class MarkerPosition(MarkerPositionBase):
    marker_position_db_id: str = Field(..., alias="markerPositionDbId")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
