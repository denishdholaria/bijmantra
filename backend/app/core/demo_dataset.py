"""Canonical demo dataset contract and deterministic helpers.

The demo dataset is a first-class asset shared by application demos and
repeatable local TDD flows. Canonical demo seeders must not rely on wall-clock
time, random number generators, or uuid4 values.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from hashlib import sha256
from typing import Sequence, TypeVar
from uuid import UUID, uuid5


DEMO_DATASET_NAME = "bijmantra-demo-canonical"
DEMO_DATASET_VERSION = "2026-03-31-v1"
DEMO_DATASET_ORG_NAME = "Demo Organization"
DEMO_DATASET_USER_EMAIL = "demo@bijmantra.org"
DEMO_DATASET_FIXED_TIMESTAMP = datetime(2025, 8, 15, 10, 0, tzinfo=UTC)
DEMO_DATASET_NAMESPACE = UUID("2b4a4183-2dcf-483b-8f2d-79e7740f8b8a")

_StableValue = TypeVar("_StableValue")


@dataclass(frozen=True)
class DemoDatasetContract:
    name: str
    version: str
    organization_name: str
    user_email: str
    fixed_timestamp: datetime
    supported_flows: tuple[str, ...]
    isolated_from: tuple[str, ...]


DEMO_DATASET = DemoDatasetContract(
    name=DEMO_DATASET_NAME,
    version=DEMO_DATASET_VERSION,
    organization_name=DEMO_DATASET_ORG_NAME,
    user_email=DEMO_DATASET_USER_EMAIL,
    fixed_timestamp=DEMO_DATASET_FIXED_TIMESTAMP,
    supported_flows=(
        "application-demos",
        "demo-logins",
        "tdd",
        "seeded-regressions",
    ),
    isolated_from=("production", "staging"),
)


def _stable_key(*parts: object) -> str:
    return "::".join(str(part) for part in parts)


def stable_demo_token(*parts: object, length: int = 8) -> str:
    return uuid5(DEMO_DATASET_NAMESPACE, _stable_key(*parts)).hex[:length]


def stable_demo_id(prefix: str, *parts: object, length: int = 8) -> str:
    return f"{prefix}_{stable_demo_token(prefix, *parts, length=length)}"


def stable_demo_code(prefix: str, *parts: object, length: int = 8) -> str:
    return f"{prefix}-{stable_demo_token(prefix, *parts, length=length).upper()}"


def demo_dataset_datetime() -> datetime:
    return DEMO_DATASET.fixed_timestamp


def demo_dataset_date() -> date:
    return DEMO_DATASET.fixed_timestamp.date()


def stable_demo_float(
    minimum: float,
    maximum: float,
    *parts: object,
    digits: int = 2,
) -> float:
    if minimum > maximum:
        raise ValueError("minimum must be <= maximum")

    if minimum == maximum:
        return round(minimum, digits)

    digest = sha256(_stable_key(parts).encode("utf-8")).digest()
    ratio = int.from_bytes(digest[:8], "big") / float((1 << 64) - 1)
    value = minimum + (maximum - minimum) * ratio
    return round(value, digits)


def stable_demo_choice(options: Sequence[_StableValue], *parts: object) -> _StableValue:
    if not options:
        raise ValueError("options must not be empty")

    digest = sha256(_stable_key(parts).encode("utf-8")).digest()
    index = int.from_bytes(digest[:4], "big") % len(options)
    return options[index]