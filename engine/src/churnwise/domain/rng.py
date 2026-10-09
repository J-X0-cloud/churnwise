"""Seeded pseudo-random numbers for the sample workspace.

This is mulberry32, bit-for-bit, so the sample model reproduces the exact numbers the original
TypeScript implementation rendered. All arithmetic is done on unsigned 32-bit integers.
"""

from __future__ import annotations

_MASK = 0xFFFFFFFF
_INCREMENT = 0x6D2B79F5
_TWO_32 = 4294967296


def _imul(a: int, b: int) -> int:
    """32-bit integer multiply (the low 32 bits of the product), like ``Math.imul``."""
    return (a * b) & _MASK


class Mulberry32:
    """Small, fast, deterministic PRNG. Not suitable for anything security related."""

    __slots__ = ("_state",)

    def __init__(self, seed: int) -> None:
        self._state = seed & _MASK

    def next(self) -> float:
        """Uniform float in [0, 1)."""
        self._state = (self._state + _INCREMENT) & _MASK
        t = self._state
        t = _imul(t ^ (t >> 15), t | 1)
        t = (t ^ ((t + _imul(t ^ (t >> 7), t | 61)) & _MASK)) & _MASK
        return ((t ^ (t >> 14)) & _MASK) / _TWO_32

    def uniform(self, low: float, high: float) -> float:
        """Uniform float in [low, high)."""
        return low + (high - low) * self.next()


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between ``a`` (t = 0) and ``b`` (t = 1)."""
    return a + (b - a) * t
