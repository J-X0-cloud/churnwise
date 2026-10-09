"""Forecasts: the dashboard's scenarios plus the statistical models behind them."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from churnwise.api import schemas as s
from churnwise.api import views
from churnwise.domain.types import Scenario

router = APIRouter(prefix="/api/forecast", tags=["forecast"])


@router.get("", response_model=s.ForecastViewOut)
def get_forecast_view() -> s.ForecastViewOut:
    """All three scenarios with their projections, intervals and monthly tables."""
    return views.forecast_view()


@router.get("/scenarios/{scenario}", response_model=s.ScenarioOut)
def get_scenario(scenario: Scenario) -> s.ScenarioOut:
    return views.scenario_out(scenario)


@router.get("/smoothing", response_model=s.SmoothingOut)
def get_smoothing(
    horizon: Annotated[int, Query(ge=1, le=36)] = 12,
    confidence: Annotated[float, Query(gt=0.5, lt=1)] = 0.8,
) -> s.SmoothingOut:
    """Holt's linear-trend exponential smoothing fitted to month-end MRR, with a prediction interval and a
    three-month holdout backtest."""
    return views.smoothing_forecast(horizon, confidence)


@router.get("/churn", response_model=s.ChurnForecastOut)
def get_churn_forecast(horizon: Annotated[int, Query(ge=1, le=36)] = 12) -> s.ChurnForecastOut:
    """Kaplan-Meier survival of the signup cohorts, a constant-hazard fit, and the logos and MRR today's
    customers are expected to churn over the horizon."""
    return views.churn_forecast(horizon)
