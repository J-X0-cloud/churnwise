from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select

from churnwise.billing.events import parse_event
from churnwise.billing.ingest import ingest_event, subscription_mrr
from churnwise.db import models
from churnwise.domain.recovery import PaymentStatus
from churnwise.domain.types import Movement
from tests.payloads import invoice_paid_event, payment_failed_event, subscription_event


def _ingest(factory, raw):
    return ingest_event(factory, parse_event(raw), now=datetime(2026, 10, 1, tzinfo=UTC))


def _movements(factory) -> list[tuple[str, float, float, float]]:
    with factory() as session:
        rows = session.scalars(select(models.MrrMovement).order_by(models.MrrMovement.occurred_at)).all()
        return [
            (r.type.value, round(r.amount, 2), round(r.mrr_before, 2), round(r.mrr_after, 2)) for r in rows
        ]


def _customer(factory, external_id: str) -> models.Customer:
    with factory() as session:
        customer = session.scalar(select(models.Customer).where(models.Customer.external_id == external_id))
        assert customer is not None
        return customer


def test_subscription_lifecycle_becomes_movements(factory):
    results = [
        _ingest(factory, subscription_event("e1", "cus_1", amount=34900, occurred_at="2026-01-10T00:00:00Z")),
        _ingest(
            factory,
            subscription_event(
                "e2", "cus_1", type_="subscription.updated", amount=119000, occurred_at="2026-03-01T00:00:00Z"
            ),
        ),
        _ingest(
            factory,
            subscription_event(
                "e3", "cus_1", type_="subscription.updated", amount=9900, occurred_at="2026-04-01T00:00:00Z"
            ),
        ),
        _ingest(
            factory,
            subscription_event(
                "e4", "cus_1", type_="subscription.canceled", amount=9900, occurred_at="2026-05-01T00:00:00Z"
            ),
        ),
        _ingest(factory, subscription_event("e5", "cus_1", amount=34900, occurred_at="2026-07-01T00:00:00Z")),
    ]
    assert [r.status for r in results] == ["processed"] * 5
    assert [r.movement.movement for r in results if r.movement] == [
        Movement.NEW,
        Movement.EXPANSION,
        Movement.CONTRACTION,
        Movement.CHURN,
        Movement.REACTIVATION,
    ]
    assert _movements(factory) == [
        ("new", 349.0, 0.0, 349.0),
        ("expansion", 841.0, 349.0, 1190.0),
        ("contraction", 1091.0, 1190.0, 99.0),
        ("churn", 99.0, 99.0, 0.0),
        ("reactivation", 349.0, 0.0, 349.0),
    ]
    customer = _customer(factory, "cus_1")
    assert customer.mrr == 349
    assert customer.churned_at is None
    assert customer.first_paid_at == datetime(2026, 1, 10, tzinfo=UTC)


def test_annual_plans_are_spread_over_twelve_months(factory):
    result = _ingest(
        factory, subscription_event("e1", "cus_a", amount=837600, interval="year", name="Northgate Tutors")
    )
    assert result.movement is not None
    assert result.movement.amount == pytest.approx(698)
    assert _customer(factory, "cus_a").name == "Northgate Tutors"


def test_quantity_changes_are_expansion(factory):
    _ingest(factory, subscription_event("e1", "cus_q", amount=2900, quantity=10))
    result = _ingest(
        factory, subscription_event("e2", "cus_q", type_="subscription.updated", amount=2900, quantity=22)
    )
    assert result.movement is not None
    assert (result.movement.movement, result.movement.amount) == (Movement.EXPANSION, pytest.approx(348))


def test_renewals_and_trials_leave_no_movement(factory):
    _ingest(factory, subscription_event("e1", "cus_t", status="trialing"))
    assert _customer(factory, "cus_t").mrr == 0
    _ingest(factory, subscription_event("e2", "cus_t", type_="subscription.updated", status="active"))
    renewal = _ingest(
        factory, subscription_event("e3", "cus_t", type_="subscription.updated", status="active")
    )
    assert renewal.status == "processed" and renewal.movement is None
    assert [m[0] for m in _movements(factory)] == ["new"]


def test_paused_subscriptions_churn_and_keep_their_names(factory):
    _ingest(factory, subscription_event("e1", "cus_p", name="Pebble & Loom", plan="Starter"))
    _ingest(
        factory, subscription_event("e2", "cus_p", type_="subscription.updated", status="paused", plan=None)
    )
    customer = _customer(factory, "cus_p")
    assert customer.mrr == 0
    assert customer.churned_at is not None
    assert (customer.name, customer.plan) == ("Pebble & Loom", "Starter")


def test_duplicate_deliveries_are_idempotent(factory):
    raw = subscription_event("evt_dup", "cus_d")
    first = _ingest(factory, raw)
    second = _ingest(factory, raw)
    assert first.status == "processed"
    assert second.status == "duplicate"
    assert second.event_id == first.event_id
    with factory() as session:
        assert session.scalar(select(func.count(models.BillingEvent.id))) == 1
        assert session.scalar(select(func.count(models.MrrMovement.id))) == 1


def test_events_are_stored_with_their_payload(factory):
    _ingest(factory, subscription_event("evt_store", "cus_s"))
    with factory() as session:
        stored = session.scalar(select(models.BillingEvent))
        assert stored is not None
        assert stored.type == "subscription.created"
        assert stored.payload["customerId"] == "cus_s"
        assert stored.processed_at == datetime(2026, 10, 1, tzinfo=UTC)


def test_unknown_workspace(factory):
    raw = subscription_event("e1", "cus_x")
    raw["workspace"] = "nope"
    assert _ingest(factory, raw).status == "unknown_workspace"


def _payment(factory, invoice: str) -> models.FailedPayment:
    with factory() as session:
        payment = session.scalar(
            select(models.FailedPayment).where(models.FailedPayment.invoice_external_id == invoice)
        )
        assert payment is not None
        return payment


def test_failed_payment_is_scheduled_then_recovered(factory):
    _ingest(
        factory,
        payment_failed_event(
            "f1", "in_1", "cus_f", code="insufficient_funds", occurred_at="2026-02-03T09:00:00Z"
        ),
    )
    payment = _payment(factory, "in_1")
    assert payment.status is PaymentStatus.OPEN
    assert payment.amount == 349
    assert payment.next_retry_at == datetime(2026, 2, 15, 14, tzinfo=UTC)

    _ingest(
        factory,
        payment_failed_event(
            "f2", "in_1", "cus_f", attempt=2, code="insufficient_funds", occurred_at="2026-02-15T14:00:00Z"
        ),
    )
    assert _payment(factory, "in_1").attempts == 2

    _ingest(factory, invoice_paid_event("p1", "in_1", "cus_f", occurred_at="2026-03-01T14:00:00Z"))
    payment = _payment(factory, "in_1")
    assert payment.status is PaymentStatus.RECOVERED
    assert payment.recovered_at == datetime(2026, 3, 1, 14, tzinfo=UTC)
    assert payment.next_retry_at is None


def test_hard_declines_wait_for_a_card_update(factory):
    _ingest(factory, payment_failed_event("f1", "in_h", "cus_h", code="expired_card"))
    payment = _payment(factory, "in_h")
    assert payment.status is PaymentStatus.OPEN
    assert payment.next_retry_at is None


def test_final_attempt_is_lost(factory):
    _ingest(factory, payment_failed_event("f1", "in_l", "cus_l", attempt=4))
    assert _payment(factory, "in_l").status is PaymentStatus.LOST


def test_stale_failures_do_not_reopen_recovered_invoices(factory):
    _ingest(factory, payment_failed_event("f1", "in_s", "cus_s", attempt=2))
    _ingest(factory, invoice_paid_event("p1", "in_s", "cus_s"))
    _ingest(factory, payment_failed_event("f0", "in_s", "cus_s", attempt=1))
    _ingest(factory, payment_failed_event("f3", "in_s", "cus_s", attempt=3))
    payment = _payment(factory, "in_s")
    assert payment.status is PaymentStatus.RECOVERED
    assert payment.attempts == 2


def test_ordinary_payments_leave_no_projection(factory):
    result = _ingest(factory, invoice_paid_event("p1", "in_ok", "cus_ok"))
    assert result.status == "processed"
    with factory() as session:
        assert session.scalar(select(func.count(models.FailedPayment.id))) == 0


def test_subscription_mrr_rules():
    active = parse_event(subscription_event("e", "c", amount=10000, quantity=3))
    canceled = parse_event(subscription_event("e", "c", type_="subscription.canceled", amount=10000))
    past_due = parse_event(subscription_event("e", "c", status="past_due"))
    assert subscription_mrr(active) == 300
    assert subscription_mrr(canceled) == 0
    assert subscription_mrr(past_due) == 349
