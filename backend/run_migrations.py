"""
Run database migrations directly
This script connects to the container database and runs migrations

SECURITY: Credentials are loaded from environment variables or .env file.
Never hardcode credentials in this file.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Load .env file if it exists (for local development)
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)

# Validate required environment variables
required_vars = ['POSTGRES_SERVER', 'POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_DB']
missing_vars = [var for var in required_vars if not os.environ.get(var)]

if missing_vars:
    print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
    print("\nSet these in your environment or .env file:")
    print("  POSTGRES_SERVER=localhost")
    print("  POSTGRES_PORT=5432")
    print("  POSTGRES_USER=your_user")
    print("  POSTGRES_PASSWORD=your_secure_password")
    print("  POSTGRES_DB=your_database")
    sys.exit(1)

from alembic.config import Config
from alembic import command

# Create Alembic configuration
alembic_cfg = Config("alembic.ini")

# Run upgrade
print("Running database migrations...")
command.upgrade(alembic_cfg, "head")
print("✓ Migrations completed successfully!")
