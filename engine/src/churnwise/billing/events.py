"""Billing events as delivered by Churnwise connectors, normalised across Stripe, Chargebee, Recurly and
others. The payload is validated strictly: amounts are integers in minor units (cents), and unknown event
types are rejected rather than silently stored."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, field_validator
from pydantic.alias_generators import to_camel

from churnwise.domain.movements import BillingInterval


class BillingSource(StrEnum):
    STRIPE = "stripe"
    CHARGEBEE = "chargebee"
    RECURLY = "recurly"
    BRAINTREE = "braintree"
    PADDLE = "paddle"
    APP_STORE = "app_store"
    CUSTOM = "custom"


class SubscriptionStatus(StrEnum):
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    PAUSED = "paused"
    CANCELED = "canceled"


MinorUnits = Annotated[int, Field(strict=True, ge=0)]
PositiveInt = Annotated[int, Field(strict=True, gt=0)]
NonEmpty = Annotated[str, Field(min_length=1)]


class _Model(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, frozen=True, extra="ignore")


class SubscriptionItem(_Model):
    price_id: str
    #: Minor units (cents).
    unit_amount: MinorUnits
    quantity: PositiveInt = 1
    interval: BillingInterval
    interval_count: PositiveInt = 1


class SubscriptionData(_Model):
    subscription_id: str
    customer_id: str
    customer_name: str | None = None
    plan: str | None = None
    status: SubscriptionStatus
    currency: Annotated[str, Field(min_length=3, max_length=3)]
    items: list[SubscriptionItem]

    @field_validator("currency")
    @classmethod
    def _upper_currency(cls, value: str) -> str:
        if not value.isalpha():
            raise ValueError("currency must be a three-letter ISO 4217 code")
        return value.upper()


class PaymentFailedData(_Model):
    invoice_id: str
    customer_id: str
    amount_due: PositiveInt
    attempt: PositiveInt
    decline_code: str


class InvoicePaidData(_Model):
    invoice_id: str
    customer_id: str
    amount_paid: MinorUnits


class _EventBase(_Model):
    id: NonEmpty
    workspace: NonEmpty
    source: BillingSource
    occurred_at: datetime

    @field_validator("occurred_at")
    @classmethod
    def _aware(cls, value: datetime) -> datetime:
        """Timestamps without an offset are taken to be UTC."""
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class SubscriptionCreated(_EventBase):
    type: Literal["subscription.created"]
    data: SubscriptionData


class SubscriptionUpdated(_EventBase):
    type: Literal["subscription.updated"]
    data: SubscriptionData


class SubscriptionCanceled(_EventBase):
    type: Literal["subscription.canceled"]
    data: SubscriptionData


class InvoicePaymentFailed(_EventBase):
    type: Literal["invoice.payment_failed"]
    data: PaymentFailedData


class InvoicePaid(_EventBase):
    type: Literal["invoice.paid"]
    data: InvoicePaidData


SubscriptionEvent = SubscriptionCreated | SubscriptionUpdated | SubscriptionCanceled
BillingEvent = Annotated[
    SubscriptionCreated | SubscriptionUpdated | SubscriptionCanceled | InvoicePaymentFailed | InvoicePaid,
    Field(discriminator="type"),
]

billing_event_adapter: TypeAdapter[BillingEvent] = TypeAdapter(BillingEvent)


def parse_event(payload: object) -> BillingEvent:
    """Validate a decoded JSON payload. Raises :class:`pydantic.ValidationError` when it is invalid."""
    return billing_event_adapter.validate_python(payload)
