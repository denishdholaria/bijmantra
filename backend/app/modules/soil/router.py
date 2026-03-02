
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps

from . import schemas, service


router = APIRouter()

# NutrientTest
@router.get("/nutrient-tests", response_model=list[schemas.NutrientTest])
async def read_nutrient_tests(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(deps.get_db)):
    return await service.get_nutrient_tests(db, skip=skip, limit=limit)

@router.post("/nutrient-tests", response_model=schemas.NutrientTest, status_code=201)
async def create_nutrient_test(test: schemas.NutrientTestCreate, db: AsyncSession = Depends(deps.get_db)):
    return await service.create_nutrient_test(db=db, test=test)

# PhysicalProperties
@router.get("/physical-properties", response_model=list[schemas.PhysicalProperties])
async def read_physical_properties(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(deps.get_db)):
    return await service.get_physical_properties(db, skip=skip, limit=limit)

@router.post("/physical-properties", response_model=schemas.PhysicalProperties, status_code=201)
async def create_physical_properties(props: schemas.PhysicalPropertiesCreate, db: AsyncSession = Depends(deps.get_db)):
    return await service.create_physical_properties(db=db, props=props)

# MicrobialActivity
@router.get("/microbial-activity", response_model=list[schemas.MicrobialActivity])
async def read_microbial_activity(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(deps.get_db)):
    return await service.get_microbial_activity(db, skip=skip, limit=limit)

@router.post("/microbial-activity", response_model=schemas.MicrobialActivity, status_code=201)
async def create_microbial_activity(activity: schemas.MicrobialActivityCreate, db: AsyncSession = Depends(deps.get_db)):
    return await service.create_microbial_activity(db=db, activity=activity)

# AmendmentLog
@router.get("/amendment-logs", response_model=list[schemas.AmendmentLog])
async def read_amendment_logs(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(deps.get_db)):
    return await service.get_amendment_logs(db, skip=skip, limit=limit)

@router.post("/amendment-logs", response_model=schemas.AmendmentLog, status_code=201)
async def create_amendment_log(log: schemas.AmendmentLogCreate, db: AsyncSession = Depends(deps.get_db)):
    return await service.create_amendment_log(db=db, log=log)

# SoilMap
@router.get("/maps", response_model=list[schemas.SoilMap])
async def read_soil_maps(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(deps.get_db)):
    return await service.get_soil_maps(db, skip=skip, limit=limit)

@router.post("/maps", response_model=schemas.SoilMap, status_code=201)
async def create_soil_map(map_data: schemas.SoilMapCreate, db: AsyncSession = Depends(deps.get_db)):
    return await service.create_soil_map(db=db, map_data=map_data)
