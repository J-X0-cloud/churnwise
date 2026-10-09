"""Failed-payment recovery: reporting for the sample workspace and dunning plans for any failure."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

from churnwise.api import schemas as s
from churnwise.api import views
from churnwise.domain.dunning import plan_dunning

router = APIRouter(prefix="/api/recovery", tags=["recovery"])


@router.get("", response_model=s.RecoveryViewOut, response_model_exclude_none=True)
def get_recovery() -> s.RecoveryViewOut:
    return views.recovery_view()


def _aware(moment: datetime) -> datetime:
    return moment.replace(tzinfo=UTC) if moment.tzinfo is None else moment.astimezone(UTC)


@router.post("/plan", response_model=s.DunningPlanOut)
def create_plan(body: s.DunningPlanRequest) -> s.DunningPlanOut:
    """Every recovery step for a failed charge: retries timed to its decline code, reminder emails, the
    in-app banner, escalation for high-value invoices, the access pause and the write-off. Steps at or
    before ``now`` (default: the current time) are marked as due."""
    plan = plan_dunning(_aware(body.failed_at), body.decline_code, body.amount)
    now = _aware(body.now) if body.now else datetime.now(UTC)
    return views.dunning_plan_out(plan, now)
