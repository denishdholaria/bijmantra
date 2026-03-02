from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.biosimulation import CropModel
from app.models.core import User
from app.services.biosimulation import biosimulation_service


router = APIRouter(prefix="/biosimulation", tags=["Biosimulation"], dependencies=[Depends(deps.get_current_active_user)])


class SimulationRequest(BaseModel):
    crop_model_id: int
    location_id: int
    start_date: datetime
    daily_weather_data: list[dict] # [{t_max, t_min, par...}]


class SimulationResponse(BaseModel):
    run_id: int
    predicted_flowering_date: datetime | None
    predicted_maturity_date: datetime | None
    predicted_yield: float | None
    status: str


@router.post("/run", response_model=SimulationResponse)
async def run_simulation(
    request: SimulationRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Execute a crop growth simulation run.
    """
    try:
        run = await biosimulation_service.run_simulation(
            db=db,
            organization_id=current_user.organization_id,
            crop_model_id=request.crop_model_id,
            location_id=request.location_id,
            start_date=request.start_date,
            daily_weather_data=request.daily_weather_data
        )

        return {
            "run_id": run.id,
            "predicted_flowering_date": run.predicted_flowering_date,
            "predicted_maturity_date": run.predicted_maturity_date,
            "predicted_yield": run.predicted_yield,
            "status": run.status
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CropModelCreate(BaseModel):
    name: str
    crop_name: str
    description: str | None = None
    base_temp: float = 10.0
    gdd_flowering: float = 800.0
    gdd_maturity: float = 1600.0
    rue: float = 1.5


@router.post("/models", response_model=dict)
async def create_crop_model(
    model: CropModelCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Create a new Crop Model definition.
    """
    db_model = CropModel(
        organization_id=current_user.organization_id,
        name=model.name,
        crop_name=model.crop_name,
        description=model.description,
        base_temp=model.base_temp,
        gdd_flowering=model.gdd_flowering,
        gdd_maturity=model.gdd_maturity,
        rue=model.rue
    )
    db.add(db_model)
    await db.commit()
    await db.refresh(db_model)
    return {"id": db_model.id, "name": db_model.name}


@router.get("/models", response_model=list[dict])
async def get_crop_models(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 100,
):
    """
    List available Crop Models.
    """
    stmt = select(CropModel).where(
        CropModel.organization_id == current_user.organization_id
    ).offset(skip).limit(limit)
    result = await db.execute(stmt)
    models = result.scalars().all()
    return [{"id": m.id, "name": m.name, "crop_name": m.crop_name} for m in models]
