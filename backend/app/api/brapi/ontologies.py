"""
BrAPI v2.1 Ontologies Endpoints
Trait ontologies for observation variables

Database-backed implementation for production use.
"""

from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List, Dict, Any
import uuid

from app.core.database import get_db
from app.api.deps import get_organization_id
from app.models.core import Ontology as OntologyModel

router = APIRouter()


def model_to_dict(ontology: OntologyModel) -> Dict[str, Any]:
    """Convert Ontology model to BrAPI response dict"""
    return {
        "ontologyDbId": ontology.ontology_db_id,
        "ontologyName": ontology.ontology_name,
        "description": ontology.description,
        "version": ontology.version,
        "authors": ontology.authors,
        "copyright": ontology.copyright,
        "licence": ontology.licence,
        "documentationURL": ontology.documentation_url,
        "additionalInfo": ontology.additional_info or {},
    }


def brapi_response(result, page: int = 0, page_size: int = 1000, total: int = None):
    """Standard BrAPI response wrapper"""
    if isinstance(result, list):
        if total is None:
            total = len(result)
        return {
            "metadata": {
                "datafiles": [],
                "pagination": {
                    "currentPage": page,
                    "pageSize": page_size,
                    "totalCount": total,
                    "totalPages": max(1, (total + page_size - 1) // page_size)
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


@router.get("/ontologies")
async def get_ontologies(
    ontologyDbId: Optional[str] = None,
    ontologyName: Optional[str] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get list of ontologies"""
    
    # Build query
    query = select(OntologyModel).where(OntologyModel.organization_id == org_id)
    
    if ontologyDbId:
        query = query.where(OntologyModel.ontology_db_id == ontologyDbId)
    if ontologyName:
        query = query.where(OntologyModel.ontology_name.ilike(f"%{ontologyName}%"))
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total_count = total_result.scalar() or 0
    
    # Apply pagination
    query = query.order_by(OntologyModel.ontology_name)
    query = query.offset(page * pageSize).limit(pageSize)
    
    result = await db.execute(query)
    ontologies = result.scalars().all()
    
    # Convert to BrAPI format
    ontologies_data = [model_to_dict(o) for o in ontologies]
    
    return brapi_response(ontologies_data, page, pageSize, total_count)


@router.get("/ontologies/{ontologyDbId}")
async def get_ontology(
    ontologyDbId: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get a single ontology by ID"""
    
    query = select(OntologyModel).where(
        OntologyModel.ontology_db_id == ontologyDbId,
        OntologyModel.organization_id == org_id
    )
    result = await db.execute(query)
    ontology = result.scalar_one_or_none()
    
    if not ontology:
        return {
            "metadata": {
                "status": [{"message": f"Ontology {ontologyDbId} not found", "messageType": "ERROR"}]
            },
            "result": None
        }
    
    return brapi_response(model_to_dict(ontology))


@router.post("/ontologies")
async def create_ontologies(
    ontologies: List[dict],
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Create new ontologies"""
    created = []
    
    for ontology_data in ontologies:
        ontology = OntologyModel(
            organization_id=org_id,
            ontology_db_id=str(uuid.uuid4()),
            ontology_name=ontology_data.get("ontologyName", ""),
            description=ontology_data.get("description"),
            version=ontology_data.get("version"),
            authors=ontology_data.get("authors"),
            copyright=ontology_data.get("copyright"),
            licence=ontology_data.get("licence"),
            documentation_url=ontology_data.get("documentationURL"),
            additional_info=ontology_data.get("additionalInfo", {}),
        )
        db.add(ontology)
        created.append(ontology)
    
    await db.commit()
    
    # Refresh and convert to dict
    created_data = []
    for ontology in created:
        await db.refresh(ontology)
        created_data.append(model_to_dict(ontology))
    
    return brapi_response(created_data)


@router.put("/ontologies/{ontologyDbId}")
async def update_ontology(
    ontologyDbId: str,
    ontology_data: dict,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Update an existing ontology"""
    
    query = select(OntologyModel).where(
        OntologyModel.ontology_db_id == ontologyDbId,
        OntologyModel.organization_id == org_id
    )
    result = await db.execute(query)
    ontology = result.scalar_one_or_none()
    
    if not ontology:
        return {
            "metadata": {
                "status": [{"message": f"Ontology {ontologyDbId} not found", "messageType": "ERROR"}]
            },
            "result": None
        }
    
    # Update fields
    if "ontologyName" in ontology_data:
        ontology.ontology_name = ontology_data["ontologyName"]
    if "description" in ontology_data:
        ontology.description = ontology_data["description"]
    if "version" in ontology_data:
        ontology.version = ontology_data["version"]
    if "authors" in ontology_data:
        ontology.authors = ontology_data["authors"]
    if "copyright" in ontology_data:
        ontology.copyright = ontology_data["copyright"]
    if "licence" in ontology_data:
        ontology.licence = ontology_data["licence"]
    if "documentationURL" in ontology_data:
        ontology.documentation_url = ontology_data["documentationURL"]
    if "additionalInfo" in ontology_data:
        ontology.additional_info = ontology_data["additionalInfo"]
    
    await db.commit()
    await db.refresh(ontology)
    
    return brapi_response(model_to_dict(ontology))


@router.delete("/ontologies/{ontologyDbId}")
async def delete_ontology(
    ontologyDbId: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Delete an ontology"""
    
    query = select(OntologyModel).where(
        OntologyModel.ontology_db_id == ontologyDbId,
        OntologyModel.organization_id == org_id
    )
    result = await db.execute(query)
    ontology = result.scalar_one_or_none()
    
    if not ontology:
        raise HTTPException(status_code=404, detail="Ontology not found")
    
    await db.delete(ontology)
    await db.commit()
    
    return {"message": "Ontology deleted successfully"}
