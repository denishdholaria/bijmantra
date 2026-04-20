from app.core.password_validation import is_strong_password


def test_is_strong_password_success():
    """Test valid strong passwords."""
    assert is_strong_password("StrongP@ss1") is True
    assert is_strong_password("Another$tr0ng!") is True
    # Exactly 10 chars
    assert is_strong_password("A1b2C3d4E$") is True


def test_is_strong_password_too_short():
    """Test password length requirement (>= 10)."""
    assert is_strong_password("Short1@") is False
    # 9 characters
    assert is_strong_password("12345678@") is False
    # 9 characters with all required types
    assert is_strong_password("A1a@BCde") is False # 8 chars
    assert is_strong_password("A1a@BCdef") is False # 9 chars


def test_is_strong_password_missing_uppercase():
    """Test requirement for uppercase letter."""
    assert is_strong_password("lowercase1@longenough") is False


def test_is_strong_password_missing_lowercase():
    """Test requirement for lowercase letter."""
    assert is_strong_password("UPPERCASE1@LONGENOUGH") is False


def test_is_strong_password_missing_digit():
    """Test requirement for digit."""
    assert is_strong_password("NoDigitHere@LongEnough") is False


def test_is_strong_password_missing_special_char():
    """Test requirement for special character."""
    assert is_strong_password("NoSpecialChar1LongEnough") is False


def test_is_strong_password_empty():
    """Test empty password."""
    assert is_strong_password("") is False


def test_is_strong_password_whitespace():
    """Test whitespace handling."""
    # Whitespace counts as special char by regex [^A-Za-z0-9]
    # "Space 1234 A a" -> length 14, has upper, lower, digit, special (space).
    assert is_strong_password("Space 1234 A a") is True

    # Just spaces
    assert is_strong_password("          ") is False # Missing upper, lower, digit


def test_is_strong_password_special_chars_variety():
    """Test various special characters."""
    special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    for char in special_chars:
        # Construct a password with the special char
        password = f"Valid1234{char}"
        assert is_strong_password(password) is True, f"Failed for char: {char}"
