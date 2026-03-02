

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field


router = APIRouter(prefix="/agronomy", tags=["Agronomy"])

# Crop Nutrient Requirements (kg/ha for 1 ton yield)
# Source: FertilizerCalculator.tsx
CROP_REQUIREMENTS: dict[str, dict[str, float]] = {
    "wheat": {"N": 120, "P": 60, "K": 40},
    "rice": {"N": 100, "P": 50, "K": 50},
    "maize": {"N": 150, "P": 75, "K": 60},
    "soybean": {"N": 30, "P": 60, "K": 40},
    "cotton": {"N": 120, "P": 60, "K": 60},
}

# Fertilizer Prices (INR per 50kg bag)
# Source: FertilizerCalculator.tsx (in a real app, this should come from a DB or external API)
FERTILIZER_PRICES = {
    "urea": 350.0,
    "dap": 1350.0,
    "mop": 850.0,
}

class FertilizerRequest(BaseModel):
    crop: str = Field(..., description="Crop name (e.g., wheat, rice)")
    area: float = Field(..., gt=0, description="Field area in hectares")
    target_yield: float = Field(..., gt=0, description="Target yield in tonnes per hectare")
    soil_n: float = Field(..., ge=0, description="Soil Nitrogen (ppm)")
    soil_p: float = Field(..., ge=0, description="Soil Phosphorus (ppm)")
    soil_k: float = Field(..., ge=0, description="Soil Potassium (ppm)")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "crop": "wheat",
                    "area": 2.5,
                    "target_yield": 5.0,
                    "soil_n": 120.0,
                    "soil_p": 20.0,
                    "soil_k": 150.0,
                }
            ]
        }
    )

class FertilizerResponse(BaseModel):
    urea: float = Field(..., description="Urea required in kg")
    dap: float = Field(..., description="DAP required in kg")
    mop: float = Field(..., description="MOP required in kg")
    nitrogen_needed: float = Field(..., description="Total Nitrogen needed in kg")
    phosphorus_needed: float = Field(..., description="Total Phosphorus needed in kg")
    potassium_needed: float = Field(..., description="Total Potassium needed in kg")
    total_cost: float = Field(..., description="Estimated cost in INR")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "urea": 163.0,
                    "dap": 230.0,
                    "mop": 133.0,
                    "nitrogen_needed": 75.0,
                    "phosphorus_needed": 105.8,
                    "potassium_needed": 80.0,
                    "total_cost": 9611.0,
                }
            ]
        }
    )

@router.post(
    "/fertilizer/calculate",
    response_model=FertilizerResponse,
    summary="Calculate Fertilizer Requirements",
    description="Calculate the required amount of Urea, DAP, and MOP fertilizers based on crop type, field area, target yield, and soil test results.",
    responses={
        200: {
            "description": "Successful calculation of fertilizer requirements.",
            "content": {
                "application/json": {
                    "example": {
                        "urea": 163.0,
                        "dap": 230.0,
                        "mop": 133.0,
                        "nitrogen_needed": 75.0,
                        "phosphorus_needed": 105.8,
                        "potassium_needed": 80.0,
                        "total_cost": 9611.0,
                    }
                }
            },
        },
        400: {
            "description": "Invalid input, such as unsupported crop type.",
            "content": {
                "application/json": {
                    "example": {"detail": "Crop 'potato' not supported. Supported: wheat, rice, maize, soybean, cotton"}
                }
            },
        },
    },
)
async def calculate_fertilizer(request: FertilizerRequest):
    """
    Calculate fertilizer requirements based on crop, area, target yield, and soil test results.

    The calculation uses standard crop nutrient requirements and subtracts available soil nutrients
    to determine the deficit. It then converts the deficit into commercial fertilizer quantities
    (Urea, DAP, MOP) and estimates the cost.

    **Note:** This is a simplified calculator intended for quick estimates. For precise recommendations,
    please use the full `Fertilizer Recommendation` module which accounts for previous crops, manure, etc.
    """
    crop_req = CROP_REQUIREMENTS.get(request.crop.lower())
    if not crop_req:
         # Fallback to general cereal if crop not found, or raise error
         # For now, let's raise error to be explicit
         raise HTTPException(status_code=400, detail=f"Crop '{request.crop}' not supported. Supported: {', '.join(CROP_REQUIREMENTS.keys())}")

    # Adjust for target yield (base is 4 t/ha in the original code, but let's assume the requirements are per hectare for a specific base yield)
    # The frontend code: const yieldFactor = targetYield / 4;
    # cropRequirements values seem to be for 4 t/ha based on that logic.
    # Logic: req.N * (targetYield / 4)
    yield_factor = request.target_yield / 4.0

    # Calculate nutrient requirements minus soil supply (simple subtraction model)
    # Note: Soil test ppm to kg/ha conversion factors used in frontend:
    # P: soilP * 2.29 (approx ppm P to kg P2O5/ha?) - Wait, P ppm * 2.29 converts P to P2O5?
    # Actually P (elemental) -> P2O5 is * 2.29.
    # Usually ppm * 2 (depth factor) = kg/ha.
    # Let's stick to the frontend logic to maintain parity for now.

    n_needed = max(0.0, (crop_req["N"] * yield_factor) - request.soil_n)
    p_needed = max(0.0, (crop_req["P"] * yield_factor) - (request.soil_p * 2.29))
    k_needed = max(0.0, (crop_req["K"] * yield_factor) - (request.soil_k * 0.12)) # Frontend had 0.12? That seems low for K ppm -> K2O kg/ha.
    # Frontend: (req.K * yieldFactor) - (soilK * 0.12)
    # Let's trust the frontend logic for this specific port.

    # Calculate fertilizer amounts (kg)
    # Urea is 46% N
    urea = (n_needed / 0.46) * request.area if n_needed > 0 else 0

    # DAP is 46% P2O5 (and 18% N, but frontend calculation treats them independently for simplicity or specific logic)
    # Frontend: const dap = (pNeeded / 0.46) * area
    # Note: Using DAP for P also adds N. The frontend simple calculator ignores this N credit.
    # We will replicate frontend logic exactly for "Phase 8 Validation".
    dap = (p_needed / 0.46) * request.area if p_needed > 0 else 0

    # MOP is 60% K2O
    mop = (k_needed / 0.60) * request.area if k_needed > 0 else 0

    # Calculate cost
    total_cost = (
        (urea / 50.0) * FERTILIZER_PRICES["urea"] +
        (dap / 50.0) * FERTILIZER_PRICES["dap"] +
        (mop / 50.0) * FERTILIZER_PRICES["mop"]
    )

    return FertilizerResponse(
        urea=round(urea),
        dap=round(dap),
        mop=round(mop),
        nitrogen_needed=round(n_needed * request.area, 2),
        phosphorus_needed=round(p_needed * request.area, 2),
        potassium_needed=round(k_needed * request.area, 2),
        total_cost=round(total_cost)
    )

@router.get(
    "/fertilizer/crops",
    summary="Get Supported Crops",
    description="Retrieve a list of crops supported by the fertilizer calculator.",
    responses={
        200: {
            "description": "List of supported crops.",
            "content": {
                "application/json": {
                    "example": {"crops": ["wheat", "rice", "maize", "soybean", "cotton"]}
                }
            },
        }
    }
)
async def get_supported_crops():
    """
    List supported crops for fertilizer calculation.

    These are the crops for which the system has nutrient requirement data defined.
    """
    return {"crops": list(CROP_REQUIREMENTS.keys())}
