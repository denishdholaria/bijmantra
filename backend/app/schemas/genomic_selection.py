from pydantic import BaseModel, Field


class GMatrixRequest(BaseModel):
    markers: list[list[int]] = Field(..., description="Genotype matrix (individuals x markers), values 0, 1, 2")
    ploidy: int = Field(2, description="Ploidy level (default 2 for diploid)")

class GMatrixResponse(BaseModel):
    matrix: list[list[float]] = Field(..., description="Genomic Relationship Matrix (G)")
    mean_diagonal: float = Field(..., description="Mean of diagonal elements (should be close to 1 + inbreeding)")
    n_markers_used: int = Field(..., description="Number of markers used in calculation")

class GBLUPRequest(BaseModel):
    phenotypes: list[float] = Field(..., description="Phenotype values for individuals")
    g_matrix: list[list[float]] = Field(..., description="Genomic Relationship Matrix (G)")
    heritability: float = Field(..., ge=0.01, le=0.99, description="Heritability (h^2)")

class GBLUPResponse(BaseModel):
    gebv: list[float] = Field(..., description="Genomic Estimated Breeding Values")
    reliability: list[float] = Field(..., description="Reliability of GEBVs")
    genetic_variance: float = Field(..., description="Estimated genetic variance")
    error_variance: float = Field(..., description="Estimated error variance")
    mean: float = Field(..., description="Population mean")
