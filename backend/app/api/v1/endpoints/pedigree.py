from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.services.pedigree_service import PedigreeService

router = APIRouter(prefix="/pedigree", tags=["Pedigree"])


@router.get("/{germplasm_id}")
async def get_pedigree_graph(
    germplasm_id: str,
    depth: int = Query(2, ge=0, le=10, description="Traversal depth for ancestors/descendants"),
    db: AsyncSession = Depends(deps.get_db),
    organization_id: int = Depends(deps.get_organization_id),
):
    service = PedigreeService(db)
    try:
        graph = await service.get_pedigree_graph(germplasm_id=germplasm_id, depth=depth, organization_id=organization_id)
        return {"success": True, "germplasm_id": germplasm_id, "depth": depth, **graph}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to build pedigree graph: {exc}")
