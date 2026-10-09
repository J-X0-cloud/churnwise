"""Failed-payment recovery analytics.

:class:`RecoveryAnalytics` reports on the sample model: monthly failed vs recovered revenue, the twelve-month
outcome funnel and involuntary churn. :func:`summarize_failed_payments` computes the same outcomes from
individual failed-payment records, which is what the event store holds.
"""

from __future__ import annotations

import statistics
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Literal

from churnwise.domain.dates import auto_month_label
from churnwise.domain.dunning import decline_label
from churnwise.domain.simulation import DAYS_PER_MONTH, RevenueModel
from churnwise.domain.types import Tone

#: Share of recovered revenue won back by retries alone (the rest by emails and card updates).
RETRY_SHARE = 0.57
#: Share of failed revenue still inside its recovery window.
IN_RECOVERY_SHARE = 0.05

FunnelKey = Literal["failed", "retries", "outreach", "pending", "lost"]


@dataclass(frozen=True, slots=True)
class MonthlyRecovery:
    label: str
    failed: float
    recovered: float

    @property
    def rate(self) -> float:
        return (self.recovered / self.failed) * 100 if self.failed else 0.0


@dataclass(frozen=True, slots=True)
class FunnelItem:
    key: FunnelKey
    label: str
    value: float
    tone: Tone


@dataclass(frozen=True, slots=True)
class RecoveryFunnel:
    items: tuple[FunnelItem, ...]
    failed: float
    recovered: float
    #: Recovered as a percent of failed.
    rate: float


class RecoveryAnalytics:
    """Recovery reporting over a daily revenue model."""

    def __init__(self, model: RevenueModel, window_days: int = 365) -> None:
        self.model = model
        self.window_days = window_days

    def _window(self) -> tuple[int, int]:
        return self.model.day_count - self.window_days, self.model.day_count

    def by_month(self, months: int = 12) -> list[MonthlyRecovery]:
        return [
            MonthlyRecovery(
                label=auto_month_label(w.month),
                failed=self.model.sum_failed(w.start, w.end),
                recovered=self.model.sum_recovered(w.start, w.end),
            )
            for w in self.model.months[-months:]
        ]

    def funnel(self) -> RecoveryFunnel:
        """Where failed revenue ended up over the window: recovered by retries, recovered by outreach,
        still in recovery, or lost to involuntary churn. The last four items add up to the first."""
        start, end = self._window()
        failed = self.model.sum_failed(start, end)
        recovered = self.model.sum_recovered(start, end)
        retries = recovered * RETRY_SHARE
        pending = failed * IN_RECOVERY_SHARE
        return RecoveryFunnel(
            failed=failed,
            recovered=recovered,
            rate=(recovered / failed) * 100,
            items=(
                FunnelItem("failed", "Failed charges", failed, "ink"),
                FunnelItem("retries", "Recovered by smart retries", retries, "brand"),
                FunnelItem("outreach", "Recovered by emails & card updates", recovered - retries, "mint"),
                FunnelItem("pending", "Still in recovery", pending, "amber"),
                FunnelItem("lost", "Lost to involuntary churn", failed - recovered - pending, "red"),
            ),
        )

    def involuntary_churn_rate(self) -> float:
        """Failed revenue that was never recovered, as a monthly share of MRR, in percent."""
        start, end = self._window()
        funnel = self.funnel()
        mrr_days = self.model.average_mrr(start, end) * (end - start)
        lost = (funnel.failed - funnel.recovered) * (1 - IN_RECOVERY_SHARE)
        return (lost / mrr_days) * DAYS_PER_MONTH * 100


# ------------------------------------------------------------------ record-level reporting


class PaymentStatus(StrEnum):
    OPEN = "open"
    RECOVERED = "recovered"
    LOST = "lost"


@dataclass(frozen=True, slots=True)
class FailedPaymentRecord:
    invoice_id: str
    customer_id: str
    amount: float
    decline_code: str
    attempts: int
    status: PaymentStatus
    failed_at: datetime
    recovered_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class DeclineBreakdown:
    code: str
    label: str
    count: int
    amount: float
    recovered: float
    #: Share of all failures with this code, in percent.
    share: float

    @property
    def recovery_rate(self) -> float:
        return (self.recovered / self.amount) * 100 if self.amount else 0.0


@dataclass(frozen=True, slots=True)
class RecoverySummary:
    count: int
    failed: float
    recovered: float
    open: float
    lost: float
    #: Recovered as a percent of the failed amount that has been resolved (recovered or lost).
    resolved_rate: float | None
    #: Median days from failure to recovery, over recovered payments.
    median_days_to_recover: float | None
    attempts_to_recover: dict[int, int]
    declines: tuple[DeclineBreakdown, ...]


def summarize_failed_payments(records: Iterable[FailedPaymentRecord]) -> RecoverySummary:
    """Totals, recovery rate, time to recover and a per-decline-code breakdown."""
    rows = list(records)
    by_status: dict[PaymentStatus, float] = defaultdict(float)
    for r in rows:
        by_status[r.status] += r.amount

    resolved = by_status[PaymentStatus.RECOVERED] + by_status[PaymentStatus.LOST]
    days = [
        (r.recovered_at - r.failed_at).total_seconds() / 86400
        for r in rows
        if r.status is PaymentStatus.RECOVERED and r.recovered_at is not None
    ]
    attempts = Counter(r.attempts for r in rows if r.status is PaymentStatus.RECOVERED)

    grouped: dict[str, list[FailedPaymentRecord]] = defaultdict(list)
    for r in rows:
        grouped[r.decline_code].append(r)
    declines = sorted(
        (
            DeclineBreakdown(
                code=code,
                label=decline_label(code),
                count=len(items),
                amount=sum(i.amount for i in items),
                recovered=sum(i.amount for i in items if i.status is PaymentStatus.RECOVERED),
                share=100 * len(items) / len(rows),
            )
            for code, items in grouped.items()
        ),
        key=lambda d: (-d.count, d.code),
    )

    return RecoverySummary(
        count=len(rows),
        failed=sum(r.amount for r in rows),
        recovered=by_status[PaymentStatus.RECOVERED],
        open=by_status[PaymentStatus.OPEN],
        lost=by_status[PaymentStatus.LOST],
        resolved_rate=(100 * by_status[PaymentStatus.RECOVERED] / resolved) if resolved else None,
        median_days_to_recover=statistics.median(days) if days else None,
        attempts_to_recover=dict(sorted(attempts.items())),
        declines=tuple(declines),
    )
