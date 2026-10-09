"""Read-side queries over the event store, returning domain records rather than ORM rows."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from churnwise.db import models
from churnwise.domain.ledger import MovementRecord
from churnwise.domain.recovery import FailedPaymentRecord, PaymentStatus


def get_workspace(session: Session, slug: str) -> models.Workspace | None:
    return session.scalar(select(models.Workspace).where(models.Workspace.slug == slug))


def create_workspace(session: Session, slug: str, name: str, currency: str = "USD") -> models.Workspace:
    workspace = models.Workspace(slug=slug, name=name, currency=currency.upper())
    session.add(workspace)
    session.flush()
    return workspace


def ensure_workspace(
    session: Session, slug: str, name: str, currency: str = "USD"
) -> tuple[models.Workspace, bool]:
    """Return the workspace with ``slug``, creating it if needed. The flag says whether it was created."""
    existing = get_workspace(session, slug)
    if existing is not None:
        return existing, False
    return create_workspace(session, slug, name, currency), True


def movement_records(
    session: Session,
    workspace_id: str,
    since: datetime | None = None,
    until: datetime | None = None,
) -> list[MovementRecord]:
    query = (
        select(models.MrrMovement, models.Customer.external_id)
        .join(models.Customer, models.Customer.id == models.MrrMovement.customer_id)
        .where(models.MrrMovement.workspace_id == workspace_id)
        .order_by(models.MrrMovement.occurred_at, models.MrrMovement.id)
    )
    if since is not None:
        query = query.where(models.MrrMovement.occurred_at >= since)
    if until is not None:
        query = query.where(models.MrrMovement.occurred_at <= until)
    return [
        MovementRecord(
            customer_id=external_id,
            movement=movement.type,
            amount=movement.amount,
            mrr_before=movement.mrr_before,
            mrr_after=movement.mrr_after,
            occurred_at=movement.occurred_at,
        )
        for movement, external_id in session.execute(query).all()
    ]


def failed_payment_records(
    session: Session, workspace_id: str, statuses: Sequence[PaymentStatus] | None = None
) -> list[FailedPaymentRecord]:
    query = (
        select(models.FailedPayment, models.Customer.external_id)
        .join(models.Customer, models.Customer.id == models.FailedPayment.customer_id)
        .where(models.FailedPayment.workspace_id == workspace_id)
        .order_by(models.FailedPayment.failed_at.desc())
    )
    if statuses:
        query = query.where(models.FailedPayment.status.in_(list(statuses)))
    return [
        FailedPaymentRecord(
            invoice_id=payment.invoice_external_id,
            customer_id=external_id,
            amount=payment.amount,
            decline_code=payment.decline_code,
            attempts=payment.attempts,
            status=payment.status,
            failed_at=payment.failed_at,
            recovered_at=payment.recovered_at,
        )
        for payment, external_id in session.execute(query).all()
    ]


def next_retries(session: Session, workspace_id: str) -> dict[str, datetime | None]:
    """Scheduled retry time per open invoice."""
    rows = session.execute(
        select(models.FailedPayment.invoice_external_id, models.FailedPayment.next_retry_at).where(
            models.FailedPayment.workspace_id == workspace_id,
            models.FailedPayment.status == PaymentStatus.OPEN,
        )
    ).all()
    return dict(rows)


def customer_counts(session: Session, workspace_id: str) -> tuple[int, float]:
    """(paying customers, total MRR) from the customer projection."""
    count, total = session.execute(
        select(func.count(models.Customer.id), func.coalesce(func.sum(models.Customer.mrr), 0.0)).where(
            models.Customer.workspace_id == workspace_id, models.Customer.mrr > 0
        )
    ).one()
    return int(count), float(total)
