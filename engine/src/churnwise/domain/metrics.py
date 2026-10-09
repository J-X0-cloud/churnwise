"""Dashboard metrics: KPI tiles with deltas and sparklines, the headline MRR line, retention series, plan
mix and per-account trends. Built on :mod:`churnwise.domain.revenue` and the daily model.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Literal

from churnwise import fixtures
from churnwise.domain.dates import auto_month_label, day_label, long_date
from churnwise.domain.formatting import MINUS, money, num, pct, signed_money, to_fixed, whole_dollars
from churnwise.domain.recovery import RecoveryAnalytics
from churnwise.domain.revenue import (
    GROSS_MARGIN,
    RangeStats,
    grr_at,
    nrr_at,
    range_definitions,
    range_stats,
    trailing_churn_rate,
)
from churnwise.domain.rng import Mulberry32, lerp
from churnwise.domain.simulation import DailyRevenue, RevenueModel
from churnwise.domain.types import RangeKey, Tone

DeltaTone = Literal["good", "bad", "neutral"]
Arrow = Literal["up", "down"]

SPARK_POINTS = 24
#: Label spacing for the headline chart so labels never collide.
MRR_LABEL_EVERY: dict[RangeKey, int] = {RangeKey.D30: 5, RangeKey.D90: 14, RangeKey.M12: 1, RangeKey.M24: 1}


@dataclass(frozen=True, slots=True)
class Delta:
    text: str
    tone: DeltaTone
    arrow: Arrow | None = None


@dataclass(frozen=True, slots=True)
class Kpi:
    label: str
    value: str
    delta: Delta
    #: Rendered small after the value, e.g. "/mo".
    unit: str | None = None
    hint: str | None = None
    spark: tuple[float, ...] | None = None
    spark_tone: Tone | None = None


@dataclass(frozen=True, slots=True)
class ChartPoint:
    #: Empty string hides the x label for this point.
    label: str
    value: float
    #: Tooltip title.
    tip: str


# ------------------------------------------------------------------ deltas


def delta(
    current: float, prior: float | None, *, good_up: bool = True, unit: Literal["%", "pts"] = "%"
) -> Delta | None:
    """Change badge between two values: relative (``+12.3%``) or in percentage points (``-0.4 pts``).

    Returns ``None`` when there is nothing to compare against.
    """
    if prior is None or prior == 0:
        return None
    change = current - prior if unit == "pts" else ((current - prior) / abs(prior)) * 100
    rising = change >= 0
    sign = "+" if rising else MINUS
    suffix = " pts" if unit == "pts" else "%"
    return Delta(
        text=f"{sign}{to_fixed(abs(change), 1)}{suffix}",
        arrow="up" if rising else "down",
        tone="good" if rising == good_up else "bad",
    )


def note(text: str) -> Delta:
    return Delta(text=text, tone="neutral")


def _or_note(value: Delta | None, fallback: str) -> Delta:
    return value if value is not None else note(fallback)


def _required(value: Delta | None) -> Delta:
    if value is None:
        raise ValueError("expected a comparable prior value")
    return value


# ------------------------------------------------------------------ series helpers


def sampled(
    model: RevenueModel, start: int, pick: Callable[[DailyRevenue, int], float], points: int = SPARK_POINTS
) -> tuple[float, ...]:
    """Sample a daily value across ``[start, end of model)`` at about ``points`` points, for sparklines."""
    step = max(1, (model.day_count - start) // points)
    return tuple(pick(model[i], i) for i in range(start, model.day_count, step))


def trailing_recovered(model: RevenueModel, index: int, days: int = 30) -> float:
    return model.sum_recovered(index - days, index + 1)


def mrr_line(model: RevenueModel, stats: RangeStats) -> list[ChartPoint]:
    """Headline MRR line: month labels at month starts for 12M/24M, day labels otherwise."""
    monthly = range_definitions(model)[stats.range].bucket == "month"
    points: list[ChartPoint] = []
    for point in stats.line:
        if monthly:
            label = auto_month_label(point.day) if point.day.day <= 7 else ""
        else:
            label = day_label(point.day)
        points.append(ChartPoint(label=label, value=point.value, tip=long_date(point.day)))
    return points


# ------------------------------------------------------------------ KPI tiles


def overview_kpis(model: RevenueModel, key: RangeKey) -> list[Kpi]:
    st = range_stats(model, key)
    s = st.start
    comparison = range_definitions(model)[key].comparison_note
    margin = to_fixed(GROSS_MARGIN * 100, 0)

    return [
        Kpi(
            label="MRR",
            value=money(st.mrr),
            hint="Monthly recurring revenue, normalized from every active subscription",
            delta=_or_note(delta(st.mrr, st.mrr_start), comparison),
            spark=sampled(model, s, lambda r, _: r.mrr),
        ),
        Kpi(
            label="Net new MRR",
            value=signed_money(st.net_new),
            hint="New + expansion + reactivation − contraction − churn",
            delta=_or_note(delta(st.net_new, st.net_new_prior), comparison),
            spark=sampled(model, s, lambda r, i: r.mrr - model[max(0, i - 30)].mrr),
            spark_tone="mint",
        ),
        Kpi(
            label="Net revenue retention",
            value=pct(st.nrr),
            hint="Trailing 12 months, existing customers only",
            delta=_or_note(delta(st.nrr, st.nrr_start, unit="pts"), comparison),
            spark=sampled(model, s, lambda _, i: nrr_at(model, i)),
            spark_tone="blue",
        ),
        Kpi(
            label="Revenue churn",
            value=pct(st.churn_rate, 2),
            unit="/mo",
            hint="Churned + contracted MRR as a share of MRR",
            delta=_or_note(
                delta(st.churn_rate, st.churn_rate_prior, good_up=False, unit="pts"), "avg. per month"
            ),
            spark=sampled(model, s, lambda _, i: trailing_churn_rate(model, i)),
            spark_tone="red",
        ),
        Kpi(
            label="Customers",
            value=num(st.customers),
            delta=_or_note(delta(st.customers, st.customers_start), comparison),
            spark=sampled(model, s, lambda r, _: r.customers),
        ),
        Kpi(
            label="ARPA",
            value=whole_dollars(st.arpa),
            hint="Average revenue per account",
            delta=_or_note(delta(st.arpa, st.arpa_start), comparison),
            spark=sampled(model, s, lambda r, _: r.arpa),
        ),
        Kpi(
            label="Customer LTV",
            value=money(st.ltv),
            hint=f"ARPA × {margin}% gross margin ÷ logo churn",
            delta=_or_note(delta(st.ltv, st.ltv_start), comparison),
            spark=sampled(model, s, lambda r, _: r.arpa),
            spark_tone="blue",
        ),
        Kpi(
            label="Recovered revenue",
            value=money(st.recovered),
            hint="Failed payments won back by retries, emails and card updates",
            delta=_or_note(
                delta(st.recovered, st.recovered_prior), f"{to_fixed(st.recovery_rate, 0)}% of failed"
            ),
            spark=sampled(model, s, lambda _, i: trailing_recovered(model, i)),
            spark_tone="mint",
        ),
    ]


@dataclass(frozen=True, slots=True)
class RetentionSeries:
    labels: tuple[str, ...]
    nrr: tuple[float, ...]
    grr: tuple[float, ...]


def retention_series(model: RevenueModel, months: int = 12) -> RetentionSeries:
    """Trailing-12-month NRR and GRR at each of the last ``months`` month ends."""
    windows = model.months[-months:]
    return RetentionSeries(
        labels=tuple(auto_month_label(w.month) for w in windows),
        nrr=tuple(nrr_at(model, w.end - 1) for w in windows),
        grr=tuple(grr_at(model, w.end - 1) for w in windows),
    )


def retention_kpis(model: RevenueModel) -> list[Kpi]:
    series = retention_series(model)
    last = model.last
    year_ago = last - 365
    return [
        Kpi(
            label="Net revenue retention",
            value=pct(nrr_at(model, last)),
            delta=_required(delta(nrr_at(model, last), nrr_at(model, year_ago), unit="pts")),
            spark=series.nrr,
            spark_tone="blue",
        ),
        Kpi(
            label="Gross revenue retention",
            value=pct(grr_at(model, last)),
            delta=_required(delta(grr_at(model, last), grr_at(model, year_ago), unit="pts")),
            spark=series.grr,
            spark_tone="red",
        ),
        Kpi(
            label="Logo churn",
            value="1.74%",
            unit="/mo",
            delta=Delta(text=f"{MINUS}0.21 pts", arrow="down", tone="good"),
        ),
        Kpi(
            label="Median customer lifetime",
            value="38 mo",
            delta=Delta(text="+4 mo", arrow="up", tone="good"),
        ),
    ]


def customer_kpis(model: RevenueModel) -> list[Kpi]:
    last = model.last
    now = model[last].customers
    past_due = sum(p.amount for p in fixtures.open_failed_payments())
    recent = model.rows[-90:]
    return [
        Kpi(
            label="Paying customers",
            value=num(now),
            delta=_required(delta(now, model[last - 30].customers)),
            spark=tuple(r.customers for r in recent[::3]),
        ),
        Kpi(label="At risk", value="41", delta=Delta(text="+6", arrow="up", tone="bad")),
        Kpi(
            label="Past due",
            value=str(len(fixtures.open_failed_payments())),
            delta=note(f"{money(past_due)} MRR"),
        ),
        Kpi(label="Expanded this month", value="58", delta=Delta(text="+9", arrow="up", tone="good")),
    ]


def recovery_kpis(recovery: RecoveryAnalytics) -> list[Kpi]:
    funnel = recovery.funnel()
    months = recovery.by_month(12)
    open_payments = fixtures.open_failed_payments()
    in_recovery = sum(p.amount for p in open_payments)
    return [
        Kpi(
            label="Recovered (12 mo)",
            value=money(funnel.recovered),
            delta=Delta(text="+14.2%", arrow="up", tone="good"),
            spark=tuple(m.recovered for m in months),
            spark_tone="mint",
        ),
        Kpi(
            label="Recovery rate",
            value=pct(funnel.rate),
            delta=Delta(text="+3.8 pts", arrow="up", tone="good"),
            spark=tuple((m.recovered / m.failed) * 100 for m in months),
            spark_tone="brand",
        ),
        Kpi(
            label="In recovery now",
            value=money(in_recovery),
            delta=note(f"{len(open_payments)} invoices"),
        ),
        Kpi(
            label="Involuntary churn",
            value=pct(recovery.involuntary_churn_rate(), 2),
            unit="/mo",
            delta=Delta(text=f"{MINUS}0.2 pts", arrow="down", tone="good"),
        ),
    ]


# ------------------------------------------------------------------ plans & accounts


@dataclass(frozen=True, slots=True)
class PlanRow:
    name: str
    price: str
    tone: Tone
    mrr: float
    #: Percent of total MRR.
    share: float
    customers: float
    #: Monthly logo churn, in percent.
    churn: float


def plan_breakdown(model: RevenueModel, day_index: int | None = None) -> list[PlanRow]:
    """MRR, customers and churn per plan on a given day. Plan shares drift linearly across the model as
    the customer base moves up-market."""
    index = model.last if day_index is None else day_index
    t = index / (model.day_count - 1)
    row = model[index]
    return [
        PlanRow(
            name=p.name,
            price=p.price,
            tone=p.tone,
            mrr=row.mrr * lerp(*p.mrr_share, t),
            share=lerp(*p.mrr_share, t) * 100,
            customers=row.customers * lerp(*p.customer_share, t),
            churn=p.churn * (1.08 - 0.12 * t),
        )
        for p in fixtures.plans()
    ]


@dataclass(frozen=True, slots=True)
class AccountRow:
    name: str
    plan: str
    mrr: float
    trend: Literal["up", "flat", "down"]
    status: fixtures.CustomerStatus
    health: int
    since: str
    owner: str
    #: Twelve months of MRR, ending at the current MRR.
    history: tuple[float, ...] = ()


def account_trend(account: fixtures.Account, seed: int, months: int = 12) -> tuple[float, ...]:
    """Twelve months of MRR for an account, ending at its current MRR, shaped by its trend."""
    rng = Mulberry32(seed + 1)
    values: list[float] = []
    span = max(1, months - 1)
    for k in range(months):
        t = k / span
        if account.trend == "up":
            shape = lerp(0.62, 1, t)
        elif account.trend == "down":
            shape = lerp(1.45, 1, t)
        else:
            shape = 1 + 0.02 * math.sin(k)
        values.append(account.mrr * shape * (1 + rng.uniform(-0.03, 0.03)))
    values[-1] = account.mrr
    return tuple(values)


def account_rows(accounts: Sequence[fixtures.Account] | None = None) -> list[AccountRow]:
    """Accounts in display order, each with its twelve-month trend."""
    rows = fixtures.accounts() if accounts is None else accounts
    return [
        AccountRow(
            name=a.name,
            plan=a.plan,
            mrr=a.mrr,
            trend=a.trend,
            status=a.status,
            health=a.health,
            since=a.since,
            owner=a.owner,
            history=account_trend(a, index),
        )
        for index, a in enumerate(rows)
    ]
