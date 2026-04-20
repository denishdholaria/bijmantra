import asyncio
import os
import sys


sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.biosimulation import CropModel
from app.models.core import Location


async def check_ids():
    async with AsyncSessionLocal() as db:
        print("--- Locations ---")
        result = await db.execute(select(Location))
        for loc in result.scalars().all():
            print(f"ID: {loc.id}, Name: {loc.location_name}, DB_ID: {loc.location_db_id}")

        print("\n--- Crop Models ---")
        result = await db.execute(select(CropModel))
        for model in result.scalars().all():
            print(f"ID: {model.id}, Name: {model.name}")


if __name__ == "__main__":
    asyncio.run(check_ids())
