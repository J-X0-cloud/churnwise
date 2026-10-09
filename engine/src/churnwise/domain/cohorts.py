"""Signup cohorts and retention matrices.

A cohort is every customer whose first paid month is the same calendar month. For each month since
signup the matrix holds two percentages:

* **net** — the cohort's MRR as a share of its starting MRR. Expansion counts, so healthy cohorts climb
  back above 100%.
* **logo** — the share of the cohort's customers still paying. It can only fall.

:func:`build_cohorts` derives the matrix from per-customer monthly MRR, which is what the event store
produces. :func:`sample_cohorts` generates the sample workspace's cohorts.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from functools import cache

from churnwise.domain.dates import add_months, month_key, month_year, months_between
from churnwise.domain.formatting import js_round
from churnwise.domain.rng import Mulberry32, lerp
from churnwise.domain.types import CohortMetric

SAMPLE_FIRST_COHORT = date(2025, 10, 1)
SAMPLE_COHORT_COUNT = 12


@dataclass(frozen=True, slots=True)
class Cohort:
    month: date
    label: str
    customers: int
    start_mrr: float
    #: Percent of starting MRR retained, by months since signup (index 0 is the signup month).
    net: tuple[float, ...]
    #: Percent of starting customers still paying, by months since signup.
    logo: tuple[float, ...]

    def series(self, metric: CohortMetric) -> tuple[float, ...]:
        return self.net if metric is CohortMetric.NET else self.logo

    @property
    def age(self) -> int:
        """Number of observed months after the signup month."""
        return len(self.net) - 1


def cohort_average(cohorts: Sequence[Cohort], metric: CohortMetric, months: int) -> list[float | None]:
    """Unweighted mean of each month-since-signup column; ``None`` where no cohort is old enough."""
    averages: list[float | None] = []
    for k in range(months):
        values = [c.series(metric)[k] for c in cohorts if k < len(c.series(metric))]
        averages.append(sum(values) / len(values) if values else None)
    return averages


def weighted_cohort_average(
    cohorts: Sequence[Cohort], metric: CohortMetric, months: int
) -> list[float | None]:
    """Column means weighted by cohort size (starting MRR for net, customers for logo).

    Large cohorts dominate, which is what a revenue forecast wants; the unweighted mean is what the heat
    map's average row shows.
    """
    averages: list[float | None] = []
    for k in range(months):
        num = den = 0.0
        for cohort in cohorts:
            series = cohort.series(metric)
            if k >= len(series):
                continue
            weight = cohort.start_mrr if metric is CohortMetric.NET else cohort.customers
            num += series[k] * weight
            den += weight
        averages.append(num / den if den else None)
    return averages


@dataclass(frozen=True, slots=True)
class CustomerHistory:
    """Month-end MRR for one customer, keyed by the first day of each month."""

    customer_id: str
    monthly_mrr: Mapping[date, float]

    @property
    def first_paid_month(self) -> date | None:
        paying = [m for m, v in self.monthly_mrr.items() if v > 0]
        return min(paying) if paying else None


def build_cohorts(
    histories: Iterable[CustomerHistory],
    as_of: date,
    first_month: date | None = None,
) -> list[Cohort]:
    """Build the cohort retention matrix from per-customer monthly MRR.

    A customer joins the cohort of the first month in which they had positive month-end MRR. Starting MRR
    is the cohort's MRR at the end of that month. Months after ``as_of`` are not observed yet.
    """
    as_of_month = month_key(as_of)
    members: dict[date, list[CustomerHistory]] = defaultdict(list)
    for history in histories:
        signup = history.first_paid_month
        if signup is None or signup > as_of_month:
            continue
        if first_month is not None and signup < month_key(first_month):
            continue
        members[signup].append(history)

    cohorts: list[Cohort] = []
    for signup in sorted(members):
        group = members[signup]
        start_mrr = sum(h.monthly_mrr.get(signup, 0.0) for h in group)
        net: list[float] = []
        logo: list[float] = []
        for k in range(months_between(signup, as_of_month) + 1):
            month = add_months(signup, k)
            mrr = sum(h.monthly_mrr.get(month, 0.0) for h in group)
            paying = sum(1 for h in group if h.monthly_mrr.get(month, 0.0) > 0)
            net.append(100 * mrr / start_mrr if start_mrr else 0.0)
            logo.append(100 * paying / len(group))
        cohorts.append(
            Cohort(
                month=signup,
                label=month_year(signup),
                customers=len(group),
                start_mrr=start_mrr,
                net=tuple(net),
                logo=tuple(logo),
            )
        )
    return cohorts


def generate_sample_cohorts(
    first_cohort: date = SAMPLE_FIRST_COHORT, count: int = SAMPLE_COHORT_COUNT, seed: int = 7
) -> list[Cohort]:
    """Monthly signup cohorts for the sample workspace. Newer cohorts retain slightly better, which is
    the story the sample tells after its onboarding changes."""
    rng = Mulberry32(seed)
    span = max(1, count - 1)
    cohorts: list[Cohort] = []
    for ci in range(count):
        month = add_months(first_cohort, ci)
        customers = js_round(lerp(58, 84, ci / span) + rng.uniform(-6, 6))
        net = [100.0]
        logo = [100.0]
        for k in range(1, count - ci):
            net.append(100 - 7.5 * (1 - math.exp(-k / 1.8)) + 1.45 * k + 0.35 * ci + rng.uniform(-1.2, 1.2))
            level = 100 - 12.5 * (1 - math.exp(-k / 2.2)) - 0.55 * k + 0.25 * ci + rng.uniform(-1, 1)
            logo.append(min(level, logo[-1] - 0.2))
        cohorts.append(
            Cohort(
                month=month,
                label=month_year(month),
                customers=customers,
                start_mrr=customers * lerp(292, 334, ci / span),
                net=tuple(net),
                logo=tuple(logo),
            )
        )
    return cohorts


@cache
def sample_cohorts() -> tuple[Cohort, ...]:
    return tuple(generate_sample_cohorts())
