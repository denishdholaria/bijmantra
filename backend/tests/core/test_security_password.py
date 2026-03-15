import pytest
import bcrypt
import logging
from app.core.security import verify_password, get_password_hash

# Helper to generate a hash with low work factor for speed
def generate_test_hash(password: str) -> str:
    # rounds=4 is the minimum allowed by bcrypt
    salt = bcrypt.gensalt(rounds=4)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def test_verify_password_correct():
    """Test verification with correct password."""
    password = "secure_password_123"
    hashed = generate_test_hash(password)
    assert verify_password(password, hashed) is True

def test_verify_password_incorrect():
    """Test verification with incorrect password."""
    password = "secure_password_123"
    hashed = generate_test_hash(password)
    assert verify_password("wrong_password", hashed) is False

def test_verify_password_logging(caplog):
    """Test that failed verification logs a warning."""
    password = "password"
    hashed = generate_test_hash(password)

    with caplog.at_level(logging.WARNING):
        result = verify_password("wrong", hashed)
        assert result is False
        assert "Authentication failed: Password verification failed." in caplog.text

def test_verify_password_empty():
    """Test verification with empty strings."""
    # Empty password
    hashed = generate_test_hash("password")
    assert verify_password("", hashed) is False

    # Empty password and empty password hash (valid case technically)
    hashed_empty = generate_test_hash("")
    assert verify_password("", hashed_empty) is True

def test_verify_password_unicode():
    """Test verification with unicode characters."""
    password = "🔒🔑abcdef"
    hashed = generate_test_hash(password)
    assert verify_password(password, hashed) is True
    assert verify_password("wrong", hashed) is False

def test_verify_password_invalid_hash():
    """Test verification with invalid hash format."""
    # bcrypt.checkpw raises ValueError or error if hash is invalid
    with pytest.raises(ValueError):
        verify_password("password", "invalid_hash_string")

    with pytest.raises(ValueError):
        verify_password("password", "")

def test_get_password_hash_and_verify():
    """Integration test between get_password_hash and verify_password."""
    # This uses the default rounds from get_password_hash, so might be slightly slower
    # but ensures the actual app function works as expected.
    password = "my_app_password"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed) is True
