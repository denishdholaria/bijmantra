"""
Calculators API
Centralized logic for agronomic and breeding calculations.
Implements specific business logic moved from frontend to backend.
"""

from typing import Any

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from scipy.interpolate import griddata

from app.services.economics import economics_service
from app.services.gdd_calculator_service import gdd_calculator_service


router = APIRouter(prefix="/calculators", tags=["Calculators"])

# ============================================================================
# Cost / ROI Calculator
# ============================================================================

class ROICalculationRequest(BaseModel):
    total_cost: float
    expected_revenue: float
    initial_investment: float | None = None
    cash_flows: list[float] | None = None
    discount_rate: float = 0.05

class ROICalculationResult(BaseModel):
    roi_percent: float
    net_present_value: float | None = None
    benefit_cost_ratio: float

@router.post("/cost/roi", response_model=ROICalculationResult)
async def calculate_roi(request: ROICalculationRequest):
    """
    Calculate ROI and NPV. Wraps economics_service.
    """
    roi = economics_service.calculate_roi(request.total_cost, request.expected_revenue)

    npv = None
    if request.initial_investment is not None and request.cash_flows:
        npv = economics_service.calculate_npv(
            request.initial_investment,
            request.cash_flows,
            request.discount_rate
        )

    return {
        "roi_percent": roi,
        "net_present_value": npv,
        "benefit_cost_ratio": (request.expected_revenue / request.total_cost) if request.total_cost > 0 else 0
    }

# ============================================================================
# Fertilizer Calculator
# ============================================================================

class FertilizerRequest(BaseModel):
    crop: str
    area: float = Field(..., gt=0, description="Area in hectares")
    target_yield: float = Field(..., gt=0, description="Target yield in t/ha")
    soil_n: float = Field(..., ge=0, description="Soil Nitrogen (ppm)")
    soil_p: float = Field(..., ge=0, description="Soil Phosphorus (ppm)")
    soil_k: float = Field(..., ge=0, description="Soil Potassium (ppm)")

class FertilizerResult(BaseModel):
    nitrogen_needed: float
    phosphorus_needed: float
    potassium_needed: float
    urea: float
    dap: float
    mop: float
    total_cost: float

CROP_REQUIREMENTS = {
    "wheat": {"N": 120, "P": 60, "K": 40},
    "rice": {"N": 100, "P": 50, "K": 50},
    "maize": {"N": 150, "P": 75, "K": 60},
    "soybean": {"N": 30, "P": 60, "K": 40},
    "cotton": {"N": 120, "P": 60, "K": 60},
}

FERTILIZER_PRICES = {
    "urea": 350,  # per 50kg bag
    "dap": 1350,
    "mop": 850,
}

@router.post("/fertilizer", response_model=FertilizerResult)
async def calculate_fertilizer(request: FertilizerRequest):
    """
    Calculate fertilizer requirements based on crop, area, target yield, and soil test.
    """
    req = CROP_REQUIREMENTS.get(request.crop.lower())
    if not req:
        # Default fallback or error
        req = {"N": 100, "P": 50, "K": 50}

    # Adjust for target yield (base is 4 t/ha)
    yield_factor = request.target_yield / 4.0

    # Calculate nutrient requirements minus soil supply
    # Soil N (ppm) is roughly kg/ha for topsoil (simplified logic from frontend parity)
    # Frontend logic: soilP * 2.29 (P -> P2O5), soilK * 0.12 (K -> K2O? No, unit conversion likely)
    # Replicating frontend logic exactly for parity:
    n_needed = max(0, (req["N"] * yield_factor) - request.soil_n)
    p_needed = max(0, (req["P"] * yield_factor) - (request.soil_p * 2.29))
    k_needed = max(0, (req["K"] * yield_factor) - (request.soil_k * 0.12)) # Preserving 0.12 factor from frontend

    # Calculate fertilizer amounts (kg)
    # Urea (46% N)
    urea = (n_needed / 0.46) * request.area
    # DAP (46% P2O5)
    dap = (p_needed / 0.46) * request.area
    # MOP (60% K2O)
    mop = (k_needed / 0.60) * request.area

    # Calculate cost
    total_cost = (urea / 50) * FERTILIZER_PRICES["urea"] + \
                 (dap / 50) * FERTILIZER_PRICES["dap"] + \
                 (mop / 50) * FERTILIZER_PRICES["mop"]

    return {
        "nitrogen_needed": round(n_needed * request.area, 2),
        "phosphorus_needed": round(p_needed * request.area, 2),
        "potassium_needed": round(k_needed * request.area, 2),
        "urea": round(urea, 0),
        "dap": round(dap, 0),
        "mop": round(mop, 0),
        "total_cost": round(total_cost, 0)
    }

# ============================================================================
# Trait Calculator
# ============================================================================

class TraitRequest(BaseModel):
    formula_id: str
    inputs: list[float]

class TraitResult(BaseModel):
    result: float
    unit: str

@router.post("/traits", response_model=TraitResult)
async def calculate_trait(request: TraitRequest):
    """
    Calculate derived traits using specific formulas.
    """
    fid = request.formula_id
    inputs = request.inputs
    res = 0.0
    unit = ""

    try:
        if fid == 'harvest-index':
            # HI = (Grain Yield / Total Biomass) * 100
            gy, tb = inputs[0], inputs[1]
            res = (gy / tb * 100) if tb > 0 else 0
            unit = "%"

        elif fid == 'yield-per-ha':
            # Yield (t/ha) = (Plot Yield kg * 10000) / (Plot Area m2 * 1000)
            py, pa = inputs[0], inputs[1]
            res = (py * 10000) / (pa * 1000) if pa > 0 else 0
            unit = "t/ha"

        elif fid == 'thousand-grain-weight':
            # TGW = (Sample Weight g / Grain Count) * 1000
            sw, gc = inputs[0], inputs[1]
            res = (sw / gc * 1000) if gc > 0 else 0
            unit = "g"

        elif fid == 'grain-moisture':
            # Moisture = ((Wet - Dry) / Wet) * 100
            wet, dry = inputs[0], inputs[1]
            res = ((wet - dry) / wet * 100) if wet > 0 else 0
            unit = "%"

        elif fid == 'plant-density':
            # Density = (Plant Count / Plot Area m2) * 10000
            pc, pa = inputs[0], inputs[1]
            res = (pc / pa * 10000) if pa > 0 else 0
            unit = "plants/ha"

        elif fid == 'lodging-score':
            # Score = (Lodged Area % / 100) * Severity (1-5)
            la, sev = inputs[0], inputs[1]
            res = (la / 100) * sev
            unit = "score"

        elif fid == 'relative-yield':
            # RY = (Entry Yield / Check Yield) * 100
            ey, cy = inputs[0], inputs[1]
            res = (ey / cy * 100) if cy > 0 else 0
            unit = "%"

        elif fid == 'protein-yield':
            # Protein Yield = Grain Yield * (Protein % / 100)
            gy, pc = inputs[0], inputs[1]
            res = gy * (pc / 100)
            unit = "t/ha"

        else:
            raise HTTPException(status_code=400, detail=f"Unknown formula ID: {fid}")

    except IndexError:
        raise HTTPException(status_code=422, detail="Insufficient inputs provided for formula")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"result": round(res, 2), "unit": unit}

# ============================================================================
# Yield Interpolation (IDW)
# ============================================================================

class PointData(BaseModel):
    x: float
    y: float
    value: float

class InterpolationRequest(BaseModel):
    points: list[PointData]
    resolution: int = 50  # Grid resolution (50x50)
    method: str = "linear" # linear, cubic, nearest

class InterpolationResult(BaseModel):
    grid_x: list[list[float]]
    grid_y: list[list[float]]
    grid_z: list[list[float]] # Interpolated values
    min_val: float
    max_val: float

@router.post("/yield/interpolation", response_model=InterpolationResult)
async def interpolate_yield(request: InterpolationRequest):
    """
    Interpolate spatial data (e.g. yield map) to a grid using scipy.interpolate.griddata.
    """
    if len(request.points) < 3:
        raise HTTPException(status_code=422, detail="At least 3 points required for interpolation")

    points = np.array([[p.x, p.y] for p in request.points])
    values = np.array([p.value for p in request.points])

    # Create grid
    min_x, max_x = points[:, 0].min(), points[:, 0].max()
    min_y, max_y = points[:, 1].min(), points[:, 1].max()

    grid_x, grid_y = np.mgrid[min_x:max_x:complex(0, request.resolution),
                              min_y:max_y:complex(0, request.resolution)]

    # Interpolate
    try:
        grid_z = griddata(points, values, (grid_x, grid_y), method=request.method)

        # Replace NaNs with nearest (extrapolation for convex hull edges)
        if np.isnan(grid_z).any():
             grid_z_nearest = griddata(points, values, (grid_x, grid_y), method='nearest')
             grid_z[np.isnan(grid_z)] = grid_z_nearest[np.isnan(grid_z)]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Interpolation failed: {str(e)}")

    return {
        "grid_x": grid_x.tolist(),
        "grid_y": grid_y.tolist(),
        "grid_z": grid_z.tolist(),
        "min_val": float(np.nanmin(grid_z)),
        "max_val": float(np.nanmax(grid_z))
    }

# ============================================================================
# Growth Calculator (GDD)
# ============================================================================

class GrowthPredictionRequest(BaseModel):
    crop: str
    planting_date: str
    current_gdd: float

class GrowthPredictionResult(BaseModel):
    current_stage: str
    next_stage: str | None
    gdd_to_next: float | None
    days_to_next: int | None
    maturity_date: str | None
    progress: float

@router.post("/growth", response_model=GrowthPredictionResult)
async def predict_growth(request: GrowthPredictionRequest):
    """
    Predict crop growth stage based on GDD.
    """
    from datetime import date
    try:
        p_date = date.fromisoformat(request.planting_date)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid planting date format (YYYY-MM-DD)")

    prediction = gdd_calculator_service.predict_growth_stages(
        crop_name=request.crop,
        cumulative_gdd=request.current_gdd,
        planting_date=p_date
    )

    return {
        "current_stage": prediction.current_stage,
        "next_stage": prediction.next_stage,
        "gdd_to_next": prediction.gdd_to_next_stage,
        "days_to_next": prediction.days_to_next_stage,
        "maturity_date": prediction.predicted_maturity_date.isoformat() if prediction.predicted_maturity_date else None,
        "progress": round((request.current_gdd / prediction.maturity_gdd) * 100, 1) if prediction.maturity_gdd > 0 else 0
    }

# ============================================================================
# Allocation Calculator (Simple What-If)
# ============================================================================

class AllocationScenarioRequest(BaseModel):
    total_budget: float
    categories: list[dict[str, Any]] # [{"name": "Labor", "weight": 0.4}, ...]

class AllocationResult(BaseModel):
    allocations: list[dict[str, Any]]
    remaining: float

@router.post("/allocation", response_model=AllocationResult)
async def calculate_allocation(request: AllocationScenarioRequest):
    """
    Calculate budget allocation based on weights or fixed amounts.
    """
    total = request.total_budget
    allocations = []
    allocated_sum = 0

    # First pass: fixed amounts
    for cat in request.categories:
        if "amount" in cat:
            amount = float(cat["amount"])
            allocations.append({"name": cat["name"], "amount": amount, "percent": round(amount/total*100, 1)})
            allocated_sum += amount

    remaining = total - allocated_sum

    # Second pass: weights for remaining
    weight_sum = sum(float(cat.get("weight", 0)) for cat in request.categories if "amount" not in cat)

    for cat in request.categories:
        if "amount" not in cat:
            weight = float(cat.get("weight", 0))
            if weight_sum > 0:
                amount = (weight / weight_sum) * remaining
                allocations.append({"name": cat["name"], "amount": round(amount, 2), "percent": round(amount/total*100, 1)})
            else:
                allocations.append({"name": cat["name"], "amount": 0, "percent": 0})

    return {
        "allocations": allocations,
        "remaining": max(0, total - sum(a["amount"] for a in allocations))
    }
