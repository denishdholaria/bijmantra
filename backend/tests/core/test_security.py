import unittest
import sys
from unittest.mock import MagicMock, patch

# --- Dependency Mocking for Isolated Environments ---
# This allows the unit tests to run even when full dependencies (like bcrypt or jose)
# are not installed in the local environment, which is common during development
# or in restricted CI environments.

def _setup_mocks():
    """Dynamically mock missing dependencies if they are not importable."""
    deps_to_mock = ["bcrypt", "jose", "fastapi"]
    for dep in deps_to_mock:
        try:
            __import__(dep)
        except ImportError:
            # Only mock if not already mocked/installed
            if dep not in sys.modules:
                mock_mod = MagicMock()
                sys.modules[dep] = mock_mod
                if dep == "jose":
                    # Ensure JWTError exists for exception handling
                    mock_mod.JWTError = type('JWTError', (Exception,), {})

    # Handle app.core.config separately to ensure settings are available
    try:
        import app.core.config # type: ignore
    except ImportError:
        if "app.core.config" not in sys.modules:
            mock_config = MagicMock()
            mock_config.settings.SECRET_KEY = "test_secret"
            mock_config.settings.ALGORITHM = "HS256"
            mock_config.settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
            sys.modules["app.core.config"] = mock_config

_setup_mocks()

# Now import the module under test
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token
)

class TestSecurity(unittest.TestCase):
    """Unit tests for security utilities in app.core.security."""

    def setUp(self):
        # Access the mocks from sys.modules
        self.mock_bcrypt = sys.modules.get("bcrypt")
        self.mock_jose = sys.modules.get("jose")

        # Reset mocks before each test if they are MagicMocks
        if isinstance(self.mock_bcrypt, MagicMock):
            self.mock_bcrypt.reset_mock()
        if isinstance(self.mock_jose, MagicMock):
            if hasattr(self.mock_jose, "jwt"):
                self.mock_jose.jwt.reset_mock()

    def test_verify_password_success(self):
        """Test successful password verification."""
        with patch("app.core.security.bcrypt") as mocked_bcrypt:
            mocked_bcrypt.checkpw.return_value = True
            plain_pw = "secret"
            hashed_pw = "hashed_secret"

            result = verify_password(plain_pw, hashed_pw)

            self.assertTrue(result)
            mocked_bcrypt.checkpw.assert_called_once_with(
                plain_pw.encode("utf-8"),
                hashed_pw.encode("utf-8")
            )

    def test_verify_password_failure(self):
        """Test failed password verification logs a warning."""
        with patch("app.core.security.bcrypt") as mocked_bcrypt:
            mocked_bcrypt.checkpw.return_value = False
            plain_pw = "secret"
            hashed_pw = "wrong_hash"

            with patch("app.core.security.logger") as mock_logger:
                result = verify_password(plain_pw, hashed_pw)

                self.assertFalse(result)
                mock_logger.warning.assert_called_once_with(
                    "Authentication failed: Password verification failed."
                )

    def test_get_password_hash(self):
        """Test password hashing calls bcrypt correctly."""
        with patch("app.core.security.bcrypt") as mocked_bcrypt:
            mocked_bcrypt.gensalt.return_value = b"salt"
            mocked_bcrypt.hashpw.return_value = b"hashed_bytes"
            password = "my_password"

            result = get_password_hash(password)

            self.assertEqual(result, "hashed_bytes")
            mocked_bcrypt.gensalt.assert_called_once()
            mocked_bcrypt.hashpw.assert_called_once_with(
                password.encode("utf-8"),
                b"salt"
            )

    def test_create_access_token(self):
        """Test JWT token creation."""
        with patch("app.core.security.jwt") as mocked_jwt:
            mocked_jwt.encode.return_value = "fake_token"
            data = {"sub": "user123"}

            token = create_access_token(data)

            self.assertEqual(token, "fake_token")
            mocked_jwt.encode.assert_called_once()
            call_args_dict = mocked_jwt.encode.call_args[0][0]
            self.assertEqual(call_args_dict["sub"], "user123")
            self.assertIn("exp", call_args_dict)

    def test_decode_access_token_success(self):
        """Test successful JWT token decoding."""
        with patch("app.core.security.jwt") as mocked_jwt:
            mocked_jwt.decode.return_value = {"sub": "user123"}
            token = "valid_token"

            payload = decode_access_token(token)

            self.assertEqual(payload, {"sub": "user123"})
            mocked_jwt.decode.assert_called_once()

    def test_decode_access_token_failure(self):
        """Test that invalid JWT tokens return None and log a warning."""
        with patch("app.core.security.jwt") as mocked_jwt:
            from jose import JWTError
            mocked_jwt.decode.side_effect = JWTError("Invalid token")
            token = "invalid_token"

            with patch("app.core.security.logger") as mock_logger:
                payload = decode_access_token(token)

                self.assertIsNone(payload)
                mock_logger.warning.assert_called_once_with(
                    "Authentication failed: Invalid token."
                )

if __name__ == "__main__":
    unittest.main()
