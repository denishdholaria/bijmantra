import sys
import os
import asyncio
from sqlalchemy import text

# Add current directory to path so we can import 'app'
# Assuming this script is run from 'backend/' directory
sys.path.append(os.getcwd())

from app.core.database import AsyncSessionLocal

async def fix_migration():
    print("Attempting to fix Alembic version...")
    try:
        async with AsyncSessionLocal() as session:
            # Check current version
            try:
                result = await session.execute(text("SELECT version_num FROM alembic_version"))
                current = result.scalar()
                print(f"Current DB version: {current}")
            except Exception as e:
                print(f"Could not read version: {e}")
                current = None

            # Always update to 045 as requested
            print("Updating version to '045'...")
            await session.execute(text("UPDATE alembic_version SET version_num = '045'"))
            await session.commit()
            print("SUCCESS: Database version forced to '045'.")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(fix_migration())
