from pydantic import BaseModel


class ObservationBase(BaseModel):
    observationUnitDbId: str | None = None
    observationVariableDbId: str | None = None
    observationVariableName: str | None = None
    value: str | None = None
    observationTimeStamp: str | None = None
    collector: str | None = None
    studyDbId: str | None = None
    germplasmDbId: str | None = None
    germplasmName: str | None = None
    seasonDbId: str | None = None


class ObservationCreate(ObservationBase):
    pass


class ObservationUpdate(ObservationBase):
    observationDbId: str | None = None
