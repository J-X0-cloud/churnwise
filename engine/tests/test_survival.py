from __future__ import annotations

import math

import pytest

from churnwise.domain.cohorts import Cohort, sample_cohorts
from churnwise.domain.rng import Mulberry32
from churnwise.domain.survival import (
    HazardFit,
    Lifetime,
    fit_constant_hazard,
    kaplan_meier,
    lifetimes_from_cohorts,
    project_churn,
)


def _lifetimes(observed: list[float], censored: list[float]) -> list[Lifetime]:
    return [Lifetime(t, True) for t in observed] + [Lifetime(t, False) for t in censored]


def test_kaplan_meier_textbook_example():
    # Events at 6, 6, 6, 7, 10; censored at 6, 9, 10, 11.
    curve = kaplan_meier(_lifetimes([6, 6, 6, 7, 10], [6, 9, 10, 11]))
    survival = {p.time: p.survival for p in curve.points}
    assert survival[6] == pytest.approx(6 / 9)
    assert survival[7] == pytest.approx(6 / 9 * 4 / 5)
    assert survival[10] == pytest.approx(6 / 9 * 4 / 5 * 2 / 3)
    assert [p.at_risk for p in curve.points] == [9, 5, 3]
    assert curve.subjects == 9 and curve.events == 5


def test_step_function_median_and_restricted_mean():
    curve = kaplan_meier(_lifetimes([1, 2, 3, 4], []))
    assert curve.survival_at(0.5) == 1
    assert curve.survival_at(2) == pytest.approx(0.5)
    assert curve.survival_at(2.9) == pytest.approx(0.5)
    assert curve.median() == 2
    # Area: 1 * 1 + 0.75 * 1 + 0.5 * 1 + 0.25 * 1 = 2.5
    assert curve.restricted_mean(4) == pytest.approx(2.5)
    assert curve.restricted_mean(10) == pytest.approx(2.5)


def test_median_is_none_when_most_customers_stay():
    assert kaplan_meier(_lifetimes([3], [12] * 9)).median() is None


def test_confidence_band_brackets_the_estimate():
    rng = Mulberry32(5)
    lifetimes = [Lifetime(round(-math.log(1 - rng.next()) / 0.05), rng.next() < 0.8) for _ in range(400)]
    curve = kaplan_meier(lifetimes)
    for point in curve.points:
        assert 0 <= point.low <= point.survival <= point.high <= 1


def test_kaplan_meier_validates():
    with pytest.raises(ValueError):
        kaplan_meier([])
    with pytest.raises(ValueError):
        kaplan_meier([Lifetime(-1, True)])


def test_constant_hazard_recovers_an_exponential_rate():
    rng = Mulberry32(9)
    rate = 0.04
    lifetimes = [Lifetime(-math.log(1 - rng.next()) / rate, True) for _ in range(5000)]
    fit = fit_constant_hazard(kaplan_meier(lifetimes))
    assert fit.rate == pytest.approx(rate, rel=0.08)
    assert fit.r_squared > 0.95
    assert fit.median_lifetime == pytest.approx(math.log(2) / fit.rate)
    assert fit.monthly_churn == pytest.approx(1 - math.exp(-fit.rate))


def test_hazard_fit_needs_events():
    with pytest.raises(ValueError):
        fit_constant_hazard(kaplan_meier([Lifetime(5, False)]))


def test_lifetimes_from_cohorts_counts_churn_and_censoring():
    cohort = Cohort(
        month=None,  # type: ignore[arg-type]
        label="Jan 2026",
        customers=10,
        start_mrr=1000,
        net=(100, 95, 90),
        logo=(100, 80, 70),
    )
    lifetimes = lifetimes_from_cohorts([cohort])
    assert len(lifetimes) == 10
    assert sum(1 for lt in lifetimes if lt.churned and lt.months == 1) == 2
    assert sum(1 for lt in lifetimes if lt.churned and lt.months == 2) == 1
    assert sum(1 for lt in lifetimes if not lt.churned and lt.months == 2) == 7


def test_sample_cohorts_survival_is_plausible():
    cohorts = sample_cohorts()
    lifetimes = lifetimes_from_cohorts(cohorts)
    assert len(lifetimes) == sum(c.customers for c in cohorts)
    curve = kaplan_meier(lifetimes)
    # Eleven months in, the oldest cohort keeps roughly 80% of its logos.
    assert 0.75 < curve.survival_at(11) < 0.9
    fit = fit_constant_hazard(curve)
    assert 0.01 < fit.rate < 0.04


def test_project_churn():
    rows = project_churn(
        1000, 100_000, HazardFit(rate=0.02, r_squared=1), revenue_churn_rate=0.015, months=12
    )
    assert len(rows) == 12
    assert rows[0].customers == pytest.approx(1000 * math.exp(-0.02))
    assert rows[-1].retained_mrr == pytest.approx(100_000 * 0.985**12)
    assert all(r.churned_mrr + r.retained_mrr == pytest.approx(100_000) for r in rows)
    assert [r.churned_customers for r in rows] == sorted(r.churned_customers for r in rows)
    with pytest.raises(ValueError):
        project_churn(10, 10, HazardFit(0.1, 1), revenue_churn_rate=1.2)
