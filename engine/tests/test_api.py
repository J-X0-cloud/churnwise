from __future__ import annotations

import time
from typing import Any

import pytest
from fastapi.testclient import TestClient

from churnwise.billing.signature import sign
from churnwise.config import Settings
from churnwise.domain.types import RangeKey
from churnwise.main import create_app
from tests.conftest import SECRET
from tests.payloads import invoice_paid_event, payment_failed_event, subscription_event


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/health/ready").json() == {"status": "ok", "database": "ok"}


# ------------------------------------------------------------------ dashboard snapshot


@pytest.fixture(scope="module")
def dashboard() -> dict[str, Any]:
    with TestClient(create_app(Settings(database_url="sqlite://"))) as client:
        response = client.get("/api/dashboard")
        assert response.status_code == 200
        return response.json()


def test_dashboard_has_every_tab(dashboard):
    assert set(dashboard) == {
        "workspace",
        "ranges",
        "views",
        "plans",
        "accounts",
        "activity",
        "retention",
        "customers",
        "forecast",
        "recovery",
        "profile",
    }
    assert set(dashboard["views"]) == {r.value for r in RangeKey}
    assert dashboard["workspace"] == {
        "name": "Quillstack",
        "slug": "quillstack",
        "currency": "USD",
        "sources": "Stripe · Chargebee · HubSpot",
        "asOf": "2026-09-24",
        "asOfLabel": "Sep 24, 2026",
    }


def test_dashboard_matches_the_typescript_numbers(dashboard, golden):
    view = dashboard["views"]["12m"]
    assert [k["value"] for k in view["kpis"]] == [k["value"] for k in golden["ranges"]["12m"]["kpis"]]
    assert view["stats"]["mrr"] == pytest.approx(golden["dailyLast"]["mrr"])
    assert view["quickRatio"] == pytest.approx(golden["ranges"]["12m"]["quick"])
    assert view["labelEvery"] == 1
    assert len(view["buckets"]) == 12
    assert view["buckets"][0]["endingMrr"] > 0
    assert view["gained"] - view["lost"] == pytest.approx(sum(b["net"] for b in view["buckets"]))


def test_dashboard_uses_camel_case_and_semantic_tones(dashboard):
    kpi = dashboard["views"]["30d"]["kpis"][1]
    assert kpi["sparkTone"] == "mint"
    assert "spark_tone" not in kpi
    assert [p["tone"] for p in dashboard["plans"]] == ["starter", "mint", "brand", "brand_dark"]
    assert dashboard["recovery"]["funnel"]["items"][0]["key"] == "failed"


def test_dashboard_tabs(dashboard):
    assert len(dashboard["accounts"]) == 12 and len(dashboard["accounts"][0]["history"]) == 12
    assert dashboard["activity"][2]["amountLabel"] == "−$349"
    assert dashboard["activity"][0]["amountLabel"] == "+$841"
    retention = dashboard["retention"]
    assert len(retention["cohorts"]) == 12 and len(retention["averages"]["net"]) == 12
    assert retention["cancellationReasons"][0] == ["Budget cuts", 26]
    forecast = dashboard["forecast"]
    assert forecast["horizonLabel"] == "September 2027"
    assert forecast["horizonShortLabel"] == "Sep 2027"
    assert [s["key"] for s in forecast["scenarios"]] == ["conservative", "base", "stretch"]
    assert forecast["scenarios"][1]["monthsToTarget"] == 7
    recovery = dashboard["recovery"]
    assert recovery["maxAttempts"] == 4
    assert recovery["openFailed"][0]["reason"] == "Insufficient funds"
    assert dashboard["profile"]["initials"] == "HP"
    assert dashboard["profile"]["stats"] == [
        {"label": "MRR", "value": "$2,380"},
        {"label": "Lifetime revenue", "value": "$48.6k"},
        {"label": "Health", "value": "92 / 100"},
    ]


def test_tab_endpoints(client):
    assert client.get("/api/ranges/90d").json()["range"] == "90d"
    assert client.get("/api/ranges/1y").status_code == 400
    assert len(client.get("/api/accounts?limit=6").json()) == 6
    assert client.get("/api/accounts?limit=0").status_code == 400
    assert len(client.get("/api/plans").json()) == 4
    assert client.get("/api/customers").json()["kpis"][0]["label"] == "Paying customers"
    assert len(client.get("/api/activity").json()) == 6
    assert client.get("/api/profile").json()["name"] == "Harbor & Pine Studio"
    assert client.get("/api/workspace").json()["slug"] == "quillstack"
    cohorts = client.get("/api/cohorts?metric=logo&months=6").json()
    assert cohorts["metric"] == "logo"
    assert all(len(c["values"]) <= 6 for c in cohorts["cohorts"])
    assert len(cohorts["average"]) == 6


# ------------------------------------------------------------------ /api/metrics (same shape as before)


def test_metrics_defaults_to_twelve_months(client, golden):
    body = client.get("/api/metrics").json()
    assert body["range"] == "12m"
    assert "movements" not in body
    assert body["metrics"]["netNew"] == pytest.approx(golden["ranges"]["12m"]["stats"]["netNew"])
    assert body["metrics"]["quickRatio"] == pytest.approx(golden["ranges"]["12m"]["quick"])
    assert body["mrrSeries"][-1] == {"date": "2026-09-24", "mrr": round(golden["dailyLast"]["mrr"], 2)}


@pytest.mark.parametrize("flag", ["true", "1", "YES", "on"])
def test_metrics_with_movements(client, flag):
    body = client.get(f"/api/metrics?range=30d&movements={flag}").json()
    assert len(body["movements"]) == 30
    assert set(body["movements"][0]) == {
        "period",
        "new",
        "expansion",
        "reactivation",
        "contraction",
        "churn",
        "net",
    }


def test_metrics_validation_errors(client):
    response = client.get("/api/metrics?range=7d&movements=perhaps")
    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "invalid_query"
    assert set(body["issues"]) == {"range", "movements"}
    assert client.get("/api/metrics?movements=off").status_code == 200


# ------------------------------------------------------------------ forecasting and recovery


def test_forecast_endpoints(client):
    view = client.get("/api/forecast").json()
    assert view["currentMrr"] > 800_000
    base = client.get("/api/forecast/scenarios/base").json()
    assert base == view["scenarios"][1]
    assert client.get("/api/forecast/scenarios/moonshot").status_code == 400

    smoothing = client.get("/api/forecast/smoothing?horizon=6&confidence=0.9").json()
    assert smoothing["method"] == "holt"
    assert len(smoothing["forecast"]) == 6
    assert len(smoothing["history"]) == len(smoothing["fitted"]) == 24
    assert smoothing["backtestMape"] < 2
    first = smoothing["forecast"][0]
    assert first["low"] < first["value"] < first["high"]
    assert client.get("/api/forecast/smoothing?confidence=1.2").status_code == 400

    churn = client.get("/api/forecast/churn?horizon=24").json()
    assert churn["subjects"] > churn["events"] > 0
    assert len(churn["projection"]) == 24
    assert 0 < churn["monthlyLogoChurn"] < 5
    assert churn["curve"][0]["survival"] > churn["curve"][-1]["survival"]


def test_recovery_endpoints(client):
    view = client.get("/api/recovery").json()
    assert view["kpis"][2]["value"] == "$5.07k"
    assert len(view["openFailed"]) == 6
    plan = client.post(
        "/api/recovery/plan",
        json={
            "failedAt": "2026-09-24T12:00:00Z",
            "declineCode": "expired_card",
            "amount": 698,
            "now": "2026-09-26T00:00:00Z",
        },
    ).json()
    assert plan["category"] == "hard"
    assert plan["steps"][0]["kind"] == "card_update_request"
    assert plan["steps"][0]["due"] is True
    assert plan["nextStep"]["template"] == "update_card"
    assert plan["retries"] == 0
    bad = client.post(
        "/api/recovery/plan", json={"failedAt": "2026-09-24T12:00:00Z", "declineCode": "x", "amount": -5}
    )
    assert bad.status_code == 400
    assert bad.json()["error"] == "invalid_request"


# ------------------------------------------------------------------ webhook


def test_webhook_end_to_end(post_event, client):
    response = post_event(subscription_event("evt_1", "cus_1", amount=837600, interval="year"))
    assert response.status_code == 200
    body = response.json()
    assert body["received"] is True and body["status"] == "processed"
    assert body["movement"] == {"type": "new", "amount": 698.0}

    again = post_event(subscription_event("evt_1", "cus_1", amount=837600, interval="year"))
    assert again.status_code == 200
    assert again.json()["status"] == "duplicate"
    assert again.json()["eventId"] == body["eventId"]


def test_webhook_rejections(post_event, client):
    event = subscription_event("evt_2", "cus_2")
    assert post_event(event, secret="wrong").json() == {"error": "invalid_signature", "reason": "mismatch"}
    assert post_event(event, timestamp=int(time.time()) - 3600).json()["reason"] == "expired"
    missing = client.post("/api/webhooks/billing", content="{}")
    assert (missing.status_code, missing.json()["reason"]) == (401, "missing")

    bad = dict(event, type="subscription.exploded")
    response = post_event(bad)
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_event"
    assert response.json()["issues"]

    unknown = dict(event, workspace="elsewhere")
    assert post_event(unknown).status_code == 404


def test_webhook_rejects_invalid_json(client):
    body = "{not json"
    response = client.post(
        "/api/webhooks/billing",
        content=body,
        headers={"x-churnwise-signature": sign(body, SECRET, int(time.time()))},
    )
    assert (response.status_code, response.json()) == (400, {"error": "invalid_json"})


def test_webhook_without_a_secret_is_disabled(engine):
    with TestClient(create_app(Settings(database_url="sqlite://"), engine=engine)) as client:
        response = client.post("/api/webhooks/billing", content="{}")
    assert response.status_code == 500
    assert response.json() == {"error": "webhook_secret_not_configured"}


# ------------------------------------------------------------------ workspace analytics


def _seed(post_event) -> None:
    events = [
        subscription_event("e1", "cus_a", amount=10000, occurred_at="2025-09-10T12:00:00Z"),
        subscription_event("e2", "cus_b", amount=20000, occurred_at="2025-09-20T12:00:00Z"),
        subscription_event(
            "e3", "cus_a", type_="subscription.updated", amount=15000, occurred_at="2026-02-01T12:00:00Z"
        ),
        subscription_event(
            "e4", "cus_b", type_="subscription.canceled", amount=20000, occurred_at="2026-03-01T12:00:00Z"
        ),
        subscription_event("e5", "cus_c", amount=5000, occurred_at="2026-04-01T12:00:00Z"),
        payment_failed_event(
            "f1", "in_1", "cus_c", code="insufficient_funds", amount=5000, occurred_at="2026-05-01T12:00:00Z"
        ),
        invoice_paid_event("p1", "in_1", "cus_c", occurred_at="2026-05-15T14:00:00Z"),
        payment_failed_event(
            "f2", "in_2", "cus_a", code="expired_card", amount=15000, occurred_at="2026-06-01T12:00:00Z"
        ),
    ]
    for event in events:
        assert post_event(event).status_code == 200


def test_workspace_summary(post_event, client):
    _seed(post_event)
    body = client.get("/api/workspaces/quillstack/summary?asOf=2026-09-30").json()
    assert body["mrr"] == pytest.approx(200)
    assert body["customers"] == 2
    retention = body["retention"]
    # Base on 2025-09-30: a=100, b=200. On 2026-09-30: a=150, b=0.
    assert retention["baseMrr"] == pytest.approx(300)
    assert retention["nrr"] == pytest.approx(50)
    assert retention["grr"] == pytest.approx(100 / 3)
    assert retention["logoRetention"] == pytest.approx(50)
    bridge = body["bridge"]
    assert len(bridge) == 12
    assert all(row["opening"] + row["net"] == pytest.approx(row["closing"]) for row in bridge)
    # a and b signed up in September 2025, before the twelve-month window; only c's cohort is in it.
    (cohort,) = body["cohorts"]
    assert (cohort["label"], cohort["customers"], cohort["startMrr"]) == ("Apr 2026", 1, 50)
    assert cohort["logo"] == [100] * 6


def test_workspace_movements_and_failed_payments(post_event, client):
    _seed(post_event)
    movements = client.get("/api/workspaces/quillstack/movements").json()
    assert [m["movement"] for m in movements] == ["new", "new", "expansion", "churn", "new"]
    assert client.get("/api/workspaces/quillstack/movements?limit=2").json() == movements[:2]

    payments = client.get("/api/workspaces/quillstack/failed-payments").json()
    assert payments["count"] == 2
    assert payments["recovered"] == pytest.approx(50)
    assert payments["open"] == pytest.approx(150)
    assert payments["medianDaysToRecover"] == pytest.approx(14 + 2 / 24)
    open_only = client.get("/api/workspaces/quillstack/failed-payments?status=open").json()
    assert [p["invoiceId"] for p in open_only["payments"]] == ["in_2"]
    assert open_only["payments"][0]["nextRetryAt"] is None


def test_unknown_workspace_is_404(client):
    response = client.get("/api/workspaces/nobody/summary")
    assert (response.status_code, response.json()) == (404, {"error": "unknown_workspace"})


def test_workspace_endpoints_require_the_api_token_when_set(engine, factory):
    settings = Settings(database_url="sqlite://", api_token="s3cret")
    with TestClient(create_app(settings, engine=engine)) as client:
        assert client.get("/api/workspaces/quillstack/movements").status_code == 401
        wrong = client.get("/api/workspaces/quillstack/movements", headers={"Authorization": "Bearer nope"})
        assert wrong.status_code == 401
        ok = client.get("/api/workspaces/quillstack/movements", headers={"Authorization": "Bearer s3cret"})
        assert ok.status_code == 200
        # The sample dashboard stays public.
        assert client.get("/api/dashboard").status_code == 200
