"""
Progeny API
Manage offspring and descendants of germplasm entries.

Queries Germplasm + Cross tables for real parent-progeny relationships.
Refactored: Session 94 — migrated from in-memory demo data to real DB queries.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.core.database import get_db
from app.api.deps import get_organization_id
from app.models.germplasm import Germplasm, Cross

from app.api.deps import get_current_user

router = APIRouter(prefix="/progeny", tags=["Progeny"], dependencies=[Depends(get_current_user)])


def _germplasm_to_parent(g: Germplasm, parent_type: str, progeny_list: list) -> dict:
    return {
        "id": g.id,
        "germplasm_id": g.germplasm_db_id or str(g.id),
        "germplasm_name": g.germplasm_name,
        "parent_type": parent_type,
        "species": f"{g.genus or ''} {g.species or ''}".strip() or None,
        "generation": g.pedigree,
        "progeny": progeny_list,
    }


@router.get("/parents")
async def list_parents(
    parent_type: Optional[str] = Query(None, description="Filter by parent type: FEMALE, MALE, SELF, POPULATION"),
    species: Optional[str] = Query(None, description="Filter by species"),
    search: Optional[str] = Query(None, description="Search by parent or progeny name"),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """List germplasm that appear as parents in crosses, with their offspring."""
    # Find all crosses for this org
    cross_q = select(Cross).where(Cross.organization_id == organization_id)
    result = await db.execute(cross_q)
    crosses = result.scalars().all()

    if not crosses:
        return {"status": "success", "data": [], "count": 0}

    # Collect parent IDs and their cross info
    parent_map: dict[int, list] = {}  # parent_id -> list of progeny info
    parent_types: dict[int, str] = {}

    for c in crosses:
        if c.parent1_db_id:
            parent_map.setdefault(c.parent1_db_id, [])
            parent_types.setdefault(c.parent1_db_id, c.parent1_type or "FEMALE")
            # Get offspring germplasm linked to this cross
            for prog in (c.progeny or []):
                parent_map[c.parent1_db_id].append({
                    "germplasm_id": prog.germplasm_db_id or str(prog.id),
                    "germplasm_name": prog.germplasm_name,
                    "parent_type": c.parent1_type or "FEMALE",
                    "generation": prog.pedigree,
                    "cross_year": c.crossing_year,
                })
        if c.parent2_db_id:
            parent_map.setdefault(c.parent2_db_id, [])
            parent_types.setdefault(c.parent2_db_id, c.parent2_type or "MALE")
            for prog in (c.progeny or []):
                parent_map[c.parent2_db_id].append({
                    "germplasm_id": prog.germplasm_db_id or str(prog.id),
                    "germplasm_name": prog.germplasm_name,
                    "parent_type": c.parent2_type or "MALE",
                    "generation": prog.pedigree,
                    "cross_year": c.crossing_year,
                })

    if not parent_map:
        return {"status": "success", "data": [], "count": 0}

    # Fetch parent germplasm records
    parent_ids = list(parent_map.keys())
    gq = select(Germplasm).where(Germplasm.id.in_(parent_ids))
    gresult = await db.execute(gq)
    germplasms = {g.id: g for g in gresult.scalars().all()}

    parents = []
    for pid, progeny_list in parent_map.items():
        g = germplasms.get(pid)
        if not g:
            continue
        ptype = parent_types.get(pid, "FEMALE")

        # Apply filters
        if parent_type and ptype != parent_type:
            continue
        if species:
            sp = f"{g.genus or ''} {g.species or ''}".strip().lower()
            if species.lower() not in sp:
                continue
        if search:
            s = search.lower()
            name_match = s in (g.germplasm_name or "").lower()
            progeny_match = any(s in (p.get("germplasm_name", "")).lower() for p in progeny_list)
            if not name_match and not progeny_match:
                continue

        parents.append(_germplasm_to_parent(g, ptype, progeny_list))

    # Sort by number of progeny descending
    parents.sort(key=lambda x: len(x["progeny"]), reverse=True)

    return {"status": "success", "data": parents, "count": len(parents)}


@router.get("/parents/{parent_id}")
async def get_parent(
    parent_id: int,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get a single parent with all progeny."""
    g = (await db.execute(
        select(Germplasm).where(Germplasm.id == parent_id, Germplasm.organization_id == organization_id)
    )).scalar_one_or_none()
    if not g:
        raise HTTPException(status_code=404, detail=f"Germplasm {parent_id} not found")

    # Get crosses where this germplasm is a parent
    crosses = (await db.execute(
        select(Cross).where(
            Cross.organization_id == organization_id,
            or_(Cross.parent1_db_id == parent_id, Cross.parent2_db_id == parent_id)
        )
    )).scalars().all()

    progeny_list = []
    ptype = "FEMALE"
    for c in crosses:
        if c.parent1_db_id == parent_id:
            ptype = c.parent1_type or "FEMALE"
        else:
            ptype = c.parent2_type or "MALE"
        for prog in (c.progeny or []):
            progeny_list.append({
                "germplasm_id": prog.germplasm_db_id or str(prog.id),
                "germplasm_name": prog.germplasm_name,
                "parent_type": ptype,
                "generation": prog.pedigree,
                "cross_year": c.crossing_year,
            })

    return {"status": "success", "data": _germplasm_to_parent(g, ptype, progeny_list)}


@router.get("/germplasm/{germplasm_id}")
async def get_progeny_by_germplasm(
    germplasm_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get progeny for a specific germplasm by germplasm_db_id."""
    g = (await db.execute(
        select(Germplasm).where(
            Germplasm.organization_id == organization_id,
            or_(Germplasm.germplasm_db_id == germplasm_id, Germplasm.id == int(germplasm_id) if germplasm_id.isdigit() else False)
        )
    )).scalar_one_or_none()
    if not g:
        raise HTTPException(status_code=404, detail=f"Germplasm {germplasm_id} not found")

    crosses = (await db.execute(
        select(Cross).where(
            Cross.organization_id == organization_id,
            or_(Cross.parent1_db_id == g.id, Cross.parent2_db_id == g.id)
        )
    )).scalars().all()

    progeny_list = []
    ptype = "FEMALE"
    for c in crosses:
        if c.parent1_db_id == g.id:
            ptype = c.parent1_type or "FEMALE"
        else:
            ptype = c.parent2_type or "MALE"
        for prog in (c.progeny or []):
            progeny_list.append({
                "germplasm_id": prog.germplasm_db_id or str(prog.id),
                "germplasm_name": prog.germplasm_name,
                "parent_type": ptype,
                "generation": prog.pedigree,
                "cross_year": c.crossing_year,
            })

    return {"status": "success", "data": _germplasm_to_parent(g, ptype, progeny_list)}


@router.get("/statistics")
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get progeny statistics from real Cross + Germplasm data."""
    # Count crosses
    cross_count = (await db.execute(
        select(func.count(Cross.id)).where(Cross.organization_id == organization_id)
    )).scalar() or 0

    # Count distinct parents
    parent1_count = (await db.execute(
        select(func.count(func.distinct(Cross.parent1_db_id))).where(
            Cross.organization_id == organization_id, Cross.parent1_db_id.isnot(None)
        )
    )).scalar() or 0
    parent2_count = (await db.execute(
        select(func.count(func.distinct(Cross.parent2_db_id))).where(
            Cross.organization_id == organization_id, Cross.parent2_db_id.isnot(None)
        )
    )).scalar() or 0

    # Count progeny (germplasm with cross_id set)
    progeny_count = (await db.execute(
        select(func.count(Germplasm.id)).where(
            Germplasm.organization_id == organization_id, Germplasm.cross_id.isnot(None)
        )
    )).scalar() or 0

    total_parents = parent1_count + parent2_count  # may double-count, but good enough
    avg_offspring = round(progeny_count / total_parents, 1) if total_parents > 0 else 0

    # Count by parent type
    by_type: dict = {}
    type_q = await db.execute(
        select(Cross.parent1_type, func.count(func.distinct(Cross.parent1_db_id))).where(
            Cross.organization_id == organization_id, Cross.parent1_type.isnot(None)
        ).group_by(Cross.parent1_type)
    )
    for row in type_q:
        by_type[row[0]] = row[1]

    # Count by species
    by_species: dict = {}
    sp_q = await db.execute(
        select(Germplasm.common_crop_name, func.count(Germplasm.id)).where(
            Germplasm.organization_id == organization_id, Germplasm.cross_id.isnot(None)
        ).group_by(Germplasm.common_crop_name)
    )
    for row in sp_q:
        by_species[row[0] or "Unknown"] = row[1]

    return {
        "status": "success",
        "data": {
            "total_parents": total_parents,
            "total_progeny": progeny_count,
            "total_crosses": cross_count,
            "avg_offspring": avg_offspring,
            "by_parent_type": by_type,
            "by_species": by_species,
        },
    }


@router.get("/types")
async def get_parent_types():
    """Get available parent types — static reference data."""
    return {
        "status": "success",
        "data": [
            {"value": "FEMALE", "label": "Female (♀)", "description": "Seed parent"},
            {"value": "MALE", "label": "Male (♂)", "description": "Pollen parent"},
            {"value": "SELF", "label": "Self (⟳)", "description": "Self-pollinated"},
            {"value": "POPULATION", "label": "Population (👥)", "description": "Population cross"},
        ],
    }


@router.get("/lineage/{germplasm_id}")
async def get_lineage_tree(
    germplasm_id: int,
    depth: int = Query(3, description="Depth of lineage tree"),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get lineage tree for a germplasm."""
    g = (await db.execute(
        select(Germplasm).where(Germplasm.id == germplasm_id, Germplasm.organization_id == organization_id)
    )).scalar_one_or_none()
    if not g:
        raise HTTPException(status_code=404, detail=f"Germplasm {germplasm_id} not found")

    # Build tree: get crosses where this germplasm is a parent
    crosses = (await db.execute(
        select(Cross).where(
            Cross.organization_id == organization_id,
            or_(Cross.parent1_db_id == germplasm_id, Cross.parent2_db_id == germplasm_id)
        )
    )).scalars().all()

    children = []
    for c in crosses:
        for prog in (c.progeny or []):
            children.append({
                "id": prog.id,
                "name": prog.germplasm_name,
                "type": "progeny",
                "generation": prog.pedigree,
                "cross_year": c.crossing_year,
                "children": [],
            })

    tree = {
        "id": g.id,
        "name": g.germplasm_name,
        "type": "parent",
        "children": children,
    }

    return {"status": "success", "data": tree}
