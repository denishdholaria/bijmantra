"""
BrAPI v2.1 Seed Lots Endpoints

Database-backed implementation (no in-memory demo data).
Demo data is seeded into Demo Organization via seeders.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
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
    """Convert SQLAlchemy model to BrAPI response format"""
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
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get list of seed lots from database"""
    query = db.query(Seedlot)
    
    if germplasmDbId:
        query = query.join(Germplasm).filter(Germplasm.germplasm_db_id == germplasmDbId)
    if locationDbId:
        query = query.join(Location).filter(Location.location_db_id == locationDbId)
    if programDbId:
        query = query.join(Program).filter(Program.program_db_id == programDbId)
    if seedLotDbId:
        query = query.filter(Seedlot.seedlot_db_id == seedLotDbId)
    if seedLotName:
        query = query.filter(Seedlot.seedlot_name.ilike(f"%{seedLotName}%"))
    
    total = query.count()
    results = query.offset(page * pageSize).limit(pageSize).all()
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
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create new seed lot in database"""
    org_id = current_user.organization_id if current_user else 1
    seedlot_db_id = f"seedlot_{uuid.uuid4().hex[:12]}"
    
    # Look up related entities
    germplasm_id = None
    location_id = None
    program_id = None
    
    if seedlot.germplasmDbId:
        g = db.query(Germplasm).filter(Germplasm.germplasm_db_id == seedlot.germplasmDbId).first()
        if g:
            germplasm_id = g.id
    if seedlot.locationDbId:
        loc = db.query(Location).filter(Location.location_db_id == seedlot.locationDbId).first()
        if loc:
            location_id = loc.id
    if seedlot.programDbId:
        prog = db.query(Program).filter(Program.program_db_id == seedlot.programDbId).first()
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
    db.commit()
    db.refresh(new_seedlot)
    
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
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    """Get seed lot by ID from database"""
    seedlot = db.query(Seedlot).filter(Seedlot.seedlot_db_id == seedLotDbId).first()
    
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
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update seed lot in database"""
    seedlot = db.query(Seedlot).filter(Seedlot.seedlot_db_id == seedLotDbId).first()
    
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
    
    db.commit()
    db.refresh(seedlot)
    
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


class TransactionCreate(TransactionBase):
    pass


def _transaction_to_brapi(tx: SeedlotTransaction) -> dict:
    """Convert transaction model to BrAPI format"""
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
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get list of all seed lot transactions from database"""
    query = db.query(SeedlotTransaction)
    
    if seedLotDbId:
        query = query.join(Seedlot).filter(Seedlot.seedlot_db_id == seedLotDbId)
    if transactionDbId:
        query = query.filter(SeedlotTransaction.transaction_db_id == transactionDbId)
    
    total = query.count()
    results = query.offset(page * pageSize).limit(pageSize).all()
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
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get transactions for a specific seed lot"""
    seedlot = db.query(Seedlot).filter(Seedlot.seedlot_db_id == seedLotDbId).first()
    if not seedlot:
        raise HTTPException(status_code=404, detail="Seed lot not found")
    
    query = db.query(SeedlotTransaction).filter(SeedlotTransaction.seedlot_id == seedlot.id)
    
    total = query.count()
    results = query.offset(page * pageSize).limit(pageSize).all()
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
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create new seed lot transaction in database"""
    org_id = current_user.organization_id if current_user else 1
    tx_db_id = f"tx_{uuid.uuid4().hex[:12]}"
    
    # Look up seedlot
    seedlot_id = None
    if transaction.seedLotDbId:
        sl = db.query(Seedlot).filter(Seedlot.seedlot_db_id == transaction.seedLotDbId).first()
        if sl:
            seedlot_id = sl.id
    
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
    )
    
    db.add(new_tx)
    db.commit()
    db.refresh(new_tx)
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Transaction created successfully", "messageType": "INFO"}]
        },
        "result": _transaction_to_brapi(new_tx)
    }
