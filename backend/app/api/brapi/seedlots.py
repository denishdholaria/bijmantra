"""
BrAPI v2.1 Seed Lots Endpoints

Database-backed implementation (no in-memory demo data).
Demo data is seeded into Demo Organization via seeders.

GOVERNANCE.md §4.3.1 Compliant: Fully async implementation.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
import uuid

from app.core.database import get_db
from app.api.deps import get_current_user, get_optional_user
from app.models.germplasm import Seedlot, SeedlotTransaction, Germplasm
from app.models.core import Location, Program

router = APIRouter()


class SeedLotBase(BaseModel):
    seedLotName: str
    seedLotDescription: Optional[str] = None
    germplasmDbId: Optional[str] = None
    locationDbId: Optional[str] = None
    programDbId: Optional[str] = None
    sourceCollection: Optional[str] = None
    storageLocation: Optional[str] = None
    count: Optional[int] = None
    units: Optional[str] = None
    createdDate: Optional[str] = None


class SeedLotCreate(SeedLotBase):
    pass


class SeedLotUpdate(SeedLotBase):
    seedLotName: Optional[str] = None


def _model_to_brapi(seedlot: Seedlot) -> dict:
    """Converts a Seedlot SQLAlchemy model to a BrAPI-compliant dictionary.

    Args:
        seedlot (Seedlot): The Seedlot SQLAlchemy model.

    Returns:
        dict: A dictionary representing the seed lot in BrAPI format.
    """
    return {
        "seedLotDbId": seedlot.seedlot_db_id,
        "seedLotName": seedlot.seedlot_name,
        "seedLotDescription": seedlot.seedlot_description,
        "germplasmDbId": seedlot.germplasm.germplasm_db_id if seedlot.germplasm else None,
        "locationDbId": seedlot.location.location_db_id if seedlot.location else None,
        "programDbId": seedlot.program.program_db_id if seedlot.program else None,
        "sourceCollection": seedlot.source_collection,
        "storageLocation": seedlot.storage_location,
        "count": seedlot.count,
        "units": seedlot.units,
        "createdDate": str(seedlot.creation_date) if seedlot.creation_date else None,
        "lastUpdated": str(seedlot.last_updated) if seedlot.last_updated else None,
        "additionalInfo": seedlot.additional_info,
        "externalReferences": seedlot.external_references,
    }


@router.get("/seedlots")
async def list_seedlots(
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    germplasmDbId: Optional[str] = None,
    locationDbId: Optional[str] = None,
    programDbId: Optional[str] = None,
    seedLotDbId: Optional[str] = None,
    seedLotName: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Gets a list of seed lots.

    Args:
        page (int, optional): The page number to return. Defaults to 0.
        pageSize (int, optional): The number of items to return per page. Defaults to 20.
        germplasmDbId (str, optional): The ID of the germplasm to filter by. Defaults to None.
        locationDbId (str, optional): The ID of the location to filter by. Defaults to None.
        programDbId (str, optional): The ID of the program to filter by. Defaults to None.
        seedLotDbId (str, optional): The ID of the seed lot to filter by. Defaults to None.
        seedLotName (str, optional): The name of the seed lot to filter by. Defaults to None.
        db (AsyncSession, optional): The database session. Defaults to Depends(get_db).
        current_user (User, optional): The current user. Defaults to Depends(get_optional_user).

    Returns:
        dict: A dictionary containing a list of seed lots and metadata.
    """
    # Build base statement with eager loading
    stmt = select(Seedlot).options(
        selectinload(Seedlot.germplasm),
        selectinload(Seedlot.location),
        selectinload(Seedlot.program),
    )
    
    # Filter by user's organization (multi-tenant isolation)
    if current_user and current_user.organization_id:
        stmt = stmt.where(Seedlot.organization_id == current_user.organization_id)
    
    # Apply filters
    if germplasmDbId:
        stmt = stmt.join(Seedlot.germplasm).where(Germplasm.germplasm_db_id == germplasmDbId)
    if locationDbId:
        stmt = stmt.join(Seedlot.location).where(Location.location_db_id == locationDbId)
    if programDbId:
        stmt = stmt.join(Seedlot.program).where(Program.program_db_id == programDbId)
    if seedLotDbId:
        stmt = stmt.where(Seedlot.seedlot_db_id == seedLotDbId)
    if seedLotName:
        stmt = stmt.where(Seedlot.seedlot_name.ilike(f"%{seedLotName}%"))
    
    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0
    
    # Apply pagination and execute
    stmt = stmt.offset(page * pageSize).limit(pageSize)
    result = await db.execute(stmt)
    results = result.scalars().all()
    data = [_model_to_brapi(sl) for sl in results]
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {
                "currentPage": page,
                "pageSize": pageSize,
                "totalCount": total,
                "totalPages": (total + pageSize - 1) // pageSize if total > 0 else 0
            },
            "status": [{"message": "Request successful", "messageType": "INFO"}]
        },
        "result": {"data": data}
    }


@router.post("/seedlots")
async def create_seedlot(
    seedlot: SeedLotCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Creates a new seed lot.

    Args:
        seedlot (SeedLotCreate): The seed lot to create.
        db (AsyncSession, optional): The database session. Defaults to Depends(get_db).
        current_user (User, optional): The current user. Defaults to Depends(get_current_user).

    Returns:
        dict: A dictionary containing the newly created seed lot and metadata.
    """
    org_id = current_user.organization_id if current_user else 1
    seedlot_db_id = f"seedlot_{uuid.uuid4().hex[:12]}"
    
    # Look up related entities
    germplasm_id = None
    location_id = None
    program_id = None
    
    if seedlot.germplasmDbId:
        stmt = select(Germplasm).where(Germplasm.germplasm_db_id == seedlot.germplasmDbId)
        result = await db.execute(stmt)
        g = result.scalar_one_or_none()
        if g:
            germplasm_id = g.id
    if seedlot.locationDbId:
        stmt = select(Location).where(Location.location_db_id == seedlot.locationDbId)
        result = await db.execute(stmt)
        loc = result.scalar_one_or_none()
        if loc:
            location_id = loc.id
    if seedlot.programDbId:
        stmt = select(Program).where(Program.program_db_id == seedlot.programDbId)
        result = await db.execute(stmt)
        prog = result.scalar_one_or_none()
        if prog:
            program_id = prog.id
    
    new_seedlot = Seedlot(
        organization_id=org_id,
        seedlot_db_id=seedlot_db_id,
        seedlot_name=seedlot.seedLotName,
        seedlot_description=seedlot.seedLotDescription,
        germplasm_id=germplasm_id,
        location_id=location_id,
        program_id=program_id,
        source_collection=seedlot.sourceCollection,
        storage_location=seedlot.storageLocation,
        count=seedlot.count,
        units=seedlot.units,
    )
    
    db.add(new_seedlot)
    await db.commit()
    await db.refresh(new_seedlot)
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Seed lot created successfully", "messageType": "INFO"}]
        },
        "result": _model_to_brapi(new_seedlot)
    }


@router.get("/seedlots/{seedLotDbId}")
async def get_seedlot(
    seedLotDbId: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    """Gets a seed lot by its ID.

    Args:
        seedLotDbId (str): The ID of the seed lot to retrieve.
        db (AsyncSession, optional): The database session. Defaults to Depends(get_db).
        current_user (User, optional): The current user. Defaults to Depends(get_optional_user).

    Raises:
        HTTPException: If the seed lot is not found.

    Returns:
        dict: A dictionary containing the seed lot and metadata.
    """
    stmt = select(Seedlot).options(
        selectinload(Seedlot.germplasm),
        selectinload(Seedlot.location),
        selectinload(Seedlot.program),
    ).where(Seedlot.seedlot_db_id == seedLotDbId)
    
    result = await db.execute(stmt)
    seedlot = result.scalar_one_or_none()
    
    if not seedlot:
        raise HTTPException(status_code=404, detail="Seed lot not found")
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": []
        },
        "result": _model_to_brapi(seedlot)
    }


@router.put("/seedlots/{seedLotDbId}")
async def update_seedlot(
    seedLotDbId: str,
    seedlot_data: SeedLotUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Updates a seed lot.

    Args:
        seedLotDbId (str): The ID of the seed lot to update.
        seedlot_data (SeedLotUpdate): The data to update the seed lot with.
        db (AsyncSession, optional): The database session. Defaults to Depends(get_db).
        current_user (User, optional): The current user. Defaults to Depends(get_current_user).

    Raises:
        HTTPException: If the seed lot is not found.

    Returns:
        dict: A dictionary containing the updated seed lot and metadata.
    """
    stmt = select(Seedlot).options(
        selectinload(Seedlot.germplasm),
        selectinload(Seedlot.location),
        selectinload(Seedlot.program),
    ).where(Seedlot.seedlot_db_id == seedLotDbId)
    
    result = await db.execute(stmt)
    seedlot = result.scalar_one_or_none()
    
    if not seedlot:
        raise HTTPException(status_code=404, detail="Seed lot not found")
    
    if seedlot_data.seedLotName:
        seedlot.seedlot_name = seedlot_data.seedLotName
    if seedlot_data.seedLotDescription:
        seedlot.seedlot_description = seedlot_data.seedLotDescription
    if seedlot_data.storageLocation:
        seedlot.storage_location = seedlot_data.storageLocation
    if seedlot_data.count is not None:
        seedlot.count = seedlot_data.count
    if seedlot_data.units:
        seedlot.units = seedlot_data.units
    
    await db.commit()
    await db.refresh(seedlot)
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Seed lot updated successfully", "messageType": "INFO"}]
        },
        "result": _model_to_brapi(seedlot)
    }


# Transaction endpoints

class TransactionBase(BaseModel):
    seedLotDbId: Optional[str] = None
    transactionDescription: Optional[str] = None
    transactionTimestamp: Optional[str] = None
    amount: Optional[float] = None
    units: Optional[str] = None
    fromSeedLotDbId: Optional[str] = None
    toSeedLotDbId: Optional[str] = None
    additionalInfo: Optional[dict] = None
    externalReferences: Optional[dict] = None


class TransactionCreate(TransactionBase):
    pass


def _transaction_to_brapi(tx: SeedlotTransaction) -> dict:
    """Converts a SeedlotTransaction SQLAlchemy model to a BrAPI-compliant dictionary.

    Args:
        tx (SeedlotTransaction): The SeedlotTransaction SQLAlchemy model.

    Returns:
        dict: A dictionary representing the seed lot transaction in BrAPI format.
    """
    return {
        "transactionDbId": tx.transaction_db_id,
        "seedLotDbId": tx.seedlot.seedlot_db_id if tx.seedlot else None,
        "transactionDescription": tx.transaction_description,
        "transactionTimestamp": tx.transaction_timestamp,
        "amount": tx.amount,
        "units": tx.units,
        "fromSeedLotDbId": tx.from_seedlot_db_id,
        "toSeedLotDbId": tx.to_seedlot_db_id,
        "additionalInfo": tx.additional_info,
        "externalReferences": tx.external_references,
    }


@router.get("/seedlots/transactions")
async def list_all_transactions(
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    seedLotDbId: Optional[str] = None,
    transactionDbId: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Gets a list of all seed lot transactions.

    Args:
        page (int, optional): The page number to return. Defaults to 0.
        pageSize (int, optional): The number of items to return per page. Defaults to 20.
        seedLotDbId (str, optional): The ID of the seed lot to filter by. Defaults to None.
        transactionDbId (str, optional): The ID of the transaction to filter by. Defaults to None.
        db (AsyncSession, optional): The database session. Defaults to Depends(get_db).
        current_user (User, optional): The current user. Defaults to Depends(get_optional_user).

    Returns:
        dict: A dictionary containing a list of seed lot transactions and metadata.
    """
    stmt = select(SeedlotTransaction).options(selectinload(SeedlotTransaction.seedlot))
    
    if seedLotDbId:
        stmt = stmt.join(SeedlotTransaction.seedlot).where(Seedlot.seedlot_db_id == seedLotDbId)
    if transactionDbId:
        stmt = stmt.where(SeedlotTransaction.transaction_db_id == transactionDbId)
    
    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0
    
    # Apply pagination and execute
    stmt = stmt.offset(page * pageSize).limit(pageSize)
    result = await db.execute(stmt)
    results = result.scalars().all()
    data = [_transaction_to_brapi(tx) for tx in results]
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {
                "currentPage": page,
                "pageSize": pageSize,
                "totalCount": total,
                "totalPages": (total + pageSize - 1) // pageSize if total > 0 else 0
            },
            "status": [{"message": "Request successful", "messageType": "INFO"}]
        },
        "result": {"data": data}
    }


@router.get("/seedlots/{seedLotDbId}/transactions")
async def list_seedlot_transactions(
    seedLotDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Gets a list of transactions for a specific seed lot.

    Args:
        seedLotDbId (str): The ID of the seed lot to retrieve transactions for.
        page (int, optional): The page number to return. Defaults to 0.
        pageSize (int, optional): The number of items to return per page. Defaults to 20.
        db (AsyncSession, optional): The database session. Defaults to Depends(get_db).
        current_user (User, optional): The current user. Defaults to Depends(get_optional_user).

    Raises:
        HTTPException: If the seed lot is not found.

    Returns:
        dict: A dictionary containing a list of seed lot transactions and metadata.
    """
    # First find the seedlot
    stmt = select(Seedlot).where(Seedlot.seedlot_db_id == seedLotDbId)
    result = await db.execute(stmt)
    seedlot = result.scalar_one_or_none()
    
    if not seedlot:
        raise HTTPException(status_code=404, detail="Seed lot not found")
    
    # Get transactions
    stmt = select(SeedlotTransaction).options(
        selectinload(SeedlotTransaction.seedlot)
    ).where(SeedlotTransaction.seedlot_id == seedlot.id)
    
    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0
    
    # Apply pagination and execute
    stmt = stmt.offset(page * pageSize).limit(pageSize)
    result = await db.execute(stmt)
    results = result.scalars().all()
    data = [_transaction_to_brapi(tx) for tx in results]
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {
                "currentPage": page,
                "pageSize": pageSize,
                "totalCount": total,
                "totalPages": (total + pageSize - 1) // pageSize if total > 0 else 0
            },
            "status": [{"message": "Request successful", "messageType": "INFO"}]
        },
        "result": {"data": data}
    }


@router.post("/seedlots/transactions")
async def create_transaction(
    transaction: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Creates a new seed lot transaction.

    Args:
        transaction (TransactionCreate): The transaction to create.
        db (AsyncSession, optional): The database session. Defaults to Depends(get_db).
        current_user (User, optional): The current user. Defaults to Depends(get_current_user).

    Returns:
        dict: A dictionary containing the newly created transaction and metadata.
    """
    org_id = current_user.organization_id if current_user else 1
    tx_db_id = f"tx_{uuid.uuid4().hex[:12]}"
    
    # Look up seedlot
    seedlot_id = None
    if transaction.seedLotDbId:
        stmt = select(Seedlot).where(Seedlot.seedlot_db_id == transaction.seedLotDbId)
        result = await db.execute(stmt)
        sl = result.scalar_one_or_none()
        if sl:
            seedlot_id = sl.id
    
    # Prepare additional info with user details
    additional_info = transaction.additionalInfo or {}
    if current_user:
        additional_info["user_id"] = current_user.id
        additional_info["user_name"] = current_user.full_name or current_user.email

    new_tx = SeedlotTransaction(
        organization_id=org_id,
        transaction_db_id=tx_db_id,
        seedlot_id=seedlot_id,
        transaction_description=transaction.transactionDescription,
        transaction_timestamp=transaction.transactionTimestamp,
        amount=transaction.amount,
        units=transaction.units,
        from_seedlot_db_id=transaction.fromSeedLotDbId,
        to_seedlot_db_id=transaction.toSeedLotDbId,
        additional_info=additional_info,
        external_references=transaction.externalReferences,
    )
    
    db.add(new_tx)
    await db.commit()
    await db.refresh(new_tx)
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Transaction created successfully", "messageType": "INFO"}]
        },
        "result": _transaction_to_brapi(new_tx)
    }
