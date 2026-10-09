"""Event-store analytics for a workspace: MRR, the monthly MRR bridge, NRR/GRR, cohorts, the movement
ledger and failed payments, all rebuilt from ingested billing events."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from churnwise.api import schemas as s
from churnwise.api.deps import SessionDep, require_api_token
from churnwise.db import models, repository
from churnwise.domain.dates import add_months, auto_month_label, month_key
from churnwise.domain.ledger import Ledger
from churnwise.domain.recovery import PaymentStatus, summarize_failed_payments

router = APIRouter(
    prefix="/api/workspaces/{slug}", tags=["workspaces"], dependencies=[Depends(require_api_token)]
)


def _workspace(session: SessionDep, slug: str) -> models.Workspace:
    workspace = repository.get_workspace(session, slug)
    if workspace is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="unknown_workspace")
    return workspace


@router.get("/summary", response_model=s.WorkspaceSummaryOut)
def summary(
    slug: str,
    session: SessionDep,
    as_of: Annotated[date | None, Query(alias="asOf")] = None,
    months: Annotated[int, Query(ge=1, le=36)] = 12,
) -> s.WorkspaceSummaryOut:
    workspace = _workspace(session, slug)
    ledger = Ledger(repository.movement_records(session, workspace.id))
    day = as_of or datetime.now(UTC).date()
    first_month = month_key(add_months(day, -(months - 1)))
    retention = ledger.trailing_retention(day)
    customers, mrr = repository.customer_counts(session, workspace.id)
    if as_of is not None:
        snapshot = ledger.mrr_by_customer(datetime.combine(day, datetime.max.time(), tzinfo=UTC))
        customers, mrr = len(snapshot), sum(snapshot.values())
    return s.WorkspaceSummaryOut(
        workspace=workspace.slug,
        as_of=day,
        mrr=mrr,
        customers=customers,
        retention=s.RetentionResultOut(
            start=retention.start,
            end=retention.end,
            base_customers=retention.base_customers,
            base_mrr=retention.base_mrr,
            retained_mrr=retention.retained_mrr,
            gross_retained_mrr=retention.gross_retained_mrr,
            nrr=retention.nrr,
            grr=retention.grr,
            logo_retention=retention.logo_retention,
        ),
        bridge=[
            s.MonthlyBridgeOut(
                month=row.month,
                label=auto_month_label(row.month),
                opening=row.opening,
                totals=s.MovementTotalsOut(**row.totals.as_dict()),
                net=row.totals.net,
                closing=row.closing,
            )
            for row in ledger.monthly_bridge(first_month, day)
        ],
        cohorts=[s.CohortOut.model_validate(c) for c in ledger.cohorts(day, first_month)],
    )


@router.get("/movements", response_model=list[s.MovementOut])
def movements(
    slug: str,
    session: SessionDep,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: Annotated[int, Query(ge=1, le=5000)] = 500,
) -> list[s.MovementOut]:
    """The MRR movement ledger, oldest first."""
    workspace = _workspace(session, slug)
    records = repository.movement_records(session, workspace.id, since=since, until=until)
    return [
        s.MovementOut(
            customer_id=r.customer_id,
            movement=r.movement.value,
            amount=r.amount,
            mrr_before=r.mrr_before,
            mrr_after=r.mrr_after,
            occurred_at=r.occurred_at,
        )
        for r in records[:limit]
    ]


@router.get("/failed-payments", response_model=s.FailedPaymentsOut)
def failed_payments(
    slug: str,
    session: SessionDep,
    status_filter: Annotated[list[PaymentStatus] | None, Query(alias="status")] = None,
) -> s.FailedPaymentsOut:
    """Failed payments with recovery totals, time to recover and a per-decline-code breakdown."""
    workspace = _workspace(session, slug)
    records = repository.failed_payment_records(session, workspace.id, status_filter)
    retries = repository.next_retries(session, workspace.id)
    summary = summarize_failed_payments(records)
    return s.FailedPaymentsOut(
        count=summary.count,
        failed=summary.failed,
        recovered=summary.recovered,
        open=summary.open,
        lost=summary.lost,
        resolved_rate=summary.resolved_rate,
        median_days_to_recover=summary.median_days_to_recover,
        attempts_to_recover=summary.attempts_to_recover,
        declines=[s.DeclineBreakdownOut.model_validate(d) for d in summary.declines],
        payments=[
            s.FailedPaymentOut(
                invoice_id=r.invoice_id,
                customer_id=r.customer_id,
                amount=r.amount,
                decline_code=r.decline_code,
                attempts=r.attempts,
                status=r.status.value,
                failed_at=r.failed_at,
                recovered_at=r.recovered_at,
                next_retry_at=retries.get(r.invoice_id),
            )
            for r in records
        ],
    )
