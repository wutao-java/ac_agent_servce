"""管理 LangGraph 检查点使用的异步 PostgreSQL 连接池。"""

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from backend.config.settings import (
    AI_AGENT_CHECKPOINTER_POSTGRES_MAX,
    AI_AGENT_CHECKPOINTER_POSTGRES_MIN,
    AI_AGENT_CHECKPOINTER_POSTGRES_URL,
    config_manager,
)


_async_pg_pool: AsyncConnectionPool | None = None


async def get_async_pg_pool() -> AsyncConnectionPool:
    """延迟创建并返回全局异步 PostgreSQL 连接池。"""

    global _async_pg_pool
    if _async_pg_pool is None:
        # 连接池只在启用持久化检查点后创建，避免默认启动依赖 PostgreSQL。
        _async_pg_pool = AsyncConnectionPool(
            config_manager.get(AI_AGENT_CHECKPOINTER_POSTGRES_URL),
            min_size=config_manager.get(AI_AGENT_CHECKPOINTER_POSTGRES_MIN),
            max_size=config_manager.get(AI_AGENT_CHECKPOINTER_POSTGRES_MAX),
            kwargs={
                "autocommit": True,
                "prepare_threshold": 0,
                "row_factory": dict_row,
            },
            open=False,
        )
        await _async_pg_pool.open()
    return _async_pg_pool


async def close_async_pg_pool() -> None:
    """关闭异步 PostgreSQL 连接池。"""

    global _async_pg_pool
    if _async_pg_pool is not None:
        await _async_pg_pool.close()
        # 清空全局引用，允许后续应用生命周期重新创建连接池。
        _async_pg_pool = None
