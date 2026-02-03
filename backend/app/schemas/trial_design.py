from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

class RCBDRequest(BaseModel):
    """Request for RCBD design"""
    genotypes: List[str] = Field(..., min_length=2, description="List of genotype names")
    n_blocks: int = Field(..., ge=2, le=20, description="Number of blocks (replicates)")
    field_rows: Optional[int] = Field(None, description="Number of field rows for layout")
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "genotypes": ["G1", "G2", "G3", "G4", "G5"],
            "n_blocks": 3,
            "seed": 42
        }
    })


class AlphaLatticeRequest(BaseModel):
    """Request for Alpha-Lattice design"""
    genotypes: List[str] = Field(..., min_length=4, description="List of genotype names")
    n_blocks: int = Field(..., ge=2, le=10, description="Number of super-blocks (replicates)")
    block_size: int = Field(..., ge=2, le=50, description="Plots per incomplete block")
    seed: Optional[int] = Field(None, description="Random seed")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "genotypes": ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9"],
            "n_blocks": 2,
            "block_size": 3,
            "seed": 42
        }
    })


class AugmentedRequest(BaseModel):
    """Request for Augmented design"""
    test_genotypes: List[str] = Field(..., min_length=1, description="Unreplicated test entries")
    check_genotypes: List[str] = Field(..., min_length=1, description="Replicated check varieties")
    n_blocks: int = Field(..., ge=2, le=20, description="Number of blocks")
    checks_per_block: int = Field(1, ge=1, le=5, description="Check plots per block")
    seed: Optional[int] = Field(None, description="Random seed")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "test_genotypes": ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"],
            "check_genotypes": ["Check1", "Check2"],
            "n_blocks": 4,
            "checks_per_block": 1,
            "seed": 42
        }
    })


class SplitPlotRequest(BaseModel):
    """Request for Split-Plot design"""
    main_treatments: List[str] = Field(..., min_length=2, description="Main plot treatments")
    sub_treatments: List[str] = Field(..., min_length=2, description="Subplot treatments")
    n_blocks: int = Field(..., ge=2, le=10, description="Number of blocks")
    seed: Optional[int] = Field(None, description="Random seed")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "main_treatments": ["Irrigated", "Rainfed"],
            "sub_treatments": ["G1", "G2", "G3", "G4"],
            "n_blocks": 3,
            "seed": 42
        }
    })


class CRDRequest(BaseModel):
    """Request for CRD design"""
    genotypes: List[str] = Field(..., min_length=2, description="List of genotype names")
    n_reps: int = Field(..., ge=2, le=20, description="Replications per genotype")
    seed: Optional[int] = Field(None, description="Random seed")


class FieldMapRequest(BaseModel):
    """Request for field map generation"""
    design_type: str = Field(..., description="Design type: rcbd, alpha-lattice, augmented, split-plot, crd")
    genotypes: List[str] = Field(..., description="Genotype list")
    n_blocks: int = Field(3, description="Number of blocks")
    plot_width: float = Field(1.5, gt=0, description="Plot width in meters")
    plot_length: float = Field(5.0, gt=0, description="Plot length in meters")
    alley_width: float = Field(0.5, ge=0, description="Alley width in meters")
    seed: Optional[int] = Field(None, description="Random seed")
