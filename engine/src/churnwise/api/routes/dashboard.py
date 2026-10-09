"""The sample workspace's dashboard, as one snapshot or tab by tab."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from churnwise.api import schemas as s
from churnwise.api import views
from churnwise.domain.cohorts import cohort_average, sample_cohorts
from churnwise.domain.types import CohortMetric

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard", response_model=s.DashboardOut, response_model_exclude_none=True)
def get_dashboard() -> s.DashboardOut:
    """Every tab of the demo dashboard for every range and scenario, in one response. The web app renders
    from this snapshot so switching ranges and tabs needs no further requests."""
    return views.dashboard()


@router.get("/workspace", response_model=s.WorkspaceOut)
def get_workspace() -> s.WorkspaceOut:
    return views.workspace_out()


@router.get("/plans", response_model=list[s.PlanRowOut])
def get_plans() -> list[s.PlanRowOut]:
    return views.plans_out()


@router.get("/customers", response_model=s.CustomersViewOut, response_model_exclude_none=True)
def get_customers() -> s.CustomersViewOut:
    return views.customers_view()


@router.get("/accounts", response_model=list[s.AccountOut])
def get_accounts(limit: Annotated[int | None, Query(ge=1, le=100)] = None) -> list[s.AccountOut]:
    """Largest and most-moved accounts, highest MRR movement first."""
    rows = views.accounts_out()
    return rows[:limit] if limit else rows


@router.get("/activity", response_model=list[s.ActivityOut])
def get_activity() -> list[s.ActivityOut]:
    return views.activity_out()


@router.get("/retention", response_model=s.RetentionViewOut, response_model_exclude_none=True)
def get_retention() -> s.RetentionViewOut:
    return views.retention_view()


@router.get("/cohorts", response_model=s.CohortsOut)
def get_cohorts(
    metric: Annotated[CohortMetric, Query()] = CohortMetric.NET,
    months: Annotated[int, Query(ge=1, le=36)] = 12,
) -> s.CohortsOut:
    """The cohort heat map for one metric, plus its cohort-average row."""
    cohorts = sample_cohorts()
    return s.CohortsOut(
        metric=metric,
        cohorts=[
            s.CohortRowOut(
                label=c.label,
                customers=c.customers,
                start_mrr=c.start_mrr,
                values=list(c.series(metric))[:months],
            )
            for c in cohorts
        ],
        average=cohort_average(cohorts, metric, months),
    )


@router.get("/profile", response_model=s.ProfileOut)
def get_profile() -> s.ProfileOut:
    return views.profile_out()
