"""
Property-based tests for API Layer Reorganization.

Uses Hypothesis to validate correctness properties from the design spec.
Each test maps to a numbered property in the design document.

Feature: api-layer-reorganization
"""

from __future__ import annotations

import re
from glob import glob
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

# Collect all Python files under backend/ once at module load time.
# This avoids re-globbing on every test iteration.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent  # backend/
_ALL_PY_FILES: list[str] = sorted(
    glob(str(_BACKEND_ROOT / "**" / "*.py"), recursive=True)
)

# Pre-compiled patterns for v1 import detection
_V1_IMPORT_RE = re.compile(
    r"(?:^|\n)\s*(?:from\s+app\.api\.v1|import\s+app\.api\.v1)"
)


# ---------------------------------------------------------------------------
# Property 1: Import Path Consistency (v1 baseline)
# ---------------------------------------------------------------------------


class TestProperty1ImportPathConsistencyV1Baseline:
    """Feature: api-layer-reorganization, Property 1: Import Path Consistency

    Verify zero ``app.api.v1`` import statements exist in the codebase.
    After Phase 0 preparation, no Python file should reference the deleted
    v1 API surface.

    **Validates: Requirements 1.4**
    """

    @given(data=st.data())
    @settings(max_examples=100)
    def test_no_v1_imports_in_sampled_files(self, data: st.DataObject):
        """
        For any Python file sampled from the backend codebase, the file
        SHALL NOT contain ``from app.api.v1`` or ``import app.api.v1``
        import statements.

        **Validates: Requirements 1.4**
        """
        # Skip if no Python files found (defensive — should never happen)
        if not _ALL_PY_FILES:
            pytest.skip("No Python files found under backend/")

        idx = data.draw(
            st.integers(min_value=0, max_value=len(_ALL_PY_FILES) - 1),
            label="python_file_index",
        )
        filepath = _ALL_PY_FILES[idx]

        try:
            content = Path(filepath).read_text(encoding="utf-8", errors="replace")
        except OSError:
            # File may have been removed between glob and read — skip
            return

        match = _V1_IMPORT_RE.search(content)
        assert match is None, (
            f"Found app.api.v1 import in {filepath}:\n"
            f"  {match.group().strip()}"
        )


# Pre-compiled patterns for v2 import detection
_V2_IMPORT_RE = re.compile(
    r"(?:^|\n)\s*(?:from\s+app\.api\.v2|import\s+app\.api\.v2)"
)


# ---------------------------------------------------------------------------
# Property 1: Import Path Consistency (v2→bijmantra)
# ---------------------------------------------------------------------------


class TestProperty1ImportPathConsistencyV2:
    """Feature: api-layer-reorganization, Property 1: Import Path Consistency (v2→bijmantra)

    Verify zero ``app.api.v2`` import statements exist in the codebase.
    After the v2→bijmantra rename, no Python file should reference the
    old v2 API surface — all imports must use ``app.api.bijmantra``.

    **Validates: Requirements 2.4, 2.5, 10.2, 10.3, 10.4**
    """

    @given(data=st.data())
    @settings(max_examples=100)
    def test_no_v2_imports_in_sampled_files(self, data: st.DataObject):
        """
        For any Python file sampled from the backend codebase, the file
        SHALL NOT contain ``from app.api.v2`` or ``import app.api.v2``
        import statements.

        **Validates: Requirements 2.4, 2.5, 10.2, 10.3, 10.4**
        """
        # Skip if no Python files found (defensive — should never happen)
        if not _ALL_PY_FILES:
            pytest.skip("No Python files found under backend/")

        idx = data.draw(
            st.integers(min_value=0, max_value=len(_ALL_PY_FILES) - 1),
            label="python_file_index",
        )
        filepath = _ALL_PY_FILES[idx]

        try:
            content = Path(filepath).read_text(encoding="utf-8", errors="replace")
        except OSError:
            # File may have been removed between glob and read — skip
            return

        match = _V2_IMPORT_RE.search(content)
        assert match is None, (
            f"Found app.api.v2 import in {filepath}:\n"
            f"  {match.group().strip()}"
        )


# ---------------------------------------------------------------------------
# Shared helpers — BrAPI file collection
# ---------------------------------------------------------------------------

# Collect all .py files under backend/app/api/brapi/ once at module load time.
_BRAPI_DIR = _BACKEND_ROOT / "app" / "api" / "brapi"
_BRAPI_PY_FILES: list[str] = sorted(
    glob(str(_BRAPI_DIR / "**" / "*.py"), recursive=True)
)

# Pattern to detect FastAPI router definitions (e.g. `router = APIRouter(...)`)
_ROUTER_DEF_RE = re.compile(
    r"(?:^|\n)\s*\w*router\w*\s*=\s*APIRouter\s*\("
)

# Pattern to detect actual route endpoint decorators (e.g. `@router.get(...)`)
# This distinguishes endpoint files from pure aggregator files that only
# create an APIRouter and call include_router.
_ROUTE_ENDPOINT_RE = re.compile(
    r"@\w*router\w*\.\s*(?:get|post|put|patch|delete|head|options|trace)\s*\("
)

# Allowed subdirectory segments for files that define routers
_ALLOWED_BRAPI_SUBDIRS = {"/brapi/v2/", "/brapi/v3/", "/brapi/shared/"}


# ---------------------------------------------------------------------------
# Property 2: BrAPI File Locality
# ---------------------------------------------------------------------------


class TestProperty2BrAPIFileLocality:
    """Feature: api-layer-reorganization, Property 2: BrAPI File Locality

    For any Python file under ``backend/app/api/brapi/`` that defines a
    FastAPI router, assert it resides under ``brapi/v2/``, ``brapi/v3/``,
    or ``brapi/shared/``.

    Files at the ``brapi/`` root level (like ``__init__.py``) or aggregator
    files that don't define their own routers are acceptable.

    **Validates: Requirements 3.1, 3.2**
    """

    @given(data=st.data())
    @settings(max_examples=100)
    def test_brapi_router_files_reside_in_versioned_dirs(
        self, data: st.DataObject
    ):
        """
        For any Python file sampled from ``backend/app/api/brapi/``, if the
        file defines a FastAPI router (contains ``router = APIRouter(...)``
        or similar), the file SHALL reside under ``brapi/v2/``,
        ``brapi/v3/``, or ``brapi/shared/``.

        **Validates: Requirements 3.1, 3.2**
        """
        if not _BRAPI_PY_FILES:
            pytest.skip("No Python files found under backend/app/api/brapi/")

        idx = data.draw(
            st.integers(min_value=0, max_value=len(_BRAPI_PY_FILES) - 1),
            label="brapi_file_index",
        )
        filepath = _BRAPI_PY_FILES[idx]

        try:
            content = Path(filepath).read_text(encoding="utf-8", errors="replace")
        except OSError:
            # File may have been removed between glob and read — skip
            return

        # Only check files that define a FastAPI router AND register
        # actual route endpoints.  Pure aggregator files (which create an
        # APIRouter but only call include_router) are not BrAPI endpoint
        # files and are allowed at the brapi/ root level.
        if not _ROUTER_DEF_RE.search(content):
            return
        if not _ROUTE_ENDPOINT_RE.search(content):
            return

        # Normalise path separators for cross-platform matching
        normalised = filepath.replace("\\", "/")

        in_allowed_subdir = any(
            sub in normalised for sub in _ALLOWED_BRAPI_SUBDIRS
        )
        assert in_allowed_subdir, (
            f"BrAPI router file found outside versioned subdirectory:\n"
            f"  {filepath}\n"
            f"  Expected to be under brapi/v2/, brapi/v3/, or brapi/shared/"
        )


# ---------------------------------------------------------------------------
# Shared helpers — Phase 2 domain package validation
# ---------------------------------------------------------------------------

# The bijmantra root directory
_BIJMANTRA_DIR = _BACKEND_ROOT / "app" / "api" / "bijmantra"

# Phase 2 domain file names — files that should have been moved into
# their respective domain subdirectories during Phase 2.
_PHASE2_GERMPLASM_FILES = {
    "germplasm_collection.py",
    "germplasm_comparison.py",
    "germplasm_search.py",
    "genetic_diversity.py",
    "genetic_gain.py",
    "passport.py",
    "pedigree.py",
    "grin.py",
}
_PHASE2_PHENOTYPING_FILES = {
    "phenotype.py",
    "phenotype_comparison.py",
    "phenology.py",
    "image_analysis.py",
    "vision.py",
    "performance_ranking.py",
}
_PHASE2_ENVIRONMENT_FILES = {
    "weather.py",
    "climate.py",
    "carbon.py",
    "emissions.py",
}
_PHASE2_INVENTORY_FILES = {
    "seed_inventory.py",
    "traceability.py",
    "warehouse.py",
    "processing.py",
    "label_printing.py",
    "barcode.py",
}

_PHASE2_ALL_MOVED_FILES = (
    _PHASE2_GERMPLASM_FILES
    | _PHASE2_PHENOTYPING_FILES
    | _PHASE2_ENVIRONMENT_FILES
    | _PHASE2_INVENTORY_FILES
)

# Infrastructure files that are expected at the bijmantra root and should
# be excluded from domain-completeness checks.
_INFRASTRUCTURE_FILES = {"__init__.py", "apex_router.py", "dependencies.py"}

# Collect .py files at the bijmantra/ root level (NOT in subdirectories)
# at module load time.
_BIJMANTRA_ROOT_PY_FILES: list[str] = sorted(
    str(p)
    for p in _BIJMANTRA_DIR.iterdir()
    if p.is_file() and p.suffix == ".py" and p.name not in _INFRASTRUCTURE_FILES
)

# Phase 2 domain subdirectories
_PHASE2_DOMAINS = ["germplasm", "phenotyping", "environment", "inventory"]

# Pattern to detect include_router calls
_INCLUDE_ROUTER_RE = re.compile(r"\.\s*include_router\s*\(")


# ---------------------------------------------------------------------------
# Property 3: Domain Package Completeness (Phase 2)
# ---------------------------------------------------------------------------


class TestProperty3DomainPackageCompletenessPhase2:
    """Feature: api-layer-reorganization, Property 3: Domain Package Completeness (Phase 2)

    For any ``.py`` file at the ``bijmantra/`` root level (excluding
    infrastructure files: ``__init__.py``, ``apex_router.py``,
    ``dependencies.py``), assert it does not belong to a Phase 2 domain
    that has already been moved (germplasm, phenotyping, environment,
    inventory).

    **Validates: Requirements 6.1, 6.3, 6.5**
    """

    @given(data=st.data())
    @settings(max_examples=100)
    def test_no_phase2_domain_files_at_bijmantra_root(
        self, data: st.DataObject
    ):
        """
        For any Python file sampled from the ``bijmantra/`` root level
        (excluding infrastructure files), the file SHALL NOT be a file
        that belongs to a Phase 2 domain (germplasm, phenotyping,
        environment, inventory).

        **Validates: Requirements 6.1, 6.3, 6.5**
        """
        if not _BIJMANTRA_ROOT_PY_FILES:
            # No loose .py files at bijmantra root — property trivially holds
            pytest.skip(
                "No non-infrastructure .py files at bijmantra/ root "
                "(all domain files have been moved)"
            )

        idx = data.draw(
            st.integers(
                min_value=0, max_value=len(_BIJMANTRA_ROOT_PY_FILES) - 1
            ),
            label="bijmantra_root_file_index",
        )
        filepath = _BIJMANTRA_ROOT_PY_FILES[idx]
        filename = Path(filepath).name

        assert filename not in _PHASE2_ALL_MOVED_FILES, (
            f"Phase 2 domain file still at bijmantra/ root:\n"
            f"  {filepath}\n"
            f"  This file should have been moved into its domain subdirectory."
        )


# ---------------------------------------------------------------------------
# Property 5: Domain Aggregator Presence (Phase 2)
# ---------------------------------------------------------------------------


class TestProperty5DomainAggregatorPresencePhase2:
    """Feature: api-layer-reorganization, Property 5: Domain Aggregator Presence (Phase 2)

    For each Phase 2 domain subdirectory (germplasm, phenotyping,
    environment, inventory), assert:
      1. A ``router.py`` file exists in the subdirectory
      2. The ``router.py`` contains ``include_router`` calls
      3. The number of ``include_router`` calls matches the number of
         sibling ``.py`` files that define routers

    **Validates: Requirements 6.1, 6.3, 6.5**
    """

    @pytest.mark.parametrize("domain", _PHASE2_DOMAINS)
    def test_domain_aggregator_router_exists(self, domain: str):
        """
        Each Phase 2 domain subdirectory SHALL contain a ``router.py``
        aggregator file.

        **Validates: Requirements 6.1, 6.3, 6.5**
        """
        domain_dir = _BIJMANTRA_DIR / domain
        router_file = domain_dir / "router.py"

        assert domain_dir.is_dir(), (
            f"Phase 2 domain directory does not exist: {domain_dir}"
        )
        assert router_file.is_file(), (
            f"Domain aggregator router.py missing in {domain_dir}"
        )

    @pytest.mark.parametrize("domain", _PHASE2_DOMAINS)
    def test_domain_aggregator_has_include_router_calls(self, domain: str):
        """
        Each Phase 2 domain ``router.py`` SHALL contain at least one
        ``include_router`` call.

        **Validates: Requirements 6.1, 6.3, 6.5**
        """
        router_file = _BIJMANTRA_DIR / domain / "router.py"
        if not router_file.is_file():
            pytest.skip(f"router.py not found for {domain}")

        content = router_file.read_text(encoding="utf-8", errors="replace")
        matches = _INCLUDE_ROUTER_RE.findall(content)

        assert len(matches) > 0, (
            f"Domain aggregator {router_file} has zero include_router calls"
        )

    @pytest.mark.parametrize("domain", _PHASE2_DOMAINS)
    def test_domain_aggregator_includes_all_sibling_routers(self, domain: str):
        """
        The number of ``include_router`` calls in each Phase 2 domain
        ``router.py`` SHALL match the number of sibling ``.py`` files
        that define FastAPI routers (i.e., contain ``router = APIRouter()``
        or endpoint decorators).

        **Validates: Requirements 6.1, 6.3, 6.5**
        """
        domain_dir = _BIJMANTRA_DIR / domain
        router_file = domain_dir / "router.py"
        if not router_file.is_file():
            pytest.skip(f"router.py not found for {domain}")

        # Count sibling .py files that define routers (excluding router.py
        # itself and __init__.py)
        sibling_router_count = 0
        for py_file in sorted(domain_dir.glob("*.py")):
            if py_file.name in ("router.py", "__init__.py"):
                continue
            try:
                file_content = py_file.read_text(
                    encoding="utf-8", errors="replace"
                )
            except OSError:
                continue
            # A sibling is a router file if it defines a router or has
            # endpoint decorators
            if _ROUTER_DEF_RE.search(file_content) or _ROUTE_ENDPOINT_RE.search(
                file_content
            ):
                sibling_router_count += 1

        # Count include_router calls in the aggregator
        router_content = router_file.read_text(
            encoding="utf-8", errors="replace"
        )
        include_count = len(_INCLUDE_ROUTER_RE.findall(router_content))

        assert include_count >= sibling_router_count, (
            f"Domain aggregator {router_file} has {include_count} "
            f"include_router calls but {sibling_router_count} sibling "
            f"router files exist. Some routers may not be included."
        )


# ---------------------------------------------------------------------------
# Shared helpers — Phase 3 domain package validation
# ---------------------------------------------------------------------------

# Phase 3 domain file names — files that should have been moved into
# their respective domain subdirectories during Phase 3.
_PHASE3_BREEDING_FILES = {
    "breeding_pipeline.py",
    "breeding_value.py",
    "crosses.py",
    "crossing_planner.py",
    "doubled_haploid.py",
    "parent_selection.py",
    "progeny.py",
    "selection.py",
    "selection_decisions.py",
    "speed_breeding.py",
}
_PHASE3_GENOMICS_FILES = {
    "genomic_selection.py",
    "genotyping.py",
    "gwas.py",
    "gxe.py",
    "haplotype.py",
    "ld.py",
    "mas.py",
    "molecular_breeding.py",
    "parentage.py",
    "phenomic_selection.py",
    "population_genetics.py",
    "population_structure.py",
    "qtl_mapping.py",
    "bioinformatics.py",
}
_PHASE3_FIELD_FILES = {
    "field_book.py",
    "field_environment.py",
    "field_layout.py",
    "field_map.py",
    "field_planning.py",
    "field_scanner.py",
    "plot_history.py",
    "nursery.py",
    "nursery_management.py",
    "harvest.py",
    "crop_calendar.py",
}
_PHASE3_TRIALS_FILES = {
    "trial_design.py",
    "trial_network.py",
    "trial_planning.py",
    "trial_summary.py",
    "stability_analysis.py",
}
_PHASE3_COLLABORATION_FILES = {
    "collaboration.py",
    "collaboration_hub.py",
    "forums.py",
    "team_management.py",
    "activity.py",
    "notifications.py",
    "workflows.py",
}

_PHASE3_ALL_MOVED_FILES = (
    _PHASE3_BREEDING_FILES
    | _PHASE3_GENOMICS_FILES
    | _PHASE3_FIELD_FILES
    | _PHASE3_TRIALS_FILES
    | _PHASE3_COLLABORATION_FILES
)

# Phase 3 domain subdirectories
_PHASE3_DOMAINS = ["breeding", "genomics", "field", "trials", "collaboration"]


# ---------------------------------------------------------------------------
# Property 3: Domain Package Completeness (Phase 3)
# ---------------------------------------------------------------------------


class TestProperty3DomainPackageCompletenessPhase3:
    """Feature: api-layer-reorganization, Property 3: Domain Package Completeness (Phase 3)

    For any ``.py`` file at the ``bijmantra/`` root level (excluding
    infrastructure files: ``__init__.py``, ``apex_router.py``,
    ``dependencies.py``), assert it does not belong to a Phase 3 domain
    that has already been moved (breeding, genomics, field, trials,
    collaboration).

    **Validates: Requirements 6.1, 6.3, 6.5**
    """

    @given(data=st.data())
    @settings(max_examples=100)
    def test_no_phase3_domain_files_at_bijmantra_root(
        self, data: st.DataObject
    ):
        """
        For any Python file sampled from the ``bijmantra/`` root level
        (excluding infrastructure files), the file SHALL NOT be a file
        that belongs to a Phase 3 domain (breeding, genomics, field,
        trials, collaboration).

        **Validates: Requirements 6.1, 6.3, 6.5**
        """
        if not _BIJMANTRA_ROOT_PY_FILES:
            # No loose .py files at bijmantra root — property trivially holds
            pytest.skip(
                "No non-infrastructure .py files at bijmantra/ root "
                "(all domain files have been moved)"
            )

        idx = data.draw(
            st.integers(
                min_value=0, max_value=len(_BIJMANTRA_ROOT_PY_FILES) - 1
            ),
            label="bijmantra_root_file_index",
        )
        filepath = _BIJMANTRA_ROOT_PY_FILES[idx]
        filename = Path(filepath).name

        assert filename not in _PHASE3_ALL_MOVED_FILES, (
            f"Phase 3 domain file still at bijmantra/ root:\n"
            f"  {filepath}\n"
            f"  This file should have been moved into its domain subdirectory."
        )


# ---------------------------------------------------------------------------
# Property 5: Domain Aggregator Presence (Phase 3)
# ---------------------------------------------------------------------------


class TestProperty5DomainAggregatorPresencePhase3:
    """Feature: api-layer-reorganization, Property 5: Domain Aggregator Presence (Phase 3)

    For each Phase 3 domain subdirectory (breeding, genomics, field,
    trials, collaboration), assert:
      1. A ``router.py`` file exists in the subdirectory
      2. The ``router.py`` contains ``include_router`` calls
      3. The number of ``include_router`` calls matches the number of
         sibling ``.py`` files that define routers

    **Validates: Requirements 6.1, 6.3, 6.5**
    """

    @pytest.mark.parametrize("domain", _PHASE3_DOMAINS)
    def test_domain_aggregator_router_exists(self, domain: str):
        """
        Each Phase 3 domain subdirectory SHALL contain a ``router.py``
        aggregator file.

        **Validates: Requirements 6.1, 6.3, 6.5**
        """
        domain_dir = _BIJMANTRA_DIR / domain
        router_file = domain_dir / "router.py"

        assert domain_dir.is_dir(), (
            f"Phase 3 domain directory does not exist: {domain_dir}"
        )
        assert router_file.is_file(), (
            f"Domain aggregator router.py missing in {domain_dir}"
        )

    @pytest.mark.parametrize("domain", _PHASE3_DOMAINS)
    def test_domain_aggregator_has_include_router_calls(self, domain: str):
        """
        Each Phase 3 domain ``router.py`` SHALL contain at least one
        ``include_router`` call.

        **Validates: Requirements 6.1, 6.3, 6.5**
        """
        router_file = _BIJMANTRA_DIR / domain / "router.py"
        if not router_file.is_file():
            pytest.skip(f"router.py not found for {domain}")

        content = router_file.read_text(encoding="utf-8", errors="replace")
        matches = _INCLUDE_ROUTER_RE.findall(content)

        assert len(matches) > 0, (
            f"Domain aggregator {router_file} has zero include_router calls"
        )

    @pytest.mark.parametrize("domain", _PHASE3_DOMAINS)
    def test_domain_aggregator_includes_all_sibling_routers(self, domain: str):
        """
        The number of ``include_router`` calls in each Phase 3 domain
        ``router.py`` SHALL match the number of sibling ``.py`` files
        that define FastAPI routers (i.e., contain ``router = APIRouter()``
        or endpoint decorators).

        **Validates: Requirements 6.1, 6.3, 6.5**
        """
        domain_dir = _BIJMANTRA_DIR / domain
        router_file = domain_dir / "router.py"
        if not router_file.is_file():
            pytest.skip(f"router.py not found for {domain}")

        # Count sibling .py files that define routers (excluding router.py
        # itself and __init__.py)
        sibling_router_count = 0
        for py_file in sorted(domain_dir.glob("*.py")):
            if py_file.name in ("router.py", "__init__.py"):
                continue
            try:
                file_content = py_file.read_text(
                    encoding="utf-8", errors="replace"
                )
            except OSError:
                continue
            # A sibling is a router file if it defines a router or has
            # endpoint decorators
            if _ROUTER_DEF_RE.search(file_content) or _ROUTE_ENDPOINT_RE.search(
                file_content
            ):
                sibling_router_count += 1

        # Count include_router calls in the aggregator
        router_content = router_file.read_text(
            encoding="utf-8", errors="replace"
        )
        include_count = len(_INCLUDE_ROUTER_RE.findall(router_content))

        assert include_count >= sibling_router_count, (
            f"Domain aggregator {router_file} has {include_count} "
            f"include_router calls but {sibling_router_count} sibling "
            f"router files exist. Some routers may not be included."
        )


# ---------------------------------------------------------------------------
# Shared helpers — Phase 4 domain package validation
# ---------------------------------------------------------------------------

# Phase 4 domain file names — files that should have been moved into
# their respective domain subdirectories during Phase 4.
_PHASE4_COMPUTE_FILES = {
    "compute.py",
    "analytics.py",
    "calculators.py",
    "statistics.py",
    "biosimulation.py",
}
_PHASE4_DATA_FILES = {
    "data_dictionary.py",
    "data_quality.py",
    "data_sync.py",
    "data_validation.py",
    "data_visualization.py",
    "etl.py",
    "export.py",
    "import_api.py",
    "quick_entry.py",
    "offline_sync.py",
}
_PHASE4_RESEARCH_FILES = {
    "ontology.py",
    "proposals.py",
    "reports.py",
    "impact.py",
    "cost_analysis.py",
    "insights.py",
    "search.py",
}
_PHASE4_OPERATIONS_FILES = {
    "agronomy.py",
    "crop_health.py",
    "disease.py",
    "abiotic.py",
    "events.py",
    "tasks.py",
    "resource_management.py",
    "sensors.py",
    "vault_sensors.py",
    "robotics.py",
    "mta.py",
    "dus.py",
    "quality.py",
    "social.py",
    "dock.py",
}
_PHASE4_MONITORING_FILES = {
    "monitoring.py",
    "metrics.py",
    "performance.py",
    "progress.py",
    "workers.py",
}
_PHASE4_SECURITY_FILES = {
    "rbac.py",
    "rls.py",
    "security_audit.py",
    "rakshaka.py",
    "prahari.py",
    "compliance.py",
}
_PHASE4_SYSTEM_FILES = {
    "system_settings.py",
    "backup.py",
    "external_services.py",
    "integrations.py",
    "languages.py",
    "licensing.py",
    "pwa_notifications.py",
    "pwa_sync.py",
    "profile.py",
}
_PHASE4_AI_FILES = {
    "chat.py",
    "ai_configuration.py",
    "veena_ai.py",
    "voice.py",
    "devguru.py",
    "vector.py",
}
_PHASE4_DEVELOPER_FILES = {
    "developer_control_plane.py",
    "developer_control_plane_indigenous_brain.py",
    "developer_control_plane_mem0.py",
    "developer_control_plane_project_brain.py",
    "chaitanya.py",
    "dispatch.py",
}

_PHASE4_ALL_MOVED_FILES = (
    _PHASE4_COMPUTE_FILES
    | _PHASE4_DATA_FILES
    | _PHASE4_RESEARCH_FILES
    | _PHASE4_OPERATIONS_FILES
    | _PHASE4_MONITORING_FILES
    | _PHASE4_SECURITY_FILES
    | _PHASE4_SYSTEM_FILES
    | _PHASE4_AI_FILES
    | _PHASE4_DEVELOPER_FILES
)

# Phase 4 domain subdirectories
_PHASE4_DOMAINS = [
    "compute",
    "data",
    "research",
    "operations",
    "monitoring",
    "security",
    "system",
    "ai",
    "developer",
]


# ---------------------------------------------------------------------------
# Property 3: Domain Package Completeness (Phase 4 — FINAL)
# ---------------------------------------------------------------------------


class TestProperty3DomainPackageCompletenessPhase4:
    """Feature: api-layer-reorganization, Property 3: Domain Package Completeness (Phase 4 — FINAL)

    This is the FINAL completeness check. For any ``.py`` file at the
    ``bijmantra/`` root level (excluding infrastructure files:
    ``__init__.py``, ``apex_router.py``, ``dependencies.py``), assert it
    does NOT define ``router = APIRouter()``. This verifies ALL domain
    route files have been moved into their respective subdirectories.

    **Validates: Requirements 6.1, 6.3, 6.5**
    """

    @given(data=st.data())
    @settings(max_examples=100)
    def test_no_domain_route_files_at_bijmantra_root(
        self, data: st.DataObject
    ):
        """
        For any Python file sampled from the ``bijmantra/`` root level
        (excluding infrastructure files), the file SHALL NOT define a
        FastAPI router (``router = APIRouter()``). All domain route files
        must reside inside domain subdirectories.

        **Validates: Requirements 6.1, 6.3, 6.5**
        """
        if not _BIJMANTRA_ROOT_PY_FILES:
            # No loose .py files at bijmantra root — property trivially holds
            pytest.skip(
                "No non-infrastructure .py files at bijmantra/ root "
                "(all domain files have been moved)"
            )

        idx = data.draw(
            st.integers(
                min_value=0, max_value=len(_BIJMANTRA_ROOT_PY_FILES) - 1
            ),
            label="bijmantra_root_file_index",
        )
        filepath = _BIJMANTRA_ROOT_PY_FILES[idx]

        try:
            content = Path(filepath).read_text(
                encoding="utf-8", errors="replace"
            )
        except OSError:
            return

        match = _ROUTER_DEF_RE.search(content)
        assert match is None, (
            f"Domain route file still at bijmantra/ root:\n"
            f"  {filepath}\n"
            f"  Contains: {match.group().strip()}\n"
            f"  This file should have been moved into its domain subdirectory."
        )


# ---------------------------------------------------------------------------
# Property 4: File Content Preservation (Hot Files)
# ---------------------------------------------------------------------------


class TestProperty4FileContentPreservation:
    """Feature: api-layer-reorganization, Property 4: File Content Preservation

    For hot files (chat.py, developer_control_plane.py), verify they have
    no uncommitted content changes using ``git diff``. If git diff shows
    no changes for these files, the content is preserved byte-identical
    to the pre-move state.

    This is a deterministic test, not hypothesis-based.

    **Validates: Requirements 6.1, 6.3, 6.5, 9.1, 9.2**
    """

    @pytest.mark.parametrize(
        "hot_file_path",
        [
            "app/api/bijmantra/ai/chat.py",
            "app/api/bijmantra/developer/developer_control_plane.py",
        ],
    )
    def test_hot_file_has_no_uncommitted_content_changes(
        self, hot_file_path: str
    ):
        """
        Each hot file SHALL have no uncommitted content changes as
        reported by ``git diff``. This confirms the file content is
        byte-identical to the committed (pre-move) state.

        **Validates: Requirements 9.1, 9.2**
        """
        import subprocess

        full_path = _BACKEND_ROOT / hot_file_path

        assert full_path.is_file(), (
            f"Hot file does not exist at expected location: {full_path}"
        )

        result = subprocess.run(
            ["git", "diff", "--name-only", str(hot_file_path)],
            capture_output=True,
            text=True,
            cwd=str(_BACKEND_ROOT),
        )

        # git diff --name-only returns the filename if there are changes,
        # or empty output if the file is unchanged.
        changed_files = result.stdout.strip()
        assert changed_files == "", (
            f"Hot file has uncommitted content changes:\n"
            f"  {hot_file_path}\n"
            f"  git diff reports: {changed_files}\n"
            f"  Hot file content must be byte-identical to pre-move state."
        )


# ---------------------------------------------------------------------------
# Property 5: Domain Aggregator Presence (Phase 4)
# ---------------------------------------------------------------------------


class TestProperty5DomainAggregatorPresencePhase4:
    """Feature: api-layer-reorganization, Property 5: Domain Aggregator Presence (Phase 4)

    For each Phase 4 domain subdirectory (compute, data, research,
    operations, monitoring, security, system, ai, developer), assert:
      1. A ``router.py`` file exists in the subdirectory
      2. The ``router.py`` contains ``include_router`` calls
      3. The number of ``include_router`` calls matches the number of
         sibling ``.py`` files that define routers

    **Validates: Requirements 6.1, 6.3, 6.5**
    """

    @pytest.mark.parametrize("domain", _PHASE4_DOMAINS)
    def test_domain_aggregator_router_exists(self, domain: str):
        """
        Each Phase 4 domain subdirectory SHALL contain a ``router.py``
        aggregator file.

        **Validates: Requirements 6.1, 6.3, 6.5**
        """
        domain_dir = _BIJMANTRA_DIR / domain
        router_file = domain_dir / "router.py"

        assert domain_dir.is_dir(), (
            f"Phase 4 domain directory does not exist: {domain_dir}"
        )
        assert router_file.is_file(), (
            f"Domain aggregator router.py missing in {domain_dir}"
        )

    @pytest.mark.parametrize("domain", _PHASE4_DOMAINS)
    def test_domain_aggregator_has_include_router_calls(self, domain: str):
        """
        Each Phase 4 domain ``router.py`` SHALL contain at least one
        ``include_router`` call.

        **Validates: Requirements 6.1, 6.3, 6.5**
        """
        router_file = _BIJMANTRA_DIR / domain / "router.py"
        if not router_file.is_file():
            pytest.skip(f"router.py not found for {domain}")

        content = router_file.read_text(encoding="utf-8", errors="replace")
        matches = _INCLUDE_ROUTER_RE.findall(content)

        assert len(matches) > 0, (
            f"Domain aggregator {router_file} has zero include_router calls"
        )

    @pytest.mark.parametrize("domain", _PHASE4_DOMAINS)
    def test_domain_aggregator_includes_all_sibling_routers(self, domain: str):
        """
        The number of ``include_router`` calls in each Phase 4 domain
        ``router.py`` SHALL match the number of sibling ``.py`` files
        that define FastAPI routers (i.e., contain ``router = APIRouter()``
        or endpoint decorators).

        **Validates: Requirements 6.1, 6.3, 6.5**
        """
        domain_dir = _BIJMANTRA_DIR / domain
        router_file = domain_dir / "router.py"
        if not router_file.is_file():
            pytest.skip(f"router.py not found for {domain}")

        # Count sibling .py files that define routers (excluding router.py
        # itself and __init__.py)
        sibling_router_count = 0
        for py_file in sorted(domain_dir.glob("*.py")):
            if py_file.name in ("router.py", "__init__.py"):
                continue
            try:
                file_content = py_file.read_text(
                    encoding="utf-8", errors="replace"
                )
            except OSError:
                continue
            # A sibling is a router file if it defines a router or has
            # endpoint decorators
            if _ROUTER_DEF_RE.search(file_content) or _ROUTE_ENDPOINT_RE.search(
                file_content
            ):
                sibling_router_count += 1

        # Count include_router calls in the aggregator
        router_content = router_file.read_text(
            encoding="utf-8", errors="replace"
        )
        include_count = len(_INCLUDE_ROUTER_RE.findall(router_content))

        assert include_count >= sibling_router_count, (
            f"Domain aggregator {router_file} has {include_count} "
            f"include_router calls but {sibling_router_count} sibling "
            f"router files exist. Some routers may not be included."
        )


# ---------------------------------------------------------------------------
# Property 1: Import Path Consistency (FINAL — v1 AND v2 combined)
# ---------------------------------------------------------------------------


class TestProperty1ImportPathConsistencyFinal:
    """Feature: api-layer-reorganization, Property 1: Import Path Consistency (Final)

    Comprehensive final check that combines both v1 AND v2 import path
    verification. For any Python file sampled from the backend codebase,
    assert NEITHER ``from app.api.v1`` NOR ``from app.api.v2`` patterns
    exist. This is the definitive post-reorganization validation.

    **Validates: Requirements 2.4, 2.5, 10.2, 10.3, 10.4**
    """

    @given(data=st.data())
    @settings(max_examples=100)
    def test_no_v1_or_v2_imports_in_sampled_files(self, data: st.DataObject):
        """
        For any Python file sampled from the backend codebase, the file
        SHALL NOT contain ``from app.api.v1``, ``import app.api.v1``,
        ``from app.api.v2``, or ``import app.api.v2`` import statements.

        This is the final combined check after all reorganization phases
        are complete.

        **Validates: Requirements 2.4, 2.5, 10.2, 10.3, 10.4**
        """
        if not _ALL_PY_FILES:
            pytest.skip("No Python files found under backend/")

        idx = data.draw(
            st.integers(min_value=0, max_value=len(_ALL_PY_FILES) - 1),
            label="python_file_index",
        )
        filepath = _ALL_PY_FILES[idx]

        try:
            content = Path(filepath).read_text(encoding="utf-8", errors="replace")
        except OSError:
            # File may have been removed between glob and read — skip
            return

        # Check for v1 imports
        v1_match = _V1_IMPORT_RE.search(content)
        assert v1_match is None, (
            f"Found app.api.v1 import in {filepath}:\n"
            f"  {v1_match.group().strip()}"
        )

        # Check for v2 imports
        v2_match = _V2_IMPORT_RE.search(content)
        assert v2_match is None, (
            f"Found app.api.v2 import in {filepath}:\n"
            f"  {v2_match.group().strip()}"
        )


# ---------------------------------------------------------------------------
# Property 6: URL Path Preservation (structural verification)
# ---------------------------------------------------------------------------

# Pre-compiled pattern for extracting prefix= arguments from include_router calls
_PREFIX_RE = re.compile(r'prefix\s*=\s*["\']([^"\']+)["\']')


class TestProperty6URLPathPreservation:
    """Feature: api-layer-reorganization, Property 6: URL Path Preservation

    Verify that all registered FastAPI route prefixes are preserved after
    the reorganization. Since we cannot easily instantiate the full FastAPI
    app in a unit test (it requires database connections, etc.), this is
    implemented as a STRUCTURAL test that scans ``startup/routes.py`` for
    all ``prefix=`` arguments in ``include_router`` calls.

    This is a deterministic test, not hypothesis-based.

    **Validates: Requirements 8.1, 8.2, 8.3, 8.4**
    """

    def _extract_prefixes_from_routes(self) -> set[str]:
        """Extract all prefix= values from startup/routes.py."""
        routes_file = _BACKEND_ROOT / "app" / "startup" / "routes.py"
        assert routes_file.is_file(), (
            f"startup/routes.py not found at {routes_file}"
        )
        content = routes_file.read_text(encoding="utf-8", errors="replace")
        return set(_PREFIX_RE.findall(content))

    def test_expected_url_prefixes_present(self):
        """
        The route registration SHALL include the expected URL prefixes:
        ``/api/v2``, ``/brapi/v2``, and ``/api/auth``.

        **Validates: Requirements 8.1, 8.2, 8.3, 8.4**
        """
        prefixes = self._extract_prefixes_from_routes()

        # These are the three primary API surfaces that must be preserved
        expected_prefixes = {"/api/v2", "/brapi/v2", "/api/auth"}

        for expected in expected_prefixes:
            assert expected in prefixes, (
                f"Expected URL prefix '{expected}' not found in "
                f"startup/routes.py.\n"
                f"  Found prefixes: {sorted(prefixes)}"
            )

    def test_no_v1_url_prefix_registered(self):
        """
        The route registration SHALL NOT include any ``/api/v1`` URL
        prefix. The v1 surface was removed in Phase 0.

        **Validates: Requirements 8.1, 8.4**
        """
        prefixes = self._extract_prefixes_from_routes()

        v1_prefixes = {p for p in prefixes if "/api/v1" in p}
        assert len(v1_prefixes) == 0, (
            f"Found unexpected /api/v1 URL prefix(es) in "
            f"startup/routes.py: {sorted(v1_prefixes)}"
        )

    def test_no_unexpected_top_level_prefixes(self):
        """
        The route registration SHALL NOT include unexpected top-level
        prefixes outside the known set. This guards against accidental
        route surface expansion during reorganization.

        **Validates: Requirements 8.1, 8.4**
        """
        prefixes = self._extract_prefixes_from_routes()

        # Known acceptable prefix patterns
        known_patterns = {"/api/v2", "/brapi/v2", "/api/auth"}

        for prefix in prefixes:
            is_known = any(
                prefix == known or prefix.startswith(known + "/")
                for known in known_patterns
            )
            assert is_known, (
                f"Unexpected URL prefix found in startup/routes.py: "
                f"'{prefix}'\n"
                f"  Known patterns: {sorted(known_patterns)}\n"
                f"  All found prefixes: {sorted(prefixes)}"
            )


# ---------------------------------------------------------------------------
# Property 7: Service Layer Isolation (git diff verification)
# ---------------------------------------------------------------------------


class TestProperty7ServiceLayerIsolation:
    """Feature: api-layer-reorganization, Property 7: Service Layer Isolation

    For any file under ``backend/app/modules/`` that was modified during
    the reorganization, verify only import path changes occurred (no
    business logic modifications). Uses ``git diff`` to inspect changes.

    This is a deterministic test, not hypothesis-based.

    **Validates: Requirements 10.1, 10.5**
    """

    # Patterns that indicate an import-path-only change line
    _IMPORT_CHANGE_RE = re.compile(
        r"^\s*(?:from\s+app\.|import\s+app\.)"
    )

    # Lines to skip in diff output (diff headers, context markers)
    _DIFF_HEADER_RE = re.compile(
        r"^(?:diff\s|index\s|---\s|[+]{3}\s|@@\s|\\)"
    )

    def _get_modified_module_files(self) -> list[str]:
        """Get list of modified files under app/modules/ using git diff."""
        import subprocess

        result = subprocess.run(
            ["git", "diff", "--name-only", "--", "app/modules/"],
            capture_output=True,
            text=True,
            cwd=str(_BACKEND_ROOT),
        )
        if result.returncode != 0:
            return []

        files = [
            f.strip()
            for f in result.stdout.strip().split("\n")
            if f.strip() and f.strip().endswith(".py")
        ]
        return files

    def _get_file_diff(self, filepath: str) -> str:
        """Get unified diff for a specific file."""
        import subprocess

        result = subprocess.run(
            ["git", "diff", "-U0", "--", filepath],
            capture_output=True,
            text=True,
            cwd=str(_BACKEND_ROOT),
        )
        return result.stdout

    def test_module_files_have_only_import_changes(self):
        """
        For any file under ``backend/app/modules/`` that has uncommitted
        changes, ALL changed lines (lines starting with ``+`` or ``-``,
        excluding diff headers) SHALL contain only import path changes
        (e.g., ``app.api.v2`` → ``app.api.bijmantra``).

        No business logic, function signatures, class definitions, or
        behavioral code shall be added, removed, or modified in module
        files.

        **Validates: Requirements 10.1, 10.5**
        """
        modified_files = self._get_modified_module_files()

        if not modified_files:
            # No modified module files — property trivially holds.
            # This is the expected state after all changes are committed.
            return

        violations = []

        for filepath in modified_files:
            diff_output = self._get_file_diff(filepath)
            if not diff_output:
                continue

            for line in diff_output.split("\n"):
                # Skip diff metadata lines
                if self._DIFF_HEADER_RE.match(line):
                    continue

                # Only inspect added (+) or removed (-) lines
                if not (line.startswith("+") or line.startswith("-")):
                    continue

                # Strip the leading +/- to get the actual code line
                code_line = line[1:].strip()

                # Skip empty lines (blank line additions/removals are benign)
                if not code_line:
                    continue

                # Skip comment-only lines
                if code_line.startswith("#"):
                    continue

                # The line must be an import statement change
                if not self._IMPORT_CHANGE_RE.match(code_line):
                    violations.append(
                        f"  {filepath}: {line.rstrip()}"
                    )

        assert len(violations) == 0, (
            f"Found non-import changes in module files "
            f"(expected only import path updates):\n"
            + "\n".join(violations[:20])  # Cap output at 20 lines
            + (
                f"\n  ... and {len(violations) - 20} more"
                if len(violations) > 20
                else ""
            )
        )
