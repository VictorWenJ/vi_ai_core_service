"""数据库 schema 初始化入口（SQLAlchemy + Alembic）。"""

from __future__ import annotations

from pathlib import Path
from threading import Lock

from alembic import command
from alembic.config import Config

from app.db.base import DBModelBase
from app.db.session import DatabaseRuntime

_SCHEMA_LOCK = Lock()
_INITIALIZED_ENGINE_IDS: set[int] = set()


def _build_alembic_config(database_url: str) -> Config:
    """构建 Alembic 配置并注入当前数据库连接地址。"""
    alembic_ini_path = Path(__file__).resolve().parents[2] / "alembic.ini"
    alembic_script_path = Path(__file__).resolve().parent / "alembic"
    config = Config(str(alembic_ini_path))
    config.set_main_option("script_location", str(alembic_script_path))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def ensure_database_schema(database_runtime: DatabaseRuntime) -> None:
    """确保当前 engine 对应的 schema 已初始化。"""
    engine_id = id(database_runtime.engine)
    if engine_id in _INITIALIZED_ENGINE_IDS:
        return
    with _SCHEMA_LOCK:
        if engine_id in _INITIALIZED_ENGINE_IDS:
            return
        try:
            alembic_config = _build_alembic_config(str(database_runtime.engine.url))
            command.upgrade(alembic_config, "head")
        except Exception:
            # Alembic 异常时兜底 create_all，保证本地和测试可运行。
            # 正式生产迁移仍应通过 Alembic 执行。
            import app.rag.repository.models  # noqa: F401

            DBModelBase.metadata.create_all(bind=database_runtime.engine)
        _INITIALIZED_ENGINE_IDS.add(engine_id)
