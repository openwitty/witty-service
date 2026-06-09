from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from witty_service.domain.errors import DomainError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.to_payload().to_dict()},
        )
