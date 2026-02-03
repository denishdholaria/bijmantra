"""
BrAPI v2.1 Germplasm Endpoints

Production-ready implementation using database only.
Demo data is sandboxed in "Demo Organization" - no in-memory fallbacks.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, ConfigDict
import uuid

from app.core.database import get_db
from app.api.deps import get_current_user, get_optional_user
from app.models.germplasm import Germplasm as GermplasmModel, Cross
from app.models.core import User

router = APIRouter()


class GermplasmBase(BaseModel):
    germplasmName: str
    accessionNumber: Optional[str] = None
    germplasmPUI: Optional[str] = None
    defaultDisplayName: Optional[str] = None
    species: Optional[str] = None
    genus: Optional[str] = None
    subtaxa: Optional[str] = None
    commonCropName: Optional[str] = None
    instituteCode: Optional[str] = None
    instituteName: Optional[str] = None
    biologicalStatusOfAccessionCode: Optional[str] = None
    countryOfOriginCode: Optional[str] = None
    synonyms: Optional[List[str]] = []
    pedigree: Optional[str] = None
    seedSource: Optional[str] = None
    seedSourceDescription: Optional[str] = None


class GermplasmCreate(GermplasmBase):
    pass


class Germplasm(GermplasmBase):
    germplasmDbId: str
    
    model_config = ConfigDict(from_attributes=True)


def _model_to_brapi(model) -> dict:
    """Convert a database model to a BrAPI response format.

    Args:
        model (GermplasmModel): The database model to convert.

    Returns:
        A dictionary representing the BrAPI response.
    """
    return {
        "germplasmDbId": model.germplasm_db_id,
        "germplasmName": model.germplasm_name,
        "germplasmPUI": model.germplasm_pui,
        "defaultDisplayName": model.default_display_name or model.germplasm_name,
        "accessionNumber": model.accession_number,
        "species": model.species,
        "genus": model.genus,
        "subtaxa": model.subtaxa,
        "commonCropName": model.common_crop_name,
        "instituteCode": model.institute_code,
        "instituteName": model.institute_name,
        "biologicalStatusOfAccessionCode": model.biological_status_of_accession_code,
        "countryOfOriginCode": model.country_of_origin_code,
        "synonyms": model.synonyms or [],
        "pedigree": model.pedigree,
        "seedSource": model.seed_source,
        "seedSourceDescription": model.seed_source_description,
        "additionalInfo": model.additional_info,
        "externalReferences": model.external_references,
    }


def _brapi_response(data, page: int = 0, pageSize: int = 20, total: int = 0, message: str = "Request successful"):
    """Create a standard BrAPI response.

    Args:
        data: The data to include in the response.
        page: The current page number.
        pageSize: The number of items per page.
        total: The total number of items.
        message: A message to include in the response.

    Returns:
        A dictionary representing the standard BrAPI response.
    """
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {
                "currentPage": page,
                "pageSize": pageSize,
                "totalCount": total,
                "totalPages": (total + pageSize - 1) // pageSize if total > 0 else 0
            },
            "status": [{"message": message, "messageType": "INFO"}]
        },
        "result": {"data": data} if isinstance(data, list) else data
    }


@router.get("/germplasm")
async def list_germplasm(
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    germplasmName: Optional[str] = None,
    commonCropName: Optional[str] = None,
    species: Optional[str] = None,
    genus: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
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
        db (AsyncSession): The database session.
        current_user (Optional[User]): The current user.

    Returns:
        A BrAPI response containing a list of germplasm.
    """
    # Build query
    query = select(GermplasmModel)
    count_query = select(func.count(GermplasmModel.id))
    
    # Filter by user's organization (multi-tenant isolation)
    if current_user and current_user.organization_id:
        query = query.where(GermplasmModel.organization_id == current_user.organization_id)
        count_query = count_query.where(GermplasmModel.organization_id == current_user.organization_id)
    
    # Apply filters
    if germplasmName:
        query = query.where(GermplasmModel.germplasm_name.ilike(f"%{germplasmName}%"))
        count_query = count_query.where(GermplasmModel.germplasm_name.ilike(f"%{germplasmName}%"))
    if commonCropName:
        query = query.where(GermplasmModel.common_crop_name.ilike(f"%{commonCropName}%"))
        count_query = count_query.where(GermplasmModel.common_crop_name.ilike(f"%{commonCropName}%"))
    if species:
        query = query.where(GermplasmModel.species.ilike(f"%{species}%"))
        count_query = count_query.where(GermplasmModel.species.ilike(f"%{species}%"))
    if genus:
        query = query.where(GermplasmModel.genus.ilike(f"%{genus}%"))
        count_query = count_query.where(GermplasmModel.genus.ilike(f"%{genus}%"))
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    query = query.offset(page * pageSize).limit(pageSize)
    
    # Execute query
    result = await db.execute(query)
    germplasm_list = result.scalars().all()
    
    data = [_model_to_brapi(g) for g in germplasm_list]
    return _brapi_response(data, page, pageSize, total)


@router.post("/germplasm")
async def create_germplasm(
    germplasm: GermplasmCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Create a new germplasm.

    Args:
        germplasm (GermplasmCreate): The germplasm to create.
        db (AsyncSession): The database session.
        current_user (User): The current user.

    Returns:
        A BrAPI response containing the new germplasm.
    """
    # Get organization from user
    org_id = getattr(current_user, 'organization_id', 1)
    
    # Generate unique ID
    germplasm_db_id = f"germplasm_{uuid.uuid4().hex[:8]}"
    
    new_germplasm = GermplasmModel(
        organization_id=org_id,
        germplasm_db_id=germplasm_db_id,
        germplasm_name=germplasm.germplasmName,
        accession_number=germplasm.accessionNumber,
        germplasm_pui=germplasm.germplasmPUI,
        default_display_name=germplasm.defaultDisplayName,
        species=germplasm.species,
        genus=germplasm.genus,
        subtaxa=germplasm.subtaxa,
        common_crop_name=germplasm.commonCropName,
        institute_code=germplasm.instituteCode,
        institute_name=germplasm.instituteName,
        biological_status_of_accession_code=germplasm.biologicalStatusOfAccessionCode,
        country_of_origin_code=germplasm.countryOfOriginCode,
        synonyms=germplasm.synonyms,
        pedigree=germplasm.pedigree,
        seed_source=germplasm.seedSource,
        seed_source_description=germplasm.seedSourceDescription,
    )
    
    db.add(new_germplasm)
    await db.commit()
    await db.refresh(new_germplasm)
    
    return _brapi_response(_model_to_brapi(new_germplasm), total=1, message="Germplasm created successfully")


@router.get("/germplasm/{germplasmDbId}")
async def get_germplasm(
    germplasmDbId: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get a germplasm by its ID.

    Args:
        germplasmDbId (str): The ID of the germplasm to get.
        db (AsyncSession): The database session.
        current_user (Optional[User]): The current user.

    Returns:
        A BrAPI response containing the germplasm.

    Raises:
        HTTPException: If the germplasm is not found.
    """
    query = select(GermplasmModel).where(GermplasmModel.germplasm_db_id == germplasmDbId)
    result = await db.execute(query)
    germplasm = result.scalar_one_or_none()
    
    if not germplasm:
        raise HTTPException(status_code=404, detail="Germplasm not found")
    
    return _brapi_response(_model_to_brapi(germplasm), total=1)


@router.put("/germplasm/{germplasmDbId}")
async def update_germplasm(
    germplasmDbId: str,
    germplasm: GermplasmCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Update a germplasm.

    Args:
        germplasmDbId (str): The ID of the germplasm to update.
        germplasm (GermplasmCreate): The new germplasm data.
        db (AsyncSession): The database session.
        current_user (User): The current user.

    Returns:
        A BrAPI response containing the updated germplasm.

    Raises:
        HTTPException: If the germplasm is not found.
    """
    query = select(GermplasmModel).where(GermplasmModel.germplasm_db_id == germplasmDbId)
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Germplasm not found")
    
    existing.germplasm_name = germplasm.germplasmName
    existing.accession_number = germplasm.accessionNumber
    existing.germplasm_pui = germplasm.germplasmPUI
    existing.default_display_name = germplasm.defaultDisplayName
    existing.species = germplasm.species
    existing.genus = germplasm.genus
    existing.subtaxa = germplasm.subtaxa
    existing.common_crop_name = germplasm.commonCropName
    existing.institute_code = germplasm.instituteCode
    existing.institute_name = germplasm.instituteName
    existing.biological_status_of_accession_code = germplasm.biologicalStatusOfAccessionCode
    existing.country_of_origin_code = germplasm.countryOfOriginCode
    existing.synonyms = germplasm.synonyms
    existing.pedigree = germplasm.pedigree
    existing.seed_source = germplasm.seedSource
    existing.seed_source_description = germplasm.seedSourceDescription
    
    await db.commit()
    await db.refresh(existing)
    
    return _brapi_response(_model_to_brapi(existing), total=1, message="Germplasm updated successfully")


@router.delete("/germplasm/{germplasmDbId}")
async def delete_germplasm(
    germplasmDbId: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Delete a germplasm.

    Args:
        germplasmDbId (str): The ID of the germplasm to delete.
        db (AsyncSession): The database session.
        current_user (User): The current user.

    Returns:
        A BrAPI response indicating that the germplasm was deleted.

    Raises:
        HTTPException: If the germplasm is not found.
    """
    query = select(GermplasmModel).where(GermplasmModel.germplasm_db_id == germplasmDbId)
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Germplasm not found")
    
    await db.delete(existing)
    await db.commit()
    
    return _brapi_response(None, total=0, message="Germplasm deleted successfully")


@router.get("/germplasm/{germplasmDbId}/pedigree")
async def get_germplasm_pedigree(
    germplasmDbId: str,
    notation: Optional[str] = Query("purdy", description="Pedigree notation: purdy, lamacraft, or rodriguez"),
    includeSiblings: bool = Query(False, description="Include siblings"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get pedigree information for a germplasm.

    Args:
        germplasmDbId (str): The ID of the germplasm to get pedigree information for.
        notation (Optional[str]): The pedigree notation to use.
        includeSiblings (bool): Whether to include siblings in the pedigree.
        db (AsyncSession): The database session.
        current_user (Optional[User]): The current user.

    Returns:
        A BrAPI response containing the pedigree information.

    Raises:
        HTTPException: If the germplasm is not found.
    """
    query = select(GermplasmModel).where(GermplasmModel.germplasm_db_id == germplasmDbId)
    result = await db.execute(query)
    germ = result.scalar_one_or_none()
    
    if not germ:
        raise HTTPException(status_code=404, detail="Germplasm not found")
    
    # TODO: Implement real pedigree traversal when Cross model is populated
    pedigree_data = {
        "germplasmDbId": germplasmDbId,
        "germplasmName": germ.germplasm_name,
        "pedigree": germ.pedigree or f"{germ.germplasm_name}/Unknown",
        "crossingProjectDbId": None,
        "crossingYear": None,
        "familyCode": None,
        "breedingMethodDbId": germ.breeding_method_db_id,
        "breedingMethodName": None,
        "parents": [],
        "siblings": []
    }
    
    return _brapi_response(pedigree_data, total=1)


@router.get("/germplasm/{germplasmDbId}/progeny")
async def get_germplasm_progeny(
    germplasmDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get the progeny of a germplasm.

    Args:
        germplasmDbId (str): The ID of the germplasm to get the progeny of.
        page (int): The page number to return.
        pageSize (int): The number of items to return per page.
        db (AsyncSession): The database session.
        current_user (Optional[User]): The current user.

    Returns:
        A BrAPI response containing the progeny of the germplasm.

    Raises:
        HTTPException: If the germplasm is not found.
    """
    query = select(GermplasmModel).where(GermplasmModel.germplasm_db_id == germplasmDbId)
    result = await db.execute(query)
    germ = result.scalar_one_or_none()
    
    if not germ:
        raise HTTPException(status_code=404, detail="Germplasm not found")
    
    # Query Cross table for actual progeny
    # 1. Find crosses where this germplasm is a parent
    stmt = select(Cross).where(
        (Cross.parent1_db_id == germ.id) |
        (Cross.parent2_db_id == germ.id)
    )
    crosses_result = await db.execute(stmt)
    crosses = crosses_result.scalars().all()

    if not crosses:
        return _brapi_response({
            "germplasmDbId": germplasmDbId,
            "germplasmName": germ.germplasm_name,
            "progeny": []
        }, page, pageSize, total=0)

    # Map cross_id to the role the parent played
    cross_roles = {}
    for c in crosses:
        if c.parent1_db_id == germ.id:
            cross_roles[c.id] = c.parent1_type
        elif c.parent2_db_id == germ.id:
            cross_roles[c.id] = c.parent2_type

    # 2. Find progeny from these crosses
    cross_ids = list(cross_roles.keys())

    progeny_query = select(GermplasmModel).where(GermplasmModel.cross_id.in_(cross_ids))
    count_query = select(func.count(GermplasmModel.id)).where(GermplasmModel.cross_id.in_(cross_ids))

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    progeny_query = progeny_query.offset(page * pageSize).limit(pageSize)

    progeny_result = await db.execute(progeny_query)
    progeny_list = progeny_result.scalars().all()

    # 3. Format response
    progeny_data_list = []
    for p in progeny_list:
        p_role = cross_roles.get(p.cross_id, "UNKNOWN")
        progeny_data_list.append({
            "germplasmDbId": p.germplasm_db_id,
            "germplasmName": p.germplasm_name,
            "parentType": p_role
        })

    result_data = {
        "germplasmDbId": germplasmDbId,
        "germplasmName": germ.germplasm_name,
        "progeny": progeny_data_list
    }
    
    return _brapi_response(result_data, page, pageSize, total)


@router.get("/germplasm/{germplasmDbId}/mcpd")
async def get_germplasm_mcpd(
    germplasmDbId: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get MCPD (Multi-Crop Passport Descriptor) data for a germplasm.

    Args:
        germplasmDbId (str): The ID of the germplasm to get MCPD data for.
        db (AsyncSession): The database session.
        current_user (Optional[User]): The current user.

    Returns:
        A BrAPI response containing the MCPD data.

    Raises:
        HTTPException: If the germplasm is not found.
    """
    query = select(GermplasmModel).where(GermplasmModel.germplasm_db_id == germplasmDbId)
    result = await db.execute(query)
    germ = result.scalar_one_or_none()
    
    if not germ:
        raise HTTPException(status_code=404, detail="Germplasm not found")
    
    mcpd_data = {
        "germplasmDbId": germplasmDbId,
        "accessionNumber": germ.accession_number,
        "accessionNames": [germ.germplasm_name],
        "acquisitionDate": str(germ.acquisition_date) if germ.acquisition_date else None,
        "acquisitionSourceCode": germ.acquisition_source_code,
        "alternateIDs": [],
        "ancestralData": germ.pedigree,
        "biologicalStatusOfAccessionCode": germ.biological_status_of_accession_code,
        "breedingInstitutes": [],
        "collectingInfo": {
            "collectingDate": str(germ.collection_date) if germ.collection_date else None,
            "collectingInstitutes": [],
            "collectingMissionIdentifier": None,
            "collectingNumber": None,
            "collectingSite": germ.collection_site
        },
        "commonCropName": germ.common_crop_name,
        "countryOfOrigin": germ.country_of_origin_code,
        "donorInfo": {
            "donorAccessionNumber": None,
            "donorAccessionPui": None,
            "donorInstitute": None
        },
        "genus": germ.genus,
        "germplasmPUI": germ.germplasm_pui,
        "instituteCode": germ.institute_code,
        "mlsStatus": None,
        "remarks": None,
        "safetyDuplicateInstitutes": [],
        "species": germ.species,
        "speciesAuthority": germ.species_authority,
        "storageTypeCodes": germ.storage_types or [],
        "subtaxon": germ.subtaxa,
        "subtaxonAuthority": germ.subtaxa_authority
    }
    
    return _brapi_response(mcpd_data, total=1)
