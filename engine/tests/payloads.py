"""Billing-event payloads as a connector would send them."""

from __future__ import annotations

from typing import Any

WORKSPACE = "quillstack"


def subscription_event(
    event_id: str,
    customer: str,
    *,
    type_: str = "subscription.created",
    amount: int = 34900,
    quantity: int = 1,
    interval: str = "month",
    status: str = "active",
    occurred_at: str = "2026-01-15T12:00:00Z",
    plan: str | None = "Growth",
    name: str | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "subscriptionId": f"sub_{customer}",
        "customerId": customer,
        "status": status,
        "currency": "USD",
        "items": [{"priceId": "price_1", "unitAmount": amount, "quantity": quantity, "interval": interval}],
    }
    if plan is not None:
        data["plan"] = plan
    if name is not None:
        data["customerName"] = name
    return {
        "id": event_id,
        "workspace": WORKSPACE,
        "source": "stripe",
        "type": type_,
        "occurredAt": occurred_at,
        "data": data,
    }


def payment_failed_event(
    event_id: str,
    invoice: str,
    customer: str,
    *,
    attempt: int = 1,
    code: str = "generic_decline",
    amount: int = 34900,
    occurred_at: str = "2026-02-01T09:00:00Z",
) -> dict[str, Any]:
    return {
        "id": event_id,
        "workspace": WORKSPACE,
        "source": "stripe",
        "type": "invoice.payment_failed",
        "occurredAt": occurred_at,
        "data": {
            "invoiceId": invoice,
            "customerId": customer,
            "amountDue": amount,
            "attempt": attempt,
            "declineCode": code,
        },
    }


def invoice_paid_event(
    event_id: str, invoice: str, customer: str, *, occurred_at: str = "2026-02-03T09:00:00Z"
) -> dict[str, Any]:
    return {
        "id": event_id,
        "workspace": WORKSPACE,
        "source": "stripe",
        "type": "invoice.paid",
        "occurredAt": occurred_at,
        "data": {"invoiceId": invoice, "customerId": customer, "amountPaid": 34900},
    }
