"""Engine and session factory."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


def make_engine(url: str, echo: bool = False) -> Engine:
    if url.startswith("sqlite"):
        in_memory = url in {"sqlite://", "sqlite:///:memory:"}
        engine = create_engine(
            url,
            echo=echo,
            connect_args={"check_same_thread": False},
            # One shared connection, or every new connection would see a fresh, empty in-memory database.
            poolclass=StaticPool if in_memory else None,
        )

        @event.listens_for(engine, "connect")
        def _enable_foreign_keys(dbapi_connection, _record) -> None:  # type: ignore[no-untyped-def]
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return engine
    return create_engine(url, echo=echo, pool_pre_ping=True)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def transaction(factory: sessionmaker[Session]) -> Iterator[Session]:
    """A session wrapped in one transaction: committed on success, rolled back on any error."""
    with factory.begin() as session:
        yield session
