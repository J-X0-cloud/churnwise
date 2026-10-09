from __future__ import annotations

import json
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from churnwise.billing.signature import sign
from churnwise.config import Settings
from churnwise.db.migrate import upgrade_engine
from churnwise.db.repository import create_workspace
from churnwise.db.session import make_engine, make_session_factory
from churnwise.domain.simulation import RevenueModel, sample_model
from churnwise.main import create_app
from tests.payloads import WORKSPACE

GOLDEN = Path(__file__).parent / "golden" / "typescript_parity.json"
SECRET = "whsec_test_secret"


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


@pytest.fixture
def settings() -> Settings:
    return Settings(database_url="sqlite://", webhook_secret=SECRET)


@pytest.fixture
def client(settings: Settings, engine: Engine, factory: sessionmaker[Session]) -> Iterator[TestClient]:
    with TestClient(create_app(settings, engine=engine)) as test_client:
        yield test_client


PostEvent = Callable[..., Any]


@pytest.fixture
def post_event(client: TestClient) -> PostEvent:
    """Sign and POST a billing event the way a connector would."""

    def _post(
        event: dict[str, Any],
        *,
        secret: str = SECRET,
        timestamp: int | None = None,
        header: str | None = None,
    ):
        body = json.dumps(event)
        stamp = int(time.time()) if timestamp is None else timestamp
        signature = sign(body, secret, stamp) if header is None else header
        return client.post(
            "/api/webhooks/billing",
            content=body,
            headers={"x-churnwise-signature": signature, "content-type": "application/json"},
        )

    return _post
