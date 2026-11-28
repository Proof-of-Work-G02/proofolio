FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY services/_shared/python/pyproject.toml ./shared/pyproject.toml
COPY services/_shared/python/proofolio_contracts/ ./shared/proofolio_contracts/
COPY services/core-backend/pyproject.toml ./core/pyproject.toml
COPY services/core-backend/src/ ./core/src/
RUN pip install --no-cache-dir ./shared ./core

USER 10001:10001
EXPOSE 8000
CMD ["python", "-m", "core_backend"]
