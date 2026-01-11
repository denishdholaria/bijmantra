"""
Unit tests for core schemas
"""
import pytest
from pydantic import ValidationError
from datetime import datetime, timezone

from app.schemas.core import UserCreate, OrganizationCreate, OrganizationUpdate, User


def test_user_create_valid_password():
    """Test UserCreate with a valid password"""
    user_data = {
        "email": "test@example.com",
        "password": "ValidPassword1!",
        "organization_id": 1
    }
    user = UserCreate(**user_data)
    assert user.email == user_data["email"]
    assert user.password == user_data["password"]


@pytest.mark.parametrize("password, error_message", [
    ("short", "String should have at least 8 characters"),
    ("nouppercase1!", "Password must contain at least one uppercase letter"),
    ("NOLOWERCASE1!", "Password must contain at least one lowercase letter"),
    ("NoDigit!", "Password must contain at least one digit"),
    ("NoSpecial1", "Password must contain at least one special character"),
    ("longpassword" * 16 + "1!A", "String should have at most 128 characters"),
])
def test_user_create_invalid_password(password, error_message):
    """Test UserCreate with invalid passwords"""
    with pytest.raises(ValidationError) as excinfo:
        UserCreate(
            email="test@example.com",
            password=password,
            organization_id=1
        )
    assert error_message in str(excinfo.value)


def test_organization_create_required_fields():
    """Test OrganizationCreate with required fields"""
    org_data = {"name": "Test Organization"}
    org = OrganizationCreate(**org_data)
    assert org.name == "Test Organization"
    assert org.description is None
    assert org.contact_email is None
    assert org.website is None


def test_organization_create_all_fields():
    """Test OrganizationCreate with all fields"""
    org_data = {
        "name": "Test Organization",
        "description": "A test org",
        "contact_email": "contact@test.org",
        "website": "https://test.org"
    }
    org = OrganizationCreate(**org_data)
    assert org.name == org_data["name"]
    assert org.description == org_data["description"]
    assert org.contact_email == org_data["contact_email"]
    assert org.website == org_data["website"]


def test_organization_create_missing_name():
    """Test OrganizationCreate with missing name field"""
    with pytest.raises(ValidationError):
        OrganizationCreate(description="Missing name")


def test_organization_update_optional_fields():
    """Test OrganizationUpdate with all fields being optional"""
    # Test with no fields
    org_update = OrganizationUpdate()
    assert org_update.name is None
    assert org_update.description is None
    assert org_update.contact_email is None
    assert org_update.website is None
    assert org_update.is_active is None

    # Test with some fields
    update_data = {
        "name": "New Name",
        "is_active": False
    }
    org_update = OrganizationUpdate(**update_data)
    assert org_update.name == "New Name"
    assert org_update.is_active is False
    assert org_update.description is None

    # Test with all fields
    update_data_all = {
        "name": "New Name",
        "description": "New description",
        "contact_email": "new@contact.org",
        "website": "https://new.org",
        "is_active": True
    }
    org_update = OrganizationUpdate(**update_data_all)
    assert org_update.name == update_data_all["name"]
    assert org_update.description == update_data_all["description"]
    assert org_update.contact_email == update_data_all["contact_email"]
    assert org_update.website == update_data_all["website"]
    assert org_update.is_active == update_data_all["is_active"]


def test_user_model_config_from_attributes():
    """Test that the User schema can be created from a model instance"""
    
    class MockUserORM:
        def __init__(self, id, email, organization_id, is_active, is_superuser, created_at, full_name=None):
            self.id = id
            self.email = email
            self.organization_id = organization_id
            self.is_active = is_active
            self.is_superuser = is_superuser
            self.created_at = created_at
            self.full_name = full_name

    now = datetime.now(timezone.utc)
    mock_user = MockUserORM(
        id=1,
        email="orm_user@example.com",
        organization_id=2,
        is_active=True,
        is_superuser=False,
        created_at=now,
        full_name="ORM User"
    )

    user_schema = User.model_validate(mock_user)

    assert user_schema.id == 1
    assert user_schema.email == "orm_user@example.com"
    assert user_schema.organization_id == 2
    assert user_schema.is_active is True
    assert user_schema.is_superuser is False
    assert user_schema.created_at == now
    assert user_schema.full_name == "ORM User"
