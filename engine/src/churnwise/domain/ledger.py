"""Analytics over the MRR movement ledger.

The webhook pipeline records one movement per change in a customer's MRR (see
:mod:`churnwise.domain.movements`). Replaying that ledger answers every revenue question without a daily
rollup: MRR on any date, the monthly MRR bridge, net and gross revenue retention between two dates, and the
cohort retention matrix.
"""

from __future__ import annotations

from bisect import bisect_right
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from churnwise.domain.cohorts import Cohort, CustomerHistory, build_cohorts
from churnwise.domain.dates import add_months, iter_months, month_key
from churnwise.domain.types import Movement, MovementTotals


@dataclass(frozen=True, slots=True)
class MovementRecord:
    customer_id: str
    movement: Movement
    amount: float
    mrr_before: float
    mrr_after: float
    occurred_at: datetime


def _utc(moment: datetime) -> datetime:
    return moment.replace(tzinfo=UTC) if moment.tzinfo is None else moment.astimezone(UTC)


def end_of_day(day: date) -> datetime:
    """The last instant of ``day`` in UTC; movements at or before it count for that day."""
    return datetime.combine(day, time.max, tzinfo=UTC)


def end_of_month(month: date) -> date:
    return add_months(month_key(month), 1) - timedelta(days=1)


class Ledger:
    """An in-memory, time-ordered view of a workspace's MRR movements."""

    def __init__(self, records: Iterable[MovementRecord]) -> None:
        ordered = sorted(records, key=lambda r: (_utc(r.occurred_at), r.customer_id))
        self.records: tuple[MovementRecord, ...] = tuple(ordered)
        self._timeline: dict[str, tuple[list[datetime], list[float]]] = {}
        per_customer: dict[str, list[MovementRecord]] = defaultdict(list)
        for record in ordered:
            per_customer[record.customer_id].append(record)
        for customer, items in per_customer.items():
            self._timeline[customer] = ([_utc(r.occurred_at) for r in items], [r.mrr_after for r in items])

    def __len__(self) -> int:
        return len(self.records)

    @property
    def customers(self) -> list[str]:
        return sorted(self._timeline)

    @property
    def first_date(self) -> date | None:
        return _utc(self.records[0].occurred_at).date() if self.records else None

    @property
    def last_date(self) -> date | None:
        return _utc(self.records[-1].occurred_at).date() if self.records else None

    # ------------------------------------------------------------------ point-in-time MRR

    def customer_mrr_at(self, customer_id: str, at: datetime) -> float:
        """A customer's MRR just after the last movement at or before ``at``."""
        timeline = self._timeline.get(customer_id)
        if timeline is None:
            return 0.0
        times, values = timeline
        index = bisect_right(times, _utc(at))
        return values[index - 1] if index else 0.0

    def mrr_by_customer(self, at: datetime) -> dict[str, float]:
        snapshot = {c: self.customer_mrr_at(c, at) for c in self._timeline}
        return {c: v for c, v in snapshot.items() if v > 0}

    def mrr_at(self, at: datetime) -> float:
        return sum(self.mrr_by_customer(at).values())

    # ------------------------------------------------------------------ movements

    def totals(self, start: datetime, end: datetime) -> MovementTotals:
        """Movement totals for ``start < occurred_at <= end``."""
        lo, hi = _utc(start), _utc(end)
        sums: dict[Movement, float] = defaultdict(float)
        for record in self.records:
            if lo < _utc(record.occurred_at) <= hi:
                sums[record.movement] += record.amount
        return MovementTotals.from_mapping(dict(sums))

    def monthly_bridge(self, first_month: date, last_month: date) -> list[MonthlyBridge]:
        """Opening MRR, movements and closing MRR for each calendar month. Each month's closing MRR equals
        its opening MRR plus its net movements, which :meth:`MonthlyBridge.reconciles` checks."""
        rows: list[MonthlyBridge] = []
        for month in iter_months(first_month, last_month):
            opening_at = end_of_day(month - timedelta(days=1))
            closing_at = end_of_day(end_of_month(month))
            rows.append(
                MonthlyBridge(
                    month=month,
                    opening=self.mrr_at(opening_at),
                    totals=self.totals(opening_at, closing_at),
                    closing=self.mrr_at(closing_at),
                )
            )
        return rows

    # ------------------------------------------------------------------ retention

    def retention(self, start: date, end: date) -> RetentionResult:
        """Net and gross revenue retention of the customers paying on ``start``, measured on ``end``.

        NRR counts expansion; GRR caps every customer at their starting MRR, so it can never exceed 100%.
        Customers acquired after ``start`` are excluded entirely.
        """
        if end < start:
            raise ValueError("end must not be before start")
        base = self.mrr_by_customer(end_of_day(start))
        base_mrr = sum(base.values())
        ending = {c: self.customer_mrr_at(c, end_of_day(end)) for c in base}
        retained = sum(ending.values())
        gross = sum(min(ending[c], base[c]) for c in base)
        still_paying = sum(1 for v in ending.values() if v > 0)
        return RetentionResult(
            start=start,
            end=end,
            base_customers=len(base),
            base_mrr=base_mrr,
            retained_mrr=retained,
            gross_retained_mrr=gross,
            retained_customers=still_paying,
        )

    def trailing_retention(self, as_of: date, months: int = 12) -> RetentionResult:
        return self.retention(add_months(as_of, -months), as_of)

    # ------------------------------------------------------------------ cohorts

    def customer_histories(self, first_month: date, last_month: date) -> list[CustomerHistory]:
        months = list(iter_months(first_month, last_month))
        histories = []
        for customer in self._timeline:
            monthly = {m: self.customer_mrr_at(customer, end_of_day(end_of_month(m))) for m in months}
            histories.append(CustomerHistory(customer, monthly))
        return histories

    def cohorts(self, as_of: date, first_month: date | None = None) -> list[Cohort]:
        """Cohort matrix as of a date. Signup months come from the full history, so a customer who started
        before ``first_month`` is left out rather than counted as a later signup."""
        if not self.records or self.first_date is None:
            return []
        histories = self.customer_histories(month_key(self.first_date), as_of)
        return build_cohorts(histories, as_of=as_of, first_month=first_month)


@dataclass(frozen=True, slots=True)
class MonthlyBridge:
    month: date
    opening: float
    totals: MovementTotals
    closing: float

    def reconciles(self, tolerance: float = 0.01) -> bool:
        return abs(self.opening + self.totals.net - self.closing) <= tolerance


@dataclass(frozen=True, slots=True)
class RetentionResult:
    start: date
    end: date
    base_customers: int
    base_mrr: float
    retained_mrr: float
    gross_retained_mrr: float
    retained_customers: int

    @property
    def nrr(self) -> float | None:
        return 100 * self.retained_mrr / self.base_mrr if self.base_mrr else None

    @property
    def grr(self) -> float | None:
        return 100 * self.gross_retained_mrr / self.base_mrr if self.base_mrr else None

    @property
    def logo_retention(self) -> float | None:
        return 100 * self.retained_customers / self.base_customers if self.base_customers else None


def lifetimes_from_ledger(ledger: Ledger, as_of: date) -> list[tuple[str, float, bool]]:
    """(customer, months paying, churned) for every customer who ever paid, for survival analysis.

    A lifetime runs from the first movement that took a customer above zero to the churn that took them
    back to zero; customers still paying on ``as_of`` are censored there.
    """
    out: list[tuple[str, float, bool]] = []
    cutoff = end_of_day(as_of)
    starts: dict[str, datetime] = {}
    ends: dict[str, datetime] = {}
    for record in ledger.records:
        moment = _utc(record.occurred_at)
        if moment > cutoff:
            break
        if record.mrr_before == 0 and record.mrr_after > 0 and record.customer_id not in starts:
            starts[record.customer_id] = moment
        if record.movement is Movement.CHURN:
            ends[record.customer_id] = moment
        elif record.mrr_after > 0:
            ends.pop(record.customer_id, None)
    for customer, began in starts.items():
        churned = customer in ends
        finished = ends.get(customer, cutoff)
        out.append((customer, max(0.0, (finished - began).days / 30.4), churned))
    return out
