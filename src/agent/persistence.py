"""提供 Thread 内短期记忆使用的 PostgreSQL Checkpointer。"""

import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

DATABASE_URL_ENV = "DATABASE_URL"
MAX_THREAD_ID_LENGTH = 255


def get_database_url() -> str:
    """读取 PostgreSQL 地址，并在缺失时给出明确错误。"""
    load_dotenv()
    database_url = os.getenv(DATABASE_URL_ENV, "").strip()
    if not database_url:
        msg = f"缺少环境变量 {DATABASE_URL_ENV}，无法创建 PostgreSQL Checkpointer。"
        raise RuntimeError(msg)
    return database_url


async def setup_checkpoint_database() -> None:
    """创建或升级 LangGraph Checkpoint 表。"""
    async with AsyncPostgresSaver.from_conn_string(get_database_url()) as checkpointer:
        await checkpointer.setup()


@asynccontextmanager
async def open_checkpointer() -> AsyncIterator[AsyncPostgresSaver]:
    """在一个明确的异步生命周期内提供 PostgreSQL Checkpointer。"""
    async with AsyncPostgresSaver.from_conn_string(get_database_url()) as checkpointer:
        yield checkpointer


def create_thread_config(
    thread_id: str,
    *,
    recursion_limit: int,
) -> RunnableConfig:
    """创建 Checkpoint 运行配置并校验 Thread 标识。"""
    normalized_thread_id = thread_id.strip()
    if not normalized_thread_id:
        msg = "thread_id 不能为空。"
        raise ValueError(msg)
    if len(normalized_thread_id) > MAX_THREAD_ID_LENGTH:
        msg = f"thread_id 长度不能超过 {MAX_THREAD_ID_LENGTH}。"
        raise ValueError(msg)
    if recursion_limit < 1:
        msg = "recursion_limit 必须大于 0。"
        raise ValueError(msg)

    return {
        "configurable": {"thread_id": normalized_thread_id},
        "recursion_limit": recursion_limit,
    }


def main() -> None:
    """执行 PostgreSQL Checkpoint 数据库初始化。"""
    asyncio.run(setup_checkpoint_database())


if __name__ == "__main__":
    main()
