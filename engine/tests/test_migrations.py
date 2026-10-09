from __future__ import annotations

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect

from churnwise.db.migrate import downgrade, upgrade, upgrade_engine
from churnwise.db.models import Base
from churnwise.db.session import make_engine

TABLES = {"workspaces", "billing_events", "customers", "mrr_movements", "failed_payments"}


def test_migrations_create_the_event_store():
    engine = make_engine("sqlite://")
    upgrade_engine(engine)
    assert set(inspect(engine).get_table_names()) >= TABLES
    unique = {tuple(u["column_names"]) for u in inspect(engine).get_unique_constraints("billing_events")}
    assert ("workspace_id", "external_id") in unique


def test_models_match_the_migrations():
    engine = make_engine("sqlite://")
    upgrade_engine(engine)
    with engine.connect() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": False})
        diff = compare_metadata(context, Base.metadata)
    assert diff == []


def test_upgrade_and_downgrade_round_trip(tmp_path):
    url = f"sqlite:///{tmp_path / 'store.db'}"
    upgrade(url)
    assert set(inspect(make_engine(url)).get_table_names()) >= TABLES
    downgrade(url)
    assert not TABLES & set(inspect(make_engine(url)).get_table_names())
    upgrade(url)
    assert set(inspect(make_engine(url)).get_table_names()) >= TABLES
