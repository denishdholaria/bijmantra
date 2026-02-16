import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.api.v2.trial_summary import get_top_performers

@pytest.mark.asyncio
async def test_get_top_performers_change_percent_calculated():
    # Mock dependencies
    mock_db = AsyncMock()
    mock_org_id = 1
    trial_id = "trial1"

    # Mock Trial
    mock_trial = MagicMock()
    mock_trial.id = 1
    mock_trial.trial_db_id = trial_id

    # 1. Trial result
    mock_trial_result = MagicMock()
    mock_trial_result.scalar_one_or_none.return_value = mock_trial

    # 2. Variable ID result
    mock_var_result = MagicMock()
    mock_var_result.scalar_one_or_none.return_value = 10  # var_id

    # 3. Check Mean result
    mock_check_mean_result = MagicMock()
    mock_check_mean_result.scalar.return_value = 100.0

    # Only 3 calls expected now: Trial, VarID, CheckMean

    mock_db.execute.side_effect = [
        mock_trial_result,
        mock_var_result,
        mock_check_mean_result
    ]

    # Mock performance_ranking_service.get_top_performers
    mock_performers = [
        {
            "rank": 1,
            "id": "101",
            "name": "Variety A",
            "yield": 120.0, # Service returns populated yield now
            "traits": []
        }
    ]

    # Patch the service used in the module
    with patch("app.api.v2.trial_summary.performance_ranking_service") as mock_service:
        mock_service.get_top_performers = AsyncMock(return_value=mock_performers)

        response = await get_top_performers(
            trial_id=trial_id,
            limit=10,
            trait="Yield",
            db=mock_db,
            organization_id=mock_org_id
        )

        data = response["data"]
        assert len(data) == 1
        # Check calculation: (120 - 100) / 100 = 20%
        assert data[0].change_percent == "+20.0%"
        assert data[0].yield_value == 120.0
