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
src/agent/
├── __init__.py
├── graph.py
├── state.py
├── schemas.py
├── configuration.py
├── models.py
├── prompts.py
└── tools.py
```

模板自身展示全部标准文件，以固定职责和命名。生成目标项目时：

- `graph.py` 和 `state.py` 必须存在；
- `configuration.py` 和 `models.py` 由整棵 Graph 树共享；
- 没有结构化模型输出时可以不生成 `schemas.py`；
- 没有模型 Prompt 时可以不生成 `prompts.py`；
- 没有工具时可以不生成 `tools.py`；
- 不提前创建没有真实业务的 Subgraph 目录。

## 4. 文件职责

### `graph.py`

定义节点函数、Graph 结构、固定 Edge、Command 路由、Send 并行和 Subgraph 挂载。
根 Graph 对外导出变量统一命名为 `graph`。

### `state.py`

定义当前 Graph 唯一的运行 State。State 只保存需要跨节点、跨循环或恢复执行的
动态业务数据。

不要在 `state.py` 中定义模型结构化输出，也不要默认给每个节点创建 State。

### `schemas.py`

定义模型单次结构化输出，例如分类、判断、规划和完成信号。这些类型不是 Graph
运行 State。

### `configuration.py`

只定义 Runtime Context，例如功能开关、并发上限、循环上限和模型名称。配置值
应当具有明确默认值和有效范围。

### `models.py`

根据 Configuration 创建模型实例。模板保持厂商中立，由目标项目添加 OpenAI、
Anthropic 或其他 Provider 依赖。API Key 从环境变量或部署环境读取。

### `prompts.py`

保存当前 Graph 使用的 Prompt。Prompt 描述模型任务；模型返回格式由
`schemas.py` 描述。

### `tools.py`

保存当前 Graph 使用的工具，文件名统一使用复数 `tools.py`。标准工具执行优先
使用 ToolNode；只有权限、事务、审计、服务端参数注入或特殊错误处理等业务要求
存在时，才实现自定义工具节点。

## 5. 一个 Graph 一个 State

每张 Graph 只定义一个主要 State：

```python
class State(TypedDict, total=False):
    ...
```

同一张 Graph 的所有节点读写这个 State，各节点只使用自己负责的字段。

不能放入 State 的内容：

- 模型名称、并发数和循环上限；
- API Key 和其他秘密；
- 只在一次函数调用中使用的局部变量；
- 被当前节点立即消费的临时路由结果。

并行节点共同写入同一字段时，必须根据业务合并方式声明 Reducer。

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
compress_research_results
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

模板保持模型厂商中立。Codex 必须根据目标项目选择 Provider，并只添加实际使用
的依赖。

## 10. 生成目标项目

Codex 完成业务设计并获得用户确认后：

1. 在用户指定的新目录创建项目；
2. 只创建业务实际使用的文件和 Subgraph；
3. 生成真实 `pyproject.toml` 和 Provider 依赖；
4. 生成真实 `.env.example`，但不写入任何密钥；
5. 生成真实 `langgraph.json`，Graph ID 和导出路径必须对应源码；
6. 确保目录层级、Graph 层级和节点命名一致。

## 11. 第一版明确不包含

- 具体业务逻辑；
- 具体模型或工具厂商；
- 测试目录和测试规范；
- AGENTS.md、README.md 和 docs 目录；
- 鉴权、数据库、队列、限流和监控实现；
- 通用基类、抽象 Graph、插件注册中心和代码生成引擎；
- Conditional Edge。
