"""Event store schema.

MRR history is always rebuilt from ``billing_events``; customers, MRR movements and failed payments are
projections kept up to date by the webhook pipeline. The schema is created by the Alembic migrations in
``engine/migrations``; these models must stay in step with them (a test checks).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    TypeDecorator,
    UniqueConstraint,
    func,
)
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from churnwise.billing.events import BillingSource
from churnwise.domain.recovery import PaymentStatus
from churnwise.domain.types import Movement

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


class UtcDateTime(TypeDecorator[datetime]):
    """Timezone-aware UTC datetimes on every backend (SQLite drops offsets, so they are restored here)."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("naive datetimes are not allowed in the event store")
        return value.astimezone(UTC)

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _enum(enum_cls: type[StrEnum], name: str) -> Enum:
    return Enum(enum_cls, name=name, values_callable=lambda e: [m.value for m in e], validate_strings=True)


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("ws"))
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), server_default=func.now())

    customers: Mapped[list[Customer]] = relationship(back_populates="workspace", cascade="all, delete-orphan")


class BillingEvent(Base):
    """Raw, append-only billing events as received from a connector. ``external_id`` makes ingestion
    idempotent."""

    __tablename__ = "billing_events"
    __table_args__ = (
        UniqueConstraint("workspace_id", "external_id", name="uq_billing_events_workspace_external"),
        Index("ix_billing_events_workspace_occurred", "workspace_id", "occurred_at"),
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("evt"))
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    source: Mapped[BillingSource] = mapped_column(_enum(BillingSource, "billing_source"))
    external_id: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(64))
    occurred_at: Mapped[datetime] = mapped_column(UtcDateTime())
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    received_at: Mapped[datetime] = mapped_column(UtcDateTime(), server_default=func.now())
    processed_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("workspace_id", "external_id", name="uq_customers_workspace_external"),
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("cus"))
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    external_id: Mapped[str] = mapped_column(String(200))
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    plan: Mapped[str | None] = mapped_column(String(120), nullable=True)
    #: Current normalised monthly recurring revenue, in major currency units.
    mrr: Mapped[float] = mapped_column(Float, default=0.0)
    first_paid_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    churned_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        UtcDateTime(), server_default=func.now(), onupdate=lambda: datetime.now(UTC)
    )

    workspace: Mapped[Workspace] = relationship(back_populates="customers")


class MrrMovement(Base):
    __tablename__ = "mrr_movements"
    __table_args__ = (
        Index("ix_mrr_movements_workspace_occurred", "workspace_id", "occurred_at"),
        Index("ix_mrr_movements_customer_occurred", "customer_id", "occurred_at"),
        CheckConstraint("amount >= 0", name="amount_positive"),
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("mov"))
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"))
    event_id: Mapped[str] = mapped_column(ForeignKey("billing_events.id", ondelete="CASCADE"))
    type: Mapped[Movement] = mapped_column(_enum(Movement, "movement_type"))
    #: Always positive; the sign comes from the movement type.
    amount: Mapped[float] = mapped_column(Float)
    mrr_before: Mapped[float] = mapped_column(Float)
    mrr_after: Mapped[float] = mapped_column(Float)
    occurred_at: Mapped[datetime] = mapped_column(UtcDateTime())

    customer: Mapped[Customer] = relationship()


class FailedPayment(Base):
    __tablename__ = "failed_payments"
    __table_args__ = (
        UniqueConstraint("workspace_id", "invoice_external_id", name="uq_failed_payments_workspace_invoice"),
        Index("ix_failed_payments_workspace_status", "workspace_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("fp"))
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"))
    invoice_external_id: Mapped[str] = mapped_column(String(200))
    amount: Mapped[float] = mapped_column(Float)
    decline_code: Mapped[str] = mapped_column(String(80))
    attempts: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[PaymentStatus] = mapped_column(
        _enum(PaymentStatus, "failed_payment_status"), default=PaymentStatus.OPEN
    )
    failed_at: Mapped[datetime] = mapped_column(UtcDateTime())
    next_retry_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    recovered_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)

    customer: Mapped[Customer] = relationship()
