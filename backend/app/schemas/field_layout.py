from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class StudyInfo(BaseModel):
    studyDbId: str
    studyName: str
    rows: int = 0
    cols: int = 0
    programDbId: Optional[str] = None
    locationDbId: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None

class Plot(BaseModel):
    plotNumber: str
    row: int
    col: int
    germplasmName: Optional[str] = None
    germplasmDbId: Optional[str] = None
    blockNumber: Optional[int] = None
    replicate: Optional[int] = None
    entryType: Optional[str] = None
    observationUnitDbId: Optional[str] = None

class FieldLayoutSummary(BaseModel):
    total_plots: int
    check_plots: int
    test_plots: int
    unique_germplasm: int
    blocks: int
    replicates: int

class FieldLayoutResponse(BaseModel):
    study: StudyInfo
    plots: List[Plot]
    summary: FieldLayoutSummary

class GermplasmRef(BaseModel):
    germplasmDbId: str
    germplasmName: str

class GermplasmListResponse(BaseModel):
    data: List[GermplasmRef]

class LayoutGenerationResponse(BaseModel):
    message: str
    study_id: str
    design: str
    blocks: int
    replicates: int
    total_plots: int
    note: Optional[str] = None

class ExportResponse(BaseModel):
    message: str
    study_id: str
    format: str
    download_url: Optional[str] = None
    note: Optional[str] = None
