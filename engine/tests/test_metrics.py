from __future__ import annotations

import pytest

from churnwise import fixtures
from churnwise.domain import metrics, revenue
from churnwise.domain.recovery import RecoveryAnalytics
from churnwise.domain.types import RangeKey

REL = 1e-8


def _assert_kpis_match(actual: list[metrics.Kpi], expected: list[dict]) -> None:
    assert [k.label for k in actual] == [e["label"] for e in expected]
    for kpi, want in zip(actual, expected, strict=True):
        assert kpi.value == want["value"], kpi.label
        assert kpi.delta.text == want["delta"]["text"], kpi.label
        assert kpi.delta.tone == want["delta"]["tone"], kpi.label
        assert kpi.delta.arrow == want["delta"].get("arrow"), kpi.label
        assert kpi.unit == want.get("unit")
        if "spark" in want:
            assert kpi.spark is not None
            assert list(kpi.spark) == pytest.approx(want["spark"], rel=REL)
        else:
            assert kpi.spark is None


@pytest.mark.parametrize("key", list(RangeKey))
def test_overview_kpis_match_typescript(model, golden, key):
    _assert_kpis_match(metrics.overview_kpis(model, key), golden["ranges"][key.value]["kpis"])


def test_other_tabs_kpis_match_typescript(model, golden):
    _assert_kpis_match(metrics.retention_kpis(model), golden["retentionKpis"])
    _assert_kpis_match(metrics.customer_kpis(model), golden["customerKpis"])
    _assert_kpis_match(metrics.recovery_kpis(RecoveryAnalytics(model)), golden["recoveryKpis"])


def test_spark_tones_replace_hex_colours(model):
    tones = {k.label: k.spark_tone for k in metrics.overview_kpis(model, RangeKey.M12)}
    assert tones["Net new MRR"] == "mint"
    assert tones["Revenue churn"] == "red"
    assert tones["MRR"] is None


@pytest.mark.parametrize(
    ("current", "prior", "kwargs", "text", "tone", "arrow"),
    [
        (110, 100, {}, "+10.0%", "good", "up"),
        (90, 100, {}, "−10.0%", "bad", "down"),
        (90, 100, {"good_up": False}, "−10.0%", "good", "down"),
        (1.5, 1.2, {"unit": "pts"}, "+0.3 pts", "good", "up"),
        (-50, -100, {}, "+50.0%", "good", "up"),
    ],
)
def test_delta(current, prior, kwargs, text, tone, arrow):
    result = metrics.delta(current, prior, **kwargs)
    assert result is not None
    assert (result.text, result.tone, result.arrow) == (text, tone, arrow)


def test_delta_without_a_comparable_prior():
    assert metrics.delta(10, None) is None
    assert metrics.delta(10, 0) is None


def test_mrr_line_labels(model, golden):
    for key in RangeKey:
        stats = revenue.range_stats(model, key)
        line = metrics.mrr_line(model, stats)
        expected = golden["ranges"][key.value]["mrrLine"]
        for point, want in zip(line, expected, strict=False):
            assert point.label == want["label"]
            assert point.tip == want["tip"]
            assert point.value == pytest.approx(want["value"], rel=REL)


def test_retention_series_matches_typescript(model, golden):
    series = metrics.retention_series(model)
    assert list(series.labels) == golden["retentionSeries"]["labels"]
    assert list(series.nrr) == pytest.approx(golden["retentionSeries"]["nrr"], rel=REL)
    assert list(series.grr) == pytest.approx(golden["retentionSeries"]["grr"], rel=REL)


def test_plan_breakdown_matches_typescript_and_adds_up(model, golden):
    plans = metrics.plan_breakdown(model)
    for plan, want in zip(plans, golden["plans"], strict=True):
        assert plan.name == want["name"]
        assert plan.mrr == pytest.approx(want["mrr"], rel=REL)
        assert plan.share == pytest.approx(want["share"], rel=REL)
        assert plan.customers == pytest.approx(want["customers"], rel=REL)
        assert plan.churn == pytest.approx(want["churn"], rel=REL)
    assert sum(p.mrr for p in plans) == pytest.approx(model[model.last].mrr)
    assert sum(p.share for p in plans) == pytest.approx(100)
    assert sum(p.customers for p in plans) == pytest.approx(model[model.last].customers)


def test_plan_mix_moves_up_market_over_time(model):
    start = {p.name: p.share for p in metrics.plan_breakdown(model, 0)}
    end = {p.name: p.share for p in metrics.plan_breakdown(model)}
    assert end["Starter"] < start["Starter"]
    assert end["Enterprise"] > start["Enterprise"]


def test_account_trends_match_typescript(golden):
    rows = metrics.account_rows()
    assert len(rows) == len(fixtures.accounts())
    for row, want in zip(rows, golden["trends"], strict=True):
        assert list(row.history) == pytest.approx(want, rel=REL)
        assert row.history[-1] == row.mrr


def test_account_trend_shapes():
    up, down = (next(a for a in fixtures.accounts() if a.trend == t) for t in ("up", "down"))
    rising = metrics.account_trend(up, 0)
    falling = metrics.account_trend(down, 0)
    assert rising[0] < rising[-1]
    assert falling[0] > falling[-1]
