from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from . import models, schemas

# NutrientTest
async def get_nutrient_tests(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(models.NutrientTest).offset(skip).limit(limit))
    return result.scalars().all()

async def create_nutrient_test(db: AsyncSession, test: schemas.NutrientTestCreate):
    db_test = models.NutrientTest(**test.dict())
    db.add(db_test)
    await db.commit()
    await db.refresh(db_test)
    return db_test

# PhysicalProperties
async def get_physical_properties(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(models.PhysicalProperties).offset(skip).limit(limit))
    return result.scalars().all()

async def create_physical_properties(db: AsyncSession, props: schemas.PhysicalPropertiesCreate):
    db_props = models.PhysicalProperties(**props.dict())
    db.add(db_props)
    await db.commit()
    await db.refresh(db_props)
    return db_props

# MicrobialActivity
async def get_microbial_activity(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(models.MicrobialActivity).offset(skip).limit(limit))
    return result.scalars().all()

async def create_microbial_activity(db: AsyncSession, activity: schemas.MicrobialActivityCreate):
    db_activity = models.MicrobialActivity(**activity.dict())
    db.add(db_activity)
    await db.commit()
    await db.refresh(db_activity)
    return db_activity

# AmendmentLog
async def get_amendment_logs(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(models.AmendmentLog).offset(skip).limit(limit))
    return result.scalars().all()

async def create_amendment_log(db: AsyncSession, log: schemas.AmendmentLogCreate):
    db_log = models.AmendmentLog(**log.dict())
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
    return db_log

# SoilMap
async def get_soil_maps(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(models.SoilMap).offset(skip).limit(limit))
    return result.scalars().all()

async def create_soil_map(db: AsyncSession, map_data: schemas.SoilMapCreate):
    db_map = models.SoilMap(**map_data.dict())
    db.add(db_map)
    await db.commit()
    await db.refresh(db_map)
    return db_map
