"""``churnwise`` command line: migrations, workspaces and the server."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence

from churnwise.config import get_settings


def _migrate(_: argparse.Namespace) -> int:
    from churnwise.db.migrate import upgrade

    upgrade(get_settings().database_url)
    print("database is up to date")
    return 0


def _create_workspace(args: argparse.Namespace) -> int:
    from churnwise.db.repository import ensure_workspace
    from churnwise.db.session import make_engine, make_session_factory

    factory = make_session_factory(make_engine(get_settings().database_url))
    with factory.begin() as session:
        workspace, created = ensure_workspace(session, args.slug, args.name, args.currency)
        print(
            f"{'created' if created else 'exists'}: {workspace.slug} ({workspace.name}, {workspace.currency})"
        )
    return 0


def _bootstrap(args: argparse.Namespace) -> int:
    """Apply migrations and make sure the sample workspace exists, so the webhook accepts its events."""
    from churnwise.domain.simulation import SAMPLE_WORKSPACE

    _migrate(args)
    settings = get_settings()
    name = (
        SAMPLE_WORKSPACE.name
        if settings.sample_workspace == SAMPLE_WORKSPACE.slug
        else settings.sample_workspace
    )
    return _create_workspace(
        argparse.Namespace(slug=settings.sample_workspace, name=name, currency=SAMPLE_WORKSPACE.currency)
    )


def _serve(args: argparse.Namespace) -> int:
    import uvicorn

    uvicorn.run(
        "churnwise.main:app_factory",
        factory=True,
        host=args.host,
        port=args.port,
        reload=args.reload,
        proxy_headers=True,
        forwarded_allow_ips="*",
        log_level=get_settings().log_level,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="churnwise", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("migrate", help="apply database migrations").set_defaults(func=_migrate)
    sub.add_parser("bootstrap", help="migrate and create the sample workspace").set_defaults(func=_bootstrap)

    ws = sub.add_parser("create-workspace", help="create a workspace for webhook ingestion")
    ws.add_argument("slug")
    ws.add_argument("name")
    ws.add_argument("--currency", default="USD")
    ws.set_defaults(func=_create_workspace)

    serve = sub.add_parser("serve", help="run the HTTP server")
    serve.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"))
    serve.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    serve.add_argument("--reload", action="store_true")
    serve.set_defaults(func=_serve)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
