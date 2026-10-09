"""Response and request models. Field names are camelCase on the wire, snake_case in Python."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from churnwise.domain.types import Bucket, CohortMetric, RangeKey, Scenario, Tone


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class ErrorBody(ApiModel):
    error: str


# ------------------------------------------------------------------ shared pieces


class DeltaOut(ApiModel):
    text: str
    tone: Literal["good", "bad", "neutral"]
    arrow: Literal["up", "down"] | None = None


class KpiOut(ApiModel):
    label: str
    value: str
    delta: DeltaOut
    unit: str | None = None
    hint: str | None = None
    spark: list[float] | None = None
    spark_tone: Tone | None = None


class ChartPointOut(ApiModel):
    label: str
    value: float
    tip: str | None = None


class MovementTotalsOut(ApiModel):
    new: float
    expansion: float
    reactivation: float
    contraction: float
    churn: float


class RangeDefinitionOut(ApiModel):
    key: RangeKey
    label: str
    short: str
    bucket: Bucket
    comparison_note: str


class WorkspaceOut(ApiModel):
    name: str
    slug: str
    currency: str
    sources: str
    as_of: date
    as_of_label: str


# ------------------------------------------------------------------ revenue


class MovementBucketOut(MovementTotalsOut):
    label: str
    start: int
    end: int
    net: float
    ending_mrr: float


class RangeStatsOut(ApiModel):
    range: RangeKey
    label: str
    start: int
    mrr: float
    mrr_start: float
    net_new: float
    net_new_prior: float | None
    churn_rate: float
    churn_rate_prior: float | None
    nrr: float
    nrr_start: float
    customers: float
    customers_start: float
    arpa: float
    arpa_start: float
    ltv: float
    ltv_start: float
    recovered: float
    recovered_prior: float | None
    recovery_rate: float
    failed: float


class RangeViewOut(ApiModel):
    range: RangeKey
    stats: RangeStatsOut
    line: list[ChartPointOut]
    label_every: int
    buckets: list[MovementBucketOut]
    totals: MovementTotalsOut
    gained: float
    lost: float
    quick_ratio: float
    kpis: list[KpiOut]


class PlanRowOut(ApiModel):
    name: str
    price: str
    tone: Tone
    mrr: float
    share: float
    customers: float
    churn: float


class AccountOut(ApiModel):
    name: str
    plan: str
    mrr: float
    trend: Literal["up", "flat", "down"]
    status: str
    health: int
    since: str
    owner: str
    history: list[float]


class ActivityOut(ApiModel):
    customer: str
    detail: str
    kind: str
    amount: float
    amount_label: str
    when: str


class CohortOut(ApiModel):
    month: date
    label: str
    customers: int
    start_mrr: float
    net: list[float]
    logo: list[float]


class CohortAveragesOut(ApiModel):
    net: list[float | None]
    logo: list[float | None]


class CohortRowOut(ApiModel):
    label: str
    customers: int
    start_mrr: float
    values: list[float]


class CohortsOut(ApiModel):
    metric: CohortMetric
    cohorts: list[CohortRowOut]
    average: list[float | None]


class RetentionSeriesOut(ApiModel):
    labels: list[str]
    nrr: list[float]
    grr: list[float]


class RetentionViewOut(ApiModel):
    kpis: list[KpiOut]
    series: RetentionSeriesOut
    cohorts: list[CohortOut]
    averages: CohortAveragesOut
    cancellation_reasons: list[tuple[str, float]]


class CustomersViewOut(ApiModel):
    kpis: list[KpiOut]
    total: float


class ProfileStatOut(ApiModel):
    label: str
    value: str


class TimelineEntryOut(ApiModel):
    date: str
    title: str
    detail: str
    tone: Tone


class ProfileOut(ApiModel):
    name: str
    initials: str
    plan: str
    status: str
    stats: list[ProfileStatOut]
    timeline: list[TimelineEntryOut]


# ------------------------------------------------------------------ forecast


class ForecastPointOut(ApiModel):
    label: str
    value: float


class ForecastOut(ApiModel):
    scenario: Scenario
    history: list[ForecastPointOut]
    projection: list[ForecastPointOut]
    band: list[tuple[float, float]]


class ForecastRowOut(ApiModel):
    month: str
    low: float
    projected: float
    high: float
    net_new: float
    run_rate_arr: float


class AssumptionsOut(ApiModel):
    new_business: str
    expansion: str
    cancelled: str
    reactivation: str


class ScenarioOut(ApiModel):
    key: Scenario
    label: str
    multiplier: float
    assumptions: AssumptionsOut
    forecast: ForecastOut
    table: list[ForecastRowOut]
    end: float
    months_to_target: int | None


class ForecastViewOut(ApiModel):
    scenarios: list[ScenarioOut]
    current_mrr: float
    horizon_months: int
    horizon_label: str
    horizon_short_label: str
    target: float


class PredictionOut(ApiModel):
    step: int
    label: str
    value: float
    low: float
    high: float


class SmoothingOut(ApiModel):
    method: Literal["holt"]
    alpha: float
    beta: float
    sigma: float
    confidence: float
    backtest_mape: float | None
    history: list[ForecastPointOut]
    fitted: list[float]
    forecast: list[PredictionOut]


class SurvivalPointOut(ApiModel):
    time: float
    at_risk: int
    events: int
    censored: int
    survival: float
    low: float
    high: float


class ChurnProjectionOut(ApiModel):
    month: int
    label: str
    customers: float
    churned_customers: float
    churned_mrr: float
    retained_mrr: float


class ChurnForecastOut(ApiModel):
    subjects: int
    events: int
    curve: list[SurvivalPointOut]
    median_lifetime_months: float | None
    hazard_rate: float
    monthly_logo_churn: float
    hazard_r_squared: float
    modelled_median_lifetime: float | None
    revenue_churn_rate: float
    projection: list[ChurnProjectionOut]


# ------------------------------------------------------------------ recovery


class FunnelItemOut(ApiModel):
    key: str
    label: str
    value: float
    tone: Tone


class FunnelOut(ApiModel):
    items: list[FunnelItemOut]
    failed: float
    recovered: float
    rate: float


class MonthlyRecoveryOut(ApiModel):
    label: str
    failed: float
    recovered: float


class OpenFailedOut(ApiModel):
    customer: str
    amount: float
    reason: str
    decline_code: str
    attempts: int
    next_retry: str
    step: str


class RecoveryViewOut(ApiModel):
    kpis: list[KpiOut]
    funnel: FunnelOut
    months: list[MonthlyRecoveryOut]
    decline_reasons: list[tuple[str, float]]
    open_failed: list[OpenFailedOut]
    max_attempts: int


class DunningPlanRequest(ApiModel):
    failed_at: datetime
    decline_code: str = Field(min_length=1, max_length=80)
    amount: float = Field(gt=0)
    now: datetime | None = None


class DunningStepOut(ApiModel):
    at: datetime
    kind: str
    description: str
    attempt: int | None = None
    template: str | None = None
    due: bool


class DunningPlanOut(ApiModel):
    decline_code: str
    decline_label: str
    category: str
    amount: float
    first_failed_at: datetime
    closes_at: datetime
    retries: int
    next_step: DunningStepOut | None
    steps: list[DunningStepOut]


# ------------------------------------------------------------------ dashboard


class DashboardOut(ApiModel):
    workspace: WorkspaceOut
    ranges: list[RangeDefinitionOut]
    views: dict[RangeKey, RangeViewOut]
    plans: list[PlanRowOut]
    accounts: list[AccountOut]
    activity: list[ActivityOut]
    retention: RetentionViewOut
    customers: CustomersViewOut
    forecast: ForecastViewOut
    recovery: RecoveryViewOut
    profile: ProfileOut


# ------------------------------------------------------------------ event store


class IngestMovementOut(ApiModel):
    type: str
    amount: float


class WebhookAccepted(ApiModel):
    received: Literal[True] = True
    status: Literal["processed", "duplicate"]
    event_id: str
    movement: IngestMovementOut | None = None


class MonthlyBridgeOut(ApiModel):
    month: date
    label: str
    opening: float
    totals: MovementTotalsOut
    net: float
    closing: float


class RetentionResultOut(ApiModel):
    start: date
    end: date
    base_customers: int
    base_mrr: float
    retained_mrr: float
    gross_retained_mrr: float
    nrr: float | None
    grr: float | None
    logo_retention: float | None


class WorkspaceSummaryOut(ApiModel):
    workspace: str
    as_of: date
    mrr: float
    customers: int
    retention: RetentionResultOut
    bridge: list[MonthlyBridgeOut]
    cohorts: list[CohortOut]


class MovementOut(ApiModel):
    customer_id: str
    movement: str
    amount: float
    mrr_before: float
    mrr_after: float
    occurred_at: datetime


class DeclineBreakdownOut(ApiModel):
    code: str
    label: str
    count: int
    amount: float
    recovered: float
    share: float
    recovery_rate: float


class FailedPaymentOut(ApiModel):
    invoice_id: str
    customer_id: str
    amount: float
    decline_code: str
    attempts: int
    status: str
    failed_at: datetime
    recovered_at: datetime | None
    next_retry_at: datetime | None = None


class FailedPaymentsOut(ApiModel):
    count: int
    failed: float
    recovered: float
    open: float
    lost: float
    resolved_rate: float | None
    median_days_to_recover: float | None
    attempts_to_recover: dict[int, int]
    declines: list[DeclineBreakdownOut]
    payments: list[FailedPaymentOut]
