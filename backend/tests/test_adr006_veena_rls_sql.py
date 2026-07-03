import importlib.util
from pathlib import Path

from app.core.rls import generate_reasoning_trace_rls_policy_sql


def _load_migration_module():
    module_path = Path(__file__).resolve().parents[1] / "alembic/versions/20260313_0200_adr006_devguru_veena_ownership_rls.py"
    spec = importlib.util.spec_from_file_location("adr006_veena_rls_migration", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reasoning_trace_rls_sql_is_symmetric_in_runtime_helper():
    sql = generate_reasoning_trace_rls_policy_sql("veena_reasoning_traces_v2")

    assert "WITH CHECK" in sql
    assert sql.count("FROM veena_audit_logs audit") == 2
    assert "audit.session_id = veena_reasoning_traces_v2.session_id" in sql


def test_reasoning_trace_rls_sql_is_symmetric_in_migration_builder():
    migration = _load_migration_module()
    sql = migration._reasoning_trace_rls_sql()

    assert "WITH CHECK" in sql
    assert sql.count("FROM veena_audit_logs audit") == 2
    assert "audit.session_id = veena_reasoning_traces_v2.session_id" in sql


def test_generic_rls_sql_remains_generic_in_migration_builder():
    migration = _load_migration_module()
    sql = migration._generic_rls_sql("research_projects")

    assert "veena_reasoning_traces_v2.session_id" not in sql
    assert sql.count("organization_id =") == 2