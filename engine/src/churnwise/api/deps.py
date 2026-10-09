"""Request-scoped dependencies."""

from __future__ import annotations

import hmac
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session, sessionmaker

from churnwise.config import Settings


def get_settings(request: Request) -> Settings:
    return request.app.state.settings  # type: ignore[no-any-return]


def get_session_factory(request: Request) -> sessionmaker[Session]:
    return request.app.state.session_factory  # type: ignore[no-any-return]


def get_session(factory: Annotated[sessionmaker[Session], Depends(get_session_factory)]) -> Iterator[Session]:
    with factory() as session:
        yield session


def require_api_token(
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    """Workspace data is private. When ``API_TOKEN`` is set, callers must send ``Authorization: Bearer``."""
    expected = settings.api_token
    if expected is None:
        return
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not hmac.compare_digest(token.encode(), expected.encode()):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="invalid_token", headers={"WWW-Authenticate": "Bearer"}
        )


SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[Session, Depends(get_session)]
SessionFactoryDep = Annotated[sessionmaker[Session], Depends(get_session_factory)]
