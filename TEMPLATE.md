# LangGraph Agent 项目规范

## 1. 使用方式

当前目录已经是完整复制后的项目骨架。`TEMPLATE.md` 是项目内永久保留的编码契约，
Coding Agent 必须读取并遵守，不能修改或删除本文件。

根据已经确认的业务设计填写固定文件。不要重新发明同职责文件名，也不要把不同职责
混入同一个文件。没有对应业务时，文件可以只保留现有中文模块说明，但不能写入假节点、
假工具、占位 Prompt 或示例业务。

固定结构：

```text
.
├── TEMPLATE.md
├── pyproject.toml
├── langgraph.json
├── langgraph.dev.json
├── .env.example
├── .gitignore
├── .editorconfig
├── scripts/
│   ├── setup.ps1
│   └── dev.ps1
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

只有业务流程内部仍包含多个步骤、循环或独立 State 时，才创建 Subgraph：

```text
src/agent/research/
├── __init__.py
├── graph.py
├── state.py
├── schemas.py
├── prompts.py
└── tools.py
```

Subgraph 共享根目录的 `configuration.py` 和 `models.py`。不要默认创建 `nodes.py`、
`services.py`、`contracts.py`、`docs/`、`tests/`、`README.md` 或 `AGENTS.md`。

## 2. 固定文件的填写边界

| 文件 | 只负责什么 |
| --- | --- |
| `schemas.py` | Graph 对外输入、对外输出、模型结构化返回 |
| `state.py` | 当前 Graph 在节点之间传递和持久化的数据 |
| `configuration.py` | 不随 Graph 执行变化的 Runtime Context 和默认运行常量 |
| `models.py` | 根据 Configuration 创建模型 |
| `prompts.py` | 当前 Graph 实际调用模型时使用的 Prompt |
| `tools.py` | 当前 Graph 暴露给模型的 Tool 和工具列表 |
| `graph.py` | Node 函数、Graph 拓扑、Subgraph 挂载和最终导出 |
| `pyproject.toml` | 当前项目名称和真实使用的 Python 依赖 |
| `langgraph.json` | 正式运行时对外根图的注册信息 |
| `langgraph.dev.json` | 本地 Studio 使用的根图和全部 Subgraph 注册信息 |
| `.env.example` | 环境变量名称、非敏感默认值和当前项目的独立数据库名 |
| `scripts/*.ps1` | 固定的依赖安装和 Agent Server 启动流程 |

`configuration.py`、`models.py` 和 `scripts/*.ps1` 已包含通用实现，没有真实需求时不
重写。Coding Agent 必须把 `pyproject.toml` 的项目名、`.env.example` 的数据库名和
两个 LangGraph 配置文件更新为当前业务的真实值；不能把 API Key 写入项目文件。

项目的数据流必须保持为：

```text
GraphInput
→ State
→ Node 读取 State 和 Runtime Context
→ Node 返回 State 更新或 Command
→ GraphOutput
```

配置流必须保持为：

```text
Run Context 或环境默认值
→ get_configuration(runtime)
→ Configuration
→ create_model(configuration)
```

## 3. Schema 与 State

每张 Graph 只定义一个主要 `State`。`GraphInput` 和 `GraphOutput` 是公开边界，
`State` 是内部完整数据。公开 Schema 的字段必须能在 State 中找到，但内部字段不能
自动暴露给调用方。

`schemas.py` 的最小模式：

```python
from typing_extensions import TypedDict


class GraphInput(TypedDict):
    request: str


class GraphOutput(TypedDict):
    result: str
```

模型结构化输出使用 Pydantic 类型，仍然放在 `schemas.py`：

```python
from pydantic import BaseModel, Field


class ActionDecision(BaseModel):
    requires_action: bool = Field(description="是否需要执行下一项业务动作")
    reason: str = Field(description="作出判断的原因")
```

`state.py` 的结构化工作流模式：

```python
import operator
from typing import Annotated

from typing_extensions import TypedDict


class State(TypedDict, total=False):
    request: str
    result: str
    pending_items: list[str]
    completed_items: Annotated[list[str], operator.add]
```

对话型 Graph 才使用 `MessagesState`。State 只保存跨节点传递或需要从 Checkpoint
恢复的可序列化业务数据。配置、密钥、模型、连接对象、格式化后的 Prompt 和局部变量
不能进入 State。

并行节点共同写入同一字段时必须声明 Reducer。Reducer 必须表达真实合并语义，不能
为了消除并发报错而随意使用列表相加。

## 4. Configuration、Runtime 与 Model

`configuration.py` 已提供 `Configuration`、`get_configuration()` 和
`DEFAULT_RECURSION_LIMIT`。Node 必须通过统一入口取得运行上下文：

```python
from langgraph.runtime import Runtime

from agent.configuration import Configuration, get_configuration
from agent.models import create_model
from agent.state import State


async def generate_response(
    state: State,
    runtime: Runtime[Configuration],
) -> dict:
    configuration = get_configuration(runtime)
    model = create_model(configuration)
    response = await model.ainvoke(state["request"])
    return {"result": str(response.content)}
```

显式传入的 Run Context 优先；没有 Context 时，`get_configuration()` 才读取环境默认
值。Node 不能自行读取 `MODEL_NAME`，也不能直接实例化 `ChatDeepSeek`。

`recursion_limit` 不是 Runtime Context。创建 Agent Server Run 时分别传递 Context、
Run Config 和 durability：

```json
{
  "context": {
    "model_name": "deepseek-v4-flash"
  },
  "config": {
    "recursion_limit": 100
  },
  "durability": "async"
}
```

## 5. 构建 Graph 与普通 Edge

Node 函数写在构建函数外，Builder 只存在于构建函数内。函数名必须表达业务行为，
注册名称必须与函数名完全一致。

根 Graph 使用 `build_graph()` 并导出 `graph`：

```python
from langgraph.graph import END, START, StateGraph

from agent.configuration import Configuration
from agent.schemas import GraphInput, GraphOutput
from agent.state import State


async def analyze_request(state: State) -> dict:
    return {"result": state["request"]}


def build_graph():
    graph_builder = StateGraph(
        State,
        input_schema=GraphInput,
        output_schema=GraphOutput,
        context_schema=Configuration,
    )
    graph_builder.add_node("analyze_request", analyze_request)
    graph_builder.add_edge(START, "analyze_request")
    graph_builder.add_edge("analyze_request", END)
    return graph_builder.compile()


graph = build_graph()
```

固定且无条件的下一步使用普通 Edge。只有包含 I/O 的 Node 必须使用 `async def`；
纯计算 Node 可以使用普通 `def`。所有模型、网络、数据库和文件 I/O 必须使用异步接口，
同步阻塞接口只能通过 `asyncio.to_thread()` 隔离。

## 6. 类型化 Command

同一个 Node 既更新 State 又动态选择下一步时返回 Command：

```python
from typing import Literal

from langgraph.types import Command

from agent.state import State


async def choose_action(
    state: State,
) -> Command[Literal["execute_action", "generate_response"]]:
    if state.get("pending_items"):
        return Command(
            update={"result": "准备执行业务动作"},
            goto="execute_action",
        )
    return Command(
        update={"result": "不需要执行业务动作"},
        goto="generate_response",
    )
```

`Literal` 必须列出全部目的地，字符串必须与 `add_node()` 注册名称一致。返回 Command
的 Node 不能再添加静态出边，否则两条路线都会执行。

本项目不使用 Conditional Edge。固定路线使用 Edge，动态路线由作出决策的 Node
直接返回类型化 Command。

## 7. ToolNode 工具循环

标准模型工具调用必须使用 `ToolNode`，不能手工执行 `tool_calls`。

`tools.py` 定义 Tool 和统一工具列表：

```python
from langchain_core.tools import tool


@tool
async def search_information(query: str) -> str:
    """根据查询词获取当前业务需要的信息。"""
    ...


TOOLS = [search_information]
```

模型 Node 负责决定调用工具还是结束：

```python
from typing import Literal

from langgraph.graph import END
from langgraph.prebuilt import ToolNode
from langgraph.runtime import Runtime
from langgraph.types import Command

from agent.configuration import Configuration, get_configuration
from agent.models import create_model
from agent.state import State
from agent.tools import TOOLS


async def call_model(
    state: State,
    runtime: Runtime[Configuration],
) -> Command[Literal["tools", "__end__"]]:
    configuration = get_configuration(runtime)
    model = create_model(configuration).bind_tools(TOOLS)
    response = await model.ainvoke(state["messages"])
    if response.tool_calls:
        return Command(update={"messages": [response]}, goto="tools")
    return Command(update={"messages": [response]}, goto=END)
```


ToolNode 在 `build_graph()` 内注册，并通过普通 Edge 返回模型 Node：

```python
graph_builder.add_node("call_model", call_model)
graph_builder.add_node("tools", ToolNode(TOOLS))
graph_builder.add_edge("tools", "call_model")
```

使用这套模式时，当前 State 必须提供采用 `add_messages` Reducer 的 `messages` 字段。
`call_model` 由 Command 路由，不能再为它添加静态出边。

## 8. Send 动态并行

运行时才知道任务数量时，返回包含多个 `Send` 的 Command。每个 Send 只携带 Worker
真正需要的输入：

```python
from typing import Literal

from langgraph.types import Command, Send

from agent.state import State


async def dispatch_items(
    state: State,
) -> Command[Literal["process_item"]]:
    tasks = [Send("process_item", {"item": item}) for item in state["pending_items"]]
    return Command(goto=tasks)


async def process_item(state: dict) -> dict:
    item = str(state["item"])
    return {"completed_items": [item]}
```

注册时，`dispatch_items` 不添加静态出边；每个 `process_item` 通过普通 Edge 进入同一个
汇总节点。`completed_items` 必须在 State 中声明对应 Reducer。

## 9. Subgraph

Subgraph 的目录名、父图 Node 名和导出变量保持对应：

```text
父图 Node：research
目录：src/agent/research/
构建函数：build_research_graph()
导出变量：research_graph
```

子图使用自己的 `State`、`GraphInput` 和 `GraphOutput`。父子 State 不同时，父图通过
业务 Node 显式转换输入输出：

```python
from agent.research.graph import research_graph
from agent.state import State


async def research(state: State) -> dict:
    child_input = {"topic": state["request"]}
    child_output = await research_graph.ainvoke(child_input)
    return {"result": child_output["summary"]}
```

```python
graph_builder.add_node("research", research)
```

只有父子 Graph 共享同一套 State 字段时，才把编译后的 Subgraph 直接注册为 Node。
不要为了拆文件创建只有一个步骤的 Subgraph；一次性并行任务优先使用 Send。

## 10. Interrupt 与恢复

需要人工补充信息或审批时，在作出决定的 Node 中调用 `interrupt()`：

```python
from typing import Literal

from langgraph.types import Command, interrupt

from agent.state import State


async def request_approval(
    state: State,
) -> Command[Literal["publish_result", "revise_result"]]:
    decision = interrupt({"result": state["result"]})
    approved = bool(decision["approved"])
    return Command(
        update={"approved": approved},
        goto="publish_result" if approved else "revise_result",
    )
```

恢复时向同一 Thread 的下一次 Run 发送：

```json
{
  "command": {
    "resume": {
      "approved": true
    }
  }
}
```

Node 恢复时会从开头重新执行，因此 `interrupt()` 之前不能执行不可重复的外部副作用。
付款、发信、删除和业务写入必须放在审批后的独立幂等 Node 中。

## 11. LangGraph 配置

空白骨架没有业务 Graph，因此两个配置文件中的 `graphs` 保持为空。填写根 Graph 后，
`langgraph.json` 只声明对外根图：

```json
{
  "$schema": "https://langgra.ph/schema.json",
  "dependencies": ["."],
  "graphs": {
    "agent": "./src/agent/graph.py:graph"
  },
  "env": ".env",
  "image_distro": "wolfi"
}
```

`langgraph.dev.json` 声明根图和全部需要在 Studio 单独查看的 Subgraph：

```json
{
  "$schema": "https://langgra.ph/schema.json",
  "dependencies": ["."],
  "graphs": {
    "agent": "./src/agent/graph.py:graph",
    "research": "./src/agent/research/graph.py:research_graph"
  },
  "env": ".env",
  "image_distro": "wolfi"
}
```

Graph 源码只调用 `compile()`。Agent Server 负责 PostgreSQL Checkpointer、Thread、Run
和 Checkpoint 生命周期，源码中不能创建 Checkpointer。

## 12. 本地运行

默认使用 `E:\PostgreSQL` 中统一运行的 PostgreSQL。每个 Agent 项目必须使用独立
数据库，数据库名只包含小写字母、数字和下划线。Agent Server 在 Docker 中运行，
因此 `.env` 中的地址必须使用：

```text
POSTGRES_URI=postgresql://langgraph:langgraph@host.docker.internal:5432/<project_database>?sslmode=disable
```

先安装依赖：

```powershell
.\scripts\setup.ps1
```

填写 `DEEPSEEK_API_KEY`、`MODEL_NAME` 和独立数据库名，并保证统一 PostgreSQL 与
Docker 已启动。然后运行：

```powershell
.\scripts\dev.ps1
```

`dev.ps1` 读取 `.env` 并使用 `langgraph.dev.json` 启动 Agent Server。项目不使用
`langgraph dev`，不提供直接调用 Graph、手动 Checkpointer、Store、跨 Thread 记忆、
上下文压缩、State 加密或 LangChain `create_agent()`。

## 13. Coding Agent 完成条件

填写业务代码后必须确认：

- 输入、State 和输出字段能够形成完整数据流；
- Node 函数名、注册名、Command 目的地和 Subgraph 目录互相一致；
- 固定路线使用 Edge，动态路线使用类型化 Command；
- 标准工具调用使用 ToolNode，并行写入字段具有正确 Reducer；
- 根图和子图导出名称与两个 LangGraph 配置文件一致；
- 没有虚假业务、未使用配置、手写 Checkpointer 和计划外同职责文件；
- `uv run ruff format .` 与 `uv run ruff check .` 执行通过。
