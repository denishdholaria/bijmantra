from pydantic import BaseModel


class StudyInfo(BaseModel):
    studyDbId: str
    studyName: str
    rows: int = 0
    cols: int = 0
    programDbId: str | None = None
    locationDbId: str | None = None
    startDate: str | None = None
    endDate: str | None = None

class Plot(BaseModel):
    plotNumber: str
    row: int
    col: int
    germplasmName: str | None = None
    germplasmDbId: str | None = None
    blockNumber: int | None = None
    replicate: int | None = None
    entryType: str | None = None
    observationUnitDbId: str | None = None

class FieldLayoutSummary(BaseModel):
    total_plots: int
    check_plots: int
    test_plots: int
    unique_germplasm: int
    blocks: int
    replicates: int

class FieldLayoutResponse(BaseModel):
    study: StudyInfo
    plots: list[Plot]
    summary: FieldLayoutSummary

class GermplasmRef(BaseModel):
    germplasmDbId: str
    germplasmName: str

class GermplasmListResponse(BaseModel):
    data: list[GermplasmRef]

class LayoutGenerationResponse(BaseModel):
    message: str
    study_id: str
    design: str
    blocks: int
    replicates: int
    total_plots: int
    note: str | None = None

class ExportResponse(BaseModel):
    message: str
    study_id: str
    format: str
    download_url: str | None = None
    note: str | None = None
