from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from churnwise.domain.simulation import RevenueModel, sample_model

GOLDEN = Path(__file__).parent / "golden" / "typescript_parity.json"


@pytest.fixture(scope="session")
def golden() -> dict[str, Any]:
    """Values captured from the original TypeScript implementation before it was removed."""
    return json.loads(GOLDEN.read_text())


@pytest.fixture(scope="session")
def model() -> RevenueModel:
    return sample_model()
