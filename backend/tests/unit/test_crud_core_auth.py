import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
# Attempt to break circular import by importing models first
try:
    import app.models
except ImportError:
    pass

from app.crud.core import CRUDUser
from app.models.core import User

@pytest.mark.asyncio
async def test_authenticate_success():
    """
    Test authenticate method with mocked dependencies to ensure
    imports and logic are correct.
    """
    # Arrange
    crud_user = CRUDUser(User)
    mock_db = MagicMock(spec=AsyncSession)

    test_email = "test@example.com"
    test_password = "password123"
    hashed_password = "hashed_password_123"

    mock_user = User(email=test_email, hashed_password=hashed_password)

    # Mock get_by_email on the instance
    crud_user.get_by_email = AsyncMock(return_value=mock_user)

    # Patch verify_password where it is used
    with patch("app.crud.core.verify_password", return_value=True) as mock_verify:
        # Act
        user = await crud_user.authenticate(mock_db, test_email, test_password)

        # Assert
        assert user is not None
        assert user.email == test_email
        mock_verify.assert_called_once_with(test_password, hashed_password)

@pytest.mark.asyncio
async def test_authenticate_failure_wrong_password():
    """Test authentication failure"""
    # Arrange
    crud_user = CRUDUser(User)
    mock_db = MagicMock(spec=AsyncSession)

    test_email = "test@example.com"
    test_password = "wrong_password"
    hashed_password = "hashed_password_123"

    mock_user = User(email=test_email, hashed_password=hashed_password)

    crud_user.get_by_email = AsyncMock(return_value=mock_user)

    # Patch verify_password where it is used
    with patch("app.crud.core.verify_password", return_value=False) as mock_verify:
        # Act
        user = await crud_user.authenticate(mock_db, test_email, test_password)

        # Assert
        assert user is None
        mock_verify.assert_called_once_with(test_password, hashed_password)
