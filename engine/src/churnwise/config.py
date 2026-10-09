"""Runtime configuration, read once from the environment."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

DEFAULT_DATABASE_URL = "sqlite:///./churnwise.db"

# Query parameters some tools (Prisma, for one) put on Postgres URLs that libpq does not understand.
_UNSUPPORTED_PG_PARAMS = {"schema", "connection_limit", "pool_timeout", "pgbouncer"}


def normalize_database_url(url: str) -> str:
    """Make a connection string usable by SQLAlchemy with the psycopg 3 driver.

    ``postgres://`` and ``postgresql://`` URLs (as Railway and most hosts hand them out) are rewritten to
    ``postgresql+psycopg://``, and parameters libpq would reject are dropped. Other URLs pass through.
    """
    parts = urlsplit(url)
    scheme = parts.scheme
    if scheme in {"postgres", "postgresql"}:
        scheme = "postgresql+psycopg"
    if not scheme.startswith("postgresql"):
        return url
    query = urlencode([(k, v) for k, v in parse_qsl(parts.query) if k not in _UNSUPPORTED_PG_PARAMS])
    return urlunsplit((scheme, parts.netloc, parts.path, query, parts.fragment))


def _split_csv(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str = DEFAULT_DATABASE_URL
    webhook_secret: str | None = None
    #: Bearer token required by the workspace endpoints; unset leaves them open (local development).
    api_token: str | None = None
    cors_origins: tuple[str, ...] = field(default_factory=tuple)
    sample_workspace: str = "quillstack"
    log_level: str = "info"

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> Settings:
        env = dict(os.environ if env is None else env)
        return cls(
            database_url=normalize_database_url(env.get("DATABASE_URL") or DEFAULT_DATABASE_URL),
            webhook_secret=env.get("BILLING_WEBHOOK_SECRET") or None,
            api_token=env.get("API_TOKEN") or None,
            cors_origins=_split_csv(env.get("CORS_ORIGINS")),
            sample_workspace=env.get("SAMPLE_WORKSPACE", "quillstack"),
            log_level=env.get("LOG_LEVEL", "info").lower(),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
