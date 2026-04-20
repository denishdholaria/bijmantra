"""
BrAPI v2.1 Scales Endpoints
Measurement scales for observation variables

Production-ready: Uses Service layer and Pydantic schemas.
"""


from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import or_, select
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.rls import set_tenant_context
from app.models.brapi_phenotyping import Scale as ScaleModel
from app.models.phenotyping import ObservationVariable
from app.schemas.brapi_scales import (
    Category,
    ExternalReference,
    OntologyReference,
    Scale,
    ScaleCreate,
    ScaleDeleteResponse,
    ScaleListResponse,
    ScaleSingleResponse,
    ScaleUpdate,
    ValidValues,
)
from app.modules.core.services.scales_service import ScalesService


router = APIRouter()


def _normalize_categories(categories: list | None) -> list[Category] | None:
    if not categories:
        return None

    normalized = []
    for category in categories:
        if isinstance(category, dict):
            label = str(category.get("label") or category.get("value") or "")
            value = str(category.get("value") or category.get("label") or "")
        else:
            label = str(category)
            value = str(category)

        normalized.append(Category(label=label, value=value))

    return normalized or None


def _build_scale_schema(
    *,
    scale_db_id: str,
    scale_name: str,
    scale_pui: str | None = None,
    data_type: str | None = None,
    decimal_places: int | None = None,
    valid_values_min: int | None = None,
    valid_values_max: int | None = None,
    valid_values_categories: list | None = None,
    ontology_db_id: str | None = None,
    ontology_name: str | None = None,
    ontology_version: str | None = None,
    external_references: list[dict] | None = None,
    additional_info: dict | None = None,
) -> Scale:
    valid_values = None
    if valid_values_min is not None or valid_values_max is not None or valid_values_categories:
        valid_values = ValidValues(
            min=valid_values_min,
            max=valid_values_max,
            categories=_normalize_categories(valid_values_categories)
        )

    ontology_ref = None
    if ontology_db_id:
        ontology_ref = OntologyReference(
            ontologyDbId=ontology_db_id,
            ontologyName=ontology_name,
            version=ontology_version
        )

    return Scale(
        scaleDbId=scale_db_id,
        scaleName=scale_name,
        scalePUI=scale_pui,
        dataType=data_type,
        decimalPlaces=decimal_places,
        validValues=valid_values,
        ontologyReference=ontology_ref,
        externalReferences=[ExternalReference(**ref) for ref in (external_references or [])],
        additionalInfo=additional_info,
    )


def _is_missing_scales_table(error: ProgrammingError) -> bool:
    return 'relation "scales" does not exist' in str(error)


def _scale_from_variable(variable: ObservationVariable) -> Scale:
    valid_values = variable.valid_values if isinstance(variable.valid_values, dict) else {}
    return _build_scale_schema(
        scale_db_id=variable.scale_db_id or variable.scale_name,
        scale_name=variable.scale_name,
        data_type=variable.data_type,
        decimal_places=variable.decimal_places,
        valid_values_min=valid_values.get("min"),
        valid_values_max=valid_values.get("max"),
        valid_values_categories=valid_values.get("categories"),
        ontology_db_id=variable.ontology_db_id,
        ontology_name=variable.ontology_name,
        external_references=variable.external_references,
        additional_info=variable.additional_info,
    )


async def _list_scales_from_variables(
    db: AsyncSession,
    page: int,
    page_size: int,
    *,
    scale_db_id: str | None = None,
    scale_name: str | None = None,
    data_type: str | None = None,
    ontology_db_id: str | None = None,
) -> tuple[list[Scale], int]:
    query = select(ObservationVariable).where(ObservationVariable.scale_name.is_not(None))

    if scale_db_id:
        query = query.where(ObservationVariable.scale_db_id == scale_db_id)
    if scale_name:
        query = query.where(ObservationVariable.scale_name.ilike(f"%{scale_name}%"))
    if data_type:
        query = query.where(ObservationVariable.data_type == data_type)
    if ontology_db_id:
        query = query.where(ObservationVariable.ontology_db_id == ontology_db_id)

    result = await db.execute(query.order_by(ObservationVariable.scale_name.asc()))
    variables = result.scalars().all()

    deduped: dict[str, Scale] = {}
    for variable in variables:
        key = variable.scale_db_id or variable.scale_name
        if not key or key in deduped:
            continue
        deduped[key] = _scale_from_variable(variable)

    scales = list(deduped.values())
    total = len(scales)
    start = page * page_size
    return scales[start:start + page_size], total


async def _get_scale_from_variables(db: AsyncSession, scale_db_id: str) -> Scale | None:
    query = select(ObservationVariable).where(
        ObservationVariable.scale_name.is_not(None),
        or_(
            ObservationVariable.scale_db_id == scale_db_id,
            ObservationVariable.scale_name == scale_db_id,
        ),
    )
    result = await db.execute(query.order_by(ObservationVariable.id.asc()))
    variable = result.scalars().first()
    if not variable:
        return None
    return _scale_from_variable(variable)

def scale_to_schema(scale: ScaleModel) -> Scale:
    """Converts a Scale SQLAlchemy model to Pydantic schema."""
    return _build_scale_schema(
        scale_db_id=scale.scale_db_id or str(scale.id),
        scale_name=scale.scale_name,
        scale_pui=scale.scale_pui,
        data_type=scale.data_type,
        decimal_places=scale.decimal_places,
        valid_values_min=scale.valid_values_min,
        valid_values_max=scale.valid_values_max,
        valid_values_categories=scale.valid_values_categories,
        ontology_db_id=scale.ontology_db_id,
        ontology_name=scale.ontology_name,
        ontology_version=scale.ontology_version,
        external_references=scale.external_references,
        additional_info=scale.additional_info,
    )

# DEPRECATED (ADR-005): Use schemas.brapi.BrAPIResponse[T] instead of this local helper.
def brapi_response(result: list[Scale] | Scale, page: int = 0, page_size: int = 1000, total_count: int | None = None) -> dict:
    if isinstance(result, list):
        if total_count is None:
            total_count = len(result)
        return {
            "metadata": {
                "datafiles": [],
                "pagination": {
                    "currentPage": page,
                    "pageSize": page_size,
                    "totalCount": total_count,
                    "totalPages": (total_count + page_size - 1) // page_size if total_count > 0 else 1
                },
                "status": [{"message": "Success", "messageType": "INFO"}]
            },
            "result": {"data": result}
        }
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Success", "messageType": "INFO"}]
        },
        "result": result
    }

@router.get("/scales", response_model=ScaleListResponse)
async def get_scales(
    request: Request,
    scaleDbId: str | None = None,
    scaleName: str | None = None,
    dataType: str | None = None,
    ontologyDbId: str | None = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves a list of scales based on search criteria."""
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)

    try:
        scales, total = await ScalesService.get_all(
            db, page, pageSize,
            scale_db_id=scaleDbId,
            scale_name=scaleName,
            data_type=dataType,
            ontology_db_id=ontologyDbId
        )
        data = [scale_to_schema(s) for s in scales]
    except ProgrammingError as error:
        if not _is_missing_scales_table(error):
            raise
        await db.rollback()
        data, total = await _list_scales_from_variables(
            db,
            page,
            pageSize,
            scale_db_id=scaleDbId,
            scale_name=scaleName,
            data_type=dataType,
            ontology_db_id=ontologyDbId,
        )

    return brapi_response(data, page, pageSize, total)

@router.get("/scales/{scaleDbId}", response_model=ScaleSingleResponse)
async def get_scale(
    scaleDbId: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves a single scale by its unique identifier."""
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)

    try:
        scale = await ScalesService.get_by_id(db, scaleDbId)
        scale_data = scale_to_schema(scale) if scale else None
    except ProgrammingError as error:
        if not _is_missing_scales_table(error):
            raise
        await db.rollback()
        scale_data = await _get_scale_from_variables(db, scaleDbId)

    if not scale_data:
        return {
            "metadata": {
                "datafiles": [],
                "pagination": {"currentPage": 0, "pageSize": 0, "totalCount": 0, "totalPages": 0},
                "status": [{"message": f"Scale {scaleDbId} not found", "messageType": "ERROR"}]
            },
            "result": None
        }

    return brapi_response(scale_data)

@router.post("/scales", response_model=ScaleListResponse)
async def create_scales(
    scales: list[ScaleCreate],
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Creates one or more new scales."""
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)

    if not org_id and not is_superuser:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Use default org for superusers if not specified (simplification)
    target_org_id = org_id if org_id else None

    created = []
    for scale_in in scales:
        new_scale = await ScalesService.create(db, scale_in, target_org_id)
        created.append(scale_to_schema(new_scale))

    await db.commit()
    return brapi_response(created)

@router.put("/scales/{scaleDbId}", response_model=ScaleSingleResponse)
async def update_scale(
    scaleDbId: str,
    scale_in: ScaleUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Updates an existing scale."""
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)

    updated_scale = await ScalesService.update(db, scaleDbId, scale_in)

    if not updated_scale:
        return {
            "metadata": {
                "datafiles": [],
                "pagination": {"currentPage": 0, "pageSize": 0, "totalCount": 0, "totalPages": 0},
                "status": [{"message": f"Scale {scaleDbId} not found", "messageType": "ERROR"}]
            },
            "result": None
        }

    await db.commit()
    return brapi_response(scale_to_schema(updated_scale))

@router.delete("/scales/{scaleDbId}", response_model=ScaleDeleteResponse)
async def delete_scale(
    scaleDbId: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Deletes a scale."""
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)

    success = await ScalesService.delete(db, scaleDbId)

    if not success:
         return {
            "metadata": {
                "datafiles": [],
                "pagination": {"currentPage": 0, "pageSize": 0, "totalCount": 0, "totalPages": 0},
                "status": [{"message": f"Scale {scaleDbId} not found", "messageType": "ERROR"}]
            },
            "result": None
        }

    await db.commit()
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 0, "totalCount": 0, "totalPages": 0},
            "status": [{"message": "Scale deleted successfully", "messageType": "INFO"}]
        },
        "result": None
    }
