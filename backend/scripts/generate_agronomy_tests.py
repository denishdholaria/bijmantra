

def calculate_expected(crop, area, target_yield, soil_n, soil_p, soil_k):
    reqs = {
        "wheat": {"N": 120, "P": 60, "K": 40},
        "rice": {"N": 100, "P": 50, "K": 50},
        "maize": {"N": 150, "P": 75, "K": 60},
        "soybean": {"N": 30, "P": 60, "K": 40},
        "cotton": {"N": 120, "P": 60, "K": 60},
    }
    r = reqs[crop]
    yf = target_yield / 4.0
    n_needed = max(0, r["N"] * yf - soil_n)
    p_needed = max(0, r["P"] * yf - soil_p * 2.29)
    k_needed = max(0, r["K"] * yf - soil_k * 0.12)

    urea = (n_needed / 0.46) * area if n_needed > 0 else 0
    dap = (p_needed / 0.46) * area if p_needed > 0 else 0
    mop = (k_needed / 0.60) * area if k_needed > 0 else 0

    return round(urea), round(dap), round(mop)

crops = ["wheat", "rice", "maize", "soybean", "cotton"]
test_cases = []

reqs = {
    "wheat": {"N": 120, "P": 60, "K": 40},
    "rice": {"N": 100, "P": 50, "K": 50},
    "maize": {"N": 150, "P": 75, "K": 60},
    "soybean": {"N": 30, "P": 60, "K": 40},
    "cotton": {"N": 120, "P": 60, "K": 60},
}

for crop in crops:
    r = reqs[crop]
    base_n = r["N"]
    base_p = r["P"]
    base_k = r["K"]

    # 1. Base Case
    test_cases.append((crop, 1.0, 4.0, 0.0, 0.0, 0.0))

    # 2. High Yield
    test_cases.append((crop, 1.0, 8.0, 0.0, 0.0, 0.0))

    # 3. Low Yield
    test_cases.append((crop, 1.0, 2.0, 0.0, 0.0, 0.0))

    # 4. Large Area
    test_cases.append((crop, 10.0, 4.0, 0.0, 0.0, 0.0))

    # 5. Small Area
    test_cases.append((crop, 0.1, 4.0, 0.0, 0.0, 0.0))

    # 6. High Soil N
    test_cases.append((crop, 1.0, 4.0, base_n + 10, 0.0, 0.0))

    # 7. High Soil P (ppm needed approx base_p / 2.29)
    p_ppm = (base_p / 2.29) + 10
    test_cases.append((crop, 1.0, 4.0, 0.0, round(p_ppm, 2), 0.0))

    # 8. High Soil K (ppm needed approx base_k / 0.12)
    k_ppm = (base_k / 0.12) + 10
    test_cases.append((crop, 1.0, 4.0, 0.0, 0.0, round(k_ppm, 2)))

    # 9. High Soil N, P
    test_cases.append((crop, 1.0, 4.0, base_n + 10, round(p_ppm, 2), 0.0))

    # 10. High Soil N, K
    test_cases.append((crop, 1.0, 4.0, base_n + 10, 0.0, round(k_ppm, 2)))

    # 11. High Soil P, K
    test_cases.append((crop, 1.0, 4.0, 0.0, round(p_ppm, 2), round(k_ppm, 2)))

    # 12. High Soil All
    test_cases.append((crop, 1.0, 4.0, base_n + 10, round(p_ppm, 2), round(k_ppm, 2)))

    # 13. Exact Soil N
    test_cases.append((crop, 1.0, 4.0, base_n, 0.0, 0.0))

    # 14. Exact Soil P
    test_cases.append((crop, 1.0, 4.0, 0.0, round(base_p / 2.29, 2), 0.0))

    # 15. Exact Soil K
    test_cases.append((crop, 1.0, 4.0, 0.0, 0.0, round(base_k / 0.12, 2)))

    # 16-20. Random / Realistic
    test_cases.append((crop, 2.5, 5.0, 50.0, 10.0, 100.0))
    test_cases.append((crop, 5.0, 3.0, 20.0, 5.0, 50.0))
    test_cases.append((crop, 0.5, 6.0, 80.0, 25.0, 200.0))
    test_cases.append((crop, 1.2, 4.5, 40.0, 15.0, 120.0))
    test_cases.append((crop, 1.0, 4.0, 10.0, 2.0, 20.0))

print("import pytest")
print("from app.api.v2.agronomy import calculate_fertilizer, FertilizerRequest, get_supported_crops")
print("from fastapi import HTTPException")
print("")
print("# Generated Test Cases")
print("agronomy_test_cases = [")

for i, (crop, area, ty, sn, sp, sk) in enumerate(test_cases):
    u, d, m = calculate_expected(crop, area, ty, sn, sp, sk)
    print(f"    # {i+1}. {crop.capitalize()} Area={area}, Yield={ty}, Soil=({sn},{sp},{sk})")
    print(f"    (\"{crop}\", {area}, {ty}, {sn}, {sp}, {sk}, {u}, {d}, {m}),")

print("]")
print("")
print("@pytest.mark.parametrize(\"crop, area, target_yield, soil_n, soil_p, soil_k, exp_urea, exp_dap, exp_mop\", agronomy_test_cases)")
print("@pytest.mark.asyncio")
print("async def test_calculate_fertilizer_generated(crop, area, target_yield, soil_n, soil_p, soil_k, exp_urea, exp_dap, exp_mop):")
print("    req = FertilizerRequest(")
print("        crop=crop, area=area, target_yield=target_yield,")
print("        soil_n=soil_n, soil_p=soil_p, soil_k=soil_k")
print("    )")
print("    res = await calculate_fertilizer(req)")
print("    assert res.urea == exp_urea")
print("    assert res.dap == exp_dap")
print("    assert res.mop == exp_mop")
print("")
print("@pytest.mark.asyncio")
print("async def test_get_supported_crops():")
print("    res = await get_supported_crops()")
print("    assert \"crops\" in res")
print("    assert len(res[\"crops\"]) == 5")
print("    assert \"wheat\" in res[\"crops\"]")
print("")
print("@pytest.mark.asyncio")
print("async def test_invalid_crop():")
print("    req = FertilizerRequest(")
print("        crop=\"invalid_crop\", area=1.0, target_yield=4.0,")
print("        soil_n=0, soil_p=0, soil_k=0")
print("    )")
print("    with pytest.raises(HTTPException) as excinfo:")
print("        await calculate_fertilizer(req)")
print("    assert excinfo.value.status_code == 400")
