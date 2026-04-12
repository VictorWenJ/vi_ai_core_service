"""数据库基础设施异常定义。"""


class DatabaseError(RuntimeError):
    """数据库访问相关通用异常。"""


class DatabaseSessionError(DatabaseError):
    """数据库会话创建或关闭失败异常。"""


class DatabaseTransactionError(DatabaseError):
    """数据库事务提交或回滚失败异常。"""

