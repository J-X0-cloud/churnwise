"""Run the Alembic migrations programmatically (used by the CLI, the container entrypoint and tests)."""

from __future__ import annotations

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine

SCRIPT_LOCATION = "churnwise.db:migrations"


def alembic_config(url: str | None = None) -> Config:
    config = Config()
    config.set_main_option("script_location", SCRIPT_LOCATION)
    if url:
        config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    config.attributes["configure_logging"] = False
    return config


def upgrade(url: str | None = None, revision: str = "head") -> None:
    command.upgrade(alembic_config(url), revision)


def upgrade_engine(engine: Engine, revision: str = "head") -> None:
    """Migrate using an existing engine (keeps in-memory SQLite databases alive across the call)."""
    config = alembic_config()
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, revision)


def downgrade(url: str | None = None, revision: str = "base") -> None:
    command.downgrade(alembic_config(url), revision)
