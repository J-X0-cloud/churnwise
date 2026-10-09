"""Rules that turn subscription changes into MRR movements.

These work on plain numbers, so the webhook pipeline, the ledger analytics and the tests all share them.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from churnwise.domain.types import Movement

DAYS_PER_MONTH = 30.4
#: Changes smaller than half a cent are rounding noise, not movements.
MOVEMENT_EPSILON = 0.005


class BillingInterval(StrEnum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


_MONTHS_PER_INTERVAL: dict[BillingInterval, float] = {
    BillingInterval.DAY: 1 / DAYS_PER_MONTH,
    BillingInterval.WEEK: 7 / DAYS_PER_MONTH,
    BillingInterval.MONTH: 1.0,
    BillingInterval.YEAR: 12.0,
}


def monthly_value(
    unit_amount: float,
    quantity: int,
    interval: BillingInterval | str,
    interval_count: int = 1,
) -> float:
    """Normalise a recurring price to a monthly amount (annual plans spread over twelve months)."""
    if quantity < 0:
        raise ValueError("quantity cannot be negative")
    if interval_count < 1:
        raise ValueError("interval_count must be at least 1")
    per_interval = unit_amount * quantity
    months = _MONTHS_PER_INTERVAL[BillingInterval(interval)] * interval_count
    return per_interval / months


@dataclass(frozen=True, slots=True)
class SubscriptionState:
    """What we knew about a customer before an event."""

    mrr: float
    #: Whether the customer had paid before and then churned to zero.
    previously_churned: bool = False


@dataclass(frozen=True, slots=True)
class MovementChange:
    movement: Movement
    #: Always positive; the sign comes from the movement.
    amount: float

    @property
    def signed_amount(self) -> float:
        return self.amount * self.movement.sign


def classify_movement(before: SubscriptionState | None, after_mrr: float) -> MovementChange | None:
    """Classify a change in a customer's MRR.

    Returns ``None`` when MRR is unchanged (a renewal, a payment-method update), which is why most billing
    events never become movements.
    """
    if after_mrr < 0:
        raise ValueError("MRR cannot be negative")
    previous = before.mrr if before else 0.0
    delta = after_mrr - previous
    if abs(delta) < MOVEMENT_EPSILON:
        return None
    if previous == 0:
        returning = before is not None and before.previously_churned
        return MovementChange(Movement.REACTIVATION if returning else Movement.NEW, after_mrr)
    if after_mrr == 0:
        return MovementChange(Movement.CHURN, previous)
    if delta > 0:
        return MovementChange(Movement.EXPANSION, delta)
    return MovementChange(Movement.CONTRACTION, -delta)
