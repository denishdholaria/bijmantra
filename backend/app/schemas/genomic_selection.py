from typing import List, Optional
from pydantic import BaseModel, Field

class GMatrixRequest(BaseModel):
    markers: List[List[int]] = Field(..., description="Genotype matrix (individuals x markers), values 0, 1, 2")
    ploidy: int = Field(2, description="Ploidy level (default 2 for diploid)")

class GMatrixResponse(BaseModel):
    matrix: List[List[float]] = Field(..., description="Genomic Relationship Matrix (G)")
    mean_diagonal: float = Field(..., description="Mean of diagonal elements (should be close to 1 + inbreeding)")
    n_markers_used: int = Field(..., description="Number of markers used in calculation")

class GBLUPRequest(BaseModel):
    phenotypes: List[float] = Field(..., description="Phenotype values for individuals")
    g_matrix: List[List[float]] = Field(..., description="Genomic Relationship Matrix (G)")
    heritability: float = Field(..., ge=0.01, le=0.99, description="Heritability (h^2)")

class GBLUPResponse(BaseModel):
    gebv: List[float] = Field(..., description="Genomic Estimated Breeding Values")
    reliability: List[float] = Field(..., description="Reliability of GEBVs")
    genetic_variance: float = Field(..., description="Estimated genetic variance")
    error_variance: float = Field(..., description="Estimated error variance")
    mean: float = Field(..., description="Population mean")
