from typing import Literal

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from core_backend.config import Settings
from core_backend.errors import handle_http_error, handle_validation_error
from core_backend.middleware import (
    REQUEST_ID_HEADER,
    CoreCORSMiddleware,
    RequestContextMiddleware,
    UnexpectedErrorMiddleware,
)


def create_app(settings: Settings) -> FastAPI:
    app = FastAPI(openapi_url=None, redirect_slashes=False)
    app.state.settings = settings
    app.add_exception_handler(HTTPException, handle_http_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_middleware(UnexpectedErrorMiddleware)
    app.add_middleware(
        CoreCORSMiddleware,
        allow_origins=[str(settings.frontend_url).removesuffix("/")],
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type", "X-CSRF-Token", REQUEST_ID_HEADER],
        expose_headers=[REQUEST_ID_HEADER],
    )
    app.add_middleware(RequestContextMiddleware)

    @app.get("/health")
    async def health() -> dict[str, Literal["ok"]]:
        return {"status": "ok"}

    return app
