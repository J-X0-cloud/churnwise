"""Assemble API responses from the domain model.

Everything here is a pure function of the (immutable) sample model, so results are cached per process.
"""

from __future__ import annotations

import math
from datetime import datetime
from functools import cache

from churnwise import fixtures
from churnwise.api import schemas as s
from churnwise.domain import metrics, revenue, smoothing, survival
from churnwise.domain.cohorts import cohort_average, sample_cohorts
from churnwise.domain.dates import add_months, auto_month_label, long_date, long_month_year, month_label
from churnwise.domain.dunning import MAX_ATTEMPTS, DunningPlan, DunningStep, decline_label
from churnwise.domain.forecast import HORIZON, SCENARIOS, forecast, forecast_table
from churnwise.domain.formatting import MINUS, grouped, js_round, money, whole_dollars
from churnwise.domain.recovery import RecoveryAnalytics
from churnwise.domain.simulation import SAMPLE_WORKSPACE, RevenueModel, sample_model
from churnwise.domain.types import CohortMetric, MovementTotals, RangeKey, Scenario

#: The milestone the forecast panel counts down to.
FORECAST_TARGET = 1_000_000.0
COHORT_MONTHS = 12


def _model() -> RevenueModel:
    return sample_model()


def totals_out(totals: MovementTotals) -> s.MovementTotalsOut:
    return s.MovementTotalsOut(**totals.as_dict())


def kpis_out(kpis: list[metrics.Kpi]) -> list[s.KpiOut]:
    return [s.KpiOut.model_validate(k) for k in kpis]


def workspace_out() -> s.WorkspaceOut:
    model = _model()
    return s.WorkspaceOut(
        name=SAMPLE_WORKSPACE.name,
        slug=SAMPLE_WORKSPACE.slug,
        currency=SAMPLE_WORKSPACE.currency,
        sources=SAMPLE_WORKSPACE.sources_label,
        as_of=model.last_day,
        as_of_label=long_date(model.last_day),
    )


def range_definitions_out() -> list[s.RangeDefinitionOut]:
    return [s.RangeDefinitionOut.model_validate(d) for d in revenue.range_definitions(_model()).values()]


@cache
def range_view(key: RangeKey) -> s.RangeViewOut:
    model = _model()
    stats = revenue.range_stats(model, key)
    buckets = revenue.movement_buckets(model, key)
    totals = MovementTotals.sum([b.totals for b in buckets])
    return s.RangeViewOut(
        range=key,
        stats=s.RangeStatsOut.model_validate(stats),
        line=[s.ChartPointOut.model_validate(p) for p in metrics.mrr_line(model, stats)],
        label_every=metrics.MRR_LABEL_EVERY[key],
        buckets=[
            s.MovementBucketOut(
                label=b.label,
                start=b.start,
                end=b.end,
                net=b.net,
                ending_mrr=b.ending_mrr,
                **b.totals.as_dict(),
            )
            for b in buckets
        ],
        totals=totals_out(totals),
        gained=totals.gained,
        lost=totals.lost,
        quick_ratio=totals.quick_ratio,
        kpis=kpis_out(metrics.overview_kpis(model, key)),
    )


def range_line_points(key: RangeKey) -> tuple[revenue.LinePoint, ...]:
    """The raw (date, MRR) samples behind a range's headline line."""
    return revenue.range_stats(_model(), key).line


def plans_out() -> list[s.PlanRowOut]:
    return [s.PlanRowOut.model_validate(p) for p in metrics.plan_breakdown(_model())]


def accounts_out() -> list[s.AccountOut]:
    return [s.AccountOut.model_validate(a) for a in metrics.account_rows()]


def signed_whole_dollars(amount: float) -> str:
    return f"{'+' if amount >= 0 else MINUS}${grouped(js_round(abs(amount)))}"


def activity_out() -> list[s.ActivityOut]:
    return [
        s.ActivityOut(
            customer=a.customer,
            detail=a.detail,
            kind=a.kind,
            amount=a.amount,
            amount_label=signed_whole_dollars(a.amount),
            when=a.when,
        )
        for a in fixtures.activity()
    ]


def cohorts_out() -> list[s.CohortOut]:
    return [s.CohortOut.model_validate(c) for c in sample_cohorts()]


@cache
def retention_view() -> s.RetentionViewOut:
    model = _model()
    cohorts = sample_cohorts()
    return s.RetentionViewOut(
        kpis=kpis_out(metrics.retention_kpis(model)),
        series=s.RetentionSeriesOut.model_validate(metrics.retention_series(model)),
        cohorts=cohorts_out(),
        averages=s.CohortAveragesOut(
            net=cohort_average(cohorts, CohortMetric.NET, COHORT_MONTHS),
            logo=cohort_average(cohorts, CohortMetric.LOGO, COHORT_MONTHS),
        ),
        cancellation_reasons=list(fixtures.cancellation_reasons()),
    )


def customers_view() -> s.CustomersViewOut:
    model = _model()
    return s.CustomersViewOut(kpis=kpis_out(metrics.customer_kpis(model)), total=model[model.last].customers)


@cache
def scenario_out(key: Scenario) -> s.ScenarioOut:
    model = _model()
    definition = next(d for d in SCENARIOS if d.key is key)
    result = forecast(model, key)
    return s.ScenarioOut(
        key=key,
        label=definition.label,
        multiplier=definition.multiplier,
        assumptions=s.AssumptionsOut.model_validate(definition.assumptions),
        forecast=s.ForecastOut.model_validate(result),
        table=[s.ForecastRowOut.model_validate(r) for r in forecast_table(result)],
        end=result.end,
        months_to_target=result.months_to_target(FORECAST_TARGET),
    )


@cache
def forecast_view() -> s.ForecastViewOut:
    model = _model()
    horizon_end = add_months(model.months[-1].month, HORIZON)
    return s.ForecastViewOut(
        scenarios=[scenario_out(d.key) for d in SCENARIOS],
        current_mrr=model[model.last].mrr,
        horizon_months=HORIZON,
        horizon_label=long_month_year(horizon_end),
        horizon_short_label=f"{month_label(horizon_end)} {horizon_end.year}",
        target=FORECAST_TARGET,
    )


@cache
def recovery_view() -> s.RecoveryViewOut:
    analytics = RecoveryAnalytics(_model())
    funnel = analytics.funnel()
    return s.RecoveryViewOut(
        kpis=kpis_out(metrics.recovery_kpis(analytics)),
        funnel=s.FunnelOut.model_validate(funnel),
        months=[s.MonthlyRecoveryOut.model_validate(m) for m in analytics.by_month(12)],
        decline_reasons=list(fixtures.decline_reasons()),
        open_failed=[
            s.OpenFailedOut(
                customer=p.customer,
                amount=p.amount,
                reason=decline_label(p.decline_code),
                decline_code=p.decline_code,
                attempts=p.attempts,
                next_retry=p.next_retry,
                step=p.step,
            )
            for p in fixtures.open_failed_payments()
        ],
        max_attempts=MAX_ATTEMPTS,
    )


def initials(name: str) -> str:
    words = [w for w in name.replace("&", " ").split() if w]
    return "".join(w[0] for w in words[:2]).upper()


def profile_out() -> s.ProfileOut:
    p = fixtures.profile()
    return s.ProfileOut(
        name=p.name,
        initials=initials(p.name),
        plan=p.plan,
        status=p.status,
        stats=[
            s.ProfileStatOut(label="MRR", value=whole_dollars(p.mrr)),
            s.ProfileStatOut(label="Lifetime revenue", value=money(p.lifetime_revenue)),
            s.ProfileStatOut(label="Health", value=f"{p.health} / 100"),
        ],
        timeline=[s.TimelineEntryOut.model_validate(e) for e in p.timeline],
    )


@cache
def dashboard() -> s.DashboardOut:
    return s.DashboardOut(
        workspace=workspace_out(),
        ranges=range_definitions_out(),
        views={key: range_view(key) for key in RangeKey},
        plans=plans_out(),
        accounts=accounts_out(),
        activity=activity_out(),
        retention=retention_view(),
        customers=customers_view(),
        forecast=forecast_view(),
        recovery=recovery_view(),
        profile=profile_out(),
    )


# ------------------------------------------------------------------ statistical forecasts


def smoothing_forecast(horizon: int, confidence: float, holdout: int = 3) -> s.SmoothingOut:
    """Holt's linear trend fitted to month-end MRR across the whole history."""
    model = _model()
    windows = model.months
    history = [model.month_end_mrr(w) for w in windows]
    fit = smoothing.holt(history)
    mape = smoothing.backtest_holt(history, holdout) if len(history) > holdout + 6 else None
    last_month = windows[-1].month
    return s.SmoothingOut(
        method="holt",
        alpha=fit.alpha,
        beta=fit.beta,
        sigma=fit.sigma,
        confidence=confidence,
        backtest_mape=mape,
        history=[
            s.ForecastPointOut(label=auto_month_label(w.month), value=v)
            for w, v in zip(windows, history, strict=True)
        ],
        fitted=list(fit.fitted),
        forecast=[
            s.PredictionOut(
                step=p.step,
                label=auto_month_label(add_months(last_month, p.step)),
                value=p.value,
                low=p.low,
                high=p.high,
            )
            for p in fit.forecast(horizon, confidence)
        ],
    )


def churn_forecast(horizon: int) -> s.ChurnForecastOut:
    """Kaplan-Meier survival of the sample cohorts, a constant-hazard fit, and the churn it implies for
    today's customer base over the horizon."""
    model = _model()
    curve = survival.kaplan_meier(survival.lifetimes_from_cohorts(sample_cohorts()))
    hazard = survival.fit_constant_hazard(curve)
    stats = revenue.range_stats(model, RangeKey.M12)
    revenue_churn = stats.churn_rate / 100
    last = model[model.last]
    last_month = model.months[-1].month
    projection = survival.project_churn(last.customers, last.mrr, hazard, revenue_churn, horizon)
    return s.ChurnForecastOut(
        subjects=curve.subjects,
        events=curve.events,
        curve=[s.SurvivalPointOut.model_validate(p) for p in curve.points],
        median_lifetime_months=curve.median(),
        hazard_rate=hazard.rate,
        monthly_logo_churn=hazard.monthly_churn * 100,
        hazard_r_squared=hazard.r_squared,
        modelled_median_lifetime=hazard.median_lifetime if math.isfinite(hazard.median_lifetime) else None,
        revenue_churn_rate=stats.churn_rate,
        projection=[
            s.ChurnProjectionOut(
                month=p.month,
                label=auto_month_label(add_months(last_month, p.month)),
                customers=p.customers,
                churned_customers=p.churned_customers,
                churned_mrr=p.churned_mrr,
                retained_mrr=p.retained_mrr,
            )
            for p in projection
        ],
    )


def dunning_plan_out(plan: DunningPlan, now: datetime) -> s.DunningPlanOut:
    def step(item: DunningStep) -> s.DunningStepOut:
        return s.DunningStepOut(
            at=item.at,
            kind=item.kind.value,
            description=item.description,
            attempt=item.attempt,
            template=item.template,
            due=item.at <= now,
        )

    upcoming = plan.next_step(now)
    return s.DunningPlanOut(
        decline_code=plan.decline_code,
        decline_label=decline_label(plan.decline_code),
        category=plan.category.value,
        amount=plan.amount,
        first_failed_at=plan.first_failed_at,
        closes_at=plan.closes_at,
        retries=plan.retries,
        next_step=step(upcoming) if upcoming else None,
        steps=[step(item) for item in plan.steps],
    )
