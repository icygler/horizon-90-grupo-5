import pytest

from horizon90.models import ScenarioInput


def test_scenario_requires_confirmation():
    scenario = ScenarioInput(
        airport_iata="GRU",
        start_at="2015-06-04T15:00:00",
        duration_minutes=90,
        capacity_reduction_pct=30,
        confirmed=False,
    )

    with pytest.raises(ValueError, match="confirmado"):
        scenario.to_contract()
