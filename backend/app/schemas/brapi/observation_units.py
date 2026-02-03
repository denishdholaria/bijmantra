from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

class ObservationUnitBase(BaseModel):
    observationUnitName: str
    observationUnitPUI: Optional[str] = None
    studyDbId: Optional[str] = None
    germplasmDbId: Optional[str] = None
    germplasmName: Optional[str] = None
    crossDbId: Optional[str] = None
    seedLotDbId: Optional[str] = None
    observationLevel: Optional[str] = None
    observationLevelCode: Optional[str] = None
    observationLevelOrder: Optional[int] = None
    positionCoordinateX: Optional[str] = None
    positionCoordinateXType: Optional[str] = None
    positionCoordinateY: Optional[str] = None
    positionCoordinateYType: Optional[str] = None
    entryType: Optional[str] = None
    treatments: Optional[List[Dict[str, Any]]] = None

class ObservationUnitCreate(ObservationUnitBase):
    pass

class ObservationUnitUpdate(BaseModel):
    observationUnitDbId: Optional[str] = None
    observationUnitName: Optional[str] = None
    observationLevel: Optional[str] = None
    positionCoordinateX: Optional[str] = None
    positionCoordinateY: Optional[str] = None
    treatments: Optional[List[Dict[str, Any]]] = None

class ObservationUnitResponse(ObservationUnitBase):
    observationUnitDbId: str
    studyName: Optional[str] = None
    geoCoordinates: Optional[Dict[str, Any]] = None
    additionalInfo: Optional[Dict[str, Any]] = None
    externalReferences: Optional[List[Dict[str, Any]]] = None

    model_config = ConfigDict(from_attributes=True)
