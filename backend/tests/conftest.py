"""
Pytest configuration for BrAPI endpoint tests.
Simplified version for testing public endpoints.
"""

import pytest
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient
from app.main import app
from app.models.core import User, Organization
from app.models.base import Base
from app.core.security import create_access_token
from datetime import timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Use an in-memory SQLite database for tests
DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from sqlalchemy import inspect

@pytest.fixture(scope="session")
def setup_db():
    inspector = inspect(engine)
    if not inspector.has_table("organizations"):
        Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(setup_db) -> Session:
    """
    Creates a new database session for a test.
    """
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def test_user(db_session: Session) -> User:
    """
    Creates a test user and organization.
    """
    org = db_session.query(Organization).filter_by(name="Test Organization").first()
    if not org:
        org = Organization(name="Test Organization")
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)

    user = db_session.query(User).filter_by(email="test@example.com").first()
    if not user:
        user = User(
            email="test@example.com",
            hashed_password="password",
            organization_id=org.id,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user

@pytest.fixture
async def authenticated_client(test_user: User) -> AsyncClient:
    """
    Creates an authenticated client.
    """
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": str(test_user.id)}, expires_delta=access_token_expires
    )
    from httpx import ASGITransport
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {access_token}"},
    ) as client:
        yield client
