"""
RBAC (Role-Based Access Control) API
Manage roles and user role assignments
"""

from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.api.deps import get_current_user, get_current_superuser
from app.models.core import User
from app.models.user_management import Role, UserRole
from app.core.permissions import Permission

router = APIRouter(prefix="/rbac", tags=["RBAC"])


# ============================================
# SCHEMAS
# ============================================

class RoleResponse(BaseModel):
    id: int
    role_id: str
    name: str
    description: Optional[str] = None
    permissions: List[str] = []
    color: Optional[str] = None
    is_system: bool = False
    user_count: int = 0

    class Config:
        from_attributes = True


class RoleCreate(BaseModel):
    role_id: str = Field(..., min_length=2, max_length=50, pattern=r'^[a-z_]+$')
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    permissions: List[str] = []
    color: Optional[str] = None


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
    color: Optional[str] = None


class UserRoleResponse(BaseModel):
    user_id: int
    email: str
    full_name: Optional[str] = None
    roles: List[RoleResponse] = []
    is_superuser: bool = False


class AssignRoleRequest(BaseModel):
    user_id: int
    role_id: str


class BulkAssignRolesRequest(BaseModel):
    user_id: int
    role_ids: List[str]


class PermissionResponse(BaseModel):
    permission: str
    description: str
    category: str


# ============================================
# ROLE ENDPOINTS
# ============================================

@router.get("/roles", response_model=List[RoleResponse])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all roles in the organization"""
    query = (
        select(Role)
        .where(Role.organization_id == current_user.organization_id)
        .order_by(Role.name)
    )
    result = await db.execute(query)
    roles = result.scalars().all()
    
    # Get user counts for each role
    response = []
    for role in roles:
        count_query = select(UserRole).where(UserRole.role_id == role.id)
        count_result = await db.execute(count_query)
        user_count = len(count_result.scalars().all())
        
        response.append(RoleResponse(
            id=role.id,
            role_id=role.role_id,
            name=role.name,
            description=role.description,
            permissions=role.permissions or [],
            color=role.color,
            is_system=role.is_system,
            user_count=user_count
        ))
    
    return response


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific role by role_id"""
    query = select(Role).where(
        and_(
            Role.organization_id == current_user.organization_id,
            Role.role_id == role_id
        )
    )
    result = await db.execute(query)
    role = result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Get user count
    count_query = select(UserRole).where(UserRole.role_id == role.id)
    count_result = await db.execute(count_query)
    user_count = len(count_result.scalars().all())
    
    return RoleResponse(
        id=role.id,
        role_id=role.role_id,
        name=role.name,
        description=role.description,
        permissions=role.permissions or [],
        color=role.color,
        is_system=role.is_system,
        user_count=user_count
    )


@router.post("/roles", response_model=RoleResponse)
async def create_role(
    role_data: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """Create a new custom role (superuser only)"""
    # Check if role_id already exists
    existing = await db.execute(
        select(Role).where(
            and_(
                Role.organization_id == current_user.organization_id,
                Role.role_id == role_data.role_id
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Role ID already exists")
    
    # Validate permissions
    valid_permissions = {p.value for p in Permission}
    invalid = set(role_data.permissions) - valid_permissions
    if invalid:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid permissions: {', '.join(invalid)}"
        )
    
    role = Role(
        organization_id=current_user.organization_id,
        role_id=role_data.role_id,
        name=role_data.name,
        description=role_data.description,
        permissions=role_data.permissions,
        color=role_data.color,
        is_system=False
    )
    db.add(role)
    await db.commit()
    await db.refresh(role)
    
    return RoleResponse(
        id=role.id,
        role_id=role.role_id,
        name=role.name,
        description=role.description,
        permissions=role.permissions or [],
        color=role.color,
        is_system=role.is_system,
        user_count=0
    )


@router.patch("/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: str,
    role_data: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """Update a role (superuser only, cannot modify system roles)"""
    query = select(Role).where(
        and_(
            Role.organization_id == current_user.organization_id,
            Role.role_id == role_id
        )
    )
    result = await db.execute(query)
    role = result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    if role.is_system:
        raise HTTPException(status_code=403, detail="Cannot modify system roles")
    
    # Validate permissions if provided
    if role_data.permissions is not None:
        valid_permissions = {p.value for p in Permission}
        invalid = set(role_data.permissions) - valid_permissions
        if invalid:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid permissions: {', '.join(invalid)}"
            )
        role.permissions = role_data.permissions
    
    if role_data.name is not None:
        role.name = role_data.name
    if role_data.description is not None:
        role.description = role_data.description
    if role_data.color is not None:
        role.color = role_data.color
    
    await db.commit()
    await db.refresh(role)
    
    # Get user count
    count_query = select(UserRole).where(UserRole.role_id == role.id)
    count_result = await db.execute(count_query)
    user_count = len(count_result.scalars().all())
    
    return RoleResponse(
        id=role.id,
        role_id=role.role_id,
        name=role.name,
        description=role.description,
        permissions=role.permissions or [],
        color=role.color,
        is_system=role.is_system,
        user_count=user_count
    )


@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """Delete a custom role (superuser only, cannot delete system roles)"""
    query = select(Role).where(
        and_(
            Role.organization_id == current_user.organization_id,
            Role.role_id == role_id
        )
    )
    result = await db.execute(query)
    role = result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    if role.is_system:
        raise HTTPException(status_code=403, detail="Cannot delete system roles")
    
    # Check if role is assigned to any users
    count_query = select(UserRole).where(UserRole.role_id == role.id)
    count_result = await db.execute(count_query)
    if count_result.scalars().all():
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete role that is assigned to users"
        )
    
    await db.delete(role)
    await db.commit()
    
    return {"message": "Role deleted successfully"}


# ============================================
# USER ROLE ASSIGNMENT ENDPOINTS
# ============================================

@router.get("/users", response_model=List[UserRoleResponse])
async def list_users_with_roles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all users with their roles"""
    query = (
        select(User)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
        .where(User.organization_id == current_user.organization_id)
        .order_by(User.email)
    )
    result = await db.execute(query)
    users = result.scalars().all()
    
    response = []
    for user in users:
        roles = []
        for ur in user.user_roles:
            if ur.role:
                roles.append(RoleResponse(
                    id=ur.role.id,
                    role_id=ur.role.role_id,
                    name=ur.role.name,
                    description=ur.role.description,
                    permissions=ur.role.permissions or [],
                    color=ur.role.color,
                    is_system=ur.role.is_system,
                    user_count=0
                ))
        
        response.append(UserRoleResponse(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            roles=roles,
            is_superuser=user.is_superuser
        ))
    
    return response


@router.get("/users/{user_id}/roles", response_model=UserRoleResponse)
async def get_user_roles(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get roles for a specific user"""
    query = (
        select(User)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
        .where(
            and_(
                User.id == user_id,
                User.organization_id == current_user.organization_id
            )
        )
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    roles = []
    for ur in user.user_roles:
        if ur.role:
            roles.append(RoleResponse(
                id=ur.role.id,
                role_id=ur.role.role_id,
                name=ur.role.name,
                description=ur.role.description,
                permissions=ur.role.permissions or [],
                color=ur.role.color,
                is_system=ur.role.is_system,
                user_count=0
            ))
    
    return UserRoleResponse(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        roles=roles,
        is_superuser=user.is_superuser
    )


@router.post("/users/{user_id}/roles")
async def assign_role_to_user(
    user_id: int,
    request: AssignRoleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """Assign a role to a user (superuser only)"""
    # Verify user exists in same org
    user_query = select(User).where(
        and_(
            User.id == user_id,
            User.organization_id == current_user.organization_id
        )
    )
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify role exists
    role_query = select(Role).where(
        and_(
            Role.organization_id == current_user.organization_id,
            Role.role_id == request.role_id
        )
    )
    role_result = await db.execute(role_query)
    role = role_result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Check if already assigned
    existing_query = select(UserRole).where(
        and_(
            UserRole.user_id == user_id,
            UserRole.role_id == role.id
        )
    )
    existing_result = await db.execute(existing_query)
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Role already assigned to user")
    
    # Create assignment
    user_role = UserRole(
        user_id=user_id,
        role_id=role.id,
        granted_at=datetime.now(timezone.utc),
        granted_by_id=current_user.id
    )
    db.add(user_role)
    await db.commit()
    
    return {"message": f"Role '{request.role_id}' assigned to user"}


@router.delete("/users/{user_id}/roles/{role_id}")
async def remove_role_from_user(
    user_id: int,
    role_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """Remove a role from a user (superuser only)"""
    # Verify user exists in same org
    user_query = select(User).where(
        and_(
            User.id == user_id,
            User.organization_id == current_user.organization_id
        )
    )
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Find the role
    role_query = select(Role).where(
        and_(
            Role.organization_id == current_user.organization_id,
            Role.role_id == role_id
        )
    )
    role_result = await db.execute(role_query)
    role = role_result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Find and delete the assignment
    assignment_query = select(UserRole).where(
        and_(
            UserRole.user_id == user_id,
            UserRole.role_id == role.id
        )
    )
    assignment_result = await db.execute(assignment_query)
    assignment = assignment_result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Role not assigned to user")
    
    await db.delete(assignment)
    await db.commit()
    
    return {"message": f"Role '{role_id}' removed from user"}


@router.put("/users/{user_id}/roles")
async def set_user_roles(
    user_id: int,
    request: BulkAssignRolesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """Set all roles for a user (replaces existing roles, superuser only)"""
    # Verify user exists in same org
    user_query = select(User).where(
        and_(
            User.id == user_id,
            User.organization_id == current_user.organization_id
        )
    )
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get all requested roles
    roles_query = select(Role).where(
        and_(
            Role.organization_id == current_user.organization_id,
            Role.role_id.in_(request.role_ids)
        )
    )
    roles_result = await db.execute(roles_query)
    roles = {r.role_id: r for r in roles_result.scalars().all()}
    
    # Verify all requested roles exist
    missing = set(request.role_ids) - set(roles.keys())
    if missing:
        raise HTTPException(
            status_code=404, 
            detail=f"Roles not found: {', '.join(missing)}"
        )
    
    # Delete existing assignments
    delete_query = select(UserRole).where(UserRole.user_id == user_id)
    delete_result = await db.execute(delete_query)
    for ur in delete_result.scalars().all():
        await db.delete(ur)
    
    # Create new assignments
    for role_id_str in request.role_ids:
        role = roles[role_id_str]
        user_role = UserRole(
            user_id=user_id,
            role_id=role.id,
            granted_at=datetime.now(timezone.utc),
            granted_by_id=current_user.id
        )
        db.add(user_role)
    
    await db.commit()
    
    return {"message": f"Assigned {len(request.role_ids)} roles to user"}


# ============================================
# PERMISSION ENDPOINTS
# ============================================

@router.get("/permissions", response_model=List[PermissionResponse])
async def list_permissions(
    current_user: User = Depends(get_current_user),
):
    """List all available permissions"""
    # Group permissions by category
    categories = {
        "plant_sciences": "Plant Sciences",
        "seed_bank": "Seed Bank",
        "earth_systems": "Earth Systems",
        "commercial": "Commercial",
        "integrations": "Integrations",
        "users": "User Management",
        "system": "System Administration",
        "audit": "Audit"
    }
    
    response = []
    for perm in Permission:
        # Extract category from permission value
        parts = perm.value.split(":")
        if len(parts) == 2:
            action, resource = parts
            category = categories.get(resource, resource.replace("_", " ").title())
            description = f"{action.title()} access to {resource.replace('_', ' ')}"
        else:
            category = "Other"
            description = perm.value
        
        response.append(PermissionResponse(
            permission=perm.value,
            description=description,
            category=category
        ))
    
    return response


@router.get("/my-permissions")
async def get_my_permissions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user's permissions"""
    # Load user with roles
    query = (
        select(User)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
        .where(User.id == current_user.id)
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if user.is_superuser:
        # Superusers have all permissions
        permissions = [p.value for p in Permission]
        roles = ["superuser"]
    else:
        permissions = user.permissions if user else []
        roles = user.roles if user else []
    
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "is_superuser": current_user.is_superuser,
        "roles": roles,
        "permissions": permissions
    }
