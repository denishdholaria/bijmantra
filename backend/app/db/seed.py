#!/usr/bin/env python3
"""
Database Seeder CLI

Usage:
    python -m app.db.seed --env=dev      # Seed demo data for development
    python -m app.db.seed --env=test     # Seed deterministic demo fixtures
    python -m app.db.seed --clear        # Clear demo-owned seeded data
    python -m app.db.seed --list         # List available seeders
    python -m app.db.seed --only=demo_germplasm  # Run specific seeder
    python -m app.db.seed --scope=system # Run admin/reference seeders
"""

import argparse
import logging
import sys


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_db_session():
    """Get a database session for seeding"""
    # Import here to avoid circular imports
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.core.config import settings

    # Use sync engine for seeding (simpler)
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "")
    engine = create_engine(sync_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def import_seeders():
    """Import all seeder modules to register them"""
    # Import seeder modules - they auto-register via @register_seeder decorator
    import app.db.seeders  # noqa: F401


def list_seeders():
    """List all available seeders"""
    from app.core.demo_dataset import DEMO_DATASET
    from app.db.seeders.base import get_all_seeders

    import_seeders()
    seeders = get_all_seeders()

    print(
        f"\n🧬 Canonical demo dataset: {DEMO_DATASET.name} ({DEMO_DATASET.version})"
    )
    print(
        f"   Demo org: {DEMO_DATASET.organization_name} | Demo user: {DEMO_DATASET.user_email}"
    )
    print("\n📦 Available Seeders:")
    print("-" * 50)
    for seeder_class in seeders:
        scope = "demo" if getattr(seeder_class, "is_demo_data", True) else "system"
        print(f"  • [{scope}] {seeder_class.name}: {seeder_class.description}")
    print("-" * 50)
    print(f"Total: {len(seeders)} seeders\n")


def _scope_includes_demo(scope: str) -> bool:
    return scope in {"demo", "all"}


def run_seed(env: str, only: list[str] | None = None, scope: str = "demo"):
    """Run seeders for the specified environment"""
    from app.core.config import settings
    from app.core.demo_dataset import DEMO_DATASET, assert_demo_dataset_mutation_allowed
    from app.db.seeders.base import run_seeders

    import_seeders()

    if _scope_includes_demo(scope):
        assert_demo_dataset_mutation_allowed(
            requested_env=env,
            runtime_environment=settings.ENVIRONMENT,
            operation="seed",
        )

    print(f"\n🌱 Running seeders for '{env}' environment...")
    print(f"   SCOPE: {scope}")
    print(f"   SEED_DEMO_DATA: {settings.SEED_DEMO_DATA}")
    print(
        f"   DATASET: {DEMO_DATASET.name} ({DEMO_DATASET.version}) -> demo creds/TDD only"
    )
    print("-" * 50)

    db = get_db_session()
    try:
        results = run_seeders(db, env=env, seeders=only, scope=scope)

        print("\n✅ Seeding complete:")
        total = 0
        for name, count in results.items():
            print(f"   • {name}: {count} records")
            total += count
        print("-" * 50)
        print(f"Total: {total} records seeded\n")

    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def clear_seed(
    env: str = "dev",
    only: list[str] | None = None,
    scope: str = "demo",
):
    """Clear seeded data"""
    from app.core.config import settings
    from app.core.demo_dataset import assert_demo_dataset_mutation_allowed
    from app.db.seeders.base import clear_seeders

    import_seeders()

    assert_demo_dataset_mutation_allowed(
        requested_env=env,
        runtime_environment=settings.ENVIRONMENT,
        operation="clear",
    )

    print("\n🧹 Clearing seeded data...")
    print(f"   SCOPE: {scope}")
    print("-" * 50)

    db = get_db_session()
    try:
        results = clear_seeders(db, seeders=only, scope=scope)

        print("\n✅ Clearing complete:")
        total = 0
        for name, count in results.items():
            print(f"   • {name}: {count} records cleared")
            total += count
        print("-" * 50)
        print(f"Total: {total} records cleared\n")

    except Exception as e:
        logger.error(f"Clearing failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Database seeder for Bijmantra",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.db.seed --env=dev          # Seed demo data only
  python -m app.db.seed --env=test         # Seed demo fixtures for tests
  python -m app.db.seed --list             # List available seeders
  python -m app.db.seed --clear            # Clear demo data only
  python -m app.db.seed --only=demo_germplasm  # Run specific seeder
  python -m app.db.seed --scope=system     # Run admin/reference seeders
        """,
    )

    parser.add_argument(
        "--env",
        choices=["dev", "test", "prod"],
        default="dev",
        help="Environment to seed for (default: dev)",
    )

    parser.add_argument("--list", action="store_true", help="List available seeders")

    parser.add_argument("--clear", action="store_true", help="Clear seeded data instead of seeding")

    parser.add_argument("--only", type=str, help="Comma-separated list of seeder names to run")

    parser.add_argument(
        "--scope",
        choices=["demo", "system", "all"],
        default="demo",
        help="Seeder scope to run or clear (default: demo)",
    )

    args = parser.parse_args()

    # Parse --only into list
    only = None
    if args.only:
        only = [s.strip() for s in args.only.split(",")]

    try:
        if args.list:
            list_seeders()
        elif args.clear:
            clear_seed(env=args.env, only=only, scope=args.scope)
        else:
            run_seed(env=args.env, only=only, scope=args.scope)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
