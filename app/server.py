"""用于 HTTP 服务的 FastAPI 应用入口。"""

from __future__ import annotations

import logging

from fastapi import FastAPI

from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.config import AppConfig
from app.observability.log_until import log_report

app = FastAPI(title="vi_ai_core_service")
app.include_router(health_router)
app.include_router(chat_router)


@app.on_event("startup")
def on_startup() -> None:
    try:
        app_config = AppConfig.from_env()
        log_report("Server.on_startup.app_config", app_config)
    except Exception:
        logging.basicConfig(level=logging.ERROR)
        logging.getLogger("vi_ai_core_service.startup").exception(
            "应用启动初始化失败。"
        )
        raise
