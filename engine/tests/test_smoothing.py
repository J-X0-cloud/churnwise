from __future__ import annotations

import itertools
import math

import pytest

from churnwise.domain.rng import Mulberry32
from churnwise.domain.smoothing import (
    backtest_holt,
    holt,
    mean_absolute_percentage_error,
    simple_exponential_smoothing,
)


def test_holt_recovers_a_perfect_linear_trend():
    series = [100 + 7 * t for t in range(20)]
    fit = holt(series)
    assert fit.sse == pytest.approx(0, abs=1e-9)
    assert fit.trend == pytest.approx(7)
    assert [p.value for p in fit.forecast(3)] == pytest.approx([240, 247, 254])


def test_holt_fixed_parameters_follow_the_recursions():
    fit = holt([10, 12, 15, 15], alpha=0.5, beta=0.5)
    # level/trend by hand: l0=10 b0=2; y=12: pred 12, l=12, b=2; y=15: pred 14, l=14.5, b=2.25;
    # y=15: pred 16.75, l=15.875, b=1.8125
    assert fit.fitted == pytest.approx((10, 12, 14, 16.75))
    assert fit.level == pytest.approx(15.875)
    assert fit.trend == pytest.approx(1.8125)
    assert fit.residuals == pytest.approx((0, 1, -1.75))


def test_holt_optimiser_beats_arbitrary_parameters():
    rng = Mulberry32(3)
    series = [1000 + 25 * t + rng.uniform(-40, 40) for t in range(36)]
    best = holt(series)
    assert best.sse <= holt(series, alpha=0.3, beta=0.3).sse
    assert best.sse <= holt(series, alpha=0.9, beta=0.1).sse
    assert 0 < best.alpha <= 1 and 0 < best.beta <= 1


def test_prediction_intervals_widen_and_bracket_the_point():
    rng = Mulberry32(11)
    series = [500 + 10 * t + rng.uniform(-30, 30) for t in range(30)]
    preds = holt(series).forecast(6, confidence=0.8)
    widths = [p.high - p.low for p in preds]
    assert all(b >= a for a, b in itertools.pairwise(widths))
    assert all(p.low < p.value < p.high for p in preds)
    wider = holt(series).forecast(6, confidence=0.95)
    assert wider[0].high - wider[0].low > widths[0]


def test_one_step_interval_uses_the_normal_quantile():
    fit = holt([1, 3, 2, 5, 4, 6, 8, 7, 9], alpha=0.4, beta=0.2)
    first = fit.forecast(1, confidence=0.8)[0]
    assert (first.high - first.value) == pytest.approx(1.2815515655 * fit.sigma, rel=1e-6)


def test_holt_validates_input():
    with pytest.raises(ValueError):
        holt([1, 2])
    with pytest.raises(ValueError):
        holt([1, 2, math.nan])
    with pytest.raises(ValueError):
        holt([1, 2, 3], alpha=0)
    with pytest.raises(ValueError):
        holt([1, 2, 3]).forecast(0)
    with pytest.raises(ValueError):
        holt([1, 2, 3]).forecast(1, confidence=1.5)


def test_simple_exponential_smoothing():
    fit = simple_exponential_smoothing([5, 5, 5, 5], alpha=0.3)
    assert fit.level == 5 and fit.sse == 0
    noisy = simple_exponential_smoothing([2.1, 1.9, 2.0, 2.2, 1.8, 2.0, 2.1, 1.9])
    assert 0 < noisy.alpha < 1
    assert noisy.level == pytest.approx(2.0, abs=0.15)
    preds = noisy.forecast(3)
    assert {p.value for p in preds} == {noisy.level}
    assert preds[2].high - preds[2].low >= preds[0].high - preds[0].low
    with pytest.raises(ValueError):
        simple_exponential_smoothing([1, 2], alpha=1.5)


def test_mape_and_backtest():
    assert mean_absolute_percentage_error([100, 200], [110, 180]) == pytest.approx(10)
    assert mean_absolute_percentage_error([0, 100], [5, 90]) == pytest.approx(10)
    with pytest.raises(ValueError):
        mean_absolute_percentage_error([0, 0], [1, 1])
    series = [200 + 4 * t for t in range(15)]
    assert backtest_holt(series, 3) == pytest.approx(0, abs=1e-9)


def test_holt_on_the_sample_mrr_history_is_accurate(model):
    history = [model.month_end_mrr(w) for w in model.months]
    assert backtest_holt(history, 3) < 2.0  # within 2% over a three-month holdout
    projection = holt(history).forecast(12)
    assert projection[-1].value > history[-1]
