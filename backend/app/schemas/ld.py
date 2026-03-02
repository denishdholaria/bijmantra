
from pydantic import BaseModel, Field


class LDCalculateRequest(BaseModel):
    region_id: str | None = Field(None, description="Region ID to filter markers (e.g. Chromosome name)")
    start: int | None = Field(None, description="Start position")
    end: int | None = Field(None, description="End position")
    variant_set_id: str | None = Field(None, description="VariantSet DB ID")
    marker_names: list[str] | None = Field(None, description="List of specific markers to analyze")
    population_id: str | None = Field(None, description="Population ID to filter samples")
    window_size: int | None = Field(100, description="Window size (number of markers) for pairwise calculation")

class LDPair(BaseModel):
    marker1: str
    marker2: str
    distance: int
    r2: float
    d_prime: float | None = None

class LDResult(BaseModel):
    pairs: list[LDPair]
    mean_r2: float
    marker_count: int
    sample_count: int

class LDMatrixRequest(BaseModel):
    region: str
    variant_set_id: str | None = None
    population_id: str | None = None

class LDMatrixResponse(BaseModel):
    markers: list[str]
    matrix: list[list[float]]
    region: str

class LDDecayRequest(BaseModel):
    variant_set_id: str | None = None
    regions: list[str] | None = None
    population_id: str | None = None
    max_distance: int | None = Field(100000, description="Max distance in base pairs")
    bin_size: int | None = Field(1000, description="Bin size for decay aggregation")

class LDDecayPoint(BaseModel):
    distance: int
    mean_r2: float
    pair_count: int

class LDDecayResponse(BaseModel):
    decay_curve: list[LDDecayPoint]
