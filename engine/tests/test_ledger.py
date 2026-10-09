from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from churnwise.domain.ledger import Ledger, MovementRecord, end_of_month, lifetimes_from_ledger
from churnwise.domain.types import Movement


def _at(day: str) -> datetime:
    return datetime.fromisoformat(day).replace(hour=12, tzinfo=UTC)


def _move(customer: str, movement: Movement, before: float, after: float, day: str) -> MovementRecord:
    return MovementRecord(customer, movement, abs(after - before), before, after, _at(day))


@pytest.fixture
def ledger() -> Ledger:
    return Ledger(
        [
            _move("a", Movement.NEW, 0, 100, "2025-01-10"),
            _move("b", Movement.NEW, 0, 200, "2025-01-20"),
            _move("c", Movement.NEW, 0, 50, "2025-02-05"),
            _move("a", Movement.EXPANSION, 100, 160, "2025-06-01"),
            _move("b", Movement.CONTRACTION, 200, 150, "2025-07-15"),
            _move("c", Movement.CHURN, 50, 0, "2025-08-01"),
            _move("d", Movement.NEW, 0, 400, "2025-09-01"),
            _move("b", Movement.CHURN, 150, 0, "2025-12-20"),
            _move("c", Movement.REACTIVATION, 0, 80, "2026-01-05"),
        ]
    )


def test_point_in_time_mrr(ledger):
    assert ledger.mrr_at(_at("2025-01-15")) == 100
    assert ledger.mrr_at(_at("2025-02-28")) == 350
    assert ledger.mrr_by_customer(_at("2025-08-02")) == {"a": 160, "b": 150}
    assert ledger.customer_mrr_at("zzz", _at("2026-01-01")) == 0
    assert ledger.mrr_at(_at("2026-01-31")) == 160 + 400 + 80


def test_ledger_orders_records_and_reports_its_span(ledger):
    assert len(ledger) == 9
    assert ledger.first_date == date(2025, 1, 10)
    assert ledger.last_date == date(2026, 1, 5)
    assert ledger.customers == ["a", "b", "c", "d"]


def test_monthly_bridge_reconciles(ledger):
    rows = ledger.monthly_bridge(date(2025, 1, 1), date(2026, 1, 31))
    assert len(rows) == 13
    assert all(row.reconciles() for row in rows)
    jan, feb = rows[0], rows[1]
    assert (jan.opening, jan.totals.new, jan.closing) == (0, 300, 300)
    assert (feb.opening, feb.totals.new, feb.closing) == (300, 50, 350)
    december = rows[11]
    assert december.totals.churn == 150
    assert rows[-1].totals.reactivation == 80


def test_retention_counts_only_the_base_cohort(ledger):
    result = ledger.retention(date(2025, 3, 1), date(2026, 2, 28))
    # Base on Mar 1: a=100, b=200, c=50 (350). A year on: a=160, b=0, c=80; d joined later and is excluded.
    assert result.base_customers == 3
    assert result.base_mrr == 350
    assert result.retained_mrr == 240
    assert result.gross_retained_mrr == 100 + 0 + 50
    assert result.nrr == pytest.approx(240 / 350 * 100)
    assert result.grr == pytest.approx(150 / 350 * 100)
    assert result.logo_retention == pytest.approx(200 / 3)
    assert result.grr <= 100


def test_trailing_retention_and_empty_base(ledger):
    assert ledger.trailing_retention(date(2026, 3, 1)).start == date(2025, 3, 1)
    empty = ledger.retention(date(2024, 1, 1), date(2024, 6, 1))
    assert empty.nrr is None and empty.grr is None and empty.logo_retention is None
    with pytest.raises(ValueError):
        ledger.retention(date(2025, 5, 1), date(2025, 4, 1))


def test_cohorts_from_the_ledger(ledger):
    cohorts = ledger.cohorts(as_of=date(2025, 12, 31))
    assert [c.label for c in cohorts] == ["Jan 2025", "Feb 2025", "Sep 2025"]
    january = cohorts[0]
    assert january.customers == 2 and january.start_mrr == 300
    # June: a expanded to 160, b still 200 -> 360 / 300.
    assert january.net[5] == pytest.approx(120)
    # December: b churned on the 20th.
    assert january.logo[11] == pytest.approx(50)
    assert cohorts[1].logo[6] == 0  # c churned in August, month 6 of the Feb cohort
    assert Ledger([]).cohorts(date(2026, 1, 1)) == []


def test_lifetimes_for_survival(ledger):
    rows = {
        customer: (months, churned)
        for customer, months, churned in lifetimes_from_ledger(ledger, date(2025, 12, 31))
    }
    assert rows["b"][1] is True
    assert rows["b"][0] == pytest.approx((date(2025, 12, 20) - date(2025, 1, 20)).days / 30.4)
    assert rows["c"][1] is True  # reactivated after the cutoff
    assert rows["a"][1] is False and rows["d"][1] is False
    after = {c: churned for c, _, churned in lifetimes_from_ledger(ledger, date(2026, 2, 1))}
    assert after["c"] is False


def test_end_of_month():
    assert end_of_month(date(2024, 2, 10)) == date(2024, 2, 29)
    assert end_of_month(date(2025, 12, 1)) == date(2025, 12, 31)
