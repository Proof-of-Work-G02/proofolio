from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core_backend.config import Settings
from core_backend.main import create_app


@pytest.fixture
def settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    example = Path(__file__).resolve().parents[3] / ".env.example"
    for line in example.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            key, value = line.split("=", 1)
            monkeypatch.setenv(key, value)
    return Settings()


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    return create_app(settings)


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)
