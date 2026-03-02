import pytest
from app.api.v2.agronomy import calculate_fertilizer, FertilizerRequest, get_supported_crops
from fastapi import HTTPException

# Generated Test Cases
agronomy_test_cases = [
    # 1. Wheat Area=1.0, Yield=4.0, Soil=(0.0,0.0,0.0)
    ("wheat", 1.0, 4.0, 0.0, 0.0, 0.0, 261, 130, 67),
    # 2. Wheat Area=1.0, Yield=8.0, Soil=(0.0,0.0,0.0)
    ("wheat", 1.0, 8.0, 0.0, 0.0, 0.0, 522, 261, 133),
    # 3. Wheat Area=1.0, Yield=2.0, Soil=(0.0,0.0,0.0)
    ("wheat", 1.0, 2.0, 0.0, 0.0, 0.0, 130, 65, 33),
    # 4. Wheat Area=10.0, Yield=4.0, Soil=(0.0,0.0,0.0)
    ("wheat", 10.0, 4.0, 0.0, 0.0, 0.0, 2609, 1304, 667),
    # 5. Wheat Area=0.1, Yield=4.0, Soil=(0.0,0.0,0.0)
    ("wheat", 0.1, 4.0, 0.0, 0.0, 0.0, 26, 13, 7),
    # 6. Wheat Area=1.0, Yield=4.0, Soil=(130,0.0,0.0)
    ("wheat", 1.0, 4.0, 130, 0.0, 0.0, 0, 130, 67),
    # 7. Wheat Area=1.0, Yield=4.0, Soil=(0.0,36.2,0.0)
    ("wheat", 1.0, 4.0, 0.0, 36.2, 0.0, 261, 0, 67),
    # 8. Wheat Area=1.0, Yield=4.0, Soil=(0.0,0.0,343.33)
    ("wheat", 1.0, 4.0, 0.0, 0.0, 343.33, 261, 130, 0),
    # 9. Wheat Area=1.0, Yield=4.0, Soil=(130,36.2,0.0)
    ("wheat", 1.0, 4.0, 130, 36.2, 0.0, 0, 0, 67),
    # 10. Wheat Area=1.0, Yield=4.0, Soil=(130,0.0,343.33)
    ("wheat", 1.0, 4.0, 130, 0.0, 343.33, 0, 130, 0),
    # 11. Wheat Area=1.0, Yield=4.0, Soil=(0.0,36.2,343.33)
    ("wheat", 1.0, 4.0, 0.0, 36.2, 343.33, 261, 0, 0),
    # 12. Wheat Area=1.0, Yield=4.0, Soil=(130,36.2,343.33)
    ("wheat", 1.0, 4.0, 130, 36.2, 343.33, 0, 0, 0),
    # 13. Wheat Area=1.0, Yield=4.0, Soil=(120,0.0,0.0)
    ("wheat", 1.0, 4.0, 120, 0.0, 0.0, 0, 130, 67),
    # 14. Wheat Area=1.0, Yield=4.0, Soil=(0.0,26.2,0.0)
    ("wheat", 1.0, 4.0, 0.0, 26.2, 0.0, 261, 0, 67),
    # 15. Wheat Area=1.0, Yield=4.0, Soil=(0.0,0.0,333.33)
    ("wheat", 1.0, 4.0, 0.0, 0.0, 333.33, 261, 130, 0),
    # 16. Wheat Area=2.5, Yield=5.0, Soil=(50.0,10.0,100.0)
    ("wheat", 2.5, 5.0, 50.0, 10.0, 100.0, 543, 283, 158),
    # 17. Wheat Area=5.0, Yield=3.0, Soil=(20.0,5.0,50.0)
    ("wheat", 5.0, 3.0, 20.0, 5.0, 50.0, 761, 365, 200),
    # 18. Wheat Area=0.5, Yield=6.0, Soil=(80.0,25.0,200.0)
    ("wheat", 0.5, 6.0, 80.0, 25.0, 200.0, 109, 36, 30),
    # 19. Wheat Area=1.2, Yield=4.5, Soil=(40.0,15.0,120.0)
    ("wheat", 1.2, 4.5, 40.0, 15.0, 120.0, 248, 86, 61),
    # 20. Wheat Area=1.0, Yield=4.0, Soil=(10.0,2.0,20.0)
    ("wheat", 1.0, 4.0, 10.0, 2.0, 20.0, 239, 120, 63),
    # 21. Rice Area=1.0, Yield=4.0, Soil=(0.0,0.0,0.0)
    ("rice", 1.0, 4.0, 0.0, 0.0, 0.0, 217, 109, 83),
    # 22. Rice Area=1.0, Yield=8.0, Soil=(0.0,0.0,0.0)
    ("rice", 1.0, 8.0, 0.0, 0.0, 0.0, 435, 217, 167),
    # 23. Rice Area=1.0, Yield=2.0, Soil=(0.0,0.0,0.0)
    ("rice", 1.0, 2.0, 0.0, 0.0, 0.0, 109, 54, 42),
    # 24. Rice Area=10.0, Yield=4.0, Soil=(0.0,0.0,0.0)
    ("rice", 10.0, 4.0, 0.0, 0.0, 0.0, 2174, 1087, 833),
    # 25. Rice Area=0.1, Yield=4.0, Soil=(0.0,0.0,0.0)
    ("rice", 0.1, 4.0, 0.0, 0.0, 0.0, 22, 11, 8),
    # 26. Rice Area=1.0, Yield=4.0, Soil=(110,0.0,0.0)
    ("rice", 1.0, 4.0, 110, 0.0, 0.0, 0, 109, 83),
    # 27. Rice Area=1.0, Yield=4.0, Soil=(0.0,31.83,0.0)
    ("rice", 1.0, 4.0, 0.0, 31.83, 0.0, 217, 0, 83),
    # 28. Rice Area=1.0, Yield=4.0, Soil=(0.0,0.0,426.67)
    ("rice", 1.0, 4.0, 0.0, 0.0, 426.67, 217, 109, 0),
    # 29. Rice Area=1.0, Yield=4.0, Soil=(110,31.83,0.0)
    ("rice", 1.0, 4.0, 110, 31.83, 0.0, 0, 0, 83),
    # 30. Rice Area=1.0, Yield=4.0, Soil=(110,0.0,426.67)
    ("rice", 1.0, 4.0, 110, 0.0, 426.67, 0, 109, 0),
    # 31. Rice Area=1.0, Yield=4.0, Soil=(0.0,31.83,426.67)
    ("rice", 1.0, 4.0, 0.0, 31.83, 426.67, 217, 0, 0),
    # 32. Rice Area=1.0, Yield=4.0, Soil=(110,31.83,426.67)
    ("rice", 1.0, 4.0, 110, 31.83, 426.67, 0, 0, 0),
    # 33. Rice Area=1.0, Yield=4.0, Soil=(100,0.0,0.0)
    ("rice", 1.0, 4.0, 100, 0.0, 0.0, 0, 109, 83),
    # 34. Rice Area=1.0, Yield=4.0, Soil=(0.0,21.83,0.0)
    ("rice", 1.0, 4.0, 0.0, 21.83, 0.0, 217, 0, 83),
    # 35. Rice Area=1.0, Yield=4.0, Soil=(0.0,0.0,416.67)
    ("rice", 1.0, 4.0, 0.0, 0.0, 416.67, 217, 109, 0),
    # 36. Rice Area=2.5, Yield=5.0, Soil=(50.0,10.0,100.0)
    ("rice", 2.5, 5.0, 50.0, 10.0, 100.0, 408, 215, 210),
    # 37. Rice Area=5.0, Yield=3.0, Soil=(20.0,5.0,50.0)
    ("rice", 5.0, 3.0, 20.0, 5.0, 50.0, 598, 283, 262),
    # 38. Rice Area=0.5, Yield=6.0, Soil=(80.0,25.0,200.0)
    ("rice", 0.5, 6.0, 80.0, 25.0, 200.0, 76, 19, 42),
    # 39. Rice Area=1.2, Yield=4.5, Soil=(40.0,15.0,120.0)
    ("rice", 1.2, 4.5, 40.0, 15.0, 120.0, 189, 57, 84),
    # 40. Rice Area=1.0, Yield=4.0, Soil=(10.0,2.0,20.0)
    ("rice", 1.0, 4.0, 10.0, 2.0, 20.0, 196, 99, 79),
    # 41. Maize Area=1.0, Yield=4.0, Soil=(0.0,0.0,0.0)
    ("maize", 1.0, 4.0, 0.0, 0.0, 0.0, 326, 163, 100),
    # 42. Maize Area=1.0, Yield=8.0, Soil=(0.0,0.0,0.0)
    ("maize", 1.0, 8.0, 0.0, 0.0, 0.0, 652, 326, 200),
    # 43. Maize Area=1.0, Yield=2.0, Soil=(0.0,0.0,0.0)
    ("maize", 1.0, 2.0, 0.0, 0.0, 0.0, 163, 82, 50),
    # 44. Maize Area=10.0, Yield=4.0, Soil=(0.0,0.0,0.0)
    ("maize", 10.0, 4.0, 0.0, 0.0, 0.0, 3261, 1630, 1000),
    # 45. Maize Area=0.1, Yield=4.0, Soil=(0.0,0.0,0.0)
    ("maize", 0.1, 4.0, 0.0, 0.0, 0.0, 33, 16, 10),
    # 46. Maize Area=1.0, Yield=4.0, Soil=(160,0.0,0.0)
    ("maize", 1.0, 4.0, 160, 0.0, 0.0, 0, 163, 100),
    # 47. Maize Area=1.0, Yield=4.0, Soil=(0.0,42.75,0.0)
    ("maize", 1.0, 4.0, 0.0, 42.75, 0.0, 326, 0, 100),
    # 48. Maize Area=1.0, Yield=4.0, Soil=(0.0,0.0,510.0)
    ("maize", 1.0, 4.0, 0.0, 0.0, 510.0, 326, 163, 0),
    # 49. Maize Area=1.0, Yield=4.0, Soil=(160,42.75,0.0)
    ("maize", 1.0, 4.0, 160, 42.75, 0.0, 0, 0, 100),
    # 50. Maize Area=1.0, Yield=4.0, Soil=(160,0.0,510.0)
    ("maize", 1.0, 4.0, 160, 0.0, 510.0, 0, 163, 0),
    # 51. Maize Area=1.0, Yield=4.0, Soil=(0.0,42.75,510.0)
    ("maize", 1.0, 4.0, 0.0, 42.75, 510.0, 326, 0, 0),
    # 52. Maize Area=1.0, Yield=4.0, Soil=(160,42.75,510.0)
    ("maize", 1.0, 4.0, 160, 42.75, 510.0, 0, 0, 0),
    # 53. Maize Area=1.0, Yield=4.0, Soil=(150,0.0,0.0)
    ("maize", 1.0, 4.0, 150, 0.0, 0.0, 0, 163, 100),
    # 54. Maize Area=1.0, Yield=4.0, Soil=(0.0,32.75,0.0)
    ("maize", 1.0, 4.0, 0.0, 32.75, 0.0, 326, 0, 100),
    # 55. Maize Area=1.0, Yield=4.0, Soil=(0.0,0.0,500.0)
    ("maize", 1.0, 4.0, 0.0, 0.0, 500.0, 326, 163, 0),
    # 56. Maize Area=2.5, Yield=5.0, Soil=(50.0,10.0,100.0)
    ("maize", 2.5, 5.0, 50.0, 10.0, 100.0, 747, 385, 262),
    # 57. Maize Area=5.0, Yield=3.0, Soil=(20.0,5.0,50.0)
    ("maize", 5.0, 3.0, 20.0, 5.0, 50.0, 1005, 487, 325),
    # 58. Maize Area=0.5, Yield=6.0, Soil=(80.0,25.0,200.0)
    ("maize", 0.5, 6.0, 80.0, 25.0, 200.0, 158, 60, 55),
    # 59. Maize Area=1.2, Yield=4.5, Soil=(40.0,15.0,120.0)
    ("maize", 1.2, 4.5, 40.0, 15.0, 120.0, 336, 130, 106),
    # 60. Maize Area=1.0, Yield=4.0, Soil=(10.0,2.0,20.0)
    ("maize", 1.0, 4.0, 10.0, 2.0, 20.0, 304, 153, 96),
    # 61. Soybean Area=1.0, Yield=4.0, Soil=(0.0,0.0,0.0)
    ("soybean", 1.0, 4.0, 0.0, 0.0, 0.0, 65, 130, 67),
    # 62. Soybean Area=1.0, Yield=8.0, Soil=(0.0,0.0,0.0)
    ("soybean", 1.0, 8.0, 0.0, 0.0, 0.0, 130, 261, 133),
    # 63. Soybean Area=1.0, Yield=2.0, Soil=(0.0,0.0,0.0)
    ("soybean", 1.0, 2.0, 0.0, 0.0, 0.0, 33, 65, 33),
    # 64. Soybean Area=10.0, Yield=4.0, Soil=(0.0,0.0,0.0)
    ("soybean", 10.0, 4.0, 0.0, 0.0, 0.0, 652, 1304, 667),
    # 65. Soybean Area=0.1, Yield=4.0, Soil=(0.0,0.0,0.0)
    ("soybean", 0.1, 4.0, 0.0, 0.0, 0.0, 7, 13, 7),
    # 66. Soybean Area=1.0, Yield=4.0, Soil=(40,0.0,0.0)
    ("soybean", 1.0, 4.0, 40, 0.0, 0.0, 0, 130, 67),
    # 67. Soybean Area=1.0, Yield=4.0, Soil=(0.0,36.2,0.0)
    ("soybean", 1.0, 4.0, 0.0, 36.2, 0.0, 65, 0, 67),
    # 68. Soybean Area=1.0, Yield=4.0, Soil=(0.0,0.0,343.33)
    ("soybean", 1.0, 4.0, 0.0, 0.0, 343.33, 65, 130, 0),
    # 69. Soybean Area=1.0, Yield=4.0, Soil=(40,36.2,0.0)
    ("soybean", 1.0, 4.0, 40, 36.2, 0.0, 0, 0, 67),
    # 70. Soybean Area=1.0, Yield=4.0, Soil=(40,0.0,343.33)
    ("soybean", 1.0, 4.0, 40, 0.0, 343.33, 0, 130, 0),
    # 71. Soybean Area=1.0, Yield=4.0, Soil=(0.0,36.2,343.33)
    ("soybean", 1.0, 4.0, 0.0, 36.2, 343.33, 65, 0, 0),
    # 72. Soybean Area=1.0, Yield=4.0, Soil=(40,36.2,343.33)
    ("soybean", 1.0, 4.0, 40, 36.2, 343.33, 0, 0, 0),
    # 73. Soybean Area=1.0, Yield=4.0, Soil=(30,0.0,0.0)
    ("soybean", 1.0, 4.0, 30, 0.0, 0.0, 0, 130, 67),
    # 74. Soybean Area=1.0, Yield=4.0, Soil=(0.0,26.2,0.0)
    ("soybean", 1.0, 4.0, 0.0, 26.2, 0.0, 65, 0, 67),
    # 75. Soybean Area=1.0, Yield=4.0, Soil=(0.0,0.0,333.33)
    ("soybean", 1.0, 4.0, 0.0, 0.0, 333.33, 65, 130, 0),
    # 76. Soybean Area=2.5, Yield=5.0, Soil=(50.0,10.0,100.0)
    ("soybean", 2.5, 5.0, 50.0, 10.0, 100.0, 0, 283, 158),
    # 77. Soybean Area=5.0, Yield=3.0, Soil=(20.0,5.0,50.0)
    ("soybean", 5.0, 3.0, 20.0, 5.0, 50.0, 27, 365, 200),
    # 78. Soybean Area=0.5, Yield=6.0, Soil=(80.0,25.0,200.0)
    ("soybean", 0.5, 6.0, 80.0, 25.0, 200.0, 0, 36, 30),
    # 79. Soybean Area=1.2, Yield=4.5, Soil=(40.0,15.0,120.0)
    ("soybean", 1.2, 4.5, 40.0, 15.0, 120.0, 0, 86, 61),
    # 80. Soybean Area=1.0, Yield=4.0, Soil=(10.0,2.0,20.0)
    ("soybean", 1.0, 4.0, 10.0, 2.0, 20.0, 43, 120, 63),
    # 81. Cotton Area=1.0, Yield=4.0, Soil=(0.0,0.0,0.0)
    ("cotton", 1.0, 4.0, 0.0, 0.0, 0.0, 261, 130, 100),
    # 82. Cotton Area=1.0, Yield=8.0, Soil=(0.0,0.0,0.0)
    ("cotton", 1.0, 8.0, 0.0, 0.0, 0.0, 522, 261, 200),
    # 83. Cotton Area=1.0, Yield=2.0, Soil=(0.0,0.0,0.0)
    ("cotton", 1.0, 2.0, 0.0, 0.0, 0.0, 130, 65, 50),
    # 84. Cotton Area=10.0, Yield=4.0, Soil=(0.0,0.0,0.0)
    ("cotton", 10.0, 4.0, 0.0, 0.0, 0.0, 2609, 1304, 1000),
    # 85. Cotton Area=0.1, Yield=4.0, Soil=(0.0,0.0,0.0)
    ("cotton", 0.1, 4.0, 0.0, 0.0, 0.0, 26, 13, 10),
    # 86. Cotton Area=1.0, Yield=4.0, Soil=(130,0.0,0.0)
    ("cotton", 1.0, 4.0, 130, 0.0, 0.0, 0, 130, 100),
    # 87. Cotton Area=1.0, Yield=4.0, Soil=(0.0,36.2,0.0)
    ("cotton", 1.0, 4.0, 0.0, 36.2, 0.0, 261, 0, 100),
    # 88. Cotton Area=1.0, Yield=4.0, Soil=(0.0,0.0,510.0)
    ("cotton", 1.0, 4.0, 0.0, 0.0, 510.0, 261, 130, 0),
    # 89. Cotton Area=1.0, Yield=4.0, Soil=(130,36.2,0.0)
    ("cotton", 1.0, 4.0, 130, 36.2, 0.0, 0, 0, 100),
    # 90. Cotton Area=1.0, Yield=4.0, Soil=(130,0.0,510.0)
    ("cotton", 1.0, 4.0, 130, 0.0, 510.0, 0, 130, 0),
    # 91. Cotton Area=1.0, Yield=4.0, Soil=(0.0,36.2,510.0)
    ("cotton", 1.0, 4.0, 0.0, 36.2, 510.0, 261, 0, 0),
    # 92. Cotton Area=1.0, Yield=4.0, Soil=(130,36.2,510.0)
    ("cotton", 1.0, 4.0, 130, 36.2, 510.0, 0, 0, 0),
    # 93. Cotton Area=1.0, Yield=4.0, Soil=(120,0.0,0.0)
    ("cotton", 1.0, 4.0, 120, 0.0, 0.0, 0, 130, 100),
    # 94. Cotton Area=1.0, Yield=4.0, Soil=(0.0,26.2,0.0)
    ("cotton", 1.0, 4.0, 0.0, 26.2, 0.0, 261, 0, 100),
    # 95. Cotton Area=1.0, Yield=4.0, Soil=(0.0,0.0,500.0)
    ("cotton", 1.0, 4.0, 0.0, 0.0, 500.0, 261, 130, 0),
    # 96. Cotton Area=2.5, Yield=5.0, Soil=(50.0,10.0,100.0)
    ("cotton", 2.5, 5.0, 50.0, 10.0, 100.0, 543, 283, 262),
    # 97. Cotton Area=5.0, Yield=3.0, Soil=(20.0,5.0,50.0)
    ("cotton", 5.0, 3.0, 20.0, 5.0, 50.0, 761, 365, 325),
    # 98. Cotton Area=0.5, Yield=6.0, Soil=(80.0,25.0,200.0)
    ("cotton", 0.5, 6.0, 80.0, 25.0, 200.0, 109, 36, 55),
    # 99. Cotton Area=1.2, Yield=4.5, Soil=(40.0,15.0,120.0)
    ("cotton", 1.2, 4.5, 40.0, 15.0, 120.0, 248, 86, 106),
    # 100. Cotton Area=1.0, Yield=4.0, Soil=(10.0,2.0,20.0)
    ("cotton", 1.0, 4.0, 10.0, 2.0, 20.0, 239, 120, 96),
]

@pytest.mark.parametrize("crop, area, target_yield, soil_n, soil_p, soil_k, exp_urea, exp_dap, exp_mop", agronomy_test_cases)
@pytest.mark.asyncio
async def test_calculate_fertilizer_generated(crop, area, target_yield, soil_n, soil_p, soil_k, exp_urea, exp_dap, exp_mop):
    req = FertilizerRequest(
        crop=crop, area=area, target_yield=target_yield,
        soil_n=soil_n, soil_p=soil_p, soil_k=soil_k
    )
    res = await calculate_fertilizer(req)
    assert res.urea == exp_urea
    assert res.dap == exp_dap
    assert res.mop == exp_mop

@pytest.mark.asyncio
async def test_get_supported_crops():
    res = await get_supported_crops()
    assert "crops" in res
    assert len(res["crops"]) == 5
    assert "wheat" in res["crops"]

@pytest.mark.asyncio
async def test_invalid_crop():
    req = FertilizerRequest(
        crop="invalid_crop", area=1.0, target_yield=4.0,
        soil_n=0, soil_p=0, soil_k=0
    )
    with pytest.raises(HTTPException) as excinfo:
        await calculate_fertilizer(req)
    assert excinfo.value.status_code == 400
