from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from churnwise.domain.recovery import (
    IN_RECOVERY_SHARE,
    RETRY_SHARE,
    FailedPaymentRecord,
    PaymentStatus,
    RecoveryAnalytics,
    summarize_failed_payments,
)

REL = 1e-9


def test_funnel_matches_typescript(model, golden):
    funnel = RecoveryAnalytics(model).funnel()
    want = golden["funnel"]
    assert funnel.failed == pytest.approx(want["failed"], rel=REL)
    assert funnel.recovered == pytest.approx(want["recovered"], rel=REL)
    assert funnel.rate == pytest.approx(want["rate"], rel=REL)
    assert [i.label for i in funnel.items] == [i["label"] for i in want["items"]]
    assert [i.value for i in funnel.items] == pytest.approx([i["value"] for i in want["items"]], rel=REL)


def test_funnel_outcomes_add_up_to_failed(model):
    funnel = RecoveryAnalytics(model).funnel()
    failed, retries, outreach, pending, lost = (i.value for i in funnel.items)
    assert retries + outreach + pending + lost == pytest.approx(failed)
    assert retries == pytest.approx(funnel.recovered * RETRY_SHARE)
    assert pending == pytest.approx(failed * IN_RECOVERY_SHARE)
    assert [i.tone for i in funnel.items] == ["ink", "brand", "mint", "amber", "red"]


def test_monthly_recovery_matches_typescript(model, golden):
    months = RecoveryAnalytics(model).by_month(12)
    assert [m.label for m in months] == [m["label"] for m in golden["byMonth"]]
    assert [m.recovered for m in months] == pytest.approx(
        [m["recovered"] for m in golden["byMonth"]], rel=REL
    )
    assert all(55 < m.rate < 80 for m in months)


def test_involuntary_churn_matches_typescript(model, golden):
    assert RecoveryAnalytics(model).involuntary_churn_rate() == pytest.approx(golden["invol"], rel=REL)


T0 = datetime(2026, 3, 1, tzinfo=UTC)


def _record(
    invoice: str,
    amount: float,
    code: str,
    status: PaymentStatus,
    attempts: int = 1,
    days: float | None = None,
):
    return FailedPaymentRecord(
        invoice_id=invoice,
        customer_id=f"cus_{invoice}",
        amount=amount,
        decline_code=code,
        attempts=attempts,
        status=status,
        failed_at=T0,
        recovered_at=T0 + timedelta(days=days) if days is not None else None,
    )


def test_summarize_failed_payments():
    summary = summarize_failed_payments(
        [
            _record("a", 100, "insufficient_funds", PaymentStatus.RECOVERED, attempts=2, days=4),
            _record("b", 300, "insufficient_funds", PaymentStatus.RECOVERED, attempts=1, days=2),
            _record("c", 200, "expired_card", PaymentStatus.LOST, attempts=4),
            _record("d", 50, "do_not_honor", PaymentStatus.OPEN),
        ]
    )
    assert summary.count == 4
    assert summary.failed == 650
    assert (summary.recovered, summary.lost, summary.open) == (400, 200, 50)
    assert summary.resolved_rate == pytest.approx(400 / 600 * 100)
    assert summary.median_days_to_recover == pytest.approx(3)
    assert summary.attempts_to_recover == {1: 1, 2: 1}
    top = summary.declines[0]
    assert (top.code, top.label, top.count, top.share) == ("insufficient_funds", "Insufficient funds", 2, 50)
    assert top.recovery_rate == 100
    assert {d.code for d in summary.declines} == {"insufficient_funds", "expired_card", "do_not_honor"}


def test_summary_of_nothing():
    summary = summarize_failed_payments([])
    assert summary.count == 0
    assert summary.resolved_rate is None
    assert summary.median_days_to_recover is None
    assert summary.declines == ()
