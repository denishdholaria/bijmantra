"""
Database Seeders

Industry-standard approach for managing demo/test data:
- Development: Seed demo data for testing
- Test: Seed test fixtures
- Production: Only reference data and admin user (no demo data)

Seeder Categories:
1. SYSTEM DATA (ignore SEED_DEMO_DATA, selected with --scope=system):
   - reference_data: Breeding methods, scales, traits
   - admin_user: Initial admin account

2. DEMO DATA (controlled by SEED_DEMO_DATA):
   - demo_users: Demo user accounts
   - demo_germplasm: Demo germplasm entries
   - demo_*: All other demo seeders

Usage:
    python -m app.db.seed --env=dev --scope=system --only=admin_user
    python -m app.db.seed --env=dev --scope=system --only=reference_data
    python -m app.db.seed --env=dev      # Seed demo data only
    python -m app.db.seed --env=test     # Seed demo test fixtures
    python -m app.db.seed --clear        # Clear all seeded data

Environment Variables:
    SEED_DEMO_DATA=true/false  # Control demo data seeding
    ADMIN_PASSWORD=xxx         # Set admin password (production)
"""

# Import order matters! Seeders are registered in import order via @register_seeder.
# The registration order determines both seed execution order (forward) and
# clear execution order (reverse). Foreign key constraints must be respected.
#
# Canonical dependency order (matches design spec Component 3):
#  1. ReferenceDataSeeder          (system, no deps)
#  2. AdminUserSeeder              (system, no deps)
#  3. DemoGermplasmSeeder          (demo, creates Demo Org + germplasm)
#  4. DemoUsersSeeder              (demo, depends on Demo Org)
#  5. DemoAIProviderSeeder         (demo, depends on Demo Org)
#  6. DemoBrAPISeeder              (demo, depends on Demo Org + germplasm)
#  7. DemoPhenotypingSeeder        (demo, depends on Demo Org + BrAPI studies)
#  8. DemoCoreSeeder               (demo, depends on Demo Org)
#  9. DemoCrossingSeeder           (demo, depends on germplasm)
# 10. DemoGenotypingSeeder         (demo, depends on Demo Org)
# 11. DemoUserManagementSeeder     (demo, depends on Demo Org + demo users)
# 12. DemoStressResistanceSeeder   (demo, depends on Demo Org)
# 13. DemoFieldOperationsSeeder    (demo, depends on Demo Org)
# 14. DemoDataManagementSeeder     (demo, depends on Demo Org)
# 15. DemoCollaborationSeeder      (demo, depends on Demo Org + demo users)
# 16. DemoBrAPIPhenotypingSeeder   (demo, depends on BrAPI + phenotyping)
# 17. DemoIoTSeeder                (demo, depends on Demo Org)
# 18. DemoBenchmarkAlignmentSeeder (demo, depends on germplasm + BrAPI + phenotyping)
# 19. DemoBioAnalyticsSeeder       (demo, depends on benchmark alignment)

from .base import BaseSeeder, clear_seeders, get_all_seeders, run_seeders

# 1. ALWAYS RUN - Reference data and admin (ignore SEED_DEMO_DATA)
from .reference_data import ReferenceDataSeeder
from .admin_user import AdminUserSeeder

# 2. DEMO DATA - Controlled by SEED_DEMO_DATA setting (dependency order)
from .demo_germplasm import DemoGermplasmSeeder
from .demo_users import DemoUsersSeeder
from .demo_ai_provider import DemoAIProviderSeeder
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
from .demo_benchmark_alignment import DemoBenchmarkAlignmentSeeder
from .demo_bio_analytics import DemoBioAnalyticsSeeder

# 3. ORG-1 BENCHMARK — not demo data; seeds real benchmark records for org 1
#    Run with: uv run python -m app.db.seed --only=org1_benchmark --scope=system
from .org1_benchmark_seeder import Org1BenchmarkSeeder

# 4. DATA PIPELINE — generated hybrid real/synthetic records for org 1 + Demo Org
#    Generate first: cd backend && PYTHONPATH=.. uv run python -m data_pipeline run
from .pipeline_trials import PipelineTrialsSeeder
from .pipeline_germplasm import PipelineGermplasmSeeder
from .pipeline_phenotyping import PipelinePhenotypingSeeder
from .pipeline_observations import PipelineObservationsSeeder
from .pipeline_genotyping import PipelineGenotypingSeeder
from .pipeline_gwas import PipelineGWASSeeder
from .pipeline_qtls import PipelineQTLSeeder


__all__ = [
    # Base
    "BaseSeeder",
    "run_seeders",
    "clear_seeders",
    "get_all_seeders",
    # Always run (system seeders)
    "ReferenceDataSeeder",
    "AdminUserSeeder",
    # Demo data (in dependency order)
    "DemoGermplasmSeeder",
    "DemoUsersSeeder",
    "DemoAIProviderSeeder",
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
    "DemoBenchmarkAlignmentSeeder",
    "DemoBioAnalyticsSeeder",
    # Org-1 benchmark (system scope)
    "Org1BenchmarkSeeder",
    # Pipeline seeders (system scope, non-production only)
    "PipelineTrialsSeeder",
    "PipelineGermplasmSeeder",
    "PipelinePhenotypingSeeder",
    "PipelineObservationsSeeder",
    "PipelineGenotypingSeeder",
    "PipelineGWASSeeder",
    "PipelineQTLSeeder",
]
