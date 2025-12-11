"""
BrAPI v2.1 - People/Contacts endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

router = APIRouter()


# ============ Schemas ============

class PersonBase(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    middleName: Optional[str] = None
    emailAddress: Optional[str] = None
    phoneNumber: Optional[str] = None
    mailingAddress: Optional[str] = None
    userType: Optional[str] = "User"
    description: Optional[str] = None
    instituteName: Optional[str] = None


class PersonCreate(PersonBase):
    pass


class PersonUpdate(PersonBase):
    pass


class Person(PersonBase):
    personDbId: str
    
    class Config:
        from_attributes = True


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


# ============ In-Memory Storage ============

# Demo data
PEOPLE_DB: dict[str, dict] = {
    "person-001": {
        "personDbId": "person-001",
        "firstName": "Raj",
        "lastName": "Sharma",
        "middleName": None,
        "emailAddress": "raj.sharma@bijmantra.org",
        "phoneNumber": "+91-9876543210",
        "mailingAddress": "ICAR-IARI, New Delhi, India",
        "userType": "Researcher",
        "description": "Senior Plant Breeder specializing in rice improvement",
        "instituteName": "ICAR-IARI",
    },
    "person-002": {
        "personDbId": "person-002",
        "firstName": "Priya",
        "lastName": "Patel",
        "middleName": "K",
        "emailAddress": "priya.patel@bijmantra.org",
        "phoneNumber": "+91-9876543211",
        "mailingAddress": "ICRISAT, Hyderabad, India",
        "userType": "Technician",
        "description": "Lab technician for molecular breeding",
        "instituteName": "ICRISAT",
    },
    "person-003": {
        "personDbId": "person-003",
        "firstName": "Amit",
        "lastName": "Kumar",
        "middleName": None,
        "emailAddress": "amit.kumar@bijmantra.org",
        "phoneNumber": "+91-9876543212",
        "mailingAddress": "PAU, Ludhiana, India",
        "userType": "Researcher",
        "description": "Wheat breeding program lead",
        "instituteName": "PAU",
    },
    "person-004": {
        "personDbId": "person-004",
        "firstName": "Sunita",
        "lastName": "Devi",
        "middleName": None,
        "emailAddress": "sunita.devi@bijmantra.org",
        "phoneNumber": "+91-9876543213",
        "mailingAddress": "NBPGR, New Delhi, India",
        "userType": "Curator",
        "description": "Germplasm curator and conservation specialist",
        "instituteName": "NBPGR",
    },
    "person-005": {
        "personDbId": "person-005",
        "firstName": "Vikram",
        "lastName": "Singh",
        "middleName": "J",
        "emailAddress": "vikram.singh@bijmantra.org",
        "phoneNumber": "+91-9876543214",
        "mailingAddress": "CIMMYT, Mexico",
        "userType": "Researcher",
        "description": "International maize breeding specialist",
        "instituteName": "CIMMYT",
    },
}


# ============ Helper Functions ============

def create_brapi_response(data: any, page: int, page_size: int, total_count: int):
    """Helper to create BrAPI response with metadata"""
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
    """Helper to create BrAPI single item response"""
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
    userType: Optional[str] = Query(None, description="Filter by user type"),
):
    """
    List all people/contacts with pagination and filtering
    
    BrAPI Endpoint: GET /people
    """
    # Filter people
    people_list = list(PEOPLE_DB.values())
    
    if firstName:
        people_list = [p for p in people_list if firstName.lower() in (p.get("firstName") or "").lower()]
    if lastName:
        people_list = [p for p in people_list if lastName.lower() in (p.get("lastName") or "").lower()]
    if userType:
        people_list = [p for p in people_list if userType.lower() == (p.get("userType") or "").lower()]
    
    total_count = len(people_list)
    
    # Paginate
    start = page * pageSize
    end = start + pageSize
    paginated = people_list[start:end]
    
    return create_brapi_response(paginated, page, pageSize, total_count)


@router.get("/people/{personDbId}")
async def get_person(personDbId: str):
    """
    Get a single person by DbId
    
    BrAPI Endpoint: GET /people/{personDbId}
    """
    person = PEOPLE_DB.get(personDbId)
    
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    return create_single_response(person)


@router.post("/people", status_code=201)
async def create_person(person_in: PersonCreate):
    """
    Create a new person/contact
    
    BrAPI Endpoint: POST /people
    """
    person_id = f"person-{uuid.uuid4().hex[:8]}"
    
    person = {
        "personDbId": person_id,
        **person_in.model_dump(),
    }
    
    PEOPLE_DB[person_id] = person
    
    return create_single_response(person)


@router.put("/people/{personDbId}")
async def update_person(personDbId: str, person_in: PersonUpdate):
    """
    Update a person/contact
    
    BrAPI Endpoint: PUT /people/{personDbId}
    """
    if personDbId not in PEOPLE_DB:
        raise HTTPException(status_code=404, detail="Person not found")
    
    existing = PEOPLE_DB[personDbId]
    
    # Update only provided fields
    update_data = person_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            existing[key] = value
    
    PEOPLE_DB[personDbId] = existing
    
    return create_single_response(existing)


@router.delete("/people/{personDbId}", status_code=204)
async def delete_person(personDbId: str):
    """
    Delete a person/contact
    
    BrAPI Endpoint: DELETE /people/{personDbId}
    """
    if personDbId not in PEOPLE_DB:
        raise HTTPException(status_code=404, detail="Person not found")
    
    del PEOPLE_DB[personDbId]
    
    return None
