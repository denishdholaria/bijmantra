"""
Run database migrations directly
This script connects to the container database and runs migrations
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Override database URL to use container
os.environ['POSTGRES_SERVER'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5432'
os.environ['POSTGRES_USER'] = 'bijmantra_user'
os.environ['POSTGRES_PASSWORD'] = 'changeme_in_production'
os.environ['POSTGRES_DB'] = 'bijmantra_db'

from alembic.config import Config
from alembic import command

# Create Alembic configuration
alembic_cfg = Config("alembic.ini")

# Run upgrade
print("Running database migrations...")
command.upgrade(alembic_cfg, "head")
print("✓ Migrations completed successfully!")
