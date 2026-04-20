"""
Security utilities for authentication and authorization
"""

import logging
import ipaddress
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt
from fastapi import Request

from app.core.config import settings


logger = logging.getLogger(__name__)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    is_valid = bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    if not is_valid:
        logger.warning("Authentication failed: Password verification failed.")
    return is_valid


def get_password_hash(password: str) -> str:
    """Hash a password"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token

    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> dict | None:
    """
    Decode and verify a JWT access token

    Args:
        token: JWT token to decode

    Returns:
        Decoded token data or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        logger.warning("Authentication failed: Invalid token.")
        return None


def is_ip_trusted(ip: str) -> bool:
    """Check if an IP address is trusted (matches trusted proxies list)."""
    trusted_proxies = settings.TRUSTED_PROXIES
    if not trusted_proxies:
        return False

    try:
        ip_obj = ipaddress.ip_address(ip)
    except ValueError:
        return False

    for proxy in trusted_proxies:
        try:
            if "/" in proxy:
                if ip_obj in ipaddress.ip_network(proxy, strict=False):
                    return True
            else:
                if ip_obj == ipaddress.ip_address(proxy):
                    return True
        except ValueError:
            continue

    return False


def get_client_ip(request: Request) -> str:
    """
    Extract client IP from request, securely handling proxies.

    Uses recursive trust algorithm:
    1. Start with the immediate peer IP (request.client.host).
    2. If trusted, check X-Forwarded-For header.
    3. Walk backwards through the proxy chain as long as IPs are trusted.
    4. Return the first untrusted IP found (the client).
    """
    if not request.client or not request.client.host:
        return "0.0.0.0"

    remote_ip = request.client.host

    # If no trusted proxies configured, we must assume direct connection
    if not settings.TRUSTED_PROXIES:
        return remote_ip

    if not is_ip_trusted(remote_ip):
        return remote_ip

    # Check X-Forwarded-For
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For: client, proxy1, proxy2
        ips = [ip.strip() for ip in forwarded_for.split(",")]

        # Start checking from the last IP (connected to trusted peer)
        for ip in reversed(ips):
            if not is_ip_trusted(ip):
                return ip

        # If all IPs in the chain are trusted, return the first one (original client)
        return ips[0]

    # Fallback to X-Real-IP if configured and peer is trusted
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    return remote_ip
