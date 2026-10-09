"""Number formatting for KPI values and deltas.

The rounding rules follow JavaScript's ``Number.prototype.toFixed`` and ``Math.round`` (round half away
from zero on the exact binary value, and half up respectively) so that values rendered by the engine read
exactly like values formatted in the browser.
"""

from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal

MINUS = "−"  # typographic minus used in deltas


def to_fixed(value: float, digits: int = 0) -> str:
    """``value.toFixed(digits)``: fixed-point string, halves rounded away from zero."""
    if not math.isfinite(value):
        raise ValueError(f"cannot format non-finite value {value!r}")
    if value == 0:
        value = 0.0  # drop the sign of -0.0
    quantum = Decimal(1).scaleb(-digits)
    return f"{Decimal(value).quantize(quantum, rounding=ROUND_HALF_UP):f}"


def js_round(value: float) -> int:
    """``Math.round``: nearest integer, halves rounded towards +infinity."""
    return math.floor(value + 0.5)


def grouped(value: int) -> str:
    """``1234567`` -> ``1,234,567``."""
    return f"{value:,}"


def money(value: float, decimals: int | None = None) -> str:
    """Currency with k / M suffixes: ``$4.20k``, ``$18.9k``, ``$1.26M``, ``$842``."""
    sign = "-" if value < 0 else ""
    a = abs(value)
    if a >= 1e6:
        return f"{sign}${to_fixed(a / 1e6, 2 if decimals is None else decimals)}M"
    if a >= 1e4:
        return f"{sign}${to_fixed(a / 1e3, 1 if decimals is None else decimals)}k"
    if a >= 1e3:
        return f"{sign}${to_fixed(a / 1e3, 2 if decimals is None else decimals)}k"
    return f"{sign}${grouped(js_round(a))}"


def signed_money(value: float) -> str:
    """Signed currency for movements: ``+$18.9k`` / ``-$4.20k``."""
    return f"+{money(value)}" if value >= 0 else money(value)


def pct(value: float, digits: int = 1, signed: bool = False) -> str:
    prefix = "+" if signed and value > 0 else ""
    return f"{prefix}{to_fixed(value, digits)}%"


def num(value: float) -> str:
    """Whole number with thousands separators."""
    return grouped(js_round(value))


def whole_dollars(value: float) -> str:
    return f"${grouped(js_round(value))}"
