"""
Database Seeders

Industry-standard approach for managing demo/test data:
- Development: Seed demo data for testing
- Test: Seed test fixtures
- Production: Only reference data and admin user (no demo data)

Seeder Categories:
1. ALWAYS RUN (ignore SEED_DEMO_DATA):
   - reference_data: Breeding methods, scales, traits
   - admin_user: Initial admin account

2. DEMO DATA (controlled by SEED_DEMO_DATA):
   - demo_users: Demo user accounts
   - demo_germplasm: Demo germplasm entries
   - demo_*: All other demo seeders

Usage:
    python -m app.db.seed --env=dev      # Seed all data
    python -m app.db.seed --env=test     # Seed test fixtures
    python -m app.db.seed --env=prod     # Only reference data + admin
    python -m app.db.seed --clear        # Clear all seeded data

Environment Variables:
    SEED_DEMO_DATA=true/false  # Control demo data seeding
    ADMIN_PASSWORD=xxx         # Set admin password (production)
"""

from .base import BaseSeeder, run_seeders, clear_seeders, get_all_seeders

# Import order matters! Reference data and admin first, then demo data.
# Seeders are registered in import order via @register_seeder decorator.

# 1. ALWAYS RUN - Reference data and admin (ignore SEED_DEMO_DATA)
from .reference_data import ReferenceDataSeeder
from .admin_user import AdminUserSeeder

# 2. DEMO DATA - Controlled by SEED_DEMO_DATA setting
from .demo_germplasm import DemoGermplasmSeeder
from .demo_users import DemoUsersSeeder
from .demo_brapi import DemoBrAPISeeder
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
    # Base
    "BaseSeeder",
    "run_seeders",
    "clear_seeders",
    "get_all_seeders",
    # Always run
    "ReferenceDataSeeder",
    "AdminUserSeeder",
    # Demo data
    "DemoGermplasmSeeder",
    "DemoUsersSeeder",
    "DemoBrAPISeeder",
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
