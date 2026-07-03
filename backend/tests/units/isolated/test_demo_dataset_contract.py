from pathlib import Path

import pytest
from hypothesis import given, assume, settings as hyp_settings
from hypothesis import strategies as st
from pydantic import ValidationError

from app.core.config import settings
from app.core.demo_dataset import (
    DEMO_DATASET,
    DemoDatasetSafetyError,
    assert_demo_dataset_mutation_allowed,
    demo_dataset_date,
    demo_dataset_datetime,
    stable_demo_choice,
    stable_demo_float,
    stable_demo_id,
)
from app.core.security import get_password_hash, verify_password
from app.db import seed as seed_cli
from app.db.seeders.base import BaseSeeder
from app.db.seeders import base as seeder_base
from app.db.seeders.admin_user import AdminUserSeeder
from app.db.seeders.reference_data import ReferenceDataSeeder
from app.models.core import AuthIdentity, Organization, User


BACKEND_ROOT = Path(__file__).resolve().parents[3]
SEEDER_REGISTRY_FILE = BACKEND_ROOT / "app" / "db" / "seeders" / "__init__.py"
DEMO_BIO_ANALYTICS_FILE = BACKEND_ROOT / "app" / "db" / "seeders" / "demo_bio_analytics.py"
CANONICAL_DEMO_SEEDERS = [
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_benchmark_alignment.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_bio_analytics.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_brapi.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_brapi_phenotyping.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_collaboration.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_core.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_crossing.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_data_management.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_field_operations.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_genotyping.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_germplasm.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_ai_provider.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_iot.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_phenotyping.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_stress_resistance.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_user_management.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_users.py",
]
PROHIBITED_PATTERNS = (
    "uuid.uuid4",
    "import random",
    "random.",
    "datetime.now(",
    "date.today(",
)


class _StubSeeder(BaseSeeder):
    def seed(self) -> int:
        return 0

    def clear(self) -> int:
        return 0


class _DemoScopedSeeder(BaseSeeder):
    name = "demo_scoped"
    description = "Demo-scoped test seeder"
    is_demo_data = True

    def seed(self) -> int:
        return 2

    def clear(self) -> int:
        return 3


class _SystemScopedSeeder(BaseSeeder):
    name = "system_scoped"
    description = "System-scoped test seeder"
    is_demo_data = False

    def seed(self) -> int:
        return 5

    def clear(self) -> int:
        return 7


def _clear_admin_seed_test_data(db_session) -> None:
    db_session.query(AuthIdentity).filter(
        AuthIdentity.issuer == settings.KEYCLOAK_ISSUER,
        AuthIdentity.subject == settings.KEYCLOAK_BOOTSTRAP_ADMIN_SUBJECT,
    ).delete(synchronize_session=False)
    db_session.query(User).filter(User.email == settings.FIRST_SUPERUSER).delete()
    db_session.query(Organization).filter(
        Organization.name.in_(["BijMantra HQ", "Legacy Admin Org"])
    ).delete(synchronize_session=False)
    db_session.commit()


def test_demo_dataset_contract_matches_runtime_settings() -> None:
    assert settings.DEMO_DATASET_NAME == DEMO_DATASET.name
    assert settings.DEMO_DATASET_VERSION == DEMO_DATASET.version
    assert settings.DEMO_ORG_NAME == DEMO_DATASET.organization_name
    assert settings.DEMO_USER_EMAIL == DEMO_DATASET.user_email
    assert "tdd" in DEMO_DATASET.supported_flows
    assert DEMO_DATASET.isolated_from == ("production", "staging")


def test_demo_dataset_helpers_are_deterministic() -> None:
    assert demo_dataset_datetime().isoformat() == "2025-08-15T10:00:00+00:00"
    assert demo_dataset_date().isoformat() == "2025-08-15"

    assert stable_demo_id("demo_loc", "IRRI Research Station") == stable_demo_id(
        "demo_loc", "IRRI Research Station"
    )
    assert stable_demo_id("demo_loc", "IRRI Research Station") != stable_demo_id(
        "demo_loc", "CRRI Research Farm"
    )

    rainfall = stable_demo_choice(
        [0.0, 0.0, 2.5, 5.0, 12.0],
        "env-kharif-2025-field-a",
        2,
        "precipitation_total",
    )
    assert rainfall == stable_demo_choice(
        [0.0, 0.0, 2.5, 5.0, 12.0],
        "env-kharif-2025-field-a",
        2,
        "precipitation_total",
    )

    assert stable_demo_float(50, 150, "Plot-001-A", "Plant Height", digits=2) == stable_demo_float(
        50,
        150,
        "Plot-001-A",
        "Plant Height",
        digits=2,
    )


def test_base_seeder_allows_same_demo_dataset_for_tdd(monkeypatch) -> None:
    seeder = _StubSeeder(db=None)

    monkeypatch.setattr(settings, "SEED_DEMO_DATA", True)
    assert seeder.should_run("dev") is True
    assert seeder.should_run("test") is True
    assert seeder.should_run("prod") is False


def test_demo_dataset_mutation_guard_rejects_production_inputs() -> None:
    with pytest.raises(DemoDatasetSafetyError):
        assert_demo_dataset_mutation_allowed(
            requested_env="prod",
            runtime_environment="development",
            operation="seed",
        )

    with pytest.raises(DemoDatasetSafetyError):
        assert_demo_dataset_mutation_allowed(
            requested_env="dev",
            runtime_environment="production",
            operation="clear",
        )


def test_default_seeder_scope_runs_only_demo_seeders(monkeypatch) -> None:
    monkeypatch.setattr(settings, "SEED_DEMO_DATA", True)
    monkeypatch.setattr(
        seeder_base,
        "_seeders",
        [_SystemScopedSeeder, _DemoScopedSeeder],
    )

    assert seeder_base.run_seeders(db=None, env="dev") == {"demo_scoped": 2}
    assert seeder_base.clear_seeders(db=None) == {"demo_scoped": 3}


def test_system_seeders_require_explicit_scope(monkeypatch) -> None:
    monkeypatch.setattr(settings, "SEED_DEMO_DATA", True)
    monkeypatch.setattr(seeder_base, "_seeders", [_SystemScopedSeeder])

    with pytest.raises(ValueError, match="system_scoped"):
        seeder_base.run_seeders(db=None, env="dev", seeders=["system_scoped"])

    assert seeder_base.run_seeders(
        db=None,
        env="dev",
        seeders=["system_scoped"],
        scope="system",
    ) == {"system_scoped": 5}


def test_admin_and_reference_seeders_are_not_demo_data() -> None:
    assert AdminUserSeeder.is_demo_data is False
    assert ReferenceDataSeeder.is_demo_data is False


def test_admin_seeder_creates_default_bootstrap_admin(db_session) -> None:
    _clear_admin_seed_test_data(db_session)

    try:
        count = AdminUserSeeder(db_session).seed()

        admin = db_session.query(User).filter(User.email == settings.FIRST_SUPERUSER).one()
        org = db_session.query(Organization).filter(Organization.id == admin.organization_id).one()

        assert count == 1
        assert admin.is_active is True
        assert admin.is_superuser is True
        assert admin.full_name == "System Administrator"
        assert org.name == "BijMantra HQ"
        assert verify_password(settings.FIRST_SUPERUSER_PASSWORD, admin.hashed_password)

        identity = (
            db_session.query(AuthIdentity)
            .filter(
                AuthIdentity.provider == "keycloak",
                AuthIdentity.issuer == settings.KEYCLOAK_ISSUER,
                AuthIdentity.subject == settings.KEYCLOAK_BOOTSTRAP_ADMIN_SUBJECT,
            )
            .one()
        )
        assert identity.user_id == admin.id
        assert identity.organization_id == org.id
    finally:
        _clear_admin_seed_test_data(db_session)


def test_admin_seeder_repairs_stale_development_admin(db_session, monkeypatch) -> None:
    _clear_admin_seed_test_data(db_session)
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "FIRST_SUPERUSER_PASSWORD", "Admin123!")

    try:
        legacy_org = Organization(name="Legacy Admin Org")
        db_session.add(legacy_org)
        db_session.flush()
        db_session.add(
            User(
                organization_id=legacy_org.id,
                email=settings.FIRST_SUPERUSER,
                full_name=None,
                hashed_password=get_password_hash("OldAdmin123!"),
                is_active=False,
                is_superuser=False,
            )
        )
        db_session.commit()

        count = AdminUserSeeder(db_session).seed()

        admin = db_session.query(User).filter(User.email == settings.FIRST_SUPERUSER).one()
        org = db_session.query(Organization).filter(Organization.id == admin.organization_id).one()

        assert count == 1
        assert admin.is_active is True
        assert admin.is_superuser is True
        assert admin.full_name == "System Administrator"
        assert org.name == "BijMantra HQ"
        assert verify_password("Admin123!", admin.hashed_password)
    finally:
        _clear_admin_seed_test_data(db_session)


def test_seed_cli_uses_demo_scope_by_default(monkeypatch) -> None:
    class FakeSession:
        def close(self) -> None:
            pass

    calls = []

    def fake_run_seeders(db, env: str, seeders, scope: str):
        calls.append((db, env, seeders, scope))
        return {"demo_scoped": 1}

    monkeypatch.setattr(settings, "SEED_DEMO_DATA", True)
    monkeypatch.setattr(seed_cli, "import_seeders", lambda: None)
    monkeypatch.setattr(seed_cli, "get_db_session", lambda: FakeSession())
    monkeypatch.setattr(seeder_base, "run_seeders", fake_run_seeders)

    seed_cli.run_seed("dev")

    assert calls
    assert calls[0][1:] == ("dev", None, "demo")


def test_clear_cli_uses_demo_scope_by_default(monkeypatch) -> None:
    class FakeSession:
        def close(self) -> None:
            pass

    calls = []

    def fake_clear_seeders(db, seeders, scope: str):
        calls.append((db, seeders, scope))
        return {"demo_scoped": 1}

    monkeypatch.setattr(seed_cli, "import_seeders", lambda: None)
    monkeypatch.setattr(seed_cli, "get_db_session", lambda: FakeSession())
    monkeypatch.setattr(seeder_base, "clear_seeders", fake_clear_seeders)

    seed_cli.clear_seed(env="dev")

    assert calls
    assert calls[0][1:] == (None, "demo")


def test_canonical_demo_seeders_avoid_runtime_entropy_and_wall_clock() -> None:
    missing_files = [path.name for path in CANONICAL_DEMO_SEEDERS if not path.exists()]
    assert not missing_files, f"Missing canonical demo seeders: {missing_files}"

    violations = []
    for path in CANONICAL_DEMO_SEEDERS:
        content = path.read_text(encoding="utf-8")
        for pattern in PROHIBITED_PATTERNS:
            if pattern in content:
                violations.append(f"{path.name}: {pattern}")

    assert not violations, (
        "Canonical demo seeders must remain deterministic and reproducible: "
        + ", ".join(violations)
    )


def test_demo_benchmark_seeders_import_after_prerequisites() -> None:
    content = SEEDER_REGISTRY_FILE.read_text(encoding="utf-8")

    demo_germplasm_import = content.index("from .demo_germplasm import DemoGermplasmSeeder")
    demo_ai_provider_import = content.index("from .demo_ai_provider import DemoAIProviderSeeder")
    demo_brapi_import = content.index("from .demo_brapi import DemoBrAPISeeder")
    demo_phenotyping_import = content.index("from .demo_phenotyping import DemoPhenotypingSeeder")
    benchmark_alignment_import = content.index(
        "from .demo_benchmark_alignment import DemoBenchmarkAlignmentSeeder"
    )
    bio_analytics_import = content.index("from .demo_bio_analytics import DemoBioAnalyticsSeeder")

    assert demo_germplasm_import < demo_brapi_import
    assert demo_germplasm_import < demo_ai_provider_import
    assert demo_ai_provider_import < demo_brapi_import
    assert demo_germplasm_import < demo_phenotyping_import
    assert demo_germplasm_import < benchmark_alignment_import
    assert demo_brapi_import < benchmark_alignment_import
    assert demo_phenotyping_import < benchmark_alignment_import

    assert demo_germplasm_import < bio_analytics_import


def test_demo_bio_analytics_clear_is_scoped_to_seeded_records() -> None:
    content = DEMO_BIO_ANALYTICS_FILE.read_text(encoding="utf-8")

    broad_delete_patterns = (
        "self.db.query(CandidateGene).filter(CandidateGene.organization_id == org_id).delete()",
        "self.db.query(BioQTL).filter(BioQTL.organization_id == org_id).delete()",
        "self.db.query(GWASResult).filter(GWASResult.organization_id == org_id).delete()",
        "self.db.query(GWASRun).filter(GWASRun.organization_id == org_id).delete()",
    )

    for pattern in broad_delete_patterns:
        assert pattern not in content

    assert "GWASRun.run_name.in_(seeded_run_names)" in content
    assert "BioQTL.qtl_db_id.in_(seeded_qtl_db_ids)" in content
    assert "CandidateGene.qtl_id.in_(seeded_qtl_ids)" in content
    assert "GWASResult.run_id.in_(seeded_run_ids)" in content


# ---------------------------------------------------------------------------
# T1 — stable_demo_id round-trip idempotence (property-based)
# ---------------------------------------------------------------------------


@hyp_settings(max_examples=200)
@given(
    prefix=st.text(
        min_size=1,
        max_size=20,
        alphabet=st.characters(whitelist_categories=("Ll",)),
    ),
    parts=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5),
)
def test_stable_demo_id_is_idempotent(prefix: str, parts: list) -> None:
    """stable_demo_id must return the same value for the same inputs on every call."""
    result1 = stable_demo_id(prefix, *parts)
    result2 = stable_demo_id(prefix, *parts)
    assert result1 == result2


# ---------------------------------------------------------------------------
# T2 — stable_demo_float bounds (property-based)
# ---------------------------------------------------------------------------


@hyp_settings(max_examples=200)
@given(
    minimum=st.floats(min_value=-1000, max_value=999, allow_nan=False, allow_infinity=False),
    maximum=st.floats(min_value=-999, max_value=1000, allow_nan=False, allow_infinity=False),
    parts=st.lists(st.text(min_size=1), min_size=1, max_size=3),
)
def test_stable_demo_float_stays_within_bounds(minimum: float, maximum: float, parts: list) -> None:
    """stable_demo_float must always return a value within [minimum, maximum]."""
    assume(minimum <= maximum)
    result = stable_demo_float(minimum, maximum, *parts)
    assert minimum <= result <= maximum


# ---------------------------------------------------------------------------
# T3 — Settings validator rejects SEED_DEMO_DATA=True in production
# ---------------------------------------------------------------------------


def test_settings_validator_rejects_demo_seed_in_production() -> None:
    """Settings must raise ValidationError when ENVIRONMENT=production and SEED_DEMO_DATA=True."""
    import os
    from unittest.mock import patch

    # Patch env vars so pydantic_settings picks them up cleanly without .env file interference
    env_overrides = {
        "ENVIRONMENT": "production",
        "SEED_DEMO_DATA": "true",
        # Satisfy the other production guards so only the demo-seed check fires
        "SECRET_KEY": "a" * 64,
        "POSTGRES_PASSWORD": "secure_prod_password",
        "MINIO_ROOT_PASSWORD": "secure_minio_password",
        "ADMIN_PASSWORD": "SecureAdmin123!",
    }
    with patch.dict(os.environ, env_overrides, clear=False):
        from app.core.config import Settings

        with pytest.raises((ValidationError, ValueError)):
            Settings()


# ---------------------------------------------------------------------------
# T5 — Unknown seeder name raises ValueError
# ---------------------------------------------------------------------------


def test_unknown_seeder_name_raises(monkeypatch) -> None:
    """run_seeders must raise ValueError identifying an unknown seeder name."""
    monkeypatch.setattr(seeder_base, "_seeders", [_DemoScopedSeeder])
    with pytest.raises(ValueError, match="nonexistent_seeder"):
        seeder_base.run_seeders(db=None, env="dev", seeders=["nonexistent_seeder"])
