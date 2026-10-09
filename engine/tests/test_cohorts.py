from __future__ import annotations

from datetime import date

import pytest

from churnwise.domain.cohorts import (
    CustomerHistory,
    build_cohorts,
    cohort_average,
    sample_cohorts,
    weighted_cohort_average,
)
from churnwise.domain.types import CohortMetric

REL = 1e-9


def test_sample_cohorts_match_typescript(golden):
    cohorts = sample_cohorts()
    assert len(cohorts) == len(golden["cohorts"]) == 12
    for cohort, want in zip(cohorts, golden["cohorts"], strict=True):
        assert cohort.label == want["label"]
        assert cohort.customers == want["customers"]
        assert cohort.start_mrr == pytest.approx(want["startMrr"], rel=REL)
        assert list(cohort.net) == pytest.approx(want["net"], rel=REL)
        assert list(cohort.logo) == pytest.approx(want["logo"], rel=REL)


def test_sample_cohorts_form_a_triangle():
    cohorts = sample_cohorts()
    assert [len(c.net) for c in cohorts] == list(range(12, 0, -1))
    assert cohorts[0].month == date(2025, 10, 1)
    assert cohorts[-1].age == 0


def test_logo_retention_never_rises():
    for cohort in sample_cohorts():
        assert all(b < a for a, b in zip(cohort.logo, cohort.logo[1:], strict=False))
        assert cohort.logo[0] == cohort.net[0] == 100


def test_cohort_averages_match_typescript(golden):
    cohorts = sample_cohorts()
    assert cohort_average(cohorts, CohortMetric.NET, 12) == pytest.approx(golden["avgNet"], rel=REL)
    assert cohort_average(cohorts, CohortMetric.LOGO, 12) == pytest.approx(golden["avgLogo"], rel=REL)


def test_cohort_average_is_none_where_no_cohort_is_old_enough():
    averages = cohort_average(sample_cohorts()[-2:], CohortMetric.NET, 4)
    assert averages[0] == 100
    assert averages[2] is None and averages[3] is None


def test_weighted_average_leans_towards_large_cohorts():
    cohorts = sample_cohorts()
    plain = cohort_average(cohorts, CohortMetric.LOGO, 3)
    weighted = weighted_cohort_average(cohorts, CohortMetric.LOGO, 3)
    assert weighted[0] == 100
    assert weighted[1] != plain[1]
    assert weighted[1] == pytest.approx(
        sum(c.logo[1] * c.customers for c in cohorts if len(c.logo) > 1)
        / sum(c.customers for c in cohorts if len(c.logo) > 1)
    )


def _history(cid: str, values: dict[str, float]) -> CustomerHistory:
    return CustomerHistory(cid, {date.fromisoformat(k): v for k, v in values.items()})


def test_build_cohorts_from_customer_histories():
    histories = [
        _history("a", {"2026-01-01": 100, "2026-02-01": 150, "2026-03-01": 150}),
        _history("b", {"2026-01-01": 100, "2026-02-01": 0, "2026-03-01": 0}),
        _history("c", {"2026-01-01": 0, "2026-02-01": 200, "2026-03-01": 100}),
        _history("never", {"2026-01-01": 0}),
    ]
    jan, feb = build_cohorts(histories, as_of=date(2026, 3, 20))

    assert (jan.label, jan.customers, jan.start_mrr) == ("Jan 2026", 2, 200)
    assert list(jan.net) == pytest.approx([100, 75, 75])
    assert list(jan.logo) == pytest.approx([100, 50, 50])

    assert (feb.label, feb.customers, feb.start_mrr) == ("Feb 2026", 1, 200)
    assert list(feb.net) == pytest.approx([100, 50])
    assert list(feb.logo) == pytest.approx([100, 100])


def test_build_cohorts_respects_first_month_and_as_of():
    histories = [_history("a", {"2025-12-01": 50, "2026-01-01": 50}), _history("b", {"2026-04-01": 80})]
    cohorts = build_cohorts(histories, as_of=date(2026, 2, 1), first_month=date(2026, 1, 1))
    assert cohorts == []
