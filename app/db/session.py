"""数据库连接、会话与事务管理。"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.db.exceptions import DatabaseSessionError, DatabaseTransactionError


class DatabaseRuntime:
    """数据库运行时容器，统一管理 engine 与 session。"""

    def __init__(
        self,
        *,
        database_url: str,
        echo_sql: bool = False,
        pool_pre_ping: bool = True,
    ) -> None:
        connect_args: dict[str, object] = {}
        if database_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        self._engine = create_engine(
            database_url,
            echo=echo_sql,
            pool_pre_ping=pool_pre_ping,
            future=True,
            connect_args=connect_args,
        )
        self._session_factory = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            class_=Session,
        )

    @property
    def engine(self) -> Engine:
        """返回底层 SQLAlchemy engine。"""
        return self._engine

    @contextmanager
    def session_scope(self) -> Iterator[Session]:
        """提供带自动提交/回滚的会话上下文。"""
        try:
            session = self._session_factory()
        except SQLAlchemyError as exc:
            raise DatabaseSessionError("数据库会话创建失败。") from exc

        try:
            yield session
            session.commit()
        except SQLAlchemyError as exc:
            try:
                session.rollback()
            except SQLAlchemyError as rollback_exc:
                raise DatabaseTransactionError("数据库事务回滚失败。") from rollback_exc
            raise DatabaseTransactionError("数据库事务执行失败。") from exc
        finally:
            session.close()

    def dispose(self) -> None:
        """关闭底层连接池。"""
        self._engine.dispose()

