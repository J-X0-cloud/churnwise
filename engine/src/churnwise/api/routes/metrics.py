"""Headline metrics for the sample workspace: the same numbers the dashboard tiles show."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Path, Query
from fastapi.responses import JSONResponse

from churnwise.api import schemas as s
from churnwise.api import views
from churnwise.domain.types import RangeKey

router = APIRouter(prefix="/api", tags=["metrics"])

_TRUE = {"true", "1", "yes", "on", "y", "enabled"}
_FALSE = {"false", "0", "no", "off", "n", "disabled"}
_RANGE_VALUES = [r.value for r in RangeKey]


def parse_bool(value: str) -> bool:
    lowered = value.strip().lower()
    if lowered in _TRUE:
        return True
    if lowered in _FALSE:
        return False
    raise ValueError("expected a boolean such as true/false, 1/0 or yes/no")


def _invalid(issues: dict[str, list[str]]) -> JSONResponse:
    return JSONResponse({"error": "invalid_query", "issues": issues}, status_code=400)


@router.get("/metrics", response_model=None)
def get_metrics(
    range_: Annotated[str | None, Query(alias="range")] = None,
    movements: Annotated[str | None, Query()] = None,
) -> dict[str, Any] | JSONResponse:
    """``GET /api/metrics?range=12m&movements=true`` — headline revenue metrics, the MRR line and,
    optionally, per-period MRR movements."""
    issues: dict[str, list[str]] = {}
    key = RangeKey.M12
    if range_ is not None:
        try:
            key = RangeKey(range_)
        except ValueError:
            issues["range"] = [f"Invalid option: expected one of {'|'.join(_RANGE_VALUES)}"]
    include_movements = False
    if movements is not None:
        try:
            include_movements = parse_bool(movements)
        except ValueError as exc:
            issues["movements"] = [str(exc)]
    if issues:
        return _invalid(issues)

    view = views.range_view(key)
    body: dict[str, Any] = {
        "range": key.value,
        "metrics": {**view.stats.model_dump(by_alias=True), "quickRatio": view.quick_ratio},
        "mrrSeries": [
            {"date": point.day.isoformat(), "mrr": round(point.value, 2)}
            for point in views.range_line_points(key)
        ],
    }
    if include_movements:
        body["movements"] = [
            {
                "period": b.label,
                "new": b.new,
                "expansion": b.expansion,
                "reactivation": b.reactivation,
                "contraction": b.contraction,
                "churn": b.churn,
                "net": b.net,
            }
            for b in view.buckets
        ]
    return body


@router.get("/ranges/{range_key}", response_model=s.RangeViewOut, response_model_exclude_none=True)
def get_range(range_key: Annotated[RangeKey, Path()]) -> s.RangeViewOut:
    """Everything the Overview and Revenue tabs show for one range."""
    return views.range_view(range_key)
