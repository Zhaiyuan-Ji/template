# LangGraph Agent Template

## 1. 模板定位

这个目录是供 Codex 等编码 Agent 阅读的 LangGraph 项目规范，不是一个可以直接
运行的 Agent，也不包含任何具体业务。

使用本模板时，应当在新的目标目录生成项目。不要直接在模板目录内填入业务代码。

## 2. 生成前先设计业务

生成代码前必须先和用户明确：

- Agent 接收什么输入；
- Agent 最终返回什么；
- 完整业务包含哪些阶段；
- 哪些阶段存在动态跳转或循环；
- 哪些任务需要并行；
- 是否需要模型、工具或 Subgraph；
- 哪些数据需要跨节点保存。

信息不足时先提问。不能使用假节点、占位业务或 TODO 代替用户决策。

固定流程：

```text
理解业务
→ 设计 Graph
→ 为每张 Graph 设计 State
→ 确定 Schema、Configuration、Model、Prompt 和 Tool
→ 向用户确认设计
→ 在目标目录生成代码
```

## 3. 目标项目的基础结构

```text
<project>/
├── TEMPLATE.md
├── pyproject.toml
├── langgraph.json
├── .env.example
├── .gitignore
├── .editorconfig
├── scripts/
│   └── setup.ps1
└── src/agent/
    ├── __init__.py
    ├── graph.py
    ├── state.py
    ├── schemas.py
    ├── configuration.py
    ├── models.py
    ├── prompts.py
    ├── tools.py
    └── persistence.py
```

Template 的通用基础设施是可以直接复用的真实代码：

```text
state.py
configuration.py
models.py
persistence.py
.gitignore
.editorconfig
scripts/setup.ps1
```

其他文件保留固定职责和命名，由 Codex 根据业务生成。生成目标项目时：

- `graph.py` 和 `state.py` 必须存在；
- `configuration.py` 和 `models.py` 由整棵 Graph 树共享；
- `persistence.py` 固定存在，并统一说明 PostgreSQL Checkpointer；
- 没有结构化模型输出时可以不生成 `schemas.py`；
- 没有模型 Prompt 时可以不生成 `prompts.py`；
- 没有工具时可以不生成 `tools.py`；
- 不提前创建没有真实业务的 Subgraph 目录。

## 4. 文件职责

### `graph.py`

定义节点函数、Graph 结构、固定 Edge、Command 路由、Send 并行和 Subgraph 挂载。
根 Graph 对外导出变量统一命名为 `graph`。

### `state.py`

提供所有项目统一继承的最低 State：

```text
messages
```

具体项目只在同一个 `State` 中增加真实业务字段。

不要在 `state.py` 中定义模型结构化输出，也不要默认给每个节点创建 State。

### `schemas.py`

定义模型单次结构化输出，例如分类、判断、规划和完成信号。这些类型不是 Graph
运行 State。

### `configuration.py`

提供默认 DeepSeek 模型、超时、重试和 `recursion_limit` 的真实配置类。具体项目
继续增加业务参数；durability 固定为 `async`，不做成配置字段。

### `models.py`

使用 `langchain-deepseek` 创建默认业务模型，对其他模块统一返回 `BaseChatModel`。
默认模型为 `deepseek-v4-flash`，API Key 从 `DEEPSEEK_API_KEY` 读取。

Graph 和 State 不能直接导入 `ChatDeepSeek`。以后更换模型时由开发者修改
`models.py` 和依赖，Codex 不自动检查或替换模型兼容性。

### `prompts.py`

保存当前 Graph 使用的 Prompt。Prompt 描述模型任务；模型返回格式由
`schemas.py` 描述。

### `tools.py`

保存当前 Graph 使用的工具，文件名统一使用复数 `tools.py`。标准工具执行优先
使用 ToolNode；只有权限、事务、审计、服务端参数注入或特殊错误处理等业务要求
存在时，才实现自定义工具节点。

### `persistence.py`

提供 `AsyncPostgresSaver` 数据库迁移、异步生命周期、`DATABASE_URL` 读取和
Thread Config 校验的真实实现。Agent Server 模式仍由使用 PostgreSQL 的 Server
持久化层管理。

## 5. 一个 Graph 一个 State

每张 Graph 只定义一个主要 State。根 State 已提供：

```python
class State(MessagesState, total=False):
    pass
```

同一张 Graph 的所有节点读写这个 State，各节点只使用自己负责的字段。

State 保存可序列化的原始业务数据，不保存已经拼接好的 Prompt。Prompt 在节点
调用模型前根据原始 State 临时格式化。

不能放入 State 的内容：

- 模型名称、并发数和循环上限；
- API Key 和其他秘密；
- 模型、数据库连接、HTTP Client、文件句柄和锁；
- 只在一次函数调用中使用的局部变量；
- 被当前节点立即消费的临时路由结果。

并行节点共同写入同一字段时，必须根据业务合并方式声明 Reducer。

调用外部副作用的流程必须在 State 中保存稳定的业务幂等 ID 和执行结果。每个
业务循环必须保存自己的迭代次数和完成状态，不能只依赖 `recursion_limit`。

如果确实需要限制 Graph 对外输入或 Subgraph 输出，可以按需创建
`contracts.py`；普通节点之间仍然只使用 State。模板自身不包含该文件。

## 6. Node 命名

普通函数节点的注册名称必须与函数名称完全一致：

```python
async def clarify_with_user(...):
    ...


graph_builder.add_node("clarify_with_user", clarify_with_user)
```

函数名称必须描述业务行为，例如：

```text
clarify_with_user
write_research_brief
generate_final_report
execute_research_tools
```

禁止使用：

```text
node_a
step_1
process
handler
run_task
do_work
```

ToolNode 变量名和注册名称也保持一致：

```python
tools = ToolNode([...])
graph_builder.add_node("tools", tools)
```

Subgraph 使用以下对应关系：

```text
Node 名称：research
目录名称：research/
导出变量：research_graph
```

## 7. 控制流规则

```text
固定且无条件的路线
→ Edge

节点更新 State 并动态跳转
→ Command

运行时动态并行创建多个任务
→ Send

标准模型工具调用和 ToolMessage 回写
→ ToolNode

多步骤且拥有独立 State 的并发 Agent
→ Subgraph

需要暂停并等待用户输入
→ interrupt + Command(resume=...)

瞬时网络或模型错误
→ RetryPolicy
```

本模板不使用 Conditional Edge。动态路由统一由产生决策的节点返回 Command，
避免为了路由创建临时 State 或额外路由函数。

## 8. Subgraph 规则

一次性并行任务使用 Send 到普通节点即可。满足以下特征时才拆 Subgraph：

- 内部包含多个步骤或循环；
- 需要独立消息历史或独立 State；
- 会被多个并行任务同时实例化；
- 对父图只暴露明确输入和输出。

每张 Subgraph 对应一个同名目录，并在该目录拥有自己的 `graph.py`、`state.py`、
`schemas.py`、`prompts.py` 和按需生成的 `tools.py`。

## 9. Configuration 和模型边界

整棵 Graph 树默认共享根目录的 Configuration 和模型创建入口。Subgraph 不重复
定义同类配置。

Configuration 只描述参数，模型实例化只放在 `models.py`。不能把模型工厂写进
`configuration.py`。

Template 默认使用 DeepSeek 官方 API 和 `deepseek-v4-flash`。具体项目没有收到
明确要求时沿用这个默认值；模型切换由开发者自行决定，不属于 Codex 的自动检查
范围。

DATABASE_URL 不进入 Configuration，由 `persistence.py` 从环境变量读取。
DEEPSEEK_API_KEY 不进入 Configuration，由 `models.py` 从环境变量读取。

## 10. PostgreSQL 短期记忆

模板只支持单个 Thread 内的短期记忆，不使用跨 Thread Store。

### Agent Server 模式

根 Graph 直接编译并导出：

```python
graph = graph_builder.compile()
```

源码中不重复创建 Checkpointer。部署或 Agent Server 必须使用 PostgreSQL 持久化
层，不能依赖进程内存。

### 直接运行模式

统一使用 `AsyncPostgresSaver`：

```python
async with AsyncPostgresSaver.from_conn_string(DATABASE_URL) as checkpointer:
    await checkpointer.setup()
    graph = graph_builder.compile(checkpointer=checkpointer)
```

Graph 的调用必须发生在 Checkpointer 的异步生命周期内。`setup()` 用于创建或
迁移 Checkpoint 表；生产部署应把迁移作为明确的启动或发布步骤。

每次运行必须提供稳定的 Thread ID：

```python
config = {
    "configurable": {"thread_id": thread_id},
    "recursion_limit": 100,
}
```

`thread_id` 使用 UUID 或短业务 ID，长度不得超过 255。调用统一指定：

```python
await graph.ainvoke(
    inputs,
    config=config,
    durability="async",
)
```

不提供 InMemory、SQLite、Store 或 State 加密分支。生产环境必须定义 Thread 和
Checkpoint 的保留、归档及删除策略。

## 11. Interrupt 和副作用

需要人工审批或补充信息时，在业务节点中调用 `interrupt()`，并通过同一个
`thread_id` 使用 `Command(resume=...)` 恢复。

`interrupt()` 之前不能执行不可重复的外部副作用，因为节点恢复时会从开头重新
执行。付款、发信、删除和数据库写入必须放在审批后的独立节点，并使用业务幂等
ID 防止重复执行。

## 12. 错误、重试和循环

- 网络查询、只读 API 和模型调用可以配置 `RetryPolicy`；
- 有副作用节点只有实现幂等后才能重试；
- 模型可修复的工具错误写回 State，再用 Command 返回模型节点；
- 用户可修复的问题使用 `interrupt()`；
- 未知异常直接抛出，不能用宽泛捕获隐藏；
- 每个循环使用业务计数控制退出，`recursion_limit` 只作为最后保护。

## 13. Tool 和业务服务边界

`tools.py` 中的模型工具只负责参数入口和结果返回。权限、事务、幂等、业务数据库
和外部 API 编排放在具体项目按需创建的 `services/` 中。Template 不预建空
`services/` 目录。

小 Graph 可以把节点函数和 Builder 都放在 `graph.py`。节点较多或文件明显难以
连续阅读时，才在当前 Graph 目录按需创建 `nodes.py`，不能建立全局 Node 仓库。

## 14. Streaming 和调试

需要流式输出时，统一使用异步 Graph API，并同时观察 `messages` 和 `updates`；
存在 Subgraph 时开启 `subgraphs=True`。调用仍固定使用 `durability="async"`。

生成项目应能使用：

```text
graph.get_state(config)
graph.get_state_history(config)
graph.update_state(config, values)
```

用于检查当前 State、历史 Checkpoint、修正 State 和从旧 Checkpoint 创建新执行
分支。

## 15. 本地 PostgreSQL

本机统一使用 `E:\PostgreSQL` 中独立运行的 PostgreSQL 16。生成的 Agent 项目只
通过 `DATABASE_URL` 连接数据库，不能在项目中重复生成 `compose.yaml` 或管理
PostgreSQL 容器生命周期。

首次开发或电脑重启后，先确认统一数据库正在运行：

```powershell
cd E:\PostgreSQL
docker compose up -d
```

目标项目的默认连接地址为：

```text
postgresql://langgraph:langgraph@localhost:5432/langgraph?sslmode=disable
```

然后在目标项目中运行：

```powershell
.\scripts\setup.ps1
```

脚本在 `.env` 不存在时复制 `.env.example`，执行 `uv sync`，并通过
`agent-db-setup` 初始化 LangGraph Checkpoint 表。脚本不启动或停止数据库。
开始调用模型前仍需填写 `DEEPSEEK_API_KEY`。

`.gitignore` 排除 `.env`、虚拟环境、Python 缓存和 Agent Server 本地数据；
`.editorconfig` 固定 UTF-8、LF、末尾换行和 Python 四空格缩进。

代码生成或修改完成后统一执行：

```powershell
uv run ruff format .
uv run ruff check .
```

## 16. 生成目标项目

Codex 完成业务设计并获得用户确认后：

1. 在用户指定的新目录创建项目；
2. 复用 State、Configuration、默认 DeepSeek Models 和 Persistence，并连接
   `E:\PostgreSQL` 中统一运行的本地 PostgreSQL；
3. 只创建业务实际使用的其他文件和 Subgraph；
4. 没有明确换模要求时保留默认 DeepSeek 依赖；
5. 生成真实 `.env.example`，但不写入生产密钥；
6. 生成真实 `langgraph.json`，Graph ID 和导出路径必须对应源码；
7. 确保目录层级、Graph 层级和节点命名一致。
8. 不在目标项目中生成 PostgreSQL `compose.yaml`。

## 17. 第一版明确不包含

- 具体业务逻辑；
- 具体工具厂商；
- 测试目录和测试规范；
- AGENTS.md、README.md 和 docs 目录；
- 鉴权、业务数据库、队列、限流和监控实现；
- 通用基类、抽象 Graph、插件注册中心和代码生成引擎；
- Conditional Edge。
- LangChain `create_agent`、AgentMiddleware 和 Deep Agents；
- Store、跨 Thread 长期记忆、InMemorySaver 和 SQLiteSaver；
- State 加密、自定义 Checkpointer 和 DeltaChannel。
