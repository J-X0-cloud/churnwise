"""Core value types shared by every part of the revenue model."""

from __future__ import annotations

from dataclasses import dataclass, fields
from enum import StrEnum
from typing import Literal


class Movement(StrEnum):
    """The five ways MRR can change. Every metric in the product is derived from these flows."""

    NEW = "new"
    EXPANSION = "expansion"
    REACTIVATION = "reactivation"
    CONTRACTION = "contraction"
    CHURN = "churn"

    @property
    def sign(self) -> int:
        """+1 for flows that add MRR, -1 for flows that remove it."""
        return 1 if self in GAINS else -1


GAINS: frozenset[Movement] = frozenset({Movement.NEW, Movement.EXPANSION, Movement.REACTIVATION})
LOSSES: frozenset[Movement] = frozenset({Movement.CONTRACTION, Movement.CHURN})
MOVEMENT_ORDER: tuple[Movement, ...] = tuple(Movement)


class RangeKey(StrEnum):
    D30 = "30d"
    D90 = "90d"
    M12 = "12m"
    M24 = "24m"


class Scenario(StrEnum):
    CONSERVATIVE = "conservative"
    BASE = "base"
    STRETCH = "stretch"


class CohortMetric(StrEnum):
    NET = "net"
    LOGO = "logo"


Bucket = Literal["day", "week", "month"]

#: Semantic colour roles. The frontend owns the palette; the engine only says which role a series plays.
Tone = Literal["brand", "brand_dark", "ink", "mint", "blue", "amber", "red", "starter"]


@dataclass(frozen=True, slots=True)
class MovementTotals:
    """MRR moved by each flow over some period. Amounts are always positive; the sign comes from the flow."""

    new: float = 0.0
    expansion: float = 0.0
    reactivation: float = 0.0
    contraction: float = 0.0
    churn: float = 0.0

    def __getitem__(self, movement: Movement | str) -> float:
        return getattr(self, Movement(movement).value)

    def __add__(self, other: MovementTotals) -> MovementTotals:
        if not isinstance(other, MovementTotals):
            return NotImplemented
        return MovementTotals(
            **{f.name: getattr(self, f.name) + getattr(other, f.name) for f in fields(self)}
        )

    @classmethod
    def from_mapping(cls, values: dict[Movement, float] | dict[str, float]) -> MovementTotals:
        return cls(**{Movement(k).value: float(v) for k, v in values.items()})

    @classmethod
    def sum(cls, items: list[MovementTotals] | tuple[MovementTotals, ...]) -> MovementTotals:
        total = cls()
        for item in items:
            total = total + item
        return total

    def as_dict(self) -> dict[str, float]:
        return {m.value: self[m] for m in MOVEMENT_ORDER}

    @property
    def gained(self) -> float:
        return self.new + self.expansion + self.reactivation

    @property
    def lost(self) -> float:
        return self.contraction + self.churn

    @property
    def net(self) -> float:
        return self.gained - self.lost

    @property
    def quick_ratio(self) -> float:
        """Gained MRR for every dollar lost. Above 4 is efficient growth; infinite when nothing was lost."""
        return self.gained / self.lost if self.lost else float("inf")
