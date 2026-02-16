"""
BrAPI v2.1 - People/Contacts endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
import uuid

from app.core.database import get_db
from app.api.deps import get_current_user, get_optional_user
from app.models.core import Person as PersonModel

router = APIRouter()


# ============ Schemas ============

class PersonBase(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    middleName: Optional[str] = None
    emailAddress: Optional[str] = None
    phoneNumber: Optional[str] = None
    mailingAddress: Optional[str] = None
    userId: Optional[str] = None
    description: Optional[str] = None
    additionalInfo: Optional[dict] = None
    externalReferences: Optional[list] = None


class PersonCreate(PersonBase):
    pass


class PersonUpdate(PersonBase):
    pass


class Person(PersonBase):
    personDbId: str

    model_config = ConfigDict(from_attributes=True)


class BrAPIMetadata(BaseModel):
    datafiles: List[str] = []
    pagination: dict
    status: List[dict]


class BrAPIListResponse(BaseModel):
    metadata: BrAPIMetadata
    result: dict


class BrAPISingleResponse(BaseModel):
    metadata: BrAPIMetadata
    result: dict


# ============ Helper Functions ============

def _model_to_brapi(person: PersonModel) -> dict:
    """Converts a PersonModel object to a BrAPI-compliant dictionary.

    Args:
        person (PersonModel): The PersonModel object to convert.

    Returns:
        dict: A dictionary representing the person in BrAPI format.
    """
    return {
        "personDbId": person.person_db_id,
        "firstName": person.first_name,
        "lastName": person.last_name,
        "middleName": person.middle_name,
        "emailAddress": person.email_address,
        "phoneNumber": person.phone_number,
        "mailingAddress": person.mailing_address,
        "userId": person.user_id,
        "additionalInfo": person.additional_info or {},
        "externalReferences": person.external_references or [],
    }


# ============ Helper Functions (BrAPI Response) ============

def create_brapi_response(data: any, page: int, page_size: int, total_count: int):
    """Creates a BrAPI-compliant list response with metadata.

    Args:
        data (any): The data to include in the response.
        page (int): The current page number.
        page_size (int): The number of items per page.
        total_count (int): The total number of items.

    Returns:
        dict: A BrAPI-compliant dictionary with metadata and data.
    """
    total_pages = max(1, (total_count + page_size - 1) // page_size)

    return {
        "metadata": {
            "datafiles": [],
            "pagination": {
                "currentPage": page,
                "pageSize": page_size,
                "totalCount": total_count,
                "totalPages": total_pages,
            },
            "status": [{"message": "Success", "messageType": "INFO"}],
        },
        "result": {"data": data},
    }


def create_single_response(data: any):
    """Creates a BrAPI-compliant single item response.

    Args:
        data (any): The data to include in the response.

    Returns:
        dict: A BrAPI-compliant dictionary for a single item.
    """
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {
                "currentPage": 0,
                "pageSize": 1,
                "totalCount": 1,
                "totalPages": 1,
            },
            "status": [{"message": "Success", "messageType": "INFO"}],
        },
        "result": data,
    }


# ============ Endpoints ============

@router.get("/people")
async def list_people(
    page: int = Query(0, ge=0, description="Page number"),
    pageSize: int = Query(20, ge=1, le=1000, description="Page size"),
    firstName: Optional[str] = Query(None, description="Filter by first name"),
    lastName: Optional[str] = Query(None, description="Filter by last name"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Lists all people with pagination and filtering.

    Args:
        page (int): The page number to return.
        pageSize (int): The number of items to return per page.
        firstName (Optional[str]): A filter for the person's first name.
        lastName (Optional[str]): A filter for the person's last name.
        db (AsyncSession): The database session.
        current_user: The current authenticated user.

    Returns:
        dict: A BrAPI-compliant list of people.
    """
    # Build query
    query = select(PersonModel)

    # Filter by user's organization (multi-tenant isolation)
    if current_user and current_user.organization_id:
        query = query.where(PersonModel.organization_id == current_user.organization_id)

    # Apply filters
    if firstName:
        query = query.where(PersonModel.first_name.ilike(f"%{firstName}%"))
    if lastName:
        query = query.where(PersonModel.last_name.ilike(f"%{lastName}%"))

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total_count = result.scalar()

    # Apply pagination
    query = query.offset(page * pageSize).limit(pageSize)

    # Execute query
    result = await db.execute(query)
    people = result.scalars().all()

    # Convert to BrAPI format
    people_list = [_model_to_brapi(p) for p in people]

    return create_brapi_response(people_list, page, pageSize, total_count)


@router.get("/people/{personDbId}")
async def get_person(
    personDbId: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Retrieves a single person by their personDbId.

    Args:
        personDbId (str): The ID of the person to retrieve.
        db (AsyncSession): The database session.
        current_user: The current authenticated user.

    Raises:
        HTTPException: If the person is not found.

    Returns:
        dict: A BrAPI-compliant dictionary of the person.
    """
    query = select(PersonModel).where(PersonModel.person_db_id == personDbId)
    result = await db.execute(query)
    person = result.scalar_one_or_none()

    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    return create_single_response(_model_to_brapi(person))


@router.post("/people", status_code=201)
async def create_person(
    person_in: PersonCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Creates a new person.

    Args:
        person_in (PersonCreate): The person to create.
        db (AsyncSession): The database session.
        current_user: The current authenticated user.

    Returns:
        dict: A BrAPI-compliant dictionary of the created person.
    """
    person_id = f"person-{uuid.uuid4().hex[:8]}"

    person = PersonModel(
        organization_id=current_user.organization_id,
        person_db_id=person_id,
        first_name=person_in.firstName,
        last_name=person_in.lastName,
        middle_name=person_in.middleName,
        email_address=person_in.emailAddress,
        phone_number=person_in.phoneNumber,
        mailing_address=person_in.mailingAddress,
        user_id=person_in.userId,
        additional_info=person_in.additionalInfo,
        external_references=person_in.externalReferences,
    )

    db.add(person)
    await db.commit()
    await db.refresh(person)

    return create_single_response(_model_to_brapi(person))


@router.put("/people/{personDbId}")
async def update_person(
    personDbId: str,
    person_in: PersonUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Updates an existing person.

    Args:
        personDbId (str): The ID of the person to update.
        person_in (PersonUpdate): The new data for the person.
        db (AsyncSession): The database session.
        current_user: The current authenticated user.

    Raises:
        HTTPException: If the person is not found.

    Returns:
        dict: A BrAPI-compliant dictionary of the updated person.
    """
    query = select(PersonModel).where(PersonModel.person_db_id == personDbId)
    result = await db.execute(query)
    person = result.scalar_one_or_none()

    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    # Update only provided fields
    update_data = person_in.model_dump(exclude_unset=True)

    if "firstName" in update_data:
        person.first_name = update_data["firstName"]
    if "lastName" in update_data:
        person.last_name = update_data["lastName"]
    if "middleName" in update_data:
        person.middle_name = update_data["middleName"]
    if "emailAddress" in update_data:
        person.email_address = update_data["emailAddress"]
    if "phoneNumber" in update_data:
        person.phone_number = update_data["phoneNumber"]
    if "mailingAddress" in update_data:
        person.mailing_address = update_data["mailingAddress"]
    if "userId" in update_data:
        person.user_id = update_data["userId"]
    if "additionalInfo" in update_data:
        person.additional_info = update_data["additionalInfo"]
    if "externalReferences" in update_data:
        person.external_references = update_data["externalReferences"]

    await db.commit()
    await db.refresh(person)

    return create_single_response(_model_to_brapi(person))


@router.delete("/people/{personDbId}", status_code=204)
async def delete_person(
    personDbId: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Deletes a person.

    Args:
        personDbId (str): The ID of the person to delete.
        db (AsyncSession): The database session.
        current_user: The current authenticated user.

    Raises:
        HTTPException: If the person is not found.

    Returns:
        None: An empty response.
    """
    query = select(PersonModel).where(PersonModel.person_db_id == personDbId)
    result = await db.execute(query)
    person = result.scalar_one_or_none()

    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    await db.delete(person)
    await db.commit()

    return None
