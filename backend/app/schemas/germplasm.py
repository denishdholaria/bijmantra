from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class CrossBase(BaseModel):
    crossName: Optional[str] = None
    crossType: Optional[str] = None
    crossingProjectDbId: Optional[str] = None
    crossingProjectName: Optional[str] = None
    parent1DbId: Optional[str] = None
    parent1Name: Optional[str] = None
    parent1Type: Optional[str] = None
    parent2DbId: Optional[str] = None
    parent2Name: Optional[str] = None
    parent2Type: Optional[str] = None
    pollinationTimeStamp: Optional[str] = None
    plannedCrossDbId: Optional[str] = None
    crossingYear: Optional[int] = None
    crossStatus: Optional[str] = None
    additionalInfo: Optional[Dict[str, Any]] = None
    externalReferences: Optional[List[Dict[str, Any]]] = None

class CrossCreate(CrossBase):
    crossName: str

class CrossUpdate(CrossBase):
    crossDbId: str

class Cross(CrossBase):
    crossDbId: str

    model_config = ConfigDict(from_attributes=True)

class CrossStats(BaseModel):
    totalCount: int
    thisSeasonCount: int
    successfulCount: int
    pendingCount: int
