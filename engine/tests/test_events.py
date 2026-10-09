from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from churnwise.billing.events import (
    InvoicePaid,
    InvoicePaymentFailed,
    SubscriptionCreated,
    SubscriptionStatus,
    parse_event,
)
from churnwise.domain.movements import BillingInterval
from tests.payloads import invoice_paid_event, payment_failed_event, subscription_event


def test_readme_example_parses():
    event = parse_event(
        {
            "id": "evt_1",
            "workspace": "quillstack",
            "source": "stripe",
            "type": "subscription.created",
            "occurredAt": "2026-09-24T12:00:00Z",
            "data": {
                "subscriptionId": "sub_1",
                "customerId": "cus_1",
                "customerName": "Northgate Tutors",
                "plan": "Growth",
                "status": "active",
                "currency": "usd",
                "items": [
                    {
                        "priceId": "price_growth_annual",
                        "unitAmount": 837600,
                        "quantity": 1,
                        "interval": "year",
                    }
                ],
            },
        }
    )
    assert isinstance(event, SubscriptionCreated)
    assert event.occurred_at == datetime(2026, 9, 24, 12, tzinfo=UTC)
    assert event.data.currency == "USD"
    assert event.data.status is SubscriptionStatus.ACTIVE
    item = event.data.items[0]
    assert (item.interval, item.interval_count, item.unit_amount) == (BillingInterval.YEAR, 1, 837600)


def test_invoice_events_parse_to_their_own_types():
    assert isinstance(parse_event(payment_failed_event("e1", "in_1", "cus_1")), InvoicePaymentFailed)
    assert isinstance(parse_event(invoice_paid_event("e2", "in_1", "cus_1")), InvoicePaid)


def test_defaults_and_naive_timestamps():
    raw = subscription_event("e", "c", occurred_at="2026-01-15T12:00:00")
    del raw["data"]["items"][0]["quantity"]
    event = parse_event(raw)
    assert event.data.items[0].quantity == 1
    assert event.occurred_at.tzinfo is UTC


def test_offsets_are_normalised_to_utc():
    event = parse_event(subscription_event("e", "c", occurred_at="2026-01-15T12:00:00-08:00"))
    assert event.occurred_at == datetime(2026, 1, 15, 20, tzinfo=UTC)


def _mutate(path: list[str | int], value: object) -> dict:
    raw = subscription_event("evt", "cus")
    target = raw
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    return raw


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (["type"], "subscription.exploded"),
        (["source"], "venmo"),
        (["id"], ""),
        (["workspace"], ""),
        (["occurredAt"], "yesterday"),
        (["data", "currency"], "US"),
        (["data", "currency"], "U$D"),
        (["data", "status"], "zombie"),
        (["data", "items", 0, "unitAmount"], -1),
        (["data", "items", 0, "unitAmount"], 12.5),
        (["data", "items", 0, "unitAmount"], "100"),
        (["data", "items", 0, "quantity"], 0),
        (["data", "items", 0, "interval"], "fortnight"),
    ],
)
def test_invalid_payloads_are_rejected(path, value):
    with pytest.raises(ValidationError):
        parse_event(_mutate(path, value))


def test_payment_failed_requires_positive_amount_and_attempt():
    with pytest.raises(ValidationError):
        parse_event(payment_failed_event("e", "in", "c", amount=0))
    with pytest.raises(ValidationError):
        parse_event(payment_failed_event("e", "in", "c", attempt=0))


def test_missing_data_is_rejected():
    raw = subscription_event("evt", "cus")
    del raw["data"]["customerId"]
    with pytest.raises(ValidationError):
        parse_event(raw)
