"""Webhook ingestion.

Store the raw event once (idempotent on its external id), then update the projections it affects:
customer MRR and MRR movements for subscription events, failed-payment records for invoice events.
Everything for one event runs in a single transaction, so a retried delivery never double-counts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from churnwise.billing.events import (
    BillingEvent,
    InvoicePaid,
    InvoicePaymentFailed,
    SubscriptionCanceled,
    SubscriptionEvent,
    SubscriptionStatus,
)
from churnwise.db import models
from churnwise.domain.dunning import next_retry
from churnwise.domain.movements import MovementChange, SubscriptionState, classify_movement, monthly_value
from churnwise.domain.recovery import PaymentStatus

#: Subscriptions in these states contribute no MRR.
_NON_PAYING = frozenset({SubscriptionStatus.CANCELED, SubscriptionStatus.PAUSED, SubscriptionStatus.TRIALING})


def to_major(minor: int) -> float:
    return minor / 100


def subscription_mrr(event: SubscriptionEvent) -> float:
    """Normalised MRR a subscription contributes after this event. Canceled, paused and trialing
    subscriptions contribute nothing; past-due ones still count until they are canceled."""
    if isinstance(event, SubscriptionCanceled) or event.data.status in _NON_PAYING:
        return 0.0
    return sum(
        monthly_value(to_major(item.unit_amount), item.quantity, item.interval, item.interval_count)
        for item in event.data.items
    )


@dataclass(frozen=True, slots=True)
class IngestResult:
    status: Literal["processed", "duplicate", "unknown_workspace"]
    event_id: str | None = None
    movement: MovementChange | None = None


def _customer(session: Session, workspace_id: str, external_id: str) -> models.Customer | None:
    return session.scalar(
        select(models.Customer).where(
            models.Customer.workspace_id == workspace_id, models.Customer.external_id == external_id
        )
    )


def _ensure_customer(session: Session, workspace_id: str, external_id: str) -> models.Customer:
    customer = _customer(session, workspace_id, external_id)
    if customer is None:
        customer = models.Customer(workspace_id=workspace_id, external_id=external_id, mrr=0.0)
        session.add(customer)
        session.flush()
    return customer


def _apply_subscription(
    session: Session, workspace_id: str, stored: models.BillingEvent, event: SubscriptionEvent
) -> MovementChange | None:
    data = event.data
    existing = _customer(session, workspace_id, data.customer_id)
    before_mrr = existing.mrr if existing else 0.0
    after = subscription_mrr(event)
    change = classify_movement(
        SubscriptionState(existing.mrr, previously_churned=existing.churned_at is not None)
        if existing
        else None,
        after,
    )

    if existing is None:
        customer = models.Customer(
            workspace_id=workspace_id,
            external_id=data.customer_id,
            name=data.customer_name,
            plan=data.plan,
            mrr=after,
            first_paid_at=event.occurred_at if after > 0 else None,
        )
        session.add(customer)
    else:
        customer = existing
        if data.customer_name is not None:
            customer.name = data.customer_name
        if data.plan is not None:
            customer.plan = data.plan
        if customer.first_paid_at is None and after > 0:
            customer.first_paid_at = event.occurred_at
        if after == 0 and before_mrr > 0:
            customer.churned_at = event.occurred_at
        elif after > 0:
            customer.churned_at = None
        customer.mrr = after
    session.flush()

    if change is not None:
        session.add(
            models.MrrMovement(
                workspace_id=workspace_id,
                customer_id=customer.id,
                event_id=stored.id,
                type=change.movement,
                amount=change.amount,
                mrr_before=before_mrr,
                mrr_after=after,
                occurred_at=event.occurred_at,
            )
        )
    return change


def _apply_payment_failed(session: Session, workspace_id: str, event: InvoicePaymentFailed) -> None:
    data = event.data
    decision = next_retry(data.decline_code, data.attempt, event.occurred_at)
    status = PaymentStatus.LOST if decision.action == "give_up" else PaymentStatus.OPEN
    retry_at = decision.at if decision.action == "retry" else None

    record = session.scalar(
        select(models.FailedPayment).where(
            models.FailedPayment.workspace_id == workspace_id,
            models.FailedPayment.invoice_external_id == data.invoice_id,
        )
    )
    if record is None:
        customer = _ensure_customer(session, workspace_id, data.customer_id)
        session.add(
            models.FailedPayment(
                workspace_id=workspace_id,
                customer_id=customer.id,
                invoice_external_id=data.invoice_id,
                amount=to_major(data.amount_due),
                decline_code=data.decline_code,
                attempts=data.attempt,
                status=status,
                failed_at=event.occurred_at,
                next_retry_at=retry_at,
            )
        )
        return
    # A failure delivered after the invoice was already paid is stale; the recovery stands.
    if record.status is PaymentStatus.RECOVERED or data.attempt < record.attempts:
        return
    record.attempts = data.attempt
    record.decline_code = data.decline_code
    record.status = status
    record.next_retry_at = retry_at


def _apply_invoice_paid(session: Session, workspace_id: str, event: InvoicePaid) -> None:
    # Only invoices that previously failed are recoveries; ordinary payments leave no projection.
    session.execute(
        update(models.FailedPayment)
        .where(
            models.FailedPayment.workspace_id == workspace_id,
            models.FailedPayment.invoice_external_id == event.data.invoice_id,
            models.FailedPayment.status == PaymentStatus.OPEN,
        )
        .values(status=PaymentStatus.RECOVERED, recovered_at=event.occurred_at, next_retry_at=None)
    )


def _ingest(session: Session, workspace_id: str, event: BillingEvent, now: datetime) -> IngestResult:
    seen = session.scalar(
        select(models.BillingEvent.id).where(
            models.BillingEvent.workspace_id == workspace_id, models.BillingEvent.external_id == event.id
        )
    )
    if seen is not None:
        return IngestResult("duplicate", seen)

    stored = models.BillingEvent(
        workspace_id=workspace_id,
        source=event.source,
        external_id=event.id,
        type=event.type,
        occurred_at=event.occurred_at,
        payload=event.data.model_dump(mode="json", by_alias=True),
    )
    session.add(stored)
    session.flush()

    movement: MovementChange | None = None
    match event:
        case InvoicePaymentFailed():
            _apply_payment_failed(session, workspace_id, event)
        case InvoicePaid():
            _apply_invoice_paid(session, workspace_id, event)
        case _:
            movement = _apply_subscription(session, workspace_id, stored, event)

    stored.processed_at = now
    return IngestResult("processed", stored.id, movement)


def ingest_event(
    factory: sessionmaker[Session], event: BillingEvent, now: datetime | None = None
) -> IngestResult:
    """Ingest one validated event. Safe to call concurrently for the same event: the loser of the race on
    the unique external id sees a duplicate."""
    moment = now or datetime.now(UTC)
    with factory() as session:
        workspace_id = session.scalar(
            select(models.Workspace.id).where(models.Workspace.slug == event.workspace)
        )
    if workspace_id is None:
        return IngestResult("unknown_workspace")
    try:
        with factory.begin() as session:
            return _ingest(session, workspace_id, event, moment)
    except IntegrityError:
        with factory() as session:
            seen = session.scalar(
                select(models.BillingEvent.id).where(
                    models.BillingEvent.workspace_id == workspace_id,
                    models.BillingEvent.external_id == event.id,
                )
            )
        if seen is None:
            raise
        return IngestResult("duplicate", seen)
