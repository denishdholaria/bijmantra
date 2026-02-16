from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.services.economics import economics_service
from app.models.economics import CostBenefitAnalysis
from pydantic import BaseModel

router = APIRouter()

class ROICalculationRequest(BaseModel):
    total_cost: float
    expected_revenue: float
    initial_investment: Optional[float] = None
    cash_flows: Optional[List[float]] = None
    discount_rate: float = 0.05

class ROICalculationResponse(BaseModel):
    roi_percent: float
    net_present_value: Optional[float] = None
    benefit_cost_ratio: float

@router.post("/calculate-roi", response_model=ROICalculationResponse)
async def calculate_roi(
    request: ROICalculationRequest,
):
    """
    Calculate ROI and NPV (Net Present Value) metrics.
    No database storage, calculation only.
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

class CostBenefitCreate(BaseModel):
    organization_id: int
    analysis_name: str
    total_cost: float
    expected_revenue: float
    cash_flows: Optional[List[float]] = None

@router.post("/cost-benefit", response_model=dict)
async def create_cost_benefit_analysis(
    analysis: CostBenefitCreate,
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Create and save a Cost-Benefit Analysis record.
    """
    result = await economics_service.create_cost_benefit_analysis(
        db=db,
        organization_id=analysis.organization_id,
        name=analysis.analysis_name,
        total_cost=analysis.total_cost,
        expected_revenue=analysis.expected_revenue,
        cash_flows=analysis.cash_flows
    )
    return {"id": result.id, "status": "created", "roi": result.roi_percent}
