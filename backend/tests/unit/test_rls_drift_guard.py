from scripts.check_rls_drift import RlsTableState, classify_rls_drift


def test_rls_drift_guard_flags_disabled_unforced_and_unregistered_tables():
    report = classify_rls_drift(
        [
            RlsTableState("programs", rls_enabled=True, rls_forced=True),
            RlsTableState("unsafe_table", rls_enabled=False, rls_forced=False),
        ],
        registered_tables=["programs"],
    )

    assert report.has_failures is True
    assert report.missing_rls_enabled == ["unsafe_table"]
    assert report.missing_rls_forced == ["unsafe_table"]
    assert report.unregistered_tenant_tables == ["unsafe_table"]


def test_rls_drift_guard_treats_registered_missing_db_tables_as_warning_only():
    report = classify_rls_drift(
        [RlsTableState("programs", rls_enabled=True, rls_forced=True)],
        registered_tables=["programs", "future_table"],
    )

    assert report.has_failures is False
    assert report.registered_tables_missing_from_db == ["future_table"]
