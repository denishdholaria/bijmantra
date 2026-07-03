"""
Base Seeder Class

Provides common functionality for all database seeders.

NOTE: Seeders use synchronous SQLAlchemy patterns intentionally.
They run via CLI only (`python -m app.db.seed`), never during async request handling.
This is compliant with GOVERNANCE.md §4.3.1 because seeders are not part of the
async request path - they are standalone CLI tools for database initialization.
"""

import logging
from abc import ABC, abstractmethod
from typing import Literal

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.demo_dataset import is_production_environment


logger = logging.getLogger(__name__)

SeederScope = Literal["demo", "system", "all"]
VALID_SEEDER_SCOPES = {"demo", "system", "all"}


class BaseSeeder(ABC):
    """
    Abstract base class for database seeders.

    Subclasses must implement:
    - seed(): Insert demo/test data
    - clear(): Remove seeded data

    NOTE: Uses sync Session because seeders run via CLI, not async endpoints.
    """

    name: str = "base"
    description: str = "Base seeder"
    is_demo_data: bool = True

    def __init__(self, db: Session):
        self.db = db

    @abstractmethod
    def seed(self) -> int:
        """
        Seed data into the database.

        Returns:
            Number of records seeded
        """
        pass

    @abstractmethod
    def clear(self) -> int:
        """
        Clear seeded data from the database.

        Returns:
            Number of records cleared
        """
        pass

    def should_run(self, env: str = "dev") -> bool:
        """
        Check if this seeder should run for the given environment.

        Args:
            env: Environment name (dev, test, prod)

        Returns:
            True if seeder should run
        """
        if is_production_environment(env):
            return False  # Never seed in production

        if not settings.SEED_DEMO_DATA:
            logger.warning(f"SEED_DEMO_DATA is False, skipping {self.name} seeder")
            return False

        return True

    def run(self, env: str = "dev") -> int:
        """
        Run the seeder if appropriate for the environment.

        Args:
            env: Environment name

        Returns:
            Number of records seeded (0 if skipped)
        """
        if not self.should_run(env):
            logger.info(f"Skipping {self.name} seeder for {env} environment")
            return 0

        logger.info(f"Running {self.name} seeder...")
        count = self.seed()
        logger.info(f"Seeded {count} records from {self.name}")
        return count


# Registry of all seeders
_seeders: list[type] = []


def register_seeder(seeder_class: type) -> type:
    """Decorator to register a seeder class"""
    _seeders.append(seeder_class)
    return seeder_class


def get_all_seeders() -> list[type]:
    """Get all registered seeder classes"""
    return _seeders.copy()


def _normalize_scope(scope: str) -> SeederScope:
    normalized = scope.strip().lower()
    if normalized not in VALID_SEEDER_SCOPES:
        raise ValueError(
            f"Unknown seeder scope {scope!r}. Expected one of: "
            f"{', '.join(sorted(VALID_SEEDER_SCOPES))}"
        )
    return normalized  # type: ignore[return-value]


def _seeder_class_name(seeder_class: type) -> str:
    return str(getattr(seeder_class, "name", seeder_class.__name__))


def _seeder_scope(seeder_class: type) -> str:
    return "demo" if getattr(seeder_class, "is_demo_data", True) else "system"


def _select_seeders(
    seeder_classes: list[type],
    *,
    seeders: list[str] | None,
    scope: str,
) -> list[type]:
    normalized_scope = _normalize_scope(scope)
    requested_names = set(seeders or [])
    available_names = {_seeder_class_name(seeder_class) for seeder_class in seeder_classes}
    unknown_names = requested_names - available_names
    if unknown_names:
        raise ValueError(f"Unknown seeder(s): {', '.join(sorted(unknown_names))}")

    selected: list[type] = []
    out_of_scope: list[str] = []

    for seeder_class in seeder_classes:
        seeder_name = _seeder_class_name(seeder_class)
        if requested_names and seeder_name not in requested_names:
            continue

        seeder_scope = _seeder_scope(seeder_class)
        in_scope = normalized_scope == "all" or seeder_scope == normalized_scope
        if not in_scope:
            if requested_names:
                out_of_scope.append(f"{seeder_name} ({seeder_scope})")
            continue

        selected.append(seeder_class)

    if out_of_scope:
        raise ValueError(
            "Seeder(s) outside requested scope: "
            + ", ".join(out_of_scope)
            + f". Use --scope={_seeder_scope_name_for_error(out_of_scope)} if intentional."
        )

    return selected


def _seeder_scope_name_for_error(out_of_scope: list[str]) -> str:
    if all("(system)" in name for name in out_of_scope):
        return "system"
    if all("(demo)" in name for name in out_of_scope):
        return "demo"
    return "all"


def run_seeders(
    db: Session,
    env: str = "dev",
    seeders: list[str] | None = None,
    scope: str = "demo",
) -> dict:
    """
    Run all or specified seeders.

    Args:
        db: Database session
        env: Environment name (dev, test, prod)
        seeders: Optional list of seeder names to run (runs all if None)
        scope: Seeder scope (demo, system, all)

    Returns:
        Dict with seeder names and record counts
    """
    results = {}

    for seeder_class in _select_seeders(_seeders, seeders=seeders, scope=scope):
        seeder = seeder_class(db)

        count = seeder.run(env)
        results[seeder.name] = count

    return results


def clear_seeders(
    db: Session,
    seeders: list[str] | None = None,
    scope: str = "demo",
) -> dict:
    """
    Clear data from all or specified seeders.

    Clears in REVERSE order to handle foreign key dependencies.
    (Later seeders may reference earlier seeder data)

    Args:
        db: Database session
        seeders: Optional list of seeder names to clear (clears all if None)
        scope: Seeder scope (demo, system, all)

    Returns:
        Dict with seeder names and record counts cleared
    """
    results = {}

    # Clear in reverse order to handle foreign key dependencies
    selected_seeders = _select_seeders(_seeders, seeders=seeders, scope=scope)
    for seeder_class in reversed(selected_seeders):
        seeder = seeder_class(db)

        logger.info(f"Clearing {seeder.name} seeder data...")
        count = seeder.clear()
        results[seeder.name] = count
        logger.info(f"Cleared {count} records from {seeder.name}")

    return results
