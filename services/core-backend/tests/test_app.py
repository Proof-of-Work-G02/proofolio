import json
import logging
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError
from starlette.responses import Response

from core_backend.config import Settings
from core_backend.logging import JsonFormatter, request_id

FRONTEND_ORIGIN = "http://localhost:5173"


def test_health_generates_request_id(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert UUID(response.headers["X-Request-Id"]).version == 4


def test_health_echoes_request_id(client: TestClient) -> None:
    response = client.get("/health", headers={"X-Request-Id": "req-health"})
    assert response.headers["X-Request-Id"] == "req-health"


@pytest.mark.parametrize(
    ("method", "path", "status", "error_code"),
    [("GET", "/missing", 404, "NOT_FOUND"), ("POST", "/health", 405, "BAD_REQUEST")],
)
def test_routing_errors_have_standard_body(
    client: TestClient, method: str, path: str, status: int, error_code: str
) -> None:
    response = client.request(method, path)
    assert response.status_code == status
    error = response.json()["error"]
    assert error["code"] == error_code
    assert error["requestId"] == response.headers["X-Request-Id"]
    if status == 405:
        assert response.headers["Allow"] == "GET"


class Payload(BaseModel):
    count: int


def test_validation_errors_are_sanitized(app: FastAPI, client: TestClient) -> None:
    @app.post("/test-payload")
    async def accept_payload(payload: Payload) -> dict[str, int]:
        return {"count": payload.count}

    response = client.post("/test-payload", json={"count": "private input"})
    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Invalid request fields.",
            "requestId": response.headers["X-Request-Id"],
        }
    }
    malformed = client.post(
        "/test-payload", content="{", headers={"Content-Type": "application/json"}
    )
    assert malformed.status_code == 400
    assert malformed.json()["error"]["code"] == "BAD_REQUEST"


def test_unhandled_exception_returns_safe_body_with_cors(
    app: FastAPI, client: TestClient
) -> None:
    @app.get("/test-failure")
    async def fail() -> Response:
        raise RuntimeError("private exception message")

    response = client.get(
        "/test-failure",
        headers={"X-Request-Id": "req-failure", "Origin": FRONTEND_ORIGIN},
    )
    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "Internal server error.",
            "requestId": "req-failure",
        }
    }
    assert response.headers["X-Request-Id"] == "req-failure"
    assert response.headers["Access-Control-Allow-Origin"] == FRONTEND_ORIGIN
    assert response.headers["Access-Control-Expose-Headers"] == "X-Request-Id"


def test_cors_preflight_accepts_only_configured_origin(client: TestClient) -> None:
    headers = {
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "X-Request-Id",
        "X-Request-Id": "req-preflight",
    }
    allowed = client.options("/health", headers={**headers, "Origin": FRONTEND_ORIGIN})
    assert allowed.status_code == 200
    assert allowed.headers["Access-Control-Allow-Origin"] == FRONTEND_ORIGIN
    assert allowed.headers["Access-Control-Allow-Credentials"] == "true"
    assert allowed.headers["X-Request-Id"] == "req-preflight"

    denied = client.options(
        "/health", headers={**headers, "Origin": "https://other.example"}
    )
    assert denied.status_code == 400
    assert "Access-Control-Allow-Origin" not in denied.headers
    assert denied.json()["error"]["code"] == "BAD_REQUEST"
    assert denied.json()["error"]["requestId"] == denied.headers["X-Request-Id"]


def test_request_logging_includes_correlation_ids(
    app: FastAPI, client: TestClient
) -> None:
    @app.get("/test-log")
    async def log_in_request() -> Response:
        record = logging.LogRecord("test", logging.INFO, __file__, 0, "Event", (), None)
        record.__dict__.update(jobId="job-example", taskId="task-example")
        return Response(JsonFormatter().format(record), media_type="application/json")

    response = client.get("/test-log", headers={"X-Request-Id": "req-log"})
    assert len(response.text.splitlines()) == 1
    log = json.loads(response.text)
    assert log["timestamp"].endswith("Z")
    assert log["level"] == "INFO"
    assert log["message"] == "Event"
    assert log["requestId"] == "req-log"
    assert log["jobId"] == "job-example"
    assert log["taskId"] == "task-example"
    assert request_id.get() is None


def test_aws_endpoints_are_optional(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert str(settings.aws_endpoint_url_s3).startswith("http://localhost:")
    assert str(settings.aws_endpoint_url_sqs).startswith("http://localhost:")
    monkeypatch.delenv("AWS_ENDPOINT_URL_S3")
    monkeypatch.delenv("AWS_ENDPOINT_URL_SQS")
    aws_settings = Settings()
    assert aws_settings.aws_endpoint_url_s3 is None
    assert aws_settings.aws_endpoint_url_sqs is None


@pytest.mark.usefixtures("settings")
def test_required_secret_has_no_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SESSION_SECRET")
    with pytest.raises(ValidationError, match="session_secret"):
        Settings()
