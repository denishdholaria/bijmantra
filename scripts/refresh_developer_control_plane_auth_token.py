#!/usr/bin/env python3
"""Refresh the local developer control-plane auth token in .env.

This helper uses the normal local login flow and stores the resulting superuser
JWT under BIJMANTRA_DEVELOPER_CONTROL_PLANE_AUTH_TOKEN for headless runtime
completion-assist staging.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    from scripts.local_env import DEFAULT_ENV_PATH, load_local_env
except ImportError:
    from local_env import DEFAULT_ENV_PATH, load_local_env


ROOT = Path(__file__).resolve().parents[1]
AUTH_TOKEN_ENV = "BIJMANTRA_DEVELOPER_CONTROL_PLANE_AUTH_TOKEN"
BASE_URL_ENV = "BIJMANTRA_DEVELOPER_CONTROL_PLANE_BASE_URL"
DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_EMAIL = "admin@bijmantra.org"
DEFAULT_PASSWORD = "Admin123!"
LOGIN_PATH = "/api/auth/login"


class DeveloperControlPlaneAuthTokenError(RuntimeError):
    """Raised when a developer control-plane auth token cannot be refreshed."""


def _normalize_base_url(base_url: str) -> str:
    normalized = base_url.strip()
    if not normalized:
        raise DeveloperControlPlaneAuthTokenError("base URL must not be empty")
    return normalized.rstrip("/")


def login_and_fetch_token(
    *,
    base_url: str,
    email: str,
    password: str,
    timeout_seconds: float,
) -> str:
    login_url = f"{_normalize_base_url(base_url)}{LOGIN_PATH}"
    request = Request(
        login_url,
        data=urlencode({"username": email, "password": password}).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            payload = json.load(response)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace").strip()
        raise DeveloperControlPlaneAuthTokenError(
            f"login failed with HTTP {exc.code}: {detail or exc.reason}"
        ) from exc
    except URLError as exc:
        raise DeveloperControlPlaneAuthTokenError(
            f"login request failed: {exc.reason}"
        ) from exc

    if not isinstance(payload, dict):
        raise DeveloperControlPlaneAuthTokenError("login response must be a JSON object")

    access_token = payload.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        raise DeveloperControlPlaneAuthTokenError("login response did not contain access_token")

    return access_token


def update_env_file(*, env_path: Path, key: str, value: str) -> None:
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
    else:
        lines = []

    updated = False
    rendered = f"{key}={value}"
    for index, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[index] = rendered
            updated = True
            break

    if not updated:
        if lines and lines[-1] != "":
            lines.append("")
        lines.append(rendered)

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def mask_token(token: str) -> str:
    if len(token) <= 16:
        return "<masked>"
    return f"{token[:8]}...{token[-6:]}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_PATH)
    parser.add_argument(
        "--base-url",
        default="",
        help=f"Backend base URL (default: ${BASE_URL_ENV} or {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--email",
        default=DEFAULT_EMAIL,
        help=f"Superuser email for local login (default: {DEFAULT_EMAIL})",
    )
    parser.add_argument(
        "--password",
        default="",
        help="Superuser password for local login (default: ADMIN_PASSWORD or local dev fallback)",
    )
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    parser.add_argument(
        "--no-write-env",
        action="store_true",
        help="Mint the token without updating the env file",
    )
    parser.add_argument(
        "--print-token",
        action="store_true",
        help="Print the raw token to stdout after success",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_local_env(keys=[BASE_URL_ENV, "ADMIN_PASSWORD"], env_path=args.env_file)

    base_url = args.base_url.strip() or os.getenv(BASE_URL_ENV, DEFAULT_BASE_URL)
    password = args.password or os.getenv("ADMIN_PASSWORD", "") or DEFAULT_PASSWORD
    token = login_and_fetch_token(
        base_url=base_url,
        email=args.email,
        password=password,
        timeout_seconds=args.timeout_seconds,
    )

    if not args.no_write_env:
        update_env_file(env_path=args.env_file, key=AUTH_TOKEN_ENV, value=token)
        print(f"Updated {args.env_file} with a refreshed {AUTH_TOKEN_ENV} value.")

    if args.print_token:
        print(token)
    else:
        print(f"Token refreshed successfully: {mask_token(token)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())