from app.services.reevu import ClaimItem, EvidencePack, PolicyGuard, ResponseValidator


def test_policy_guard_allows_default_read_scope():
    guard = PolicyGuard()

    decision = guard.evaluate_access(domain_scope="breeding", entity="trials", operation="read")

    assert decision.allowed is True
    assert decision.tier == "A"


def test_policy_guard_blocks_security_denylist_entity():
    guard = PolicyGuard()

    decision = guard.evaluate_access(domain_scope="breeding", entity="auth_tokens", operation="read")

    assert decision.allowed is False
    assert decision.tier == "D"


def test_response_validator_rejects_unmatched_reference_and_calculation_claims():
    validator = ResponseValidator()
    evidence = EvidencePack(evidence_refs={"ev-1"}, calculation_ids={"calc-1"})
    claims = [
        ClaimItem(statement="supported reference", claim_type="reference", evidence_refs=("ev-1",)),
        ClaimItem(statement="bad reference", claim_type="reference", evidence_refs=("ev-x",)),
        ClaimItem(statement="bad quantitative", claim_type="quantitative", calculation_ids=("calc-x",)),
    ]

    result = validator.validate_claims(claims=claims, evidence_pack=evidence)

    assert result.valid is False
    assert any("unmatched evidence refs" in err for err in result.errors)
    assert any("unmatched calculation ids" in err for err in result.errors)
