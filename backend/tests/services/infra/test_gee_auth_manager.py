import logging
import json
from unittest.mock import AsyncMock, patch

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt

from app.modules.core.services.infra.gee_auth_manager import GeeAuthManager

# Disable logging during tests to keep output clean
logging.getLogger("app.services.infra.gee_auth_manager").setLevel(logging.CRITICAL)

# Generate a temporary RSA key pair for testing
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)
pem_private_key = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
).decode("utf-8")


@pytest.fixture
def auth_manager():
    return GeeAuthManager(
        service_account_email="test-service-account@test.iam.gserviceaccount.com",
        private_key=pem_private_key,
    )


def test_initialization(auth_manager):
    assert auth_manager.service_account_email == "test-service-account@test.iam.gserviceaccount.com"
    assert auth_manager.private_key == pem_private_key


def test_create_signed_jwt(auth_manager):
    token = auth_manager.create_signed_jwt()
    assert token is not None

    # Decode without verification just to check claims
    claims = jwt.get_unverified_claims(token)
    assert claims["iss"] == auth_manager.service_account_email
    assert claims["sub"] == auth_manager.service_account_email
    assert claims["aud"] == auth_manager.TOKEN_URI
    assert "https://www.googleapis.com/auth/earthengine" in claims["scope"]
    assert claims["exp"] > claims["iat"]


@pytest.mark.asyncio
async def test_get_access_token_success(auth_manager):
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "mock_access_token_123",
        "expires_in": 3600,
        "token_type": "Bearer",
    }
    mock_response.raise_for_status = lambda: None

    mock_client_instance = AsyncMock()
    mock_client_instance.post.return_value = mock_response

    # Mocking the context manager
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mock_client_instance.__aexit__.return_value = None

    with patch("httpx.AsyncClient", return_value=mock_client_instance):
        token = await auth_manager.get_access_token()
        assert token == "mock_access_token_123"

        # Verify call arguments
        mock_client_instance.post.assert_called_once()
        args, kwargs = mock_client_instance.post.call_args
        assert args[0] == auth_manager.TOKEN_URI
        assert "grant_type" in kwargs["data"]
        assert "assertion" in kwargs["data"]


@pytest.mark.asyncio
async def test_get_access_token_failure(auth_manager):
    mock_client_instance = AsyncMock()
    # Simulate network error
    mock_client_instance.post.side_effect = Exception("Network error")
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mock_client_instance.__aexit__.return_value = None

    with patch("httpx.AsyncClient", return_value=mock_client_instance):
        token = await auth_manager.get_access_token()
        assert token is None


def test_load_private_key_from_string():
    # Test loading key from string content
    manager = GeeAuthManager(service_account_email="test@example.com", private_key=pem_private_key)
    assert manager.private_key == pem_private_key


def test_load_private_key_invalid():
    manager = GeeAuthManager(
        service_account_email="test@example.com", private_key="invalid_key_content"
    )
    assert manager.private_key is None


def test_load_private_key_escaped_newlines():
    # Test loading key with escaped newlines (env var style)
    escaped_key = pem_private_key.replace("\n", "\\n")
    manager = GeeAuthManager(service_account_email="test@example.com", private_key=escaped_key)
    assert manager.private_key == pem_private_key


def test_load_private_key_from_service_account_json_string():
    key_json = json.dumps(
        {
            "type": "service_account",
            "private_key": pem_private_key.replace("\n", "\\n"),
            "client_email": "test-service-account@test.iam.gserviceaccount.com",
        }
    )

    manager = GeeAuthManager(service_account_email="test@example.com", private_key=key_json)
    assert manager.private_key == pem_private_key


def test_load_private_key_from_service_account_json_file(tmp_path):
    key_file = tmp_path / "service-account.json"
    key_file.write_text(
        json.dumps(
            {
                "type": "service_account",
                "private_key": pem_private_key.replace("\n", "\\n"),
                "client_email": "test-service-account@test.iam.gserviceaccount.com",
            }
        )
    )

    manager = GeeAuthManager(service_account_email="test@example.com", private_key=str(key_file))
    assert manager.private_key == pem_private_key
