"""
Secret value encryption utilities (ADR-004).

Provides Fernet symmetric encryption for secrets stored in the database
(e.g. provider API keys in ai_configuration).

Usage:
    from app.core.secrets import encrypt_value, decrypt_value

    # Encrypt before storing
    encrypted = encrypt_value("sk-live-abc123")

    # Decrypt after reading
    plaintext = decrypt_value(encrypted)

Environment:
    BIJMANTRA_SECRET_KEY — base64-encoded 32-byte Fernet key.
    Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""

from __future__ import annotations

import logging
import os

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

# Marker prefix so we can distinguish encrypted values from legacy plaintext
_ENCRYPTED_PREFIX = "enc:v1:"

_fernet: Fernet | None = None


def _get_fernet() -> Fernet | None:
    """Lazy-init Fernet instance from environment key."""
    global _fernet
    if _fernet is not None:
        return _fernet

    key = os.environ.get("BIJMANTRA_SECRET_KEY")
    if not key:
        logger.warning(
            "[secrets] BIJMANTRA_SECRET_KEY not set — "
            "API keys will be stored/read as plaintext (legacy mode)."
        )
        return None

    try:
        _fernet = Fernet(key.encode() if isinstance(key, str) else key)
        return _fernet
    except Exception as exc:
        logger.error("[secrets] Invalid BIJMANTRA_SECRET_KEY: %s", exc)
        return None


def encrypt_value(plaintext: str | None) -> str | None:
    """Encrypt a plaintext value for database storage.

    Returns the encrypted string prefixed with ``enc:v1:`` so
    :func:`decrypt_value` can detect it. If the encryption key
    is not configured, returns the value unchanged (legacy mode).
    """
    if plaintext is None:
        return None

    f = _get_fernet()
    if f is None:
        return plaintext  # legacy: no-op

    token = f.encrypt(plaintext.encode("utf-8"))
    return _ENCRYPTED_PREFIX + token.decode("utf-8")


def decrypt_value(stored: str | None) -> str | None:
    """Decrypt a value read from the database.

    If the value does not carry the ``enc:v1:`` prefix it is returned
    unchanged — this supports a zero-downtime migration from plaintext
    to encrypted storage.
    """
    if stored is None:
        return None

    if not stored.startswith(_ENCRYPTED_PREFIX):
        return stored  # legacy plaintext or empty

    f = _get_fernet()
    if f is None:
        logger.error(
            "[secrets] Cannot decrypt value — BIJMANTRA_SECRET_KEY not set. "
            "Returning None to prevent leaking cipher text."
        )
        return None

    cipher_text = stored[len(_ENCRYPTED_PREFIX):]
    try:
        return f.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        logger.error(
            "[secrets] Decryption failed — key mismatch or corrupted data. "
            "Returning None."
        )
        return None
