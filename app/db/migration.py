"""数据库 schema 初始化入口。"""

from __future__ import annotations

from threading import Lock

from app.db.base import DBModelBase
from app.db.session import DatabaseRuntime

_SCHEMA_LOCK = Lock()
_INITIALIZED_ENGINE_IDS: set[int] = set()


def ensure_database_schema(database_runtime: DatabaseRuntime) -> None:
    """确保当前 engine 对应的 schema 已初始化。"""
    engine_id = id(database_runtime.engine)
    if engine_id in _INITIALIZED_ENGINE_IDS:
        return
    with _SCHEMA_LOCK:
        if engine_id in _INITIALIZED_ENGINE_IDS:
            return
        # 延迟导入，确保 RAG 控制面 ORM 模型已注册到 metadata。
        import app.rag.repository.models  # noqa: F401

        DBModelBase.metadata.create_all(bind=database_runtime.engine)
        _INITIALIZED_ENGINE_IDS.add(engine_id)

