"""SQLAlchemy ORM 公共基类。"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class DBModelBase(DeclarativeBase):
    """全项目共享的 ORM 基类。"""

