from __future__ import annotations

import pytest

from churnwise.domain.forecast import (
    SCENARIOS,
    forecast,
    forecast_table,
    monthly_net_new_pace,
    scenario_definition,
)
from churnwise.domain.types import Scenario

REL = 1e-9


@pytest.mark.parametrize("scenario", list(Scenario))
def test_forecast_matches_typescript(model, golden, scenario):
    result = forecast(model, scenario)
    want = golden["forecasts"][scenario.value]
    assert [p.label for p in result.history] == [p["label"] for p in want["f"]["history"]]
    assert [p.label for p in result.projection] == [p["label"] for p in want["f"]["projection"]]
    assert [p.value for p in result.projection] == pytest.approx(
        [p["value"] for p in want["f"]["projection"]], rel=REL
    )
    for (low, high), (want_low, want_high) in zip(result.band, want["f"]["band"], strict=True):
        assert low == pytest.approx(want_low, rel=REL)
        assert high == pytest.approx(want_high, rel=REL)
    assert result.months_to_target(1_000_000) == want["m1"]


def test_scenarios_are_ordered_by_ambition(model):
    ends = [forecast(model, d.key).end for d in SCENARIOS]
    assert ends == sorted(ends)
    assert scenario_definition(Scenario.BASE).multiplier == 1


def test_history_ends_at_todays_mrr(model):
    result = forecast(model, Scenario.BASE)
    assert result.history[-1].value == model[model.last].mrr
    assert result.history[-1].label == "Sep"
    assert result.projection[0].label == "Oct"
    assert result.projection[3].label == "Jan '27"


def test_interval_widens_with_horizon_and_brackets_the_projection(model):
    result = forecast(model, Scenario.STRETCH)
    widths = [high - low for low, high in result.band]
    assert widths == sorted(widths)
    for point, (low, high) in zip(result.projection, result.band, strict=True):
        assert low < point.value < high


def test_forecast_table(model, golden):
    result = forecast(model, Scenario.CONSERVATIVE)
    rows = forecast_table(result)
    want = golden["forecasts"]["conservative"]["table"]
    assert len(rows) == 12
    for row, expected in zip(rows, want, strict=True):
        assert row.month == expected["month"]
        assert row.net_new == pytest.approx(expected["netNew"], rel=REL)
        assert row.run_rate_arr == pytest.approx(row.projected * 12)
    assert rows[0].net_new == pytest.approx(result.projection[0].value - result.history[-1].value)


def test_months_to_target_outside_horizon(model):
    assert forecast(model, Scenario.CONSERVATIVE).months_to_target(10_000_000) is None
    assert forecast(model, Scenario.BASE).months_to_target(0) == 1


def test_pace_and_validation(model):
    assert monthly_net_new_pace(model) == pytest.approx(
        (model[model.last].mrr - model[model.last - 90].mrr) / 3
    )
    with pytest.raises(ValueError):
        forecast(model, Scenario.BASE, horizon=0)
    with pytest.raises(KeyError):
        scenario_definition("nope")  # type: ignore[arg-type]
