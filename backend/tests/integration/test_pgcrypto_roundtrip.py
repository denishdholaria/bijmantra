"""
pgcrypto round-trip integration test.

Requires a live PostgreSQL instance with pgcrypto enabled.
Set BIJMANTRA_TEST_POSTGRES_DSN to run.
"""

import os
import pytest
from sqlalchemy import create_engine, text

pytestmark = [pytest.mark.integration, pytest.mark.postgres_integration]

POSTGRES_DSN_ENV = "BIJMANTRA_TEST_POSTGRES_DSN"
TEST_KEY = "test-encryption-key-for-roundtrip"
TEST_DATA = '{"api_key": "secret-api-key-12345", "email": "test@example.com"}'


def get_dsn():
    dsn = os.environ.get(POSTGRES_DSN_ENV)
    if not dsn:
        pytest.skip(f"{POSTGRES_DSN_ENV} not configured")
    return dsn


def test_pgcrypto_extension_enabled():
    """pgcrypto extension must be present in pg_extension."""
    engine = create_engine(get_dsn())
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'pgcrypto'")
        )
        row = result.fetchone()
        assert row is not None, "pgcrypto extension is not enabled"
        assert row[0] == "pgcrypto"


def test_pgcrypto_encrypt_decrypt_roundtrip():
    """pgp_sym_encrypt → pgp_sym_decrypt must recover the original plaintext."""
    engine = create_engine(get_dsn())
    with engine.connect() as conn:
        # Encrypt
        encrypted = conn.execute(
            text("SELECT pgp_sym_encrypt(:data, :key)"),
            {"data": TEST_DATA, "key": TEST_KEY}
        ).scalar_one()

        assert encrypted is not None
        # Encrypted bytes should not equal the plaintext
        assert encrypted != TEST_DATA.encode()

        # Decrypt
        decrypted = conn.execute(
            text("SELECT pgp_sym_decrypt(:data, :key)"),
            {"data": encrypted, "key": TEST_KEY}
        ).scalar_one()

        assert decrypted == TEST_DATA


def test_pgcrypto_encrypted_value_is_opaque():
    """The encrypted value must not contain the plaintext."""
    engine = create_engine(get_dsn())
    with engine.connect() as conn:
        encrypted = conn.execute(
            text("SELECT pgp_sym_encrypt(:data, :key)"),
            {"data": "super-secret-api-key", "key": TEST_KEY}
        ).scalar_one()

        # The encrypted bytes should not contain the plaintext
        assert b"super-secret-api-key" not in bytes(encrypted)


def test_pgcrypto_wrong_key_fails():
    """Decryption with wrong key must raise an error."""
    engine = create_engine(get_dsn())
    with engine.connect() as conn:
        encrypted = conn.execute(
            text("SELECT pgp_sym_encrypt(:data, :key)"),
            {"data": TEST_DATA, "key": TEST_KEY}
        ).scalar_one()

        with pytest.raises(Exception):
            conn.execute(
                text("SELECT pgp_sym_decrypt(:data, :key)"),
                {"data": encrypted, "key": "wrong-key"}
            ).scalar_one()


def test_pgcrypto_session_variable_roundtrip():
    """Round-trip using current_setting('app.encryption_key') — mirrors production usage."""
    engine = create_engine(get_dsn())
    with engine.connect() as conn:
        # Set the session variable (as the connection event listener does in production)
        conn.execute(
            text("SELECT set_config('app.encryption_key', :key, false)"),
            {"key": TEST_KEY}
        )

        # Encrypt using session variable
        encrypted = conn.execute(
            text("SELECT pgp_sym_encrypt(:data, current_setting('app.encryption_key'))"),
            {"data": TEST_DATA}
        ).scalar_one()

        # Decrypt using session variable
        decrypted = conn.execute(
            text("SELECT pgp_sym_decrypt(:data, current_setting('app.encryption_key'))"),
            {"data": encrypted}
        ).scalar_one()

        assert decrypted == TEST_DATA
