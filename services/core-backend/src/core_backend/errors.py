from http import HTTPStatus

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from proofolio_contracts.models import Error, ErrorCode, ErrorResponse
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from core_backend.logging import request_id

HTTP_ERRORS = {
    400: ErrorCode.BAD_REQUEST,
    401: ErrorCode.UNAUTHENTICATED,
    403: ErrorCode.FORBIDDEN,
    404: ErrorCode.NOT_FOUND,
    409: ErrorCode.NOT_READY,
    413: ErrorCode.FILE_TOO_LARGE,
    415: ErrorCode.UNSUPPORTED_FILE_TYPE,
    422: ErrorCode.VALIDATION_ERROR,
    429: ErrorCode.RATE_LIMITED,
    503: ErrorCode.SERVICE_UNAVAILABLE,
}


def error_response(
    status: int,
    code: ErrorCode,
    message: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    current_id = request_id.get()
    assert current_id is not None, "HTTP error responses require request ID middleware"
    body = ErrorResponse(error=Error(code=code, message=message, requestId=current_id))
    content = body.model_dump(mode="json", exclude_none=True)
    return JSONResponse(content, status_code=status, headers=headers)



async def handle_http_error(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, HTTPException):
        raise exc

    try:
        message = HTTPStatus(exc.status_code).phrase
    except ValueError:
        message = "Request failed."

    fallback = (
        ErrorCode.INTERNAL_ERROR if exc.status_code >= 500 else ErrorCode.BAD_REQUEST
    )

    return error_response(
        exc.status_code,
        HTTP_ERRORS.get(exc.status_code, fallback),
        message,
        dict(exc.headers) if exc.headers else None,
    )


async def handle_validation_error(
    _request: Request, exc: Exception
) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        raise exc

    if any(error["type"] == "json_invalid" for error in exc.errors()):
        return error_response(400, ErrorCode.BAD_REQUEST, "Malformed JSON request.")

    return error_response(422, ErrorCode.VALIDATION_ERROR, "Invalid request fields.")
