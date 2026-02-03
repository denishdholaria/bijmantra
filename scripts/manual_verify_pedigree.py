import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.pedigree_service import PedigreeService
from app.models.germplasm import Germplasm, Cross

async def verify_logic():
    print("Verifying PedigreeService logic with mocks...")

    # Mock Session
    session = AsyncMock()

    # Mock result for execute
    mock_result = MagicMock()
    # scalar_one_or_none returns None (not found) or Object
    mock_result.scalar_one_or_none.return_value = None
    # scalars().all() returns list
    mock_result.scalars.return_value.all.return_value = []

    session.execute.return_value = mock_result

    service = PedigreeService(session)

    # 1. Test load_pedigree
    data = [{"id": "F1", "sire_id": "P1", "dam_id": "P2"}]
    try:
        await service.load_pedigree(data)
        print("load_pedigree: OK")
    except Exception as e:
        print(f"load_pedigree: FAILED - {e}")
        import traceback
        traceback.print_exc()

    # 2. Test get_individuals
    try:
        data, count = await service.get_individuals(page=0, page_size=10)
        print("get_individuals: OK")
    except Exception as e:
        print(f"get_individuals: FAILED - {e}")
        import traceback
        traceback.print_exc()

    # 3. Test get_ancestors
    try:
        await service.get_ancestors("F1")
        print("get_ancestors: OK")
    except Exception as e:
        print(f"get_ancestors: FAILED - {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_logic())
