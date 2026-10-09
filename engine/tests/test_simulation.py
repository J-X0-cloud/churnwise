from __future__ import annotations

from datetime import date, timedelta

import pytest

from churnwise.domain.simulation import (
    FIRST_DAY,
    LAST_DAY,
    OPENING_MRR,
    RevenueModel,
    simulate,
)
from churnwise.domain.types import MOVEMENT_ORDER, Movement

REL = 1e-9


def test_model_spans_the_sample_period(model):
    assert model.day_count == 724
    assert model.first_day == FIRST_DAY
    assert model.last_day == LAST_DAY
    assert model[0].day == date(2024, 10, 1)


@pytest.mark.parametrize(("index", "key"), [(0, "daily0"), (100, "daily100"), (-1, "dailyLast")])
def test_daily_rows_match_the_typescript_model(model, golden, index, key):
    row, expected = model[index], golden[key]
    for movement in MOVEMENT_ORDER:
        assert row.flows[movement] == pytest.approx(expected["flows"][movement.value], rel=REL)
    for field in ("mrr", "arpa", "customers", "failed", "recovered"):
        assert getattr(row, field) == pytest.approx(expected[field], rel=REL)


def test_mrr_identity_holds_every_day(model):
    previous = OPENING_MRR
    for row in model.rows:
        assert row.mrr == pytest.approx(previous + row.flows.net, rel=1e-12)
        previous = row.mrr


def test_customers_follow_from_mrr_and_arpa(model):
    for row in model.rows[::50]:
        assert row.customers == pytest.approx(row.mrr / row.arpa)
        assert 0 < row.recovered < row.failed


def test_weekday_sales_outpace_weekends(model):
    weekday = [r.flows.new for r in model.rows if r.day.weekday() < 5]
    weekend = [r.flows.new for r in model.rows if r.day.weekday() >= 5]
    assert sum(weekday) / len(weekday) > 1.8 * sum(weekend) / len(weekend)


def test_churn_clusters_at_month_start(model):
    early = [r.flows.churn for r in model.rows if r.day.day <= 3]
    rest = [r.flows.churn for r in model.rows if r.day.day > 3]
    assert sum(early) / len(early) > 1.7 * sum(rest) / len(rest)


def test_month_windows_cover_every_day_once(model, golden):
    assert [[w.start, w.end] for w in model.months] == golden["months"]
    assert model.months[0].start == 0
    assert model.months[-1].end == model.day_count
    assert all(a.end == b.start for a, b in zip(model.months, model.months[1:], strict=False))


def test_range_sums_clamp_to_the_series(model):
    assert model.sum_flow(Movement.NEW, -50, 1) == pytest.approx(model[0].flows.new)
    assert model.sum_flow(Movement.NEW, 720, 10_000) == pytest.approx(
        sum(r.flows.new for r in model.rows[720:])
    )
    assert model.sum_flow(Movement.CHURN, 10, 5) == 0


def test_prefix_sums_agree_with_direct_sums(model):
    assert model.sum_failed(100, 200) == pytest.approx(sum(r.failed for r in model.rows[100:200]))
    assert model.average_mrr(0, 30) == pytest.approx(sum(r.mrr for r in model.rows[:30]) / 30)
    totals = model.flow_totals(0, model.day_count)
    assert totals.net == pytest.approx(model[model.last].mrr - OPENING_MRR)


def test_average_of_empty_window_is_an_error(model):
    with pytest.raises(ValueError):
        model.average_mrr(5, 5)


def test_simulation_is_reproducible_and_seed_sensitive():
    short = simulate(date(2025, 1, 1), date(2025, 3, 31))
    assert [r.mrr for r in short] == [r.mrr for r in simulate(date(2025, 1, 1), date(2025, 3, 31))]
    other = simulate(date(2025, 1, 1), date(2025, 3, 31), seed=1)
    assert short[-1].mrr != other[-1].mrr


def test_model_rejects_gaps_and_tiny_series():
    rows = simulate(date(2025, 1, 1), date(2025, 1, 10))
    with pytest.raises(ValueError):
        RevenueModel(rows[:1])
    gapped = [rows[0], rows[2]]
    with pytest.raises(ValueError):
        RevenueModel(gapped)
    with pytest.raises(ValueError):
        simulate(date(2025, 1, 1), date(2025, 1, 1) - timedelta(days=1))
