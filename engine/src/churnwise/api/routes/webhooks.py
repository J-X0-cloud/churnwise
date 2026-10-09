"""``POST /api/webhooks/billing`` — normalised billing events from connectors.

401 on a bad signature, 400 on an invalid payload, 404 for an unknown workspace, 200 otherwise
(including duplicates, so the sender stops retrying).
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from churnwise.api import schemas as s
from churnwise.api.deps import SessionFactoryDep, SettingsDep
from churnwise.billing.events import parse_event
from churnwise.billing.ingest import ingest_event
from churnwise.billing.signature import HEADER, verify_signature

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])
log = logging.getLogger(__name__)

#: Deliveries larger than this are refused before any parsing.
MAX_BODY_BYTES = 256 * 1024


def _error(status: int, error: str, **extra: object) -> JSONResponse:
    return JSONResponse({"error": error, **extra}, status_code=status)


@router.post(
    "/billing",
    response_model=s.WebhookAccepted,
    response_model_exclude_none=True,
    responses={400: {}, 401: {}, 404: {}, 413: {}, 500: {}},
)
async def billing_webhook(
    request: Request, settings: SettingsDep, factory: SessionFactoryDep
) -> s.WebhookAccepted | JSONResponse:
    secret = settings.webhook_secret
    if not secret:
        return _error(500, "webhook_secret_not_configured")

    raw = await request.body()
    if len(raw) > MAX_BODY_BYTES:
        return _error(413, "payload_too_large")

    signature = verify_signature(raw, request.headers.get(HEADER), secret)
    if not signature.ok:
        return _error(401, "invalid_signature", reason=signature.reason)

    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _error(400, "invalid_json")

    try:
        event = parse_event(payload)
    except ValidationError as exc:
        issues = [
            {"path": [str(p) for p in err["loc"]], "message": err["msg"], "code": err["type"]}
            for err in exc.errors(include_url=False, include_input=False)
        ]
        return _error(400, "invalid_event", issues=issues)

    result = await run_in_threadpool(ingest_event, factory, event)
    if result.status == "unknown_workspace":
        return _error(404, "unknown_workspace")
    assert result.event_id is not None
    log.info("billing event %s %s (%s)", event.id, event.type, result.status)
    return s.WebhookAccepted(
        status=result.status,
        event_id=result.event_id,
        movement=(
            s.IngestMovementOut(type=result.movement.movement.value, amount=result.movement.amount)
            if result.movement
            else None
        ),
    )
