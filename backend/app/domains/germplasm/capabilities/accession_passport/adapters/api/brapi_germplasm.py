"""
BrAPI v2.1 Germplasm Endpoints

Production-ready implementation using database only.
Demo data is sandboxed in "Demo Organization" - no in-memory fallbacks.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_current_user, get_optional_user
from app.domains.germplasm.capabilities.accession_passport.adapters.api.access import (
    require_accession_passport_api_access,
)
from app.domains.germplasm.capabilities.accession_passport.adapters.api.brapi_germplasm_dependencies import (
    build_brapi_germplasm_application_service,
)
from app.domains.germplasm.capabilities.accession_passport.application import (
    BrAPIGermplasmOperationResult,
)
from app.domains.germplasm.capabilities.accession_passport.schemas import (
    GermplasmCreate as BrAPIGermplasmCreateRequest,
)
from app.domains.germplasm.capabilities.accession_passport.schemas import (
    brapi_response,
)
from app.middleware.tenant_context import get_tenant_db


__all__ = [
    "_require_brapi_germplasm_manage_access",
    "_require_brapi_germplasm_read_access",
    "create_germplasm",
    "delete_germplasm",
    "get_current_user",
    "get_germplasm",
    "get_germplasm_mcpd",
    "get_germplasm_pedigree",
    "get_germplasm_progeny",
    "get_optional_user",
    "get_tenant_db",
    "list_germplasm",
    "router",
    "update_germplasm",
]


router = APIRouter()


def _brapi_operation_response(result: BrAPIGermplasmOperationResult):
    return brapi_response(
        result.data,
        result.page,
        result.page_size,
        result.total,
        result.message,
    )


@router.get("/germplasm")
async def list_germplasm(
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    germplasmName: str | None = None,
    commonCropName: str | None = None,
    species: str | None = None,
    genus: str | None = None,
    db: Any = Depends(get_tenant_db),
    current_user = Depends(get_optional_user),
):
    """Get a list of germplasm from the database.

    Args:
        page (int): The page number to return.
        pageSize (int): The number of items to return per page.
        germplasmName (Optional[str]): A name to filter by.
        commonCropName (Optional[str]): A common crop name to filter by.
        species (Optional[str]): A species to filter by.
        genus (Optional[str]): A genus to filter by.
        db: The database session.
        current_user (Optional[User]): The current user.

    Returns:
        A BrAPI response containing a list of germplasm.
    """
    await _require_brapi_germplasm_read_access(current_user, db)

    service = build_brapi_germplasm_application_service(db)
    result = await service.list_germplasm_for_request(
        page=page,
        page_size=pageSize,
        organization_id=getattr(current_user, "organization_id", None),
        germplasm_name=germplasmName,
        common_crop_name=commonCropName,
        species=species,
        genus=genus,
    )

    return _brapi_operation_response(result)


@router.post("/germplasm")
async def create_germplasm(
    germplasm: BrAPIGermplasmCreateRequest,
    db: Any = Depends(get_tenant_db),
    current_user = Depends(get_current_user),
):
    """Create a new germplasm.

    Args:
        germplasm (GermplasmCreate): The germplasm to create.
        db: The database session.
        current_user (User): The current user.

    Returns:
        A BrAPI response containing the new germplasm.
    """
    await _require_brapi_germplasm_manage_access(current_user, db)

    service = build_brapi_germplasm_application_service(db)
    result = await service.create_germplasm_from_payload(
        organization_id=current_user.organization_id,
        actor_id=getattr(current_user, "id", None),
        germplasm=germplasm,
    )

    return _brapi_operation_response(result)


@router.get("/germplasm/{germplasmDbId}")
async def get_germplasm(
    germplasmDbId: str,
    db: Any = Depends(get_tenant_db),
    current_user = Depends(get_optional_user),
):
    """Get a germplasm by its ID.

    Args:
        germplasmDbId (str): The ID of the germplasm to get.
        db: The database session.
        current_user (Optional[User]): The current user.

    Returns:
        A BrAPI response containing the germplasm.

    Raises:
        HTTPException: If the germplasm is not found.
    """
    await _require_brapi_germplasm_read_access(current_user, db)

    service = build_brapi_germplasm_application_service(db)
    result = await service.get_germplasm_for_request(
        germplasm_db_id=germplasmDbId,
        organization_id=getattr(current_user, "organization_id", None),
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Germplasm not found")

    return _brapi_operation_response(result)


@router.put("/germplasm/{germplasmDbId}")
async def update_germplasm(
    germplasmDbId: str,
    germplasm: BrAPIGermplasmCreateRequest,
    db: Any = Depends(get_tenant_db),
    current_user = Depends(get_current_user),
):
    """Update a germplasm.

    Args:
        germplasmDbId (str): The ID of the germplasm to update.
        germplasm (GermplasmCreate): The new germplasm data.
        db: The database session.
        current_user (User): The current user.

    Returns:
        A BrAPI response containing the updated germplasm.

    Raises:
        HTTPException: If the germplasm is not found.
    """
    await _require_brapi_germplasm_manage_access(current_user, db)

    service = build_brapi_germplasm_application_service(db)
    result = await service.update_germplasm_from_payload(
        germplasm_db_id=germplasmDbId,
        organization_id=current_user.organization_id,
        actor_id=getattr(current_user, "id", None),
        germplasm=germplasm,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Germplasm not found")

    return _brapi_operation_response(result)


@router.delete("/germplasm/{germplasmDbId}")
async def delete_germplasm(
    germplasmDbId: str,
    db: Any = Depends(get_tenant_db),
    current_user = Depends(get_current_user),
):
    """Delete a germplasm.

    Args:
        germplasmDbId (str): The ID of the germplasm to delete.
        db: The database session.
        current_user (User): The current user.

    Returns:
        A BrAPI response indicating that the germplasm was deleted.

    Raises:
        HTTPException: If the germplasm is not found.
    """
    await _require_brapi_germplasm_manage_access(current_user, db)

    service = build_brapi_germplasm_application_service(db)
    result = await service.delete_germplasm_for_request(
        germplasm_db_id=germplasmDbId,
        organization_id=current_user.organization_id,
        actor_id=getattr(current_user, "id", None),
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Germplasm not found")

    return _brapi_operation_response(result)


async def _require_brapi_germplasm_read_access(current_user, db: Any) -> None:
    await require_accession_passport_api_access(
        current_user,
        db=db,
        required_permission="germplasm.read",
    )


async def _require_brapi_germplasm_manage_access(current_user, db: Any) -> None:
    await require_accession_passport_api_access(
        current_user,
        db=db,
        required_permission="germplasm.passport.manage",
    )


@router.get("/germplasm/{germplasmDbId}/pedigree")
async def get_germplasm_pedigree(
    germplasmDbId: str,
    notation: str | None = Query("purdy", description="Pedigree notation: purdy, lamacraft, or rodriguez"),
    includeSiblings: bool = Query(False, description="Include siblings"),
    db: Any = Depends(get_tenant_db),
    current_user = Depends(get_optional_user),
):
    """Get pedigree information for a germplasm.

    Args:
        germplasmDbId (str): The ID of the germplasm to get pedigree information for.
        notation (Optional[str]): The pedigree notation to use.
        includeSiblings (bool): Whether to include siblings in the pedigree.
        db: The database session.
        current_user (Optional[User]): The current user.

    Returns:
        A BrAPI response containing the pedigree information.

    Raises:
        HTTPException: If the germplasm is not found.
    """
    await _require_brapi_germplasm_read_access(current_user, db)

    service = build_brapi_germplasm_application_service(db)
    result = await service.get_pedigree_for_request(
        germplasm_db_id=germplasmDbId,
        organization_id=getattr(current_user, "organization_id", None),
        notation=notation,
        include_siblings=includeSiblings,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Germplasm not found")

    return _brapi_operation_response(result)


@router.get("/germplasm/{germplasmDbId}/progeny")
async def get_germplasm_progeny(
    germplasmDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    db: Any = Depends(get_tenant_db),
    current_user = Depends(get_optional_user),
):
    """Get the progeny of a germplasm.

    Args:
        germplasmDbId (str): The ID of the germplasm to get the progeny of.
        page (int): The page number to return.
        pageSize (int): The number of items to return per page.
        db: The database session.
        current_user (Optional[User]): The current user.

    Returns:
        A BrAPI response containing the progeny of the germplasm.

    Raises:
        HTTPException: If the germplasm is not found.
    """
    await _require_brapi_germplasm_read_access(current_user, db)

    service = build_brapi_germplasm_application_service(db)
    result = await service.get_progeny_for_request(
        germplasm_db_id=germplasmDbId,
        page=page,
        page_size=pageSize,
        organization_id=getattr(current_user, "organization_id", None),
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Germplasm not found")

    return _brapi_operation_response(result)


@router.get("/germplasm/{germplasmDbId}/mcpd")
async def get_germplasm_mcpd(
    germplasmDbId: str,
    db: Any = Depends(get_tenant_db),
    current_user = Depends(get_optional_user),
):
    """Get MCPD (Multi-Crop Passport Descriptor) data for a germplasm.

    Args:
        germplasmDbId (str): The ID of the germplasm to get MCPD data for.
        db: The database session.
        current_user (Optional[User]): The current user.

    Returns:
        A BrAPI response containing the MCPD data.

    Raises:
        HTTPException: If the germplasm is not found.
    """
    await _require_brapi_germplasm_read_access(current_user, db)

    service = build_brapi_germplasm_application_service(db)
    result = await service.get_mcpd_for_request(
        germplasm_db_id=germplasmDbId,
        organization_id=getattr(current_user, "organization_id", None),
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Germplasm not found")

    return _brapi_operation_response(result)
