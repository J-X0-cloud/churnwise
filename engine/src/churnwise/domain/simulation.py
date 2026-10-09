"""Deterministic daily revenue model for the sample workspace ("Quillstack", a fictional B2B SaaS company).

Every tile, chart, table and forecast in the demo is computed from these rows, so they always agree with
each other. The generator is seeded, so the model is identical on every run and on every machine.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from functools import cache
from itertools import accumulate, pairwise

from churnwise.domain.dates import add_months, day_of_year, is_weekday
from churnwise.domain.rng import Mulberry32, lerp
from churnwise.domain.types import MOVEMENT_ORDER, Movement, MovementTotals

FIRST_DAY = date(2024, 10, 1)
LAST_DAY = date(2026, 9, 24)
OPENING_MRR = 318_400.0
SEED = 20260924
DAYS_PER_MONTH = 30.4


@dataclass(frozen=True, slots=True)
class WorkspaceInfo:
    name: str
    slug: str
    currency: str
    sources: tuple[str, ...]

    @property
    def sources_label(self) -> str:
        return " · ".join(self.sources)


SAMPLE_WORKSPACE = WorkspaceInfo(
    name="Quillstack", slug="quillstack", currency="USD", sources=("Stripe", "Chargebee", "HubSpot")
)

#: Monthly MRR moved by each flow at the start and the end of the model; interpolated in between.
MONTHLY_FLOW: dict[Movement, tuple[float, float]] = {
    Movement.NEW: (14200, 21800),
    Movement.EXPANSION: (11800, 17600),
    Movement.REACTIVATION: (1250, 1900),
    Movement.CONTRACTION: (3400, 4300),
    Movement.CHURN: (6900, 7900),
}


@dataclass(frozen=True, slots=True)
class DailyRevenue:
    """One day of the workspace's revenue model. ``flows`` are the MRR amounts moved that day."""

    day: date
    flows: MovementTotals
    #: MRR at the end of the day.
    mrr: float
    arpa: float
    customers: float
    #: Value of charges that failed that day, and how much of it was eventually recovered.
    failed: float
    recovered: float


@dataclass(frozen=True, slots=True)
class MonthWindow:
    """A calendar month of the model as day indices ``[start, end)`` into the daily series."""

    month: date
    start: int
    end: int

    @property
    def days(self) -> int:
        return self.end - self.start


def simulate(
    first_day: date = FIRST_DAY,
    last_day: date = LAST_DAY,
    opening_mrr: float = OPENING_MRR,
    seed: int = SEED,
) -> list[DailyRevenue]:
    """Generate the daily rows. Sales close on weekdays and follow a mild yearly season; churn clusters in
    the first days of each month, when most renewals fall."""
    if last_day <= first_day:
        raise ValueError("the model needs at least two days")
    rng = Mulberry32(seed)
    count = (last_day - first_day).days + 1
    rows: list[DailyRevenue] = []
    mrr = opening_mrr

    for i in range(count):
        day = first_day + timedelta(days=i)
        t = i / (count - 1)
        weekday = 1.18 if is_weekday(day) else 0.55
        season = 1 + 0.08 * math.sin((day_of_year(day) / 365) * 2 * math.pi + 1.2)

        flows: dict[Movement, float] = {}
        for movement, (start, end) in MONTHLY_FLOW.items():
            value = (lerp(start, end, t) / DAYS_PER_MONTH) * (1 + rng.uniform(-0.45, 0.45))
            if movement in (Movement.NEW, Movement.EXPANSION):
                value *= weekday * season
            if movement is Movement.CHURN and day.day <= 3:
                value *= 2.1
            flows[movement] = value
        totals = MovementTotals.from_mapping(flows)
        # Same operation order as the daily identity is written everywhere else, so runs are bit-identical.
        mrr += (
            flows[Movement.NEW]
            + flows[Movement.EXPANSION]
            + flows[Movement.REACTIVATION]
            - flows[Movement.CONTRACTION]
            - flows[Movement.CHURN]
        )

        arpa = lerp(281, 318, t)
        failed = ((mrr * 0.031) / DAYS_PER_MONTH) * (1 + rng.uniform(-0.3, 0.3))
        recovery_rate = lerp(0.61, 0.71, t) + rng.uniform(-0.04, 0.04)
        rows.append(
            DailyRevenue(
                day=day,
                flows=totals,
                mrr=mrr,
                arpa=arpa,
                customers=mrr / arpa,
                failed=failed,
                recovered=failed * recovery_rate,
            )
        )
    return rows


def _prefix(values: Sequence[float]) -> list[float]:
    return [0.0, *accumulate(values)]


class RevenueModel:
    """A daily revenue series with O(1) range sums.

    Ranges are half-open day-index intervals ``[start, end)`` and are clamped to the series, so callers can
    ask for trailing windows near the start of the history without special cases.
    """

    def __init__(self, rows: Sequence[DailyRevenue]) -> None:
        if len(rows) < 2:
            raise ValueError("a revenue model needs at least two days")
        days = [r.day for r in rows]
        if any((b - a).days != 1 for a, b in pairwise(days)):
            raise ValueError("daily rows must be consecutive days")
        self.rows: tuple[DailyRevenue, ...] = tuple(rows)
        self.first_day = days[0]
        self.last_day = days[-1]
        self._flows = {m: _prefix([r.flows[m] for r in rows]) for m in MOVEMENT_ORDER}
        self._failed = _prefix([r.failed for r in rows])
        self._recovered = _prefix([r.recovered for r in rows])
        self._mrr = _prefix([r.mrr for r in rows])
        self.months: tuple[MonthWindow, ...] = self._month_windows()

    # ------------------------------------------------------------------ indexing

    @property
    def day_count(self) -> int:
        return len(self.rows)

    @property
    def last(self) -> int:
        """Index of the last day."""
        return len(self.rows) - 1

    def __getitem__(self, index: int) -> DailyRevenue:
        return self.rows[index]

    def day_index(self, day: date) -> int:
        return (day - self.first_day).days

    def _clamp(self, start: int, end: int) -> tuple[int, int]:
        start = max(0, start)
        end = min(end, self.day_count)
        return start, max(start, end)

    def _window_sum(self, prefix: list[float], start: int, end: int) -> float:
        start, end = self._clamp(start, end)
        return prefix[end] - prefix[start]

    # ------------------------------------------------------------------ sums

    def sum_flow(self, movement: Movement, start: int, end: int) -> float:
        return self._window_sum(self._flows[movement], start, end)

    def flow_totals(self, start: int, end: int) -> MovementTotals:
        return MovementTotals.from_mapping({m: self.sum_flow(m, start, end) for m in MOVEMENT_ORDER})

    def sum_failed(self, start: int, end: int) -> float:
        return self._window_sum(self._failed, start, end)

    def sum_recovered(self, start: int, end: int) -> float:
        return self._window_sum(self._recovered, start, end)

    def average_mrr(self, start: int, end: int) -> float:
        start, end = self._clamp(start, end)
        if end == start:
            raise ValueError("cannot average an empty window")
        return (self._mrr[end] - self._mrr[start]) / (end - start)

    # ------------------------------------------------------------------ calendar

    def _month_windows(self) -> tuple[MonthWindow, ...]:
        windows: list[MonthWindow] = []
        month = self.first_day
        while month <= self.last_day:
            following = add_months(month, 1)
            windows.append(
                MonthWindow(
                    month=month,
                    start=self.day_index(month),
                    end=min(self.day_index(following), self.day_count),
                )
            )
            month = following
        return tuple(windows)

    def month_end_mrr(self, window: MonthWindow) -> float:
        """MRR on the last day of a month window."""
        return self.rows[window.end - 1].mrr


@cache
def sample_model() -> RevenueModel:
    """The sample workspace's model. Built once per process; it is immutable."""
    return RevenueModel(simulate())
