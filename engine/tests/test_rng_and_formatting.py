from __future__ import annotations

import math

import pytest

from churnwise.domain.formatting import js_round, money, num, pct, signed_money, to_fixed, whole_dollars
from churnwise.domain.rng import Mulberry32, lerp


def test_mulberry32_matches_the_typescript_generator(golden):
    rng = Mulberry32(42)
    assert [rng.next() for _ in range(5)] == golden["rng42"]


def test_mulberry32_is_deterministic_and_in_unit_interval():
    a, b = Mulberry32(7), Mulberry32(7)
    draws = [a.next() for _ in range(2000)]
    assert draws == [b.next() for _ in range(2000)]
    assert all(0 <= d < 1 for d in draws)
    # Roughly uniform: the mean of 2,000 draws sits close to one half.
    assert abs(sum(draws) / len(draws) - 0.5) < 0.03


def test_seed_is_reduced_to_32_bits():
    assert Mulberry32(2**32 + 5).next() == Mulberry32(5).next()


def test_uniform_respects_bounds():
    rng = Mulberry32(1)
    values = [rng.uniform(-3, 4) for _ in range(500)]
    assert min(values) >= -3 and max(values) < 4


def test_lerp():
    assert lerp(10, 20, 0) == 10
    assert lerp(10, 20, 1) == 20
    assert lerp(10, 20, 0.25) == 12.5


@pytest.mark.parametrize(
    ("value", "digits", "expected"),
    [
        (1.005, 2, "1.00"),  # binary 1.005 is just below the half, as in JavaScript
        (2.5, 0, "3"),  # halves round away from zero, unlike Python's round()
        (-2.5, 0, "-3"),
        (0.125, 2, "0.13"),
        (-0.04, 1, "-0.0"),
        (-0.0, 1, "0.0"),
        (1234.5678, 1, "1234.6"),
        (7, 3, "7.000"),
    ],
)
def test_to_fixed_follows_javascript(value, digits, expected):
    assert to_fixed(value, digits) == expected


def test_to_fixed_rejects_non_finite():
    with pytest.raises(ValueError):
        to_fixed(math.inf, 1)


def test_js_round_rounds_halves_up():
    assert js_round(2.5) == 3
    assert js_round(-2.5) == -2
    assert js_round(2.49) == 2


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (842.4, "$842"),
        (4200, "$4.20k"),
        (18_900, "$18.9k"),
        (1_260_000, "$1.26M"),
        (-4200, "-$4.20k"),
        (0, "$0"),
    ],
)
def test_money(value, expected):
    assert money(value) == expected


def test_money_with_explicit_decimals():
    assert money(1_140_421.41, 2) == "$1.14M"
    assert money(18_900, 0) == "$19k"


def test_signed_money_and_counts():
    assert signed_money(288_300) == "+$288.3k"
    assert signed_money(-4200) == "-$4.20k"
    assert num(2620.69) == "2,621"
    assert whole_dollars(318) == "$318"
    assert pct(107.375) == "107.4%"
    assert pct(1.23, 2) == "1.23%"
    assert pct(3.04, 1, signed=True) == "+3.0%"
    assert pct(-3.04, 1, signed=True) == "-3.0%"
