import uvicorn

from core_backend.config import Settings
from core_backend.logging import configure_logging
from core_backend.main import create_app


def main() -> None:
    settings = Settings()
    configure_logging(settings.log_level)
    uvicorn.run(
        create_app(settings),
        host="0.0.0.0",
        port=8000,
        log_config=None,
        access_log=False,
    )


if __name__ == "__main__":
    main()
