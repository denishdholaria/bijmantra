"""
Germplasm Collection API
Endpoints for managing germplasm collections
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime, timezone
import uuid

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.data_management import (
    GermplasmCollection, GermplasmCollectionMember,
    CollectionType, CollectionStatus
)

router = APIRouter(prefix="/collections", tags=["Germplasm Collections"], dependencies=[Depends(get_current_user)])


@router.get("")
async def get_collections(
    type: Optional[str] = Query(None, description="Filter by type: core, working, active, base, breeding"),
    species: Optional[str] = Query(None, description="Filter by species"),
    curator: Optional[str] = Query(None, description="Filter by curator"),
    search: Optional[str] = Query(None, description="Search by name or description"),
    status: Optional[str] = Query(None, description="Filter by status: active, archived"),
    db: AsyncSession = Depends(get_db)
):
    """Get all germplasm collections"""
    query = select(GermplasmCollection)
    
    if type:
        try:
            collection_type = CollectionType(type)
            query = query.where(GermplasmCollection.collection_type == collection_type)
        except ValueError:
            pass
    
    if species:
        query = query.where(GermplasmCollection.species.contains([species]))
    
    if curator:
        query = query.where(GermplasmCollection.curator_name.ilike(f"%{curator}%"))
    
    if status:
        try:
            collection_status = CollectionStatus(status)
            query = query.where(GermplasmCollection.status == collection_status)
        except ValueError:
            pass
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                GermplasmCollection.name.ilike(search_term),
                GermplasmCollection.description.ilike(search_term)
            )
        )
    
    result = await db.execute(query.order_by(GermplasmCollection.created_at.desc()))
    collections = result.scalars().all()
    
    # Format response
    data = []
    for c in collections:
        data.append({
            "id": str(c.id),
            "name": c.name,
            "description": c.description,
            "type": c.collection_type.value if c.collection_type else "working",
            "accession_count": c.accession_count or 0,
            "species": c.species or [],
            "curator": c.curator_name or "",
            "curator_email": c.curator_email or "",
            "created_at": c.created_at.strftime("%Y-%m-%d") if c.created_at else "",
            "updated_at": c.updated_at.strftime("%Y-%m-%d") if c.updated_at else "",
            "status": c.status.value if c.status else "active"
        })
    
    return {"status": "success", "data": data, "count": len(data)}


@router.get("/stats")
async def get_collection_stats(db: AsyncSession = Depends(get_db)):
    """Get collection statistics"""
    result = await db.execute(select(GermplasmCollection))
    collections = result.scalars().all()
    
    total_accessions = sum(c.accession_count or 0 for c in collections)
    all_species = set()
    all_curators = set()
    
    for c in collections:
        if c.species:
            all_species.update(c.species)
        if c.curator_name:
            all_curators.add(c.curator_name)
    
    by_type = {}
    for c in collections:
        type_val = c.collection_type.value if c.collection_type else "working"
        by_type[type_val] = by_type.get(type_val, 0) + 1
    
    active_count = len([c for c in collections if c.status == CollectionStatus.ACTIVE])
    
    return {
        "status": "success",
        "data": {
            "total_collections": len(collections),
            "total_accessions": total_accessions,
            "unique_species": len(all_species),
            "species_list": list(all_species),
            "unique_curators": len(all_curators),
            "by_type": by_type,
            "active_collections": active_count
        }
    }


@router.get("/types")
async def get_collection_types():
    """Get available collection types"""
    types = [
        {"id": "core", "name": "Core Collection", "description": "Representative diversity set", "color": "purple"},
        {"id": "working", "name": "Working Collection", "description": "Active breeding materials", "color": "blue"},
        {"id": "active", "name": "Active Collection", "description": "Medium-term storage for distribution", "color": "green"},
        {"id": "base", "name": "Base Collection", "description": "Long-term conservation", "color": "orange"},
        {"id": "breeding", "name": "Breeding Collection", "description": "Advanced breeding lines", "color": "pink"},
        {"id": "reference", "name": "Reference Collection", "description": "Standard reference materials", "color": "cyan"},
    ]
    return {"status": "success", "data": types}


@router.get("/{collection_id}")
async def get_collection(collection_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific collection"""
    try:
        coll_uuid = uuid.UUID(collection_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid collection ID format")
    
    result = await db.execute(
        select(GermplasmCollection).where(GermplasmCollection.id == coll_uuid)
    )
    collection = result.scalar_one_or_none()
    
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    data = {
        "id": str(collection.id),
        "name": collection.name,
        "description": collection.description,
        "type": collection.collection_type.value if collection.collection_type else "working",
        "accession_count": collection.accession_count or 0,
        "species": collection.species or [],
        "curator": collection.curator_name or "",
        "curator_email": collection.curator_email or "",
        "created_at": collection.created_at.strftime("%Y-%m-%d") if collection.created_at else "",
        "updated_at": collection.updated_at.strftime("%Y-%m-%d") if collection.updated_at else "",
        "status": collection.status.value if collection.status else "active"
    }
    
    return {"status": "success", "data": data}


@router.post("")
async def create_collection(data: dict, db: AsyncSession = Depends(get_db)):
    """Create a new collection"""
    # Parse collection type
    collection_type = CollectionType.WORKING
    if data.get("type"):
        try:
            collection_type = CollectionType(data["type"])
        except ValueError:
            pass
    
    collection = GermplasmCollection(
        id=uuid.uuid4(),
        collection_code=f"COL{str(uuid.uuid4())[:8].upper()}",
        name=data.get("name", ""),
        description=data.get("description", ""),
        collection_type=collection_type,
        accession_count=data.get("accession_count", 0),
        species=data.get("species", []),
        curator_name=data.get("curator", ""),
        curator_email=data.get("curator_email", ""),
        status=CollectionStatus.ACTIVE
    )
    
    db.add(collection)
    await db.commit()
    await db.refresh(collection)
    
    response_data = {
        "id": str(collection.id),
        "name": collection.name,
        "description": collection.description,
        "type": collection.collection_type.value if collection.collection_type else "working",
        "accession_count": collection.accession_count or 0,
        "species": collection.species or [],
        "curator": collection.curator_name or "",
        "curator_email": collection.curator_email or "",
        "created_at": collection.created_at.strftime("%Y-%m-%d") if collection.created_at else "",
        "updated_at": collection.updated_at.strftime("%Y-%m-%d") if collection.updated_at else "",
        "status": collection.status.value if collection.status else "active"
    }
    
    return {"status": "success", "data": response_data, "message": "Collection created"}


@router.patch("/{collection_id}")
async def update_collection(collection_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    """Update a collection"""
    try:
        coll_uuid = uuid.UUID(collection_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid collection ID format")
    
    result = await db.execute(
        select(GermplasmCollection).where(GermplasmCollection.id == coll_uuid)
    )
    collection = result.scalar_one_or_none()
    
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    # Update fields
    if "name" in data:
        collection.name = data["name"]
    if "description" in data:
        collection.description = data["description"]
    if "type" in data:
        try:
            collection.collection_type = CollectionType(data["type"])
        except ValueError:
            pass
    if "species" in data:
        collection.species = data["species"]
    if "curator" in data:
        collection.curator_name = data["curator"]
    if "curator_email" in data:
        collection.curator_email = data["curator_email"]
    if "status" in data:
        try:
            collection.status = CollectionStatus(data["status"])
        except ValueError:
            pass
    
    collection.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(collection)
    
    response_data = {
        "id": str(collection.id),
        "name": collection.name,
        "description": collection.description,
        "type": collection.collection_type.value if collection.collection_type else "working",
        "accession_count": collection.accession_count or 0,
        "species": collection.species or [],
        "curator": collection.curator_name or "",
        "curator_email": collection.curator_email or "",
        "created_at": collection.created_at.strftime("%Y-%m-%d") if collection.created_at else "",
        "updated_at": collection.updated_at.strftime("%Y-%m-%d") if collection.updated_at else "",
        "status": collection.status.value if collection.status else "active"
    }
    
    return {"status": "success", "data": response_data, "message": "Collection updated"}


@router.delete("/{collection_id}")
async def delete_collection(collection_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a collection"""
    try:
        coll_uuid = uuid.UUID(collection_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid collection ID format")
    
    result = await db.execute(
        select(GermplasmCollection).where(GermplasmCollection.id == coll_uuid)
    )
    collection = result.scalar_one_or_none()
    
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    await db.delete(collection)
    await db.commit()
    
    return {"status": "success", "message": "Collection deleted"}


@router.post("/{collection_id}/accessions")
async def add_accessions(collection_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    """Add accessions to a collection"""
    try:
        coll_uuid = uuid.UUID(collection_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid collection ID format")
    
    result = await db.execute(
        select(GermplasmCollection).where(GermplasmCollection.id == coll_uuid)
    )
    collection = result.scalar_one_or_none()
    
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    count = data.get("count", 1)
    collection.accession_count = (collection.accession_count or 0) + count
    collection.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(collection)
    
    response_data = {
        "id": str(collection.id),
        "name": collection.name,
        "accession_count": collection.accession_count or 0,
    }
    
    return {"status": "success", "data": response_data, "message": f"Added {count} accessions"}
