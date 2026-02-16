from app.services.yield_gap_service import yield_gap_service


def test_calculate_potential_yield_benchmarks():
    value = yield_gap_service._cached_potential_yield(
        crop="wheat",
        location_id=1,
        gdd=20.0,
        ptu=250.0,
        water=1.0,
        nitrogen=1.0,
        phosphorus=1.0,
        temp_stress=1.0,
    )
    assert 4.0 <= value <= 8.5


def test_identify_limiting_factors_orders_by_score():
    factors = yield_gap_service.identify_limiting_factors(
        environment_data={"water_index": 0.55, "temperature_index": 0.9},
        soil_data={"nitrogen_index": 0.5, "phosphorus_index": 0.8},
    )

    assert factors
    assert factors[0].factor in {"Nitrogen", "Water"}
    assert factors[0].score >= factors[-1].score
