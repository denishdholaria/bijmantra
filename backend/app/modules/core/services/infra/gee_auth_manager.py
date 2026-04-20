"""
Google Earth Engine Authentication Manager

Handles Server-to-Server authentication using JWT assertions.
Generates signed JWTs and exchanges them for OAuth2 access tokens.
"""

import logging
import json
import os
import time
from pathlib import Path

import httpx
from jose import jwt

from app.core.http_tracing import create_traced_async_client

logger = logging.getLogger(__name__)


class GeeAuthManager:
    """
    Manages Google Earth Engine authentication.

    Generates signed JWTs and exchanges them for access tokens.
    """

    # Google OAuth2 Token Endpoint
    # Using the standard endpoint for token exchange
    TOKEN_URI = "https://oauth2.googleapis.com/token"

    # Scopes for Earth Engine and Cloud Platform
    SCOPES = [
        "https://www.googleapis.com/auth/earthengine",
        "https://www.googleapis.com/auth/cloud-platform",
    ]

    def __init__(self, service_account_email: str | None = None, private_key: str | None = None):
        """
        Initialize GeeAuthManager.

        Args:
            service_account_email: GEE Service Account Email. Defaults to env GEE_SERVICE_ACCOUNT_EMAIL.
            private_key: PEM-formatted private key content or path to key file.
                         Defaults to env GEE_PRIVATE_KEY_PATH (file) or GEE_PRIVATE_KEY (content).
        """
        self.service_account_email = service_account_email or os.getenv("GEE_SERVICE_ACCOUNT_EMAIL")

        # Private key handling: could be path or content
        key_input = private_key or os.getenv("GEE_PRIVATE_KEY_PATH") or os.getenv("GEE_PRIVATE_KEY")
        self.private_key = self._load_private_key(key_input)

        if not self.service_account_email:
            logger.warning("GEE_SERVICE_ACCOUNT_EMAIL not set.")

        if not self.private_key:
            logger.warning(
                "GEE Private Key not found (checked input, GEE_PRIVATE_KEY_PATH, GEE_PRIVATE_KEY)."
            )

    def _load_private_key(self, key_input: str | None) -> str | None:
        """Load private key from file path, JSON service-account key, or direct string content."""
        if not key_input:
            return None

        parsed_key = self._extract_private_key(key_input)
        if parsed_key:
            return parsed_key

        # Check if it's a file path
        try:
            path = Path(key_input)
            if path.is_file():
                try:
                    file_content = path.read_text().strip()
                    parsed_file_key = self._extract_private_key(file_content)
                    if parsed_file_key:
                        return parsed_file_key

                    logger.warning(
                        "Key file exists but does not contain a valid PEM key or JSON private_key field."
                    )
                    return None
                except Exception as e:
                    logger.error(f"Failed to read key file {path}: {e}")
                    return None
        except OSError:
            pass  # Not a valid path or filesystem error

        # Handle JSON string passed directly via env var/input.
        parsed_json_key = self._extract_private_key(key_input)
        if parsed_json_key:
            return parsed_json_key

        # If it reached here, it's neither clear content nor a valid file
        logger.warning(
            "Provided key input does not look like a PEM private key or a valid file path."
        )
        return None

    def _extract_private_key(self, value: str) -> str | None:
        """Extract PEM private key from PEM or service-account JSON content."""
        if not value:
            return None

        normalized = value.strip()

        if "-----BEGIN PRIVATE KEY-----" in normalized:
            return normalized.replace("\\n", "\n").strip()

        try:
            json_data = json.loads(normalized)
        except json.JSONDecodeError:
            return None

        private_key = json_data.get("private_key") if isinstance(json_data, dict) else None
        if isinstance(private_key, str) and private_key.strip():
            return private_key.replace("\\n", "\n").strip()

        return None

    def create_signed_jwt(self, expiration_minutes: int = 60) -> str | None:
        """
        Create a signed JWT assertion for Google OAuth2.
        """
        if not self.service_account_email or not self.private_key:
            logger.error("Cannot create JWT: Missing credentials.")
            return None

        now = int(time.time())
        exp = now + (expiration_minutes * 60)

        claims = {
            "iss": self.service_account_email,
            "sub": self.service_account_email,
            "aud": self.TOKEN_URI,
            "iat": now,
            "exp": exp,
            "scope": " ".join(self.SCOPES),
        }

        try:
            # Sign with RS256
            token = jwt.encode(claims, self.private_key, algorithm="RS256")
            return token
        except Exception as e:
            logger.error(f"Failed to sign JWT: {e}")
            return None

    async def get_access_token(self) -> str | None:
        """
        Exchange signed JWT for an OAuth2 access token.
        """
        assertion = self.create_signed_jwt()
        if not assertion:
            return None

        data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion,
        }

        try:
            async with create_traced_async_client() as client:
                response = await client.post(self.TOKEN_URI, data=data)
                response.raise_for_status()
                result = response.json()
                return result.get("access_token")
        except httpx.HTTPError as e:
            logger.error(f"Token exchange failed: {e}")
            if hasattr(e, "response") and e.response:
                logger.error(f"Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during token exchange: {e}")
            return None


# Singleton instance
_gee_auth_manager = None


def get_gee_auth_manager() -> GeeAuthManager:
    global _gee_auth_manager
    if _gee_auth_manager is None:
        _gee_auth_manager = GeeAuthManager()
    return _gee_auth_manager
