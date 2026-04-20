from types import SimpleNamespace

from app.modules.breeding.services.trial_search_service import _location_matches


def test_location_matches_uses_additional_location_context():
    trial = SimpleNamespace(
        location=SimpleNamespace(location_name="PAU Research Station", abbreviation="PAU", country_name="India"),
        additional_info={"location_context": "Ludhiana"},
    )

    assert _location_matches(trial, "Ludhiana") is True
    assert _location_matches(trial, "Punjab") is False