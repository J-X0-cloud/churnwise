"""Application factory."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy import Engine

from churnwise import __version__
from churnwise.api.errors import install_error_handlers
from churnwise.api.routes import dashboard, forecast, health, metrics, recovery, webhooks, workspaces
from churnwise.config import Settings, get_settings
from churnwise.db.session import make_engine, make_session_factory


def create_app(settings: Settings | None = None, engine: Engine | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(level=settings.log_level.upper(), format="%(levelname)s %(name)s: %(message)s")

    app = FastAPI(
        title="Churnwise engine",
        version=__version__,
        description="MRR movements, retention, cohorts, forecasting and failed-payment recovery.",
    )
    app.state.settings = settings
    app.state.engine = engine or make_engine(settings.database_url)
    app.state.session_factory = make_session_factory(app.state.engine)

    app.add_middleware(GZipMiddleware, minimum_size=2048)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_origins),
            allow_methods=["GET", "POST"],
            allow_headers=["Authorization", "Content-Type"],
        )
    install_error_handlers(app)
    for module in (health, metrics, dashboard, forecast, recovery, webhooks, workspaces):
        app.include_router(module.router)
    return app


def app_factory() -> FastAPI:
    """Entry point for ``uvicorn --factory churnwise.main:app_factory``."""
    return create_app()
