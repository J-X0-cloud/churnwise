"""Scenario MRR forecast.

Projects the trailing-quarter net-new pace forward under three scenarios, compounding slightly as the
customer base grows, with an 80% interval that widens with the horizon. This is the forecast the
dashboard plots; :mod:`churnwise.domain.smoothing` and :mod:`churnwise.domain.survival` provide the
statistical models used to sanity-check it.
"""

from __future__ import annotations

from dataclasses import dataclass

from churnwise.domain.dates import add_months, auto_month_label
from churnwise.domain.simulation import RevenueModel
from churnwise.domain.types import Scenario

HORIZON = 12
#: Net-new pace compounds slightly as the customer base grows.
PACE_GROWTH = 0.012
#: Half-width of the 80% interval one month out, as a share of today's MRR.
BAND_BASE = 0.011
#: How fast the interval widens with the horizon (sub-linear: k ** 0.85).
BAND_EXPONENT = 0.85
PACE_WINDOW_DAYS = 90


@dataclass(frozen=True, slots=True)
class ScenarioAssumptions:
    """Monthly assumptions shown next to each scenario."""

    new_business: str
    expansion: str
    cancelled: str
    reactivation: str


@dataclass(frozen=True, slots=True)
class ScenarioDefinition:
    key: Scenario
    label: str
    multiplier: float
    assumptions: ScenarioAssumptions


SCENARIOS: tuple[ScenarioDefinition, ...] = (
    ScenarioDefinition(
        Scenario.CONSERVATIVE, "Conservative", 0.62, ScenarioAssumptions("$15.1k", "1.9%", "1.4%", "0.3%")
    ),
    ScenarioDefinition(Scenario.BASE, "Base", 1.0, ScenarioAssumptions("$18.9k", "2.3%", "1.3%", "0.3%")),
    ScenarioDefinition(
        Scenario.STRETCH, "Stretch", 1.32, ScenarioAssumptions("$22.4k", "2.7%", "1.1%", "0.3%")
    ),
)


def scenario_definition(key: Scenario) -> ScenarioDefinition:
    for definition in SCENARIOS:
        if definition.key is key:
            return definition
    raise KeyError(key)


@dataclass(frozen=True, slots=True)
class ForecastPoint:
    label: str
    value: float


@dataclass(frozen=True, slots=True)
class Forecast:
    scenario: Scenario
    history: tuple[ForecastPoint, ...]
    projection: tuple[ForecastPoint, ...]
    #: 80% interval per projected month, as (low, high).
    band: tuple[tuple[float, float], ...]

    @property
    def end(self) -> float:
        """Projected MRR at the end of the horizon."""
        return self.projection[-1].value

    def months_to_target(self, target: float) -> int | None:
        """First projected month (1-based) at or above ``target``; ``None`` if not reached in the horizon."""
        for month, point in enumerate(self.projection, start=1):
            if point.value >= target:
                return month
        return None


def monthly_net_new_pace(model: RevenueModel, window_days: int = PACE_WINDOW_DAYS) -> float:
    """Average monthly net-new MRR over the trailing window (90 days = three months)."""
    return (model[model.last].mrr - model[model.last - window_days].mrr) / (window_days / 30)


def forecast(model: RevenueModel, scenario: Scenario, horizon: int = HORIZON) -> Forecast:
    if horizon < 1:
        raise ValueError("the horizon must be at least one month")
    history = tuple(
        ForecastPoint(auto_month_label(w.month), model.month_end_mrr(w)) for w in model.months[-12:]
    )
    multiplier = scenario_definition(scenario).multiplier
    last = history[-1].value
    pace = monthly_net_new_pace(model)
    last_month = model.months[-1].month

    projection: list[ForecastPoint] = []
    band: list[tuple[float, float]] = []
    value = last
    for k in range(1, horizon + 1):
        month = add_months(last_month, k)
        value += pace * multiplier * (1 + PACE_GROWTH * k)
        projection.append(ForecastPoint(auto_month_label(month), value))
        spread = last * BAND_BASE * k**BAND_EXPONENT
        band.append((value - spread, value + spread))
    return Forecast(scenario=scenario, history=history, projection=tuple(projection), band=tuple(band))


@dataclass(frozen=True, slots=True)
class ForecastRow:
    month: str
    low: float
    projected: float
    high: float
    net_new: float
    run_rate_arr: float


def forecast_table(f: Forecast) -> list[ForecastRow]:
    rows: list[ForecastRow] = []
    previous = f.history[-1].value
    for point, (low, high) in zip(f.projection, f.band, strict=True):
        rows.append(
            ForecastRow(
                month=point.label,
                low=low,
                projected=point.value,
                high=high,
                net_new=point.value - previous,
                run_rate_arr=point.value * 12,
            )
        )
        previous = point.value
    return rows
