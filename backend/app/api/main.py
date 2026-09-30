"""FastAPI entrypoint for the ``api`` process (ADR-0004)."""

import logging
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from app import __version__
from app.core.config import get_settings
from app.core.db import ping_database
from app.core.logging import configure_logging, correlation_id

logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(title=settings.app_name, version=__version__)

    @app.middleware("http")
    async def request_id(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        rid = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
        token = correlation_id.set(rid)
        try:
            response = await call_next(request)
        finally:
            correlation_id.reset(token)
        response.headers[REQUEST_ID_HEADER] = rid
        return response

    @app.get("/health", tags=["ops"])
    async def health() -> dict[str, str]:
        """Liveness: the process is up."""
        return {"status": "ok", "version": __version__}

    @app.get("/ready", tags=["ops"])
    async def ready() -> JSONResponse:
        """Readiness: dependencies (the database) are reachable."""
        db_ok = await ping_database()
        body = {"status": "ready" if db_ok else "not_ready", "database": db_ok}
        return JSONResponse(body, status_code=200 if db_ok else 503)

    logger.info("api started", extra={"environment": settings.environment.value})
    return app


app = create_app()
