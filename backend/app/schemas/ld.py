from typing import List, Optional
from pydantic import BaseModel, Field

class LDCalculateRequest(BaseModel):
    region_id: Optional[str] = Field(None, description="Region ID to filter markers (e.g. Chromosome name)")
    start: Optional[int] = Field(None, description="Start position")
    end: Optional[int] = Field(None, description="End position")
    variant_set_id: Optional[str] = Field(None, description="VariantSet DB ID")
    marker_names: Optional[List[str]] = Field(None, description="List of specific markers to analyze")
    population_id: Optional[str] = Field(None, description="Population ID to filter samples")
    window_size: Optional[int] = Field(100, description="Window size (number of markers) for pairwise calculation")

class LDPair(BaseModel):
    marker1: str
    marker2: str
    distance: int
    r2: float
    d_prime: Optional[float] = None

class LDResult(BaseModel):
    pairs: List[LDPair]
    mean_r2: float
    marker_count: int
    sample_count: int

class LDMatrixRequest(BaseModel):
    region: str
    variant_set_id: Optional[str] = None
    population_id: Optional[str] = None

class LDMatrixResponse(BaseModel):
    markers: List[str]
    matrix: List[List[float]]
    region: str

class LDDecayRequest(BaseModel):
    variant_set_id: Optional[str] = None
    regions: Optional[List[str]] = None
    population_id: Optional[str] = None
    max_distance: Optional[int] = Field(100000, description="Max distance in base pairs")
    bin_size: Optional[int] = Field(1000, description="Bin size for decay aggregation")

class LDDecayPoint(BaseModel):
    distance: int
    mean_r2: float
    pair_count: int

class LDDecayResponse(BaseModel):
    decay_curve: List[LDDecayPoint]
