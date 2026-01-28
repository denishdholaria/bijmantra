"""
Base Seeder Class

Provides common functionality for all database seeders.

NOTE: Seeders use synchronous SQLAlchemy patterns intentionally.
They run via CLI only (`python -m app.db.seed`), never during async request handling.
This is compliant with GOVERNANCE.md §4.3.1 because seeders are not part of the
async request path - they are standalone CLI tools for database initialization.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from sqlalchemy.orm import Session
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


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
        if env == "prod":
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
_seeders: List[type] = []


def register_seeder(seeder_class: type) -> type:
    """Decorator to register a seeder class"""
    _seeders.append(seeder_class)
    return seeder_class


def get_all_seeders() -> List[type]:
    """Get all registered seeder classes"""
    return _seeders.copy()


def run_seeders(db: Session, env: str = "dev", seeders: Optional[List[str]] = None) -> dict:
    """
    Run all or specified seeders.
    
    Args:
        db: Database session
        env: Environment name (dev, test, prod)
        seeders: Optional list of seeder names to run (runs all if None)
        
    Returns:
        Dict with seeder names and record counts
    """
    results = {}
    
    for seeder_class in _seeders:
        seeder = seeder_class(db)
        
        # Skip if specific seeders requested and this isn't one
        if seeders and seeder.name not in seeders:
            continue
        
        count = seeder.run(env)
        results[seeder.name] = count
    
    return results


def clear_seeders(db: Session, seeders: Optional[List[str]] = None) -> dict:
    """
    Clear data from all or specified seeders.
    
    Clears in REVERSE order to handle foreign key dependencies.
    (Later seeders may reference earlier seeder data)
    
    Args:
        db: Database session
        seeders: Optional list of seeder names to clear (clears all if None)
        
    Returns:
        Dict with seeder names and record counts cleared
    """
    results = {}
    
    # Clear in reverse order to handle foreign key dependencies
    for seeder_class in reversed(_seeders):
        seeder = seeder_class(db)
        
        if seeders and seeder.name not in seeders:
            continue
        
        logger.info(f"Clearing {seeder.name} seeder data...")
        count = seeder.clear()
        results[seeder.name] = count
        logger.info(f"Cleared {count} records from {seeder.name}")
    
    return results
