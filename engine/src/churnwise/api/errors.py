"""Uniform error bodies: every error response is ``{"error": "<code>", ...}``."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def _http_error(_request: Request, exc: HTTPException) -> JSONResponse:
        code = exc.detail if isinstance(exc.detail, str) else "error"
        return JSONResponse({"error": code}, status_code=exc.status_code, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
        issues = [
            {"path": [str(p) for p in err["loc"]], "message": err["msg"], "code": err["type"]}
            for err in exc.errors()
        ]
        return JSONResponse({"error": "invalid_request", "issues": issues}, status_code=400)
