import logging
from uuid import uuid4

from proofolio_contracts.models import ErrorCode
from starlette.datastructures import Headers, MutableHeaders
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from core_backend.errors import error_response
from core_backend.logging import request_id

logger = logging.getLogger(__name__)
REQUEST_ID_HEADER = "X-Request-Id"


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        supplied_id = Headers(scope=scope).get(REQUEST_ID_HEADER, "")
        if supplied_id.strip() and supplied_id.isascii() and supplied_id.isprintable():
            current_id = supplied_id
        else:
            current_id = str(uuid4())
        token = request_id.set(current_id)

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = current_id
                logger.info(
                    "HTTP response started",
                    extra={"event": "http.response", "statusCode": message["status"]},
                )
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            request_id.reset(token)


class CoreCORSMiddleware(CORSMiddleware):
    def preflight_response(self, request_headers: Headers) -> Response:
        response = super().preflight_response(request_headers)
        if response.status_code != 400:
            return response
        headers = dict(response.headers)
        headers.pop("content-type", None)
        headers.pop("content-length", None)
        return error_response(
            400, ErrorCode.BAD_REQUEST, "CORS preflight denied.", headers
        )


class UnexpectedErrorMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        response_started = False

        async def track_response(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, track_response)
        except Exception:
            logger.error(
                "Unhandled HTTP request error",
                extra={"event": "http.error", "errorCode": ErrorCode.INTERNAL_ERROR},
            )
            if response_started:
                raise
            response = error_response(
                500, ErrorCode.INTERNAL_ERROR, "Internal server error."
            )
            await response(scope, receive, send)
