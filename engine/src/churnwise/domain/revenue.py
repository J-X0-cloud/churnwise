"""Revenue math on the daily model: net and gross revenue retention, churn rates, date ranges, MRR
movement buckets and the headline numbers for each range.

Every function takes the model explicitly, so the same code serves the sample workspace, tests with
synthetic series, and any future per-workspace daily rollup.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from churnwise.domain.dates import add_months, day_label, long_date, month_label, start_of_month
from churnwise.domain.simulation import DAYS_PER_MONTH, RevenueModel
from churnwise.domain.types import Bucket, Movement, MovementTotals, RangeKey

#: Assumed gross margin used in LTV.
GROSS_MARGIN = 0.82
#: Logo churn runs ahead of revenue churn because small accounts churn more often.
LOGO_TO_REVENUE_CHURN = 1.22
#: Share of a trailing year's expansion that comes from the base cohort rather than from customers
#: acquired inside the window.
BASE_COHORT_EXPANSION_SHARE = 0.74
#: Share of a trailing year's lost MRR that belongs to the base cohort.
BASE_COHORT_LOSS_SHARE = 0.42
YEAR_DAYS = 365


# ------------------------------------------------------------------ retention


def nrr_at(model: RevenueModel, index: int) -> float:
    """Trailing-12-month net revenue retention at day ``index``, in percent.

    What last year's customers pay today as a share of what they paid then. Part of the window's
    expansion comes from customers acquired inside it, so the movement is scaled to the base cohort.
    """
    start = max(0, index - YEAR_DAYS)
    base = model[start].mrr
    change = (
        model.sum_flow(Movement.EXPANSION, start, index)
        + model.sum_flow(Movement.REACTIVATION, start, index)
        - model.sum_flow(Movement.CONTRACTION, start, index)
        - model.sum_flow(Movement.CHURN, start, index)
    )
    return (100 * (base + change * BASE_COHORT_EXPANSION_SHARE)) / base


def grr_at(model: RevenueModel, index: int) -> float:
    """Trailing-12-month gross revenue retention. It ignores expansion, so it can never exceed 100%."""
    start = max(0, index - YEAR_DAYS)
    base = model[start].mrr
    lost = model.sum_flow(Movement.CONTRACTION, start, index) + model.sum_flow(Movement.CHURN, start, index)
    return (100 * (base - lost * BASE_COHORT_LOSS_SHARE)) / base


def trailing_churn_rate(model: RevenueModel, index: int) -> float:
    """Churned + contracted MRR over the trailing 30 days as a share of MRR on day ``index``, in percent."""
    lost = model.sum_flow(Movement.CHURN, index - 30, index + 1) + model.sum_flow(
        Movement.CONTRACTION, index - 30, index + 1
    )
    return (lost / model[index].mrr) * 100


def ltv(arpa: float, monthly_logo_churn: float, gross_margin: float = GROSS_MARGIN) -> float:
    """Customer lifetime value: ARPA x gross margin / monthly logo churn (as a fraction)."""
    if monthly_logo_churn <= 0:
        raise ValueError("logo churn must be positive to compute a finite LTV")
    return (arpa * gross_margin) / monthly_logo_churn


# ------------------------------------------------------------------ ranges


@dataclass(frozen=True, slots=True)
class RangeDefinition:
    key: RangeKey
    label: str
    short: str
    bucket: Bucket
    comparison_note: str


def range_definitions(model: RevenueModel) -> dict[RangeKey, RangeDefinition]:
    """The four dashboard ranges. Long ranges compare against the first day of their window."""
    twelve_months_start = start_of_month(add_months(model.last_day, -11))
    return {
        RangeKey.D30: RangeDefinition(RangeKey.D30, "Last 30 days", "30D", "day", "vs 30 days ago"),
        RangeKey.D90: RangeDefinition(RangeKey.D90, "Last 90 days", "90D", "week", "vs 90 days ago"),
        RangeKey.M12: RangeDefinition(
            RangeKey.M12, "Last 12 months", "12M", "month", f"vs {long_date(twelve_months_start)}"
        ),
        RangeKey.M24: RangeDefinition(
            RangeKey.M24, "Last 24 months", "24M", "month", f"vs {long_date(model.first_day)}"
        ),
    }


def range_start(model: RevenueModel, key: RangeKey) -> int:
    """First day index of a range."""
    match key:
        case RangeKey.D30:
            return model.day_count - 30
        case RangeKey.D90:
            return model.day_count - 91
        case RangeKey.M12:
            return model.day_index(start_of_month(add_months(model.last_day, -11)))
        case RangeKey.M24:
            return 0
    raise ValueError(f"unknown range {key!r}")


@dataclass(frozen=True, slots=True)
class MovementBucket:
    """Movement totals for one chart bucket: day indices ``[start, end)``."""

    label: str
    start: int
    end: int
    totals: MovementTotals
    ending_mrr: float

    @property
    def net(self) -> float:
        return self.totals.net


def movement_buckets(model: RevenueModel, key: RangeKey) -> list[MovementBucket]:
    """Movement totals per chart bucket: days for 30D, weeks for 90D, calendar months otherwise."""
    start = range_start(model, key)
    bucket = range_definitions(model)[key].bucket
    windows: list[tuple[str, int, int]] = []

    if bucket == "day":
        windows = [(day_label(model[i].day), i, i + 1) for i in range(start, model.day_count)]
    elif bucket == "week":
        windows = [
            (day_label(model[i].day), i, min(i + 7, model.day_count))
            for i in range(start, model.day_count, 7)
        ]
    else:
        for window in model.months:
            if window.start < start:
                continue
            with_year = window.month.month == 1 or (key is RangeKey.M24 and window.start == 0)
            windows.append((month_label(window.month, with_year), window.start, window.end))

    return [
        MovementBucket(
            label=label,
            start=lo,
            end=hi,
            totals=model.flow_totals(lo, hi),
            ending_mrr=model[hi - 1].mrr,
        )
        for label, lo, hi in windows
    ]


@dataclass(frozen=True, slots=True)
class LinePoint:
    day: date
    value: float


@dataclass(frozen=True, slots=True)
class RangeStats:
    """Headline numbers for a range, each paired with its value at the start of the range or in the
    prior period of the same length (``None`` when the history does not reach that far back)."""

    range: RangeKey
    label: str
    start: int
    mrr: float
    mrr_start: float
    net_new: float
    net_new_prior: float | None
    churn_rate: float
    churn_rate_prior: float | None
    nrr: float
    nrr_start: float
    customers: float
    customers_start: float
    arpa: float
    arpa_start: float
    ltv: float
    ltv_start: float
    recovered: float
    recovered_prior: float | None
    recovery_rate: float
    failed: float
    #: MRR sampled for the headline line chart.
    line: tuple[LinePoint, ...]


def _monthly_revenue_churn(model: RevenueModel, start: int, end: int) -> float:
    """Average monthly revenue churn (churn + contraction) over a window, in percent of average MRR."""
    lost = model.sum_flow(Movement.CHURN, start, end) + model.sum_flow(Movement.CONTRACTION, start, end)
    per_month = DAYS_PER_MONTH / (end - start)
    return (lost / model.average_mrr(start, end)) * per_month * 100


def range_stats(model: RevenueModel, key: RangeKey) -> RangeStats:
    s = range_start(model, key)
    n = model.day_count
    last = model.last
    prior_start = s - (n - s)
    has_prior = prior_start >= 0

    churn_rate = _monthly_revenue_churn(model, s, n)
    churn_rate_prior = _monthly_revenue_churn(model, prior_start, s) if has_prior else None
    logo_churn = (churn_rate * LOGO_TO_REVENUE_CHURN) / 100
    logo_churn_prior = (
        (churn_rate_prior if churn_rate_prior is not None else churn_rate * 1.06) * LOGO_TO_REVENUE_CHURN
    ) / 100

    step = 7 if range_definitions(model)[key].bucket == "month" else 1
    indices = list(range(s, n, step))
    if indices[-1] != last:
        indices.append(last)

    recovered = model.sum_recovered(s, n)
    failed = model.sum_failed(s, n)
    return RangeStats(
        range=key,
        label=range_definitions(model)[key].label,
        start=s,
        mrr=model[last].mrr,
        mrr_start=model[s].mrr,
        net_new=model[last].mrr - model[s].mrr,
        net_new_prior=model[s].mrr - model[prior_start].mrr if has_prior else None,
        churn_rate=churn_rate,
        churn_rate_prior=churn_rate_prior,
        nrr=nrr_at(model, last),
        nrr_start=nrr_at(model, max(s, YEAR_DAYS)),
        customers=model[last].customers,
        customers_start=model[s].customers,
        arpa=model[last].arpa,
        arpa_start=model[s].arpa,
        ltv=ltv(model[last].arpa, logo_churn),
        ltv_start=ltv(model[s].arpa, logo_churn_prior),
        recovered=recovered,
        recovered_prior=model.sum_recovered(prior_start, s) if has_prior else None,
        recovery_rate=(recovered / failed) * 100,
        failed=failed,
        line=tuple(LinePoint(model[i].day, model[i].mrr) for i in indices),
    )
