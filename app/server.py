"""FastAPI application entrypoint for HTTP serving."""

from __future__ import annotations

import logging

from fastapi import FastAPI

from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.config import AppConfig
from app.observability.events import log_startup_config_summary
from app.observability.logging_setup import configure_logging
from app.observability.middleware import request_logging_middleware

app = FastAPI(title="vi_ai_core_service")
app.middleware("http")(request_logging_middleware)
app.include_router(health_router)
app.include_router(chat_router)


@app.on_event("startup")
def on_startup() -> None:
    try:
        config = AppConfig.from_env()
        configure_logging(config.observability)
        log_startup_config_summary(config)
    except Exception:
        logging.basicConfig(level=logging.ERROR)
        logging.getLogger("vi_ai_core_service.startup").exception(
            "Application startup initialization failed."
        )
        raise
