from typing import Any

from pydantic import BaseModel, ConfigDict


class CrossBase(BaseModel):
    crossName: str | None = None
    crossType: str | None = None
    crossingProjectDbId: str | None = None
    crossingProjectName: str | None = None
    parent1DbId: str | None = None
    parent1Name: str | None = None
    parent1Type: str | None = None
    parent2DbId: str | None = None
    parent2Name: str | None = None
    parent2Type: str | None = None
    pollinationTimeStamp: str | None = None
    plannedCrossDbId: str | None = None
    crossingYear: int | None = None
    crossStatus: str | None = None
    additionalInfo: dict[str, Any] | None = None
    externalReferences: list[dict[str, Any]] | None = None

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
