#!/usr/bin/env python3
"""
Database Seeder CLI

Usage:
    python -m app.db.seed --env=dev      # Seed demo data for development
    python -m app.db.seed --env=test     # Seed test fixtures
    python -m app.db.seed --env=prod     # No seeding (production)
    python -m app.db.seed --clear        # Clear all seeded data
    python -m app.db.seed --list         # List available seeders
    python -m app.db.seed --only=demo_germplasm  # Run specific seeder
"""

import argparse
import sys
import logging
from typing import Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_db_session():
    """Get a database session for seeding"""
    # Import here to avoid circular imports
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings

    # Use sync engine for seeding (simpler)
    sync_url = settings.DATABASE_URL.replace('+asyncpg', '')
    engine = create_engine(sync_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def import_seeders():
    """Import all seeder modules to register them"""
    # Import seeder modules - they auto-register via @register_seeder decorator
    from app.db.seeders import demo_germplasm
    # Add more seeder imports here as they are created:
    # from app.db.seeders import demo_trials
    # from app.db.seeders import demo_brapi
    # from app.db.seeders import test_fixtures


def list_seeders():
    """List all available seeders"""
    from app.db.seeders.base import get_all_seeders

    import_seeders()
    seeders = get_all_seeders()

    print("\n📦 Available Seeders:")
    print("-" * 50)
    for seeder_class in seeders:
        print(f"  • {seeder_class.name}: {seeder_class.description}")
    print("-" * 50)
    print(f"Total: {len(seeders)} seeders\n")


def run_seed(env: str, only: Optional[List[str]] = None):
    """Run seeders for the specified environment"""
    from app.db.seeders.base import run_seeders
    from app.core.config import settings

    import_seeders()

    print(f"\n🌱 Running seeders for '{env}' environment...")
    print(f"   DEMO_MODE: {settings.DEMO_MODE}")
    print(f"   FEATURE_DEMO_DATA: {settings.FEATURE_DEMO_DATA}")
    print("-" * 50)

    if env == "prod":
        print("⚠️  Production environment - no seeding performed")
        print("   Run migrations only: alembic upgrade head")
        return

    db = get_db_session()
    try:
        results = run_seeders(db, env=env, seeders=only)

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


def clear_seed(only: Optional[List[str]] = None):
    """Clear seeded data"""
    from app.db.seeders.base import clear_seeders

    import_seeders()

    print("\n🧹 Clearing seeded data...")
    print("-" * 50)

    db = get_db_session()
    try:
        results = clear_seeders(db, seeders=only)

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
  python -m app.db.seed --env=dev          # Seed demo data
  python -m app.db.seed --env=test         # Seed test fixtures
  python -m app.db.seed --list             # List available seeders
  python -m app.db.seed --clear            # Clear all seeded data
  python -m app.db.seed --only=demo_germplasm  # Run specific seeder
        """
    )

    parser.add_argument(
        '--env',
        choices=['dev', 'test', 'prod'],
        default='dev',
        help='Environment to seed for (default: dev)'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List available seeders'
    )

    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear seeded data instead of seeding'
    )

    parser.add_argument(
        '--only',
        type=str,
        help='Comma-separated list of seeder names to run'
    )

    args = parser.parse_args()

    # Parse --only into list
    only = None
    if args.only:
        only = [s.strip() for s in args.only.split(',')]

    try:
        if args.list:
            list_seeders()
        elif args.clear:
            clear_seed(only=only)
        else:
            run_seed(env=args.env, only=only)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
