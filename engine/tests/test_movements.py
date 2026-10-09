from __future__ import annotations

import pytest

from churnwise.domain.movements import (
    BillingInterval,
    MovementChange,
    SubscriptionState,
    classify_movement,
    monthly_value,
)
from churnwise.domain.types import Movement, MovementTotals


def test_monthly_value_matches_typescript(golden):
    computed = [
        monthly_value(8376, 1, "year"),
        monthly_value(10, 3, "week", 2),
        monthly_value(1, 1, "day"),
    ]
    assert computed == pytest.approx(golden["monthly"])


def test_monthly_value_normalises_every_interval():
    assert monthly_value(349, 1, BillingInterval.MONTH) == 349
    assert monthly_value(4188, 1, BillingInterval.YEAR) == pytest.approx(349)
    assert monthly_value(349, 2, BillingInterval.MONTH, interval_count=3) == pytest.approx(232.67, abs=0.01)
    assert monthly_value(10, 1, BillingInterval.DAY) == pytest.approx(304)


@pytest.mark.parametrize("bad", [{"quantity": -1}, {"interval_count": 0}])
def test_monthly_value_validates(bad):
    args = {"unit_amount": 10, "quantity": 1, "interval": "month", "interval_count": 1} | bad
    with pytest.raises(ValueError):
        monthly_value(**args)


@pytest.mark.parametrize(
    ("before", "after", "expected"),
    [
        (None, 349, MovementChange(Movement.NEW, 349)),
        (SubscriptionState(0), 349, MovementChange(Movement.NEW, 349)),
        (SubscriptionState(0, previously_churned=True), 99, MovementChange(Movement.REACTIVATION, 99)),
        (SubscriptionState(349), 1190, MovementChange(Movement.EXPANSION, 841)),
        (SubscriptionState(349), 99, MovementChange(Movement.CONTRACTION, 250)),
        (SubscriptionState(349), 0, MovementChange(Movement.CHURN, 349)),
        (SubscriptionState(349), 349.004, None),
        (None, 0, None),
    ],
)
def test_classify_movement(before, after, expected):
    assert classify_movement(before, after) == expected


def test_classify_rejects_negative_mrr():
    with pytest.raises(ValueError):
        classify_movement(None, -1)


def test_signed_amounts_follow_the_movement():
    assert MovementChange(Movement.EXPANSION, 10).signed_amount == 10
    assert MovementChange(Movement.CHURN, 10).signed_amount == -10


def test_movement_totals_arithmetic():
    a = MovementTotals(new=10, expansion=5, reactivation=1, contraction=2, churn=4)
    b = MovementTotals(new=1)
    total = a + b
    assert total.new == 11
    assert total.gained == 17
    assert total.lost == 6
    assert total.net == 11
    assert total.quick_ratio == pytest.approx(17 / 6)
    assert MovementTotals(new=5).quick_ratio == float("inf")
    assert MovementTotals.sum([a, b]) == total
    assert total["churn"] == 4
    assert set(total.as_dict()) == {"new", "expansion", "reactivation", "contraction", "churn"}
    assert Movement.CHURN.sign == -1 and Movement.NEW.sign == 1
