# LangGraph Agent Template

## 1. 模板定位

这是供 Coding Agent 生成 LangGraph Agent 项目时遵守的固定工程规范。

模板只规定最终项目的目录、文件职责、Graph 组织方式和运行边界，不包含具体业务，
也不负责需求澄清、业务设计和方案确认。上述工作由独立 Skill 完成。

空文件是结构约束：即使当前业务暂时不需要 Prompt、Schema 或 Tool，也必须保留对应
文件，避免随意命名和职责混放。空文件只保留中文模块说明，不能填入虚假业务或示例
实现。

## 2. 固定项目结构

```text
<project>/
├── TEMPLATE.md
├── pyproject.toml
├── langgraph.json
├── langgraph.dev.json
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
    └── tools.py
```

`SKILL_REQUIREMENTS.md` 是模板仓库中用于设计未来 Skill 的辅助文档，不复制到生成后
的 Agent 项目中。

只有业务确实需要独立 Subgraph 时，才在 `src/agent/` 下创建与业务节点同名的目录：

```text
src/agent/<business>/
├── graph.py
├── state.py
├── schemas.py
├── prompts.py
└── tools.py
```

Subgraph 共用根目录的 `configuration.py` 和 `models.py`，不重复定义通用配置与模型
工厂。模板不创建 `nodes.py`、`services.py`、`contracts.py`、`docs/`、`tests/`、
`README.md` 或 `AGENTS.md`。

## 3. 文件职责

### `graph.py`

定义当前 Graph 的节点函数、Builder、Edge、Command、Send、ToolNode 和 Subgraph
挂载。节点函数写在构建函数外，Builder 只存在于构建函数内。

根 Graph 统一使用：

```python
def build_graph(): ...


graph = build_graph()
```

Subgraph 统一使用：

```python
def build_<business>_graph():
    ...


<business>_graph = build_<business>_graph()
```

构建函数内部使用当前 Graph 的 `State`、`GraphInput`、`GraphOutput` 和共享的
`Configuration`：

```python
graph_builder = StateGraph(
    State,
    input_schema=GraphInput,
    output_schema=GraphOutput,
    context_schema=Configuration,
)
```

最终只调用 `graph_builder.compile()`，不能在源码中创建或传入 Checkpointer。

### `state.py`

每张 Graph 对应一个 `state.py`，其中只定义一个主要 `State`，供这一层 Graph 的
全部节点传递运行时数据。

- 对话型 Agent 可以继承 `MessagesState`；
- 结构化工作流使用符合业务字段的 `TypedDict`；
- 不允许无条件默认使用 `MessagesState`；
- 不为每个节点分别定义 State；
- 并行节点写入同一字段时必须声明符合业务语义的 Reducer。

State 只保存需要跨节点传递或从 Checkpoint 恢复的可序列化业务数据。模型配置、
API Key、数据库连接、HTTP Client、文件句柄、格式化后的 Prompt 和一次调用内的
局部变量不能进入 State。

### `schemas.py`

定义当前 Graph 的公开输入 `GraphInput`、公开输出 `GraphOutput`，以及模型必须
遵守的结构化输出类型。

节点之间依然通过 `State` 传递数据。Schema 负责限制 Graph 边界和模型单次返回
格式，不能代替 State。

### `configuration.py`

定义整棵 Graph 树共享的 `Configuration`。它作为 `StateGraph` 的
`context_schema`，节点通过 `Runtime[Configuration]` 读取不可变运行参数：

```python
async def call_model(state: State, runtime: Runtime[Configuration]):
    configuration = runtime.context
```

`recursion_limit` 继续保存在 `configuration.py` 中作为默认运行配置，但它不是
State 字段。创建 Agent Server Run 时，调用方必须把该值放在 Run 的顶层
`config.recursion_limit` 中；仅把它放进 Runtime Context 不会限制 Graph 执行。

API Key、PostgreSQL URI 等秘密只存在于环境变量中，不能进入 Configuration。

### `models.py`

集中创建默认 DeepSeek 模型，对其他模块只暴露 `BaseChatModel`。Graph、State 和
Node 不能直接实例化 `ChatDeepSeek`。默认模型为 `deepseek-v4-flash`；以后更换
Provider 时由开发者修改本文件和依赖，Coding Agent 不自动检查兼容性。

### `prompts.py`

只保存当前 Graph 实际使用的 Prompt。Prompt 说明模型任务，结构化返回格式由
`schemas.py` 定义。没有 Prompt 时保留文件和中文模块说明，不创建占位常量。

### `tools.py`

只保存当前 Graph 实际使用的模型工具，文件名固定为复数 `tools.py`。标准工具调用
优先交给 `ToolNode` 执行并回写 `ToolMessage`。只有权限、事务、审计、服务端参数
注入或特殊错误处理确实存在时，才实现自定义工具节点。

## 4. Node 与 Graph 命名

普通函数节点的注册名称必须与函数名称完全一致：

```python
async def clarify_with_user(...):
    ...


graph_builder.add_node("clarify_with_user", clarify_with_user)
```

函数名必须直接描述业务行为，例如 `write_research_brief`、
`execute_research_tools`、`generate_final_report`。禁止使用 `node_a`、`step_1`、
`process`、`handler`、`run_task` 等无法表达业务含义的名称。

Subgraph 节点名、目录名和导出变量必须保持对应：

```text
节点名：research
目录名：research/
导出变量：research_graph
```

## 5. 控制流规则

| 业务含义 | LangGraph 结构 |
| --- | --- |
| 固定且无条件的下一步 | 普通 Edge |
| 节点更新 State 后动态选择下一步 | 类型化 Command |
| 运行时动态生成多个并行任务 | Send |
| 标准模型工具调用 | ToolNode |
| 拥有独立 State 的多步骤流程 | Subgraph |
| 暂停并等待人工输入或审批 | `interrupt()` 与 `Command(resume=...)` |

模板不使用 Conditional Edge。固定路线不能滥用 Command；动态路线也不能额外创建
只负责路由的临时 State 字段。

返回 Command 的节点必须通过 `Literal` 声明全部可能目的地，保证 Graph 可被 Studio
正确渲染：

```python
async def route_request(...) -> Command[Literal["use_tools", "finish"]]:
    ...
```

目的地名称必须与 `add_node()` 注册名称一致。一个由 Command 路由的节点不能再添加
静态出边，否则两条路线都会执行。Subgraph 跳回父图时按需使用 `Command.PARENT`。

## 6. Subgraph 与并行

一次性、单步骤并行任务使用 `Send` 到普通节点。只有内部仍包含多个步骤、循环、
独立消息历史或独立 State 时，才拆成 Subgraph。

每张 Subgraph 只向父图暴露明确的 `GraphInput` 和 `GraphOutput`。父图负责调度，
Subgraph 负责自己的内部流程；不能为了拆文件而制造额外 Graph 层级。

## 7. 异步边界

- Graph 构建函数使用普通 `def`；
- Node、Tool、模型调用、网络、数据库和文件 I/O 使用 `async def`；
- 模型统一使用 `ainvoke()` 或 `astream()`；
- HTTP 调用使用异步客户端；
- `async def` 中禁止直接调用 `requests`、`time.sleep()` 等阻塞接口；
- 无法替换的同步接口通过 `asyncio.to_thread()` 隔离。

未知异常直接抛出，不能使用宽泛捕获隐藏。网络和只读模型调用可以使用
`RetryPolicy`；有外部副作用的节点只有完成业务幂等后才能重试。

## 8. Thread 短期记忆与 Agent Server

本模板只提供单个 Thread 内的短期记忆，不提供 Store、跨 Thread 记忆、State
加密、InMemorySaver、SQLiteSaver 或自定义 Checkpointer。

Agent Server 是唯一默认运行入口。Server 负责 Thread、Run 和 PostgreSQL
Checkpoint 生命周期，Graph 源码只导出编译后的 Graph。

需要人工交互时调用 `interrupt()`，并在同一个 Thread 中使用
`Command(resume=...)` 恢复。`interrupt()` 之前不能执行不可重复的外部副作用，
因为恢复时节点会从开头重新执行。

每个业务循环必须在 State 中保存业务计数和完成状态；`recursion_limit` 只是防止
Graph 无限执行的最后保护。Agent Server 调用方还必须统一使用异步运行方式，并将
durability 设为 `async`。

## 9. PostgreSQL 约定

本机统一使用 `E:\PostgreSQL` 中运行的 PostgreSQL 16，不在 Agent 项目中生成
`compose.yaml`，也不由 Agent 项目启动、停止或迁移 PostgreSQL 服务。

一个 PostgreSQL 服务可以供多个 Agent 项目使用，但每个 Agent 项目或部署必须使用
独立数据库。数据库名由稳定的项目名生成，只使用小写字母、数字和下划线。

Agent Server 运行在 Docker 中，因此 PostgreSQL URI 必须使用
`host.docker.internal`，不能使用 `localhost`：

```text
postgresql://langgraph:langgraph@host.docker.internal:5432/<project_database>?sslmode=disable
```

数据库必须在启动 Agent Server 前由外部流程创建。模板不包含数据库创建脚本和
Checkpoint 表迁移脚本；这些由 Agent Server 管理。

## 10. LangGraph 配置与启动

`langgraph.json` 是正式配置，只声明对外使用的根 Graph。`langgraph.dev.json` 是
本地 Studio 调试配置，声明根 Graph 和全部 Subgraph。两个文件中的 Graph ID、
模块路径和导出变量必须与源码一致。

准备依赖：

```powershell
.\scripts\setup.ps1
```

本地默认使用真实 PostgreSQL 启动 Agent Server：

```powershell
$PostgresUri = (Get-Content .env | Select-String "^POSTGRES_URI=").Line `
  -replace "^POSTGRES_URI=", ""

uv run langgraph up -c langgraph.dev.json `
  --postgres-uri $PostgresUri `
  --watch `
  --wait
```

正式运行改用 `langgraph.json` 并移除 `--watch`。模板不使用 `langgraph dev`，也不
提供直接调用编译 Graph 的第二套运行方式。

## 11. 第一版明确不包含

- 具体业务、虚假节点、假工具和占位 Prompt；
- Conditional Edge；
- LangChain `create_agent()`、Middleware 和 Deep Agents；
- 手动 Checkpointer、直接运行模式和数据库迁移代码；
- 上下文压缩、跨 Thread 长期记忆和 State 加密；
- 鉴权、队列、限流、监控和业务数据库实现；
- 通用基类、抽象 Graph、插件注册中心和代码生成引擎；
- 测试目录与测试规范。
