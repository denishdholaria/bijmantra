"""
BrAPI v2.1 Planned Crosses Endpoints
GET/POST/PUT /plannedcrosses

Database-backed implementation for production use.
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_organization_id
from app.core.database import get_db
from app.models.germplasm import CrossingProject, Germplasm
from app.models.germplasm import PlannedCross as PlannedCrossModel


router = APIRouter()


class PlannedCrossParent(BaseModel):
    germplasmDbId: str
    germplasmName: str | None = None
    observationUnitDbId: str | None = None
    observationUnitName: str | None = None
    parentType: str  # MALE, FEMALE, SELF, POPULATION


class PlannedCrossBase(BaseModel):
    crossingProjectDbId: str | None = None
    crossingProjectName: str | None = None
    crossType: str | None = "BIPARENTAL"
    plannedCrossName: str | None = None
    status: str | None = "TODO"  # TODO, DONE, FAILED
    parent1: PlannedCrossParent | None = None
    parent2: PlannedCrossParent | None = None
    additionalInfo: dict = {}
    externalReferences: list[dict] = []


class PlannedCrossCreate(PlannedCrossBase):
    pass


class PlannedCrossUpdate(BaseModel):
    plannedCrossDbId: str
    crossingProjectDbId: str | None = None
    crossType: str | None = None
    plannedCrossName: str | None = None
    status: str | None = None
    parent1: PlannedCrossParent | None = None
    parent2: PlannedCrossParent | None = None
    additionalInfo: dict | None = None


def model_to_dict(cross: PlannedCrossModel, project_name: str = None,
                  parent1_name: str = None, parent2_name: str = None) -> dict[str, Any]:
    """Convert PlannedCross model to BrAPI response dict"""
    result = {
        "plannedCrossDbId": cross.planned_cross_db_id,
        "plannedCrossName": cross.planned_cross_name,
        "crossingProjectDbId": None,
        "crossingProjectName": project_name,
        "crossType": cross.cross_type,
        "status": cross.status,
        "additionalInfo": cross.additional_info or {},
        "externalReferences": cross.external_references or [],
    }

    # Build parent1
    if cross.parent1_db_id:
        result["parent1"] = {
            "germplasmDbId": str(cross.parent1_db_id),
            "germplasmName": parent1_name,
            "parentType": cross.parent1_type or "FEMALE",
        }
    else:
        result["parent1"] = None

    # Build parent2
    if cross.parent2_db_id:
        result["parent2"] = {
            "germplasmDbId": str(cross.parent2_db_id),
            "germplasmName": parent2_name,
            "parentType": cross.parent2_type or "MALE",
        }
    else:
        result["parent2"] = None

    return result


def create_response(data, page=0, page_size=1000, total_count=1):
    total_pages = max(1, (total_count + page_size - 1) // page_size)
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {
                "currentPage": page,
                "pageSize": page_size,
                "totalCount": total_count,
                "totalPages": total_pages
            },
            "status": [{"message": "Success", "messageType": "INFO"}]
        },
        "result": data
    }


@router.get("/plannedcrosses")
async def get_planned_crosses(
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=2000),
    crossingProjectDbId: str | None = Query(None),
    crossingProjectName: str | None = Query(None),
    plannedCrossDbId: str | None = Query(None),
    plannedCrossName: str | None = Query(None),
    status: str | None = Query(None),
    externalReferenceId: str | None = Query(None, alias="externalReferenceID"),
    externalReferenceSource: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Get list of planned crosses

    BrAPI Endpoint: GET /plannedcrosses
    """
    # Build query
    query = select(PlannedCrossModel).where(PlannedCrossModel.organization_id == org_id)
    query = query.options(
        selectinload(PlannedCrossModel.crossing_project),
        selectinload(PlannedCrossModel.parent1),
        selectinload(PlannedCrossModel.parent2),
    )

    if plannedCrossDbId:
        query = query.where(PlannedCrossModel.planned_cross_db_id == plannedCrossDbId)
    if plannedCrossName:
        query = query.where(PlannedCrossModel.planned_cross_name.ilike(f"%{plannedCrossName}%"))
    if status:
        query = query.where(PlannedCrossModel.status == status)
    if crossingProjectDbId:
        # Need to join with CrossingProject
        subquery = select(CrossingProject.id).where(
            CrossingProject.crossing_project_db_id == crossingProjectDbId
        )
        query = query.where(PlannedCrossModel.crossing_project_id.in_(subquery))

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total_count = total_result.scalar() or 0

    # Apply pagination
    query = query.order_by(PlannedCrossModel.planned_cross_name)
    query = query.offset(page * pageSize).limit(pageSize)

    result = await db.execute(query)
    crosses = result.scalars().all()

    # Build response with related data
    result_data = []
    for cross in crosses:
        project_name = (
            cross.crossing_project.crossing_project_name if cross.crossing_project else None
        )
        parent1_name = cross.parent1.germplasm_name if cross.parent1 else None
        parent2_name = cross.parent2.germplasm_name if cross.parent2 else None

        result_data.append(model_to_dict(cross, project_name, parent1_name, parent2_name))

    return create_response({"data": result_data}, page, pageSize, total_count)


@router.get("/plannedcrosses/{plannedCrossDbId}")
async def get_planned_cross(
    plannedCrossDbId: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get a single planned cross by ID"""
    query = select(PlannedCrossModel).where(
        PlannedCrossModel.planned_cross_db_id == plannedCrossDbId,
        PlannedCrossModel.organization_id == org_id
    )
    result = await db.execute(query)
    cross = result.scalar_one_or_none()

    if not cross:
        raise HTTPException(status_code=404, detail="Planned cross not found")

    # Get related data
    project_name = None
    if cross.crossing_project_id:
        proj_result = await db.execute(
            select(CrossingProject.crossing_project_name).where(
                CrossingProject.id == cross.crossing_project_id
            )
        )
        project_name = proj_result.scalar()

    parent1_name = None
    parent2_name = None
    if cross.parent1_db_id:
        p1_result = await db.execute(
            select(Germplasm.germplasm_name).where(Germplasm.id == cross.parent1_db_id)
        )
        parent1_name = p1_result.scalar()
    if cross.parent2_db_id:
        p2_result = await db.execute(
            select(Germplasm.germplasm_name).where(Germplasm.id == cross.parent2_db_id)
        )
        parent2_name = p2_result.scalar()

    return create_response(model_to_dict(cross, project_name, parent1_name, parent2_name))


@router.post("/plannedcrosses", status_code=201)
async def create_planned_crosses(
    crosses: list[PlannedCrossCreate],
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Create new planned crosses

    BrAPI Endpoint: POST /plannedcrosses
    """
    created = []

    # Collect external IDs for batch resolution
    project_db_ids = set()
    germplasm_db_ids = set()

    for cross_in in crosses:
        if cross_in.crossingProjectDbId:
            project_db_ids.add(cross_in.crossingProjectDbId)
        if cross_in.parent1 and cross_in.parent1.germplasmDbId:
            germplasm_db_ids.add(cross_in.parent1.germplasmDbId)
        if cross_in.parent2 and cross_in.parent2.germplasmDbId:
            germplasm_db_ids.add(cross_in.parent2.germplasmDbId)

    # Batch resolve projects
    project_map = {}
    if project_db_ids:
        query = select(CrossingProject.crossing_project_db_id, CrossingProject.id).where(
            CrossingProject.crossing_project_db_id.in_(project_db_ids),
            CrossingProject.organization_id == org_id
        )
        result = await db.execute(query)
        project_map = {row.crossing_project_db_id: row.id for row in result.all()}

    # Batch resolve germplasm
    germplasm_map = {}
    if germplasm_db_ids:
        query = select(Germplasm.germplasm_db_id, Germplasm.id).where(
            Germplasm.germplasm_db_id.in_(germplasm_db_ids),
            Germplasm.organization_id == org_id
        )
        result = await db.execute(query)
        germplasm_map = {row.germplasm_db_id: row.id for row in result.all()}

    for cross_in in crosses:
        cross_id = f"pc-{uuid.uuid4().hex[:8]}"

        # Resolve crossing project ID
        project_id = project_map.get(cross_in.crossingProjectDbId)

        # Resolve parent IDs
        parent1_id = None
        if cross_in.parent1 and cross_in.parent1.germplasmDbId:
            parent1_id = germplasm_map.get(cross_in.parent1.germplasmDbId)

        parent2_id = None
        if cross_in.parent2 and cross_in.parent2.germplasmDbId:
            parent2_id = germplasm_map.get(cross_in.parent2.germplasmDbId)

        new_cross = PlannedCrossModel(
            organization_id=org_id,
            crossing_project_id=project_id,
            planned_cross_db_id=cross_id,
            planned_cross_name=cross_in.plannedCrossName,
            cross_type=cross_in.crossType,
            parent1_db_id=parent1_id,
            parent1_type=cross_in.parent1.parentType if cross_in.parent1 else None,
            parent2_db_id=parent2_id,
            parent2_type=cross_in.parent2.parentType if cross_in.parent2 else None,
            status=cross_in.status,
            additional_info=cross_in.additionalInfo,
            external_references=cross_in.externalReferences,
        )

        db.add(new_cross)
        created.append(new_cross)

    await db.commit()

    # Build response
    result_data = []
    for cross in created:
        await db.refresh(cross)
        result_data.append(model_to_dict(cross))

    return create_response({"data": result_data}, total_count=len(result_data))


@router.put("/plannedcrosses")
async def update_planned_crosses(
    crosses: list[PlannedCrossUpdate],
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Update planned crosses

    BrAPI Endpoint: PUT /plannedcrosses
    """
    # 1. Batch fetch existing crosses
    cross_ids = [c.plannedCrossDbId for c in crosses]
    existing_crosses = {}
    if cross_ids:
        query = select(PlannedCrossModel).where(
            PlannedCrossModel.planned_cross_db_id.in_(cross_ids),
            PlannedCrossModel.organization_id == org_id
        )
        result = await db.execute(query)
        existing_crosses = {c.planned_cross_db_id: c for c in result.scalars().all()}

    # 2. Batch fetch parent germplasm
    parent_db_ids = set()
    for c in crosses:
        if c.parent1 and c.parent1.germplasmDbId:
            parent_db_ids.add(c.parent1.germplasmDbId)
        if c.parent2 and c.parent2.germplasmDbId:
            parent_db_ids.add(c.parent2.germplasmDbId)

    parent_map = {}
    if parent_db_ids:
        parent_query = select(Germplasm.germplasm_db_id, Germplasm.id).where(
            Germplasm.germplasm_db_id.in_(parent_db_ids),
            Germplasm.organization_id == org_id
        )
        parent_result = await db.execute(parent_query)
        parent_map = {row.germplasm_db_id: row.id for row in parent_result.all()}

    updated = []

    for cross_in in crosses:
        cross_id = cross_in.plannedCrossDbId
        cross = existing_crosses.get(cross_id)

        if not cross:
            # Create new if doesn't exist
            cross = PlannedCrossModel(
                organization_id=org_id,
                planned_cross_db_id=cross_id,
                planned_cross_name=cross_in.plannedCrossName,
                cross_type=cross_in.crossType or "BIPARENTAL",
                status=cross_in.status or "TODO",
                additional_info=cross_in.additionalInfo or {},
            )
            db.add(cross)
        else:
            # Update existing
            if cross_in.plannedCrossName is not None:
                cross.planned_cross_name = cross_in.plannedCrossName
            if cross_in.crossType is not None:
                cross.cross_type = cross_in.crossType
            if cross_in.status is not None:
                cross.status = cross_in.status
            if cross_in.additionalInfo is not None:
                cross.additional_info = cross_in.additionalInfo

        # Update parents if provided
        if cross_in.parent1:
            if cross_in.parent1.germplasmDbId:
                cross.parent1_db_id = parent_map.get(cross_in.parent1.germplasmDbId)
            cross.parent1_type = cross_in.parent1.parentType

        if cross_in.parent2:
            if cross_in.parent2.germplasmDbId:
                cross.parent2_db_id = parent_map.get(cross_in.parent2.germplasmDbId)
            cross.parent2_type = cross_in.parent2.parentType

        updated.append(cross)

    await db.commit()

    # Build response - Batch refresh
    result_data = []

    # Re-fetch all processed crosses to ensure fresh data (including DB defaults/triggers)
    if cross_ids:
        final_query = select(PlannedCrossModel).where(
            PlannedCrossModel.planned_cross_db_id.in_(cross_ids),
            PlannedCrossModel.organization_id == org_id
        )
        final_result = await db.execute(final_query)
        final_crosses_map = {c.planned_cross_db_id: c for c in final_result.scalars().all()}

        # Preserve input order
        for cross_in in crosses:
            c = final_crosses_map.get(cross_in.plannedCrossDbId)
            if c:
                result_data.append(model_to_dict(c))

    return create_response({"data": result_data}, total_count=len(result_data))


@router.delete("/plannedcrosses/{plannedCrossDbId}")
async def delete_planned_cross(
    plannedCrossDbId: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Delete a planned cross"""
    query = select(PlannedCrossModel).where(
        PlannedCrossModel.planned_cross_db_id == plannedCrossDbId,
        PlannedCrossModel.organization_id == org_id
    )
    result = await db.execute(query)
    cross = result.scalar_one_or_none()

    if not cross:
        raise HTTPException(status_code=404, detail="Planned cross not found")

    await db.delete(cross)
    await db.commit()

    return {"message": "Planned cross deleted successfully"}
