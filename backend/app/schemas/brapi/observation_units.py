from typing import Any

from pydantic import BaseModel, ConfigDict


class ObservationUnitBase(BaseModel):
    observationUnitName: str
    observationUnitPUI: str | None = None
    studyDbId: str | None = None
    germplasmDbId: str | None = None
    germplasmName: str | None = None
    crossDbId: str | None = None
    seedLotDbId: str | None = None
    observationLevel: str | None = None
    observationLevelCode: str | None = None
    observationLevelOrder: int | None = None
    positionCoordinateX: str | None = None
    positionCoordinateXType: str | None = None
    positionCoordinateY: str | None = None
    positionCoordinateYType: str | None = None
    entryType: str | None = None
    treatments: list[dict[str, Any]] | None = None

class ObservationUnitCreate(ObservationUnitBase):
    pass

class ObservationUnitUpdate(BaseModel):
    observationUnitDbId: str | None = None
    observationUnitName: str | None = None
    observationLevel: str | None = None
    positionCoordinateX: str | None = None
    positionCoordinateY: str | None = None
    treatments: list[dict[str, Any]] | None = None

class ObservationUnitResponse(ObservationUnitBase):
    observationUnitDbId: str
    studyName: str | None = None
    geoCoordinates: dict[str, Any] | None = None
    additionalInfo: dict[str, Any] | None = None
    externalReferences: list[dict[str, Any]] | None = None

    model_config = ConfigDict(from_attributes=True)
