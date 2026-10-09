from __future__ import annotations

import itertools

import pytest

from churnwise.domain import revenue
from churnwise.domain.types import MovementTotals, RangeKey

REL = 1e-9
STAT_FIELDS = [
    ("start", "start"),
    ("mrr", "mrr"),
    ("mrr_start", "mrrStart"),
    ("net_new", "netNew"),
    ("net_new_prior", "netNewPrior"),
    ("churn_rate", "churnRate"),
    ("churn_rate_prior", "churnRatePrior"),
    ("nrr", "nrr"),
    ("nrr_start", "nrrStart"),
    ("customers", "customers"),
    ("customers_start", "customersStart"),
    ("arpa", "arpa"),
    ("arpa_start", "arpaStart"),
    ("ltv", "ltv"),
    ("ltv_start", "ltvStart"),
    ("recovered", "recovered"),
    ("recovered_prior", "recoveredPrior"),
    ("recovery_rate", "recoveryRate"),
    ("failed", "failed"),
]


def test_trailing_retention_matches_typescript(model, golden):
    assert revenue.nrr_at(model, model.last) == pytest.approx(golden["nrrLast"], rel=REL)
    assert revenue.grr_at(model, model.last) == pytest.approx(golden["grrLast"], rel=REL)
    assert revenue.trailing_churn_rate(model, model.last) == pytest.approx(golden["churnLast"], rel=REL)


def test_grr_never_exceeds_100_and_nrr_beats_grr(model):
    for index in range(0, model.day_count, 30):
        grr = revenue.grr_at(model, index)
        assert grr <= 100
        assert revenue.nrr_at(model, index) >= grr


def test_retention_on_day_zero_is_flat(model):
    assert revenue.nrr_at(model, 0) == pytest.approx(100)
    assert revenue.grr_at(model, 0) == pytest.approx(100)


@pytest.mark.parametrize("key", list(RangeKey))
def test_range_stats_match_typescript(model, golden, key):
    stats = revenue.range_stats(model, key)
    expected = golden["ranges"][key.value]["stats"]
    assert stats.label == expected["label"]
    for attr, field in STAT_FIELDS:
        value, want = getattr(stats, attr), expected[field]
        if want is None:
            assert value is None, attr
        else:
            assert value == pytest.approx(want, rel=REL), attr
    assert len(stats.line) == expected["line"]
    assert stats.line[0].value == pytest.approx(golden["ranges"][key.value]["lineFirst"]["value"], rel=REL)
    assert stats.line[-1].day == model.last_day


@pytest.mark.parametrize("key", list(RangeKey))
def test_movement_buckets_match_typescript(model, golden, key):
    buckets = revenue.movement_buckets(model, key)
    expected = golden["ranges"][key.value]["buckets"]
    assert [b.label for b in buckets] == [e["label"] for e in expected]
    for bucket, want in zip(buckets, expected, strict=True):
        assert (bucket.start, bucket.end) == (want["start"], want["end"])
        assert bucket.net == pytest.approx(want["net"], rel=1e-8)
        for movement in ("new", "expansion", "reactivation", "contraction", "churn"):
            assert bucket.totals[movement] == pytest.approx(want[movement], rel=1e-8)


def test_bucket_cadence(model):
    assert len(revenue.movement_buckets(model, RangeKey.D30)) == 30
    assert len(revenue.movement_buckets(model, RangeKey.D90)) == 13
    assert len(revenue.movement_buckets(model, RangeKey.M12)) == 12
    assert len(revenue.movement_buckets(model, RangeKey.M24)) == 24


def test_buckets_tile_the_range_and_reconcile(model):
    for key in RangeKey:
        buckets = revenue.movement_buckets(model, key)
        assert buckets[0].start == revenue.range_start(model, key)
        assert buckets[-1].end == model.day_count
        assert all(a.end == b.start for a, b in itertools.pairwise(buckets))
        start_mrr = model[buckets[0].start - 1].mrr if buckets[0].start else 318_400
        assert start_mrr + sum(b.net for b in buckets) == pytest.approx(model[model.last].mrr, rel=1e-9)
        assert buckets[-1].ending_mrr == model[model.last].mrr


def test_year_labels_only_where_the_axis_needs_them(model):
    labels = [b.label for b in revenue.movement_buckets(model, RangeKey.M24)]
    assert labels[0] == "Oct '24"
    assert "Jan '25" in labels and "Jan '26" in labels
    assert labels[1] == "Nov"


def test_quick_ratio_matches_typescript(model, golden):
    for key in RangeKey:
        buckets = revenue.movement_buckets(model, key)
        total = MovementTotals.sum([b.totals for b in buckets])
        assert total.quick_ratio == pytest.approx(golden["ranges"][key.value]["quick"], rel=1e-8)


def test_range_definitions_compare_against_window_starts(model):
    definitions = revenue.range_definitions(model)
    assert definitions[RangeKey.M12].comparison_note == "vs Oct 1, 2025"
    assert definitions[RangeKey.M24].comparison_note == "vs Oct 1, 2024"
    assert [d.short for d in definitions.values()] == ["30D", "90D", "12M", "24M"]


def test_ltv_requires_positive_churn():
    assert revenue.ltv(300, 0.02) == pytest.approx(300 * 0.82 / 0.02)
    with pytest.raises(ValueError):
        revenue.ltv(300, 0)
