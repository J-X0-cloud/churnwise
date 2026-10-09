"""Exponential smoothing, implemented from first principles.

* :func:`simple_exponential_smoothing` — level only, for rates that wander without a trend (monthly churn).
* :func:`holt` — Holt's linear trend method (double exponential smoothing), for MRR.

Parameters are chosen by minimising the one-step-ahead sum of squared errors over a coarse grid followed by
a finer grid around the best point. Prediction intervals use the analytical variance of Holt's method under
additive Gaussian errors: ``sigma^2 * (1 + sum_{j=1}^{h-1} alpha^2 * (1 + j*beta)^2)``.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from statistics import NormalDist


def _grid(lo: float, hi: float, steps: int) -> list[float]:
    return [lo + (hi - lo) * i / (steps - 1) for i in range(steps)]


def _check_series(series: Sequence[float], minimum: int) -> list[float]:
    values = [float(v) for v in series]
    if len(values) < minimum:
        raise ValueError(f"need at least {minimum} observations, got {len(values)}")
    if any(not math.isfinite(v) for v in values):
        raise ValueError("series contains non-finite values")
    return values


def _z(confidence: float) -> float:
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1")
    return NormalDist().inv_cdf(0.5 + confidence / 2)


@dataclass(frozen=True, slots=True)
class Prediction:
    step: int
    value: float
    low: float
    high: float


# ------------------------------------------------------------------ simple exponential smoothing


@dataclass(frozen=True, slots=True)
class SesFit:
    alpha: float
    level: float
    fitted: tuple[float, ...]
    sse: float

    @property
    def sigma(self) -> float:
        n = len(self.fitted)
        return math.sqrt(self.sse / max(1, n - 1))

    def forecast(self, horizon: int, confidence: float = 0.8) -> list[Prediction]:
        """Flat forecast at the final level; the interval widens as ``sigma * sqrt(1 + (h-1) * alpha^2)``."""
        z = _z(confidence)
        out = []
        for h in range(1, horizon + 1):
            half = z * self.sigma * math.sqrt(1 + (h - 1) * self.alpha**2)
            out.append(Prediction(h, self.level, self.level - half, self.level + half))
        return out


def _ses_pass(values: list[float], alpha: float) -> tuple[float, list[float], float]:
    level = values[0]
    fitted = [level]
    sse = 0.0
    for y in values[1:]:
        fitted.append(level)
        sse += (y - level) ** 2
        level = alpha * y + (1 - alpha) * level
    return level, fitted, sse


def simple_exponential_smoothing(series: Sequence[float], alpha: float | None = None) -> SesFit:
    values = _check_series(series, 2)
    if alpha is None:
        coarse = min(_grid(0.01, 0.99, 50), key=lambda a: _ses_pass(values, a)[2])
        alpha = min(
            _grid(max(0.01, coarse - 0.02), min(0.99, coarse + 0.02), 41),
            key=lambda a: _ses_pass(values, a)[2],
        )
    elif not 0 < alpha <= 1:
        raise ValueError("alpha must be in (0, 1]")
    level, fitted, sse = _ses_pass(values, alpha)
    return SesFit(alpha=alpha, level=level, fitted=tuple(fitted), sse=sse)


# ------------------------------------------------------------------ Holt's linear trend


@dataclass(frozen=True, slots=True)
class HoltFit:
    alpha: float
    beta: float
    level: float
    trend: float
    #: One-step-ahead fitted values; the first equals the first observation.
    fitted: tuple[float, ...]
    residuals: tuple[float, ...]
    sse: float

    @property
    def sigma(self) -> float:
        """Residual standard deviation (two parameters plus two initial states estimated)."""
        dof = max(1, len(self.residuals) - 2)
        return math.sqrt(self.sse / dof)

    def point(self, h: int) -> float:
        return self.level + h * self.trend

    def forecast(self, horizon: int, confidence: float = 0.8) -> list[Prediction]:
        if horizon < 1:
            raise ValueError("horizon must be at least 1")
        z = _z(confidence)
        out = []
        for h in range(1, horizon + 1):
            variance_factor = 1 + sum((self.alpha * (1 + j * self.beta)) ** 2 for j in range(1, h))
            half = z * self.sigma * math.sqrt(variance_factor)
            value = self.point(h)
            out.append(Prediction(h, value, value - half, value + half))
        return out


def _holt_pass(
    values: list[float], alpha: float, beta: float
) -> tuple[float, float, list[float], list[float]]:
    level = values[0]
    trend = values[1] - values[0]
    fitted = [values[0]]
    residuals: list[float] = []
    for y in values[1:]:
        prediction = level + trend
        fitted.append(prediction)
        residuals.append(y - prediction)
        new_level = alpha * y + (1 - alpha) * prediction
        trend = beta * (new_level - level) + (1 - beta) * trend
        level = new_level
    return level, trend, fitted, residuals


def _holt_sse(values: list[float], alpha: float, beta: float) -> float:
    return sum(r * r for r in _holt_pass(values, alpha, beta)[3])


def holt(series: Sequence[float], alpha: float | None = None, beta: float | None = None) -> HoltFit:
    """Fit Holt's linear trend method. Either parameter can be fixed; the others are optimised."""
    values = _check_series(series, 3)
    for name, value in (("alpha", alpha), ("beta", beta)):
        if value is not None and not 0 < value <= 1:
            raise ValueError(f"{name} must be in (0, 1]")

    alphas = [alpha] if alpha is not None else _grid(0.05, 0.95, 19)
    betas = [beta] if beta is not None else _grid(0.01, 0.91, 19)
    best_a, best_b = min(((a, b) for a in alphas for b in betas), key=lambda ab: _holt_sse(values, *ab))

    # Refine around the coarse optimum.
    fine_a = [alpha] if alpha is not None else _grid(max(0.01, best_a - 0.05), min(1.0, best_a + 0.05), 21)
    fine_b = [beta] if beta is not None else _grid(max(0.005, best_b - 0.05), min(1.0, best_b + 0.05), 21)
    best_a, best_b = min(((a, b) for a in fine_a for b in fine_b), key=lambda ab: _holt_sse(values, *ab))

    level, trend, fitted, residuals = _holt_pass(values, best_a, best_b)
    return HoltFit(
        alpha=best_a,
        beta=best_b,
        level=level,
        trend=trend,
        fitted=tuple(fitted),
        residuals=tuple(residuals),
        sse=sum(r * r for r in residuals),
    )


def mean_absolute_percentage_error(actual: Sequence[float], predicted: Sequence[float]) -> float:
    """MAPE in percent, skipping zero actuals."""
    pairs = [(a, p) for a, p in zip(actual, predicted, strict=True) if a != 0]
    if not pairs:
        raise ValueError("MAPE is undefined when every actual value is zero")
    return 100 * sum(abs((a - p) / a) for a, p in pairs) / len(pairs)


def backtest_holt(series: Sequence[float], holdout: int) -> float:
    """Fit on all but the last ``holdout`` points, forecast them, and return the MAPE."""
    values = _check_series(series, holdout + 3)
    fit = holt(values[:-holdout])
    predicted = [p.value for p in fit.forecast(holdout)]
    return mean_absolute_percentage_error(values[-holdout:], predicted)
