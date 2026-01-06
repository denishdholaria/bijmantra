"""
Database Seeders

Industry-standard approach for managing demo/test data:
- Development: Seed demo data for testing
- Test: Seed test fixtures
- Production: No seeding (empty database)

Usage:
    python -m app.db.seed --env=dev      # Seed demo data
    python -m app.db.seed --env=test     # Seed test fixtures
    python -m app.db.seed --env=prod     # No seeding
    python -m app.db.seed --clear        # Clear all seeded data
"""

from .base import BaseSeeder, run_seeders
from .demo_germplasm import DemoGermplasmSeeder
from .demo_brapi import DemoBrAPISeeder
from .demo_users import DemoUsersSeeder
from .demo_phenotyping import DemoPhenotypingSeeder
from .demo_core import DemoCoreSeeder
from .demo_crossing import DemoCrossingSeeder
from .demo_genotyping import DemoGenotypingSeeder
from .demo_user_management import DemoUserManagementSeeder
from .demo_stress_resistance import DemoStressResistanceSeeder
from .demo_field_operations import DemoFieldOperationsSeeder
from .demo_data_management import DemoDataManagementSeeder
from .demo_collaboration import DemoCollaborationSeeder
from .demo_brapi_phenotyping import DemoBrAPIPhenotypingSeeder
from .demo_iot import DemoIoTSeeder

__all__ = [
    "BaseSeeder",
    "run_seeders",
    "DemoGermplasmSeeder",
    "DemoBrAPISeeder",
    "DemoUsersSeeder",
    "DemoPhenotypingSeeder",
    "DemoCoreSeeder",
    "DemoCrossingSeeder",
    "DemoGenotypingSeeder",
    "DemoUserManagementSeeder",
    "DemoStressResistanceSeeder",
    "DemoFieldOperationsSeeder",
    "DemoDataManagementSeeder",
    "DemoCollaborationSeeder",
    "DemoBrAPIPhenotypingSeeder",
    "DemoIoTSeeder",
]
