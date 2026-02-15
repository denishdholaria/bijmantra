"""
Trial Design API for Plant Breeding
Experimental design generation and randomization

Endpoints:
- POST /api/v2/trial-design/rcbd - RCBD design
- POST /api/v2/trial-design/alpha-lattice - Alpha-lattice design
- POST /api/v2/trial-design/augmented - Augmented design
- POST /api/v2/trial-design/split-plot - Split-plot design
- POST /api/v2/trial-design/crd - CRD design
- POST /api/v2/trial-design/field-map - Generate field map
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends

from app.services.trial_design import get_trial_design_service
from app.api.deps import get_current_user
from app.schemas.trial_design import (
    RCBDRequest,
    AlphaLatticeRequest,
    AugmentedRequest,
    SplitPlotRequest,
    CRDRequest,
    FieldMapRequest
)

router = APIRouter(prefix="/trial-design", tags=["Trial Design"], dependencies=[Depends(get_current_user)])


# ============================================
# ENDPOINTS
# ============================================

@router.post("/rcbd")
async def generate_rcbd(request: RCBDRequest):
    """
    Generate Randomized Complete Block Design (RCBD)
    
    Most common design for variety trials. Each block contains
    all genotypes in random order. Blocks account for field
    heterogeneity.
    
    Use when:
    - Number of genotypes is manageable (< 20-30)
    - Field has known gradient (blocks perpendicular to gradient)
    - Need to compare all genotypes fairly
    """
    service = get_trial_design_service()
    
    if request.seed is not None:
        service.set_seed(request.seed)
    
    try:
        design = service.rcbd(
            genotypes=request.genotypes,
            n_blocks=request.n_blocks,
            field_rows=request.field_rows,
        )
        
        return {
            "success": True,
            **design.to_dict(),
            "seed": request.seed,
        }
    except Exception as e:
        raise HTTPException(500, f"RCBD generation failed: {str(e)}")


@router.post("/alpha-lattice")
async def generate_alpha_lattice(request: AlphaLatticeRequest):
    """
    Generate Alpha-Lattice (Resolvable Incomplete Block) Design
    
    For large numbers of genotypes where complete blocks are
    impractical. Genotypes are distributed across smaller
    incomplete blocks within each replicate.
    
    Use when:
    - Many genotypes (> 30-50)
    - Field heterogeneity within blocks
    - Need spatial control at smaller scale
    
    Block size should be chosen based on field conditions
    (typically 4-10 plots per incomplete block).
    """
    service = get_trial_design_service()
    
    if request.seed is not None:
        service.set_seed(request.seed)
    
    try:
        design = service.alpha_lattice(
            genotypes=request.genotypes,
            n_blocks=request.n_blocks,
            block_size=request.block_size,
        )
        
        return {
            "success": True,
            **design.to_dict(),
            "block_size": request.block_size,
            "seed": request.seed,
        }
    except Exception as e:
        raise HTTPException(500, f"Alpha-lattice generation failed: {str(e)}")


@router.post("/augmented")
async def generate_augmented(request: AugmentedRequest):
    """
    Generate Augmented Design
    
    Checks are replicated in each block, test genotypes are
    unreplicated. Efficient for early generation testing with
    many lines and limited seed.
    
    Use when:
    - Many test entries (hundreds to thousands)
    - Limited seed available
    - Early generation screening
    - Need to compare to standard checks
    
    Analysis uses check performance to adjust for spatial variation.
    """
    service = get_trial_design_service()
    
    if request.seed is not None:
        service.set_seed(request.seed)
    
    try:
        design = service.augmented_design(
            test_genotypes=request.test_genotypes,
            check_genotypes=request.check_genotypes,
            n_blocks=request.n_blocks,
            checks_per_block=request.checks_per_block,
        )
        
        return {
            "success": True,
            **design.to_dict(),
            "n_test_genotypes": len(request.test_genotypes),
            "n_check_genotypes": len(request.check_genotypes),
            "seed": request.seed,
        }
    except Exception as e:
        raise HTTPException(500, f"Augmented design generation failed: {str(e)}")


@router.post("/split-plot")
async def generate_split_plot(request: SplitPlotRequest):
    """
    Generate Split-Plot Design
    
    Main plots contain main treatments (e.g., irrigation, tillage),
    split into subplots for sub-treatments (e.g., genotypes).
    
    Use when:
    - Two factors with different plot size requirements
    - Main treatment difficult to apply to small plots
    - Interested in interaction between factors
    
    Main plots are randomized within blocks, subplots within main plots.
    """
    service = get_trial_design_service()
    
    if request.seed is not None:
        service.set_seed(request.seed)
    
    try:
        design = service.split_plot(
            main_treatments=request.main_treatments,
            sub_treatments=request.sub_treatments,
            n_blocks=request.n_blocks,
        )
        
        return {
            "success": True,
            **design.to_dict(),
            "n_main_treatments": len(request.main_treatments),
            "n_sub_treatments": len(request.sub_treatments),
            "seed": request.seed,
        }
    except Exception as e:
        raise HTTPException(500, f"Split-plot generation failed: {str(e)}")


@router.post("/crd")
async def generate_crd(request: CRDRequest):
    """
    Generate Completely Randomized Design (CRD)
    
    All plots randomized without blocking. Simplest design
    but assumes homogeneous experimental conditions.
    
    Use when:
    - Experimental conditions are uniform
    - Greenhouse or growth chamber experiments
    - Small number of treatments
    
    Not recommended for field trials with spatial variation.
    """
    service = get_trial_design_service()
    
    if request.seed is not None:
        service.set_seed(request.seed)
    
    try:
        design = service.crd(
            genotypes=request.genotypes,
            n_reps=request.n_reps,
        )
        
        return {
            "success": True,
            **design.to_dict(),
            "n_reps": request.n_reps,
            "seed": request.seed,
        }
    except Exception as e:
        raise HTTPException(500, f"CRD generation failed: {str(e)}")


@router.post("/field-map")
async def generate_field_map(request: FieldMapRequest):
    """
    Generate field map with plot coordinates
    
    Creates a spatial layout with X/Y coordinates for each plot.
    Useful for:
    - Field book generation
    - GPS-based planting
    - Spatial analysis
    - Visualization
    """
    service = get_trial_design_service()
    
    if request.seed is not None:
        service.set_seed(request.seed)
    
    try:
        # Generate the base design
        if request.design_type.lower() == "rcbd":
            design = service.rcbd(request.genotypes, request.n_blocks)
        elif request.design_type.lower() == "crd":
            design = service.crd(request.genotypes, request.n_blocks)
        else:
            design = service.rcbd(request.genotypes, request.n_blocks)
        
        # Generate field map
        field_map = service.generate_field_map(
            design=design,
            plot_width=request.plot_width,
            plot_length=request.plot_length,
            alley_width=request.alley_width,
        )
        
        return {
            "success": True,
            **field_map,
        }
    except Exception as e:
        raise HTTPException(500, f"Field map generation failed: {str(e)}")


@router.get("/designs")
async def list_designs():
    """List available experimental designs"""
    return {
        "designs": [
            {
                "id": "rcbd",
                "name": "Randomized Complete Block Design",
                "abbreviation": "RCBD",
                "use_case": "Standard variety trials with moderate number of entries",
                "advantages": ["Simple analysis", "All comparisons equally precise"],
                "limitations": ["Block size = number of genotypes"],
            },
            {
                "id": "alpha_lattice",
                "name": "Alpha-Lattice Design",
                "abbreviation": "α-lattice",
                "use_case": "Large trials with many genotypes",
                "advantages": ["Smaller blocks", "Better spatial control"],
                "limitations": ["More complex analysis", "Requires software"],
            },
            {
                "id": "augmented",
                "name": "Augmented Design",
                "abbreviation": "Aug",
                "use_case": "Early generation testing with limited seed",
                "advantages": ["Efficient for many entries", "Uses checks for adjustment"],
                "limitations": ["Test entries unreplicated", "Lower precision"],
            },
            {
                "id": "split_plot",
                "name": "Split-Plot Design",
                "abbreviation": "SP",
                "use_case": "Two-factor experiments with different plot sizes",
                "advantages": ["Practical for some treatments", "Tests interactions"],
                "limitations": ["Unequal precision for factors"],
            },
            {
                "id": "crd",
                "name": "Completely Randomized Design",
                "abbreviation": "CRD",
                "use_case": "Uniform conditions (greenhouse, lab)",
                "advantages": ["Simple", "Flexible"],
                "limitations": ["No blocking", "Assumes homogeneity"],
            },
        ]
    }
