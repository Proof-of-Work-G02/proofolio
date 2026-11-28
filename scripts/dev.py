#!/usr/bin/env python3
"""Local development helper (KAN-8). Works the same on Windows, macOS and Linux.

    python scripts/dev.py up       start Postgres, ElasticMQ, S3 (RustFS); create buckets; run migrations
    python scripts/dev.py smoke    prove every queue, DLQ and bucket works
    python scripts/dev.py down     stop the stack (data is kept)
    python scripts/dev.py reset    stop, delete all data, start again
    python scripts/dev.py migrate  run database migrations (Core first, then Website Service)
    python scripts/dev.py ps|logs  show containers / follow logs

  Contracts (KAN-7), no Docker needed, Node 20+:
    python scripts/dev.py contracts-setup     install the tooling (npm ci + Python venv), once
    python scripts/dev.py contracts-validate  every schema compiles, valid examples pass, invalid ones fail
    python scripts/dev.py contracts-types     regenerate TypeScript and Python types (commit the result)
    python scripts/dev.py contracts-check     validate + generated types up to date + types smoke test
    python scripts/dev.py contracts-breaking  breaking-change check against origin/main

  CI (KAN-9):
    python scripts/dev.py test                contracts and Core Backend checks
    python scripts/dev.py backend-test        Core Backend lint, type checks and tests
                                              (add `smoke` after `up` for the compose-smoke check)

Uses .env when it exists, otherwise .env.example. Only needs Python 3.10+ and Docker.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPOSE_FILE = ROOT / "infra" / "compose" / "docker-compose.yml"
INFRA_SERVICES = ["postgres", "elasticmq", "s3"]
CONTRACT_TOOLING = ROOT / "contracts" / "tooling"

# Migration histories, in the order they must run: websites has foreign keys to Core tables.
MIGRATION_DIRS = [ROOT / "services" / "core-backend", ROOT / "services" / "website-service"]


def env_file() -> Path:
    local = ROOT / ".env"
    return local if local.exists() else ROOT / ".env.example"


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
    return values


def compose(*args: str, check: bool = True) -> int:
    path = env_file()
    cmd = ["docker", "compose", "--env-file", str(path), "-f", str(COMPOSE_FILE), *args]
    env = {**os.environ, "PROOFOLIO_ENV_FILE": str(path)}
    print("+ " + " ".join(cmd[2:]), flush=True)
    code = subprocess.call(cmd, env=env)
    if check and code != 0:
        sys.exit(code)
    return code


def require_docker() -> None:
    if shutil.which("docker") is None:
        sys.exit("Docker is not installed or not on PATH. Install Docker Desktop first.")
    if subprocess.call(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
        sys.exit("Docker is installed but not running. Start Docker Desktop and try again.")


def cmd_up() -> None:
    print(f"Using {env_file().name}")
    compose("up", "-d", "--build", "--wait", *INFRA_SERVICES)
    compose("run", "--rm", "--build", "init")
    cmd_migrate()
    env = read_env(env_file())
    print(
        "\nStack is up.\n"
        f"  Postgres       localhost:{env.get('POSTGRES_PORT', '5432')}  (db {env.get('POSTGRES_DB', 'proofolio')})\n"
        f"  SQS            http://localhost:{env.get('SQS_PORT', '9324')}\n"
        f"  S3 (RustFS)    http://localhost:{env.get('S3_PORT', '9000')}   console: http://localhost:{env.get('S3_CONSOLE_PORT', '9001')}/rustfs/console/index.html\n"
        "Next: python scripts/dev.py smoke"
    )


def cmd_migrate() -> None:
    env = {**os.environ, **read_env(env_file())}
    ran = False
    for service in MIGRATION_DIRS:
        if not (service / "alembic.ini").exists():
            continue
        ran = True
        print(f"Migrating {service.name}...", flush=True)
        code = subprocess.call([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=service, env=env)
        if code != 0:
            sys.exit(f"Migrations failed in {service.name}. Is alembic installed in this Python? ({sys.executable})")
    if not ran:
        print("No migrations yet (BE-8 adds them); skipping.")


def cmd_smoke() -> None:
    sys.exit(compose("run", "--rm", "--build", "smoke", check=False))


def cmd_down() -> None:
    compose("--profile", "tools", "down", "--remove-orphans")


def cmd_reset() -> None:
    compose("--profile", "tools", "down", "--volumes", "--remove-orphans")
    cmd_up()


def run(cmd: list[str], cwd: Path = CONTRACT_TOOLING) -> None:
    print("+ " + " ".join(cmd), flush=True)
    code = subprocess.call(cmd, cwd=cwd, shell=sys.platform == "win32" and cmd[0] == "npm")
    if code != 0:
        sys.exit(code)


def node(script: str, *args: str) -> None:
    if not (CONTRACT_TOOLING / "node_modules").exists():
        sys.exit("Contract tooling is not installed. Run: python scripts/dev.py contracts-setup")
    run(["node", script, *args])


def cmd_contracts_setup() -> None:
    run(["npm", "ci", "--no-audit", "--no-fund"])
    venv = CONTRACT_TOOLING / ".venv"
    if not venv.exists():
        run([sys.executable, "-m", "venv", str(venv)])
    py = venv / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    run([str(py), "-m", "pip", "install", "-q", "-r", "requirements.txt"])


def cmd_contracts_check() -> None:
    node("validate.mjs")
    node("generate-types.mjs", "--check")
    node("test-types.mjs")


def cmd_test() -> None:
    cmd_contracts_check()
    node("breaking-check.mjs")
    cmd_backend_test()


def cmd_backend_test() -> None:
    service = ROOT / "services" / "core-backend"
    run([sys.executable, "-m", "ruff", "check", "."], cwd=service)
    run([sys.executable, "-m", "mypy"], cwd=service)
    run([sys.executable, "-m", "pytest"], cwd=service)


COMMANDS = {
    "up": cmd_up,
    "down": cmd_down,
    "smoke": cmd_smoke,
    "reset": cmd_reset,
    "migrate": cmd_migrate,
    "ps": lambda: compose("ps", "-a"),
    "logs": lambda: compose("logs", "-f", "--tail", "100"),
    "contracts-setup": cmd_contracts_setup,
    "contracts-validate": lambda: node("validate.mjs"),
    "contracts-types": lambda: node("generate-types.mjs"),
    "contracts-check": cmd_contracts_check,
    "contracts-breaking": lambda: node("breaking-check.mjs", *sys.argv[2:]),
    "test": cmd_test,
    "backend-test": cmd_backend_test,
}
DOCKER_COMMANDS = {"up", "down", "smoke", "reset", "ps", "logs"}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(2)
    if sys.argv[1] in DOCKER_COMMANDS:
        require_docker()
    COMMANDS[sys.argv[1]]()


if __name__ == "__main__":
    main()
