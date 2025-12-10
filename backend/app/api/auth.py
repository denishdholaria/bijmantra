"""
Authentication endpoints
Login, register, token management
"""

from typing import Optional
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.crud.core import user as user_crud
from app.schemas.core import User, UserCreate
from app.api.deps import get_current_user
from app.models.core import User as UserModel

router = APIRouter()


class Token(BaseModel):
    """Token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data"""
    user_id: Optional[int] = None


@router.post("/login", response_model=Token)
async def login(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login
    """
    user = await user_crud.authenticate(
        db,
        email=form_data.username,
        password=form_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user
    """
    # Check if user already exists
    existing_user = await user_crud.get_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = await user_crud.create(db, obj_in=user_in)
    await db.commit()
    
    return user


@router.get("/me", response_model=User)
async def get_me(
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get current authenticated user
    """
    return current_user
