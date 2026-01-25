"""
CRUD operations for BrAPI Core module
"""

import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from app.crud.base import CRUDBase
from app.models.core import Program, Location, Trial, Study, Person, Organization, User
from app.models.user_management import UserRole
from app.schemas.core import (
    ProgramCreate, ProgramUpdate,
    LocationCreate, LocationUpdate,
    TrialCreate, TrialUpdate,
    StudyCreate, StudyUpdate,
    PersonCreate, PersonUpdate,
    OrganizationCreate, OrganizationUpdate,
    UserCreate, UserUpdate
)
from app.core.security import get_password_hash


class CRUDOrganization(CRUDBase[Organization, OrganizationCreate, OrganizationUpdate]):
    """CRUD operations for Organization"""
    
    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Organization]:
        """Get organization by name"""
        result = await db.execute(select(Organization).where(Organization.name == name))
        return result.scalar_one_or_none()


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """CRUD operations for User"""
    
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email with roles eagerly loaded for RBAC"""
        result = await db.execute(
            select(User)
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
            .where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def create(self, db: AsyncSession, *, obj_in: UserCreate, org_id: Optional[int] = None) -> User:
        """Create user with hashed password"""
        obj_data = obj_in.model_dump(exclude={'password'})
        obj_data['hashed_password'] = get_password_hash(obj_in.password)
        
        if org_id is not None:
            obj_data['organization_id'] = org_id
        
        db_obj = User(**obj_data)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj
    
    async def authenticate(self, db: AsyncSession, email: str, password: str) -> Optional[User]:
        """Authenticate user"""
        from app.core.security import verify_password
        
        user = await self.get_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user


class CRUDProgram(CRUDBase[Program, ProgramCreate, ProgramUpdate]):
    """CRUD operations for Program"""
    
    async def create(self, db: AsyncSession, *, obj_in: ProgramCreate, org_id: int) -> Program:
        """Create program with auto-generated DbId"""
        obj_data = obj_in.model_dump(exclude_unset=True, by_alias=False)
        
        # Generate unique program_db_id
        obj_data['program_db_id'] = f"prog_{uuid.uuid4().hex[:12]}"
        obj_data['organization_id'] = org_id
        
        db_obj = Program(**obj_data)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj


class CRUDLocation(CRUDBase[Location, LocationCreate, LocationUpdate]):
    """CRUD operations for Location"""
    
    async def create(self, db: AsyncSession, *, obj_in: LocationCreate, org_id: int) -> Location:
        """Create location with spatial data"""
        obj_data = obj_in.model_dump(exclude_unset=True, exclude={'coordinates'}, by_alias=False)
        
        # Generate unique location_db_id
        obj_data['location_db_id'] = f"loc_{uuid.uuid4().hex[:12]}"
        obj_data['organization_id'] = org_id
        
        # Handle coordinates (PostGIS)
        if obj_in.coordinates:
            point = Point(obj_in.coordinates.longitude, obj_in.coordinates.latitude)
            obj_data['coordinates'] = from_shape(point, srid=4326)
        
        db_obj = Location(**obj_data)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj
    
    async def update(self, db: AsyncSession, *, db_obj: Location, obj_in: LocationUpdate) -> Location:
        """Update location with spatial data"""
        obj_data = obj_in.model_dump(exclude_unset=True, exclude={'coordinates'}, by_alias=False)
        
        # Handle coordinates update
        if obj_in.coordinates:
            point = Point(obj_in.coordinates.longitude, obj_in.coordinates.latitude)
            obj_data['coordinates'] = from_shape(point, srid=4326)
        
        for field, value in obj_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj


class CRUDTrial(CRUDBase[Trial, TrialCreate, TrialUpdate]):
    """CRUD operations for Trial"""
    
    async def create(self, db: AsyncSession, *, obj_in: TrialCreate, org_id: int) -> Trial:
        """Create trial with auto-generated DbId"""
        from fastapi import HTTPException
        
        obj_data = obj_in.model_dump(exclude_unset=True, by_alias=False)
        
        # Generate unique trial_db_id
        obj_data['trial_db_id'] = f"trial_{uuid.uuid4().hex[:12]}"
        obj_data['organization_id'] = org_id
        
        # Resolve program_db_id to program_id (REQUIRED - program_id is NOT NULL)
        if 'program_db_id' in obj_data:
            program_db_id = obj_data.pop('program_db_id')
            if program_db_id:  # Only lookup if provided
                result = await db.execute(
                    select(Program).where(
                        Program.program_db_id == program_db_id,
                        Program.organization_id == org_id
                    )
                )
                program = result.scalar_one_or_none()
                if program:
                    obj_data['program_id'] = program.id
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Program with ID '{program_db_id}' not found in your organization. Please create a program first or select a valid program."
                    )
        
        # Validate program_id is set (required field)
        if 'program_id' not in obj_data:
            raise HTTPException(
                status_code=400,
                detail="A program is required to create a trial. Please select a program."
            )
        
        db_obj = Trial(**obj_data)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj


class CRUDStudy(CRUDBase[Study, StudyCreate, StudyUpdate]):
    """CRUD operations for Study"""
    
    async def create(self, db: AsyncSession, *, obj_in: StudyCreate, org_id: int) -> Study:
        """Create study with auto-generated DbId"""
        from fastapi import HTTPException
        
        obj_data = obj_in.model_dump(exclude_unset=True, by_alias=False)
        
        # Generate unique study_db_id
        obj_data['study_db_id'] = f"study_{uuid.uuid4().hex[:12]}"
        obj_data['organization_id'] = org_id
        
        # Resolve trial_db_id to trial_id (REQUIRED - trial_id is NOT NULL)
        if 'trial_db_id' in obj_data:
            trial_db_id = obj_data.pop('trial_db_id')
            if trial_db_id:  # Only lookup if provided
                result = await db.execute(
                    select(Trial).where(
                        Trial.trial_db_id == trial_db_id,
                        Trial.organization_id == org_id
                    )
                )
                trial = result.scalar_one_or_none()
                if trial:
                    obj_data['trial_id'] = trial.id
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Trial with ID '{trial_db_id}' not found in your organization. Please create a trial first or select a valid trial."
                    )
        
        # Validate trial_id is set (required field)
        if 'trial_id' not in obj_data:
            raise HTTPException(
                status_code=400,
                detail="A trial is required to create a study. Please select a trial."
            )
        
        # Resolve location_db_id to location_id (optional)
        if 'location_db_id' in obj_data:
            location_db_id = obj_data.pop('location_db_id')
            if location_db_id:  # Only lookup if provided
                result = await db.execute(
                    select(Location).where(
                        Location.location_db_id == location_db_id,
                        Location.organization_id == org_id
                    )
                )
                location = result.scalar_one_or_none()
                if location:
                    obj_data['location_id'] = location.id
                # Location is optional, so no error if not found
        
        db_obj = Study(**obj_data)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj


class CRUDPerson(CRUDBase[Person, PersonCreate, PersonUpdate]):
    """CRUD operations for Person"""
    
    async def create(self, db: AsyncSession, *, obj_in: PersonCreate, org_id: int) -> Person:
        """Create person with auto-generated DbId"""
        obj_data = obj_in.model_dump(exclude_unset=True, by_alias=False)
        
        # Generate unique person_db_id
        obj_data['person_db_id'] = f"person_{uuid.uuid4().hex[:12]}"
        obj_data['organization_id'] = org_id
        
        db_obj = Person(**obj_data)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj


# Create instances
organization = CRUDOrganization(Organization)
user = CRUDUser(User)
program = CRUDProgram(Program)
location = CRUDLocation(Location)
trial = CRUDTrial(Trial)
study = CRUDStudy(Study)
person = CRUDPerson(Person)
