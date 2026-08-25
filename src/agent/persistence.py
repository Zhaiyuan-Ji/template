"""定义 Thread 内短期记忆使用的 PostgreSQL Checkpointer 规范。

生成的项目统一使用 AsyncPostgresSaver，并从 DATABASE_URL 读取连接地址。直接运行
Graph 时，应在异步上下文中创建 Checkpointer、执行一次 setup() 迁移，并在同一
生命周期内编译和调用 Graph。通过 Agent Server 运行时，不在源码中重复创建
Checkpointer，而是由使用 PostgreSQL 的 Server 持久化层管理。

所有运行都必须提供稳定的 thread_id，并固定使用 durability="async"。本文件不
提供 Store、跨 Thread 长期记忆、InMemory、SQLite 或 State 加密实现。
"""
