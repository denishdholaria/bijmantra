"""
Password validation utilities
"""
import re


def is_strong_password(password: str) -> bool:
    """
    Check if a password meets complexity requirements:
    - At least 8 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit
    - Contains at least one special character (non-alphanumeric)
    """
    return (
        len(password) >= 8
        and bool(re.search(r"[A-Z]", password))
        and bool(re.search(r"[a-z]", password))
        and bool(re.search(r"[0-9]", password))
        and bool(re.search(r"[^A-Za-z0-9]", password))
    )
