from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from churnwise.db.migrate import upgrade_engine
from churnwise.db.repository import create_workspace
from churnwise.db.session import make_engine, make_session_factory
from churnwise.domain.simulation import RevenueModel, sample_model
from tests.payloads import WORKSPACE

GOLDEN = Path(__file__).parent / "golden" / "typescript_parity.json"


@pytest.fixture(scope="session")
def golden() -> dict[str, Any]:
    """Values captured from the original TypeScript implementation before it was removed."""
    return json.loads(GOLDEN.read_text())


@pytest.fixture(scope="session")
def model() -> RevenueModel:
    return sample_model()


@pytest.fixture
def engine() -> Iterator[Engine]:
    engine = make_engine("sqlite://")
    upgrade_engine(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def factory(engine: Engine) -> sessionmaker[Session]:
    factory = make_session_factory(engine)
    with factory.begin() as session:
        create_workspace(session, WORKSPACE, "Quillstack")
    return factory
