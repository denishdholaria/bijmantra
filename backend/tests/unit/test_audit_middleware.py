import pytest

from app.middleware.audit_middleware import AuditMiddleware, _mask_payload, high_resource_limiter


def test_mask_payload_masks_pii_fields():
    payload = {"full_name": "Alice", "email": "a@x.com", "meta": {"phone": "123"}, "value": 1}
    masked = _mask_payload(payload)
    assert masked["full_name"] == "***"
    assert masked["email"] == "***"
    assert masked["meta"]["phone"] == "***"
    assert masked["value"] == 1


def test_critical_path_detection():
    mw = AuditMiddleware(app=lambda s, r, se: None)
    assert mw._is_critical('/api/v2/vision/datasets')
    assert mw._is_critical('/api/v2/trials')
    assert not mw._is_critical('/api/v2/health')


def test_high_resource_limiter_blocks_burst():
    key = 't:resource'
    allowed = [high_resource_limiter.allow(key) for _ in range(high_resource_limiter.max_requests)]
    assert all(allowed)
    assert high_resource_limiter.allow(key) is False
