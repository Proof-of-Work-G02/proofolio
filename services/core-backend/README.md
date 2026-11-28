# Core Backend

The FastAPI service listens on port 8000. `GET /health` returns `{"status":"ok"}`
and checks that the HTTP process is running. All responses include `X-Request-Id`.

## Run locally

With Python 3.12 active in a virtual environment, install from the repository root.

```sh
python -m pip install -e services/_shared/python -e 'services/core-backend[dev]'
```

Export the settings from the root `.env.example` or supply them through your
environment. The service reads environment variables directly. For example, the
following POSIX shell commands run it with local settings.

```sh
set -a
. ./.env.example
set +a
python -m core_backend
```

Set `FRONTEND_URL` to the exact browser origin. Leave `AWS_ENDPOINT_URL_S3` and
`AWS_ENDPOINT_URL_SQS` unset on AWS to use the default AWS endpoints. Set the
bucket names, queue URLs, `DATABASE_URL`, `SESSION_SECRET`, and
`INTERNAL_SERVICE_SECRET` for the target environment. The example secrets are
for local use only.

## Container

Build from the repository root so Docker can include the shared Python contracts.

```sh
docker build -f services/core-backend/Dockerfile -t proofolio-core-backend .
docker run --rm --env-file .env.example -p 8000:8000 proofolio-core-backend
```

## Checks

Run from the repository root after installing the development dependencies.

```sh
python scripts/dev.py backend-test
```
