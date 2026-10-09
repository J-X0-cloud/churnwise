"""Customer survival curves and churn forecasting.

* :func:`kaplan_meier` estimates the share of customers still paying after ``t`` months from individual
  lifetimes, handling customers who are still active (right-censored). Confidence bands use Greenwood's
  variance on the log-log scale, which keeps them inside [0, 1].
* :func:`lifetimes_from_cohorts` turns a logo-retention cohort matrix into individual lifetimes, so the
  same estimator runs on cohort data.
* :func:`fit_constant_hazard` fits an exponential survival model, ``S(t) = exp(-lambda * t)``, by least
  squares through the origin on ``-log S(t)``; it gives a single monthly churn rate to project forward.
* :func:`project_churn` turns a hazard into expected customers, churned logos and churned MRR by month.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from statistics import NormalDist

from churnwise.domain.cohorts import Cohort
from churnwise.domain.formatting import js_round


@dataclass(frozen=True, slots=True)
class Lifetime:
    #: Months from first payment to churn (observed) or to today (censored).
    months: float
    churned: bool


@dataclass(frozen=True, slots=True)
class SurvivalPoint:
    time: float
    at_risk: int
    events: int
    censored: int
    survival: float
    low: float
    high: float


@dataclass(frozen=True, slots=True)
class SurvivalCurve:
    points: tuple[SurvivalPoint, ...]
    subjects: int
    events: int

    def survival_at(self, t: float) -> float:
        """S(t): the estimate from the last event time at or before ``t`` (a step function)."""
        value = 1.0
        for point in self.points:
            if point.time > t:
                break
            value = point.survival
        return value

    def median(self) -> float | None:
        """First time at which survival drops to 50% or below; ``None`` if it never does."""
        for point in self.points:
            if point.survival <= 0.5:
                return point.time
        return None

    def restricted_mean(self, horizon: float) -> float:
        """Area under the curve up to ``horizon``: expected months of paying life within the horizon."""
        area = 0.0
        previous_time, previous_survival = 0.0, 1.0
        for point in self.points:
            if point.time >= horizon:
                break
            area += previous_survival * (point.time - previous_time)
            previous_time, previous_survival = point.time, point.survival
        return area + previous_survival * (horizon - previous_time)


def kaplan_meier(lifetimes: Sequence[Lifetime], confidence: float = 0.95) -> SurvivalCurve:
    """Product-limit estimator. Censored lifetimes at the same time as events count as still at risk."""
    if not lifetimes:
        raise ValueError("need at least one lifetime")
    if any(lt.months < 0 for lt in lifetimes):
        raise ValueError("lifetimes cannot be negative")
    z = NormalDist().inv_cdf(0.5 + confidence / 2)
    events = Counter(lt.months for lt in lifetimes if lt.churned)
    censored = Counter(lt.months for lt in lifetimes if not lt.churned)
    at_risk = len(lifetimes)
    survival = 1.0
    greenwood = 0.0
    points: list[SurvivalPoint] = []

    for t in sorted(set(events) | set(censored)):
        d = events.get(t, 0)
        c = censored.get(t, 0)
        if d:
            survival *= 1 - d / at_risk
            if at_risk > d:
                greenwood += d / (at_risk * (at_risk - d))
            low, high = _loglog_interval(survival, greenwood, z)
            points.append(SurvivalPoint(t, at_risk, d, c, survival, low, high))
        at_risk -= d + c

    return SurvivalCurve(points=tuple(points), subjects=len(lifetimes), events=sum(events.values()))


def _loglog_interval(survival: float, greenwood: float, z: float) -> tuple[float, float]:
    if survival <= 0 or survival >= 1 or greenwood == 0:
        return survival, survival
    log_s = math.log(survival)
    se = math.sqrt(greenwood) / abs(log_s)
    low = survival ** math.exp(z * se)
    high = survival ** math.exp(-z * se)
    return low, high


def lifetimes_from_cohorts(cohorts: Sequence[Cohort]) -> list[Lifetime]:
    """Expand logo retention into individual lifetimes.

    For a cohort of ``n`` customers with ``a_k`` still paying at month ``k``, ``a_{k-1} - a_k`` customers
    churned at month ``k`` and the ``a_m`` still paying at its latest observed month ``m`` are censored there.
    """
    lifetimes: list[Lifetime] = []
    for cohort in cohorts:
        alive: list[int] = []
        for share in cohort.logo:
            count = js_round(cohort.customers * share / 100)
            alive.append(min(count, alive[-1]) if alive else count)
        for k in range(1, len(alive)):
            lifetimes.extend(Lifetime(k, True) for _ in range(alive[k - 1] - alive[k]))
        lifetimes.extend(Lifetime(len(alive) - 1, False) for _ in range(alive[-1]))
    return lifetimes


@dataclass(frozen=True, slots=True)
class HazardFit:
    #: Constant monthly hazard (lambda).
    rate: float
    #: Coefficient of determination of the fit on -log S(t).
    r_squared: float

    @property
    def monthly_churn(self) -> float:
        """Probability of churning in a given month: 1 - exp(-lambda)."""
        return 1 - math.exp(-self.rate)

    @property
    def median_lifetime(self) -> float:
        return math.log(2) / self.rate if self.rate > 0 else math.inf

    @property
    def expected_lifetime(self) -> float:
        return 1 / self.rate if self.rate > 0 else math.inf

    def survival(self, t: float) -> float:
        return math.exp(-self.rate * t)


def fit_constant_hazard(curve: SurvivalCurve) -> HazardFit:
    """Least squares through the origin on the cumulative hazard ``H(t) = -log S(t)``."""
    pairs = [(p.time, -math.log(p.survival)) for p in curve.points if 0 < p.survival < 1 and p.time > 0]
    if not pairs:
        raise ValueError("the curve has no usable points to fit")
    sxx = sum(t * t for t, _ in pairs)
    rate = sum(t * h for t, h in pairs) / sxx
    mean_h = sum(h for _, h in pairs) / len(pairs)
    ss_tot = sum((h - mean_h) ** 2 for _, h in pairs)
    ss_res = sum((h - rate * t) ** 2 for t, h in pairs)
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return HazardFit(rate=rate, r_squared=r_squared)


@dataclass(frozen=True, slots=True)
class ChurnProjection:
    month: int
    customers: float
    churned_customers: float
    churned_mrr: float
    retained_mrr: float


def project_churn(
    customers: float,
    mrr: float,
    logo_hazard: HazardFit,
    revenue_churn_rate: float,
    months: int = 12,
) -> list[ChurnProjection]:
    """Expected churn of today's customer base, ignoring new sales and expansion.

    Logos decay with the fitted hazard. MRR decays at ``revenue_churn_rate`` (monthly, as a fraction),
    which is usually lower than logo churn because small accounts churn more often.
    """
    if not 0 <= revenue_churn_rate < 1:
        raise ValueError("revenue churn rate must be a fraction in [0, 1)")
    out: list[ChurnProjection] = []
    for k in range(1, months + 1):
        remaining = customers * logo_hazard.survival(k)
        retained = mrr * (1 - revenue_churn_rate) ** k
        out.append(
            ChurnProjection(
                month=k,
                customers=remaining,
                churned_customers=customers - remaining,
                churned_mrr=mrr - retained,
                retained_mrr=retained,
            )
        )
    return out
