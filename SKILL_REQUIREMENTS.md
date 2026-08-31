# LangGraph Coding Agent Skill 需求定义

## 定位

这个 Skill 是提供给 Claude Code、Codex 等 Coding Agent 使用的行为规范。

用户会同时向 Coding Agent 提供：

1. 这个 Skill；
2. 本次需要实现的 Agent 业务需求；
3. 已经准备好的 LangGraph Template。

Coding Agent 必须先按照 Skill 理解和设计业务，得到用户确认后，再遵守
Template 中的 `TEMPLATE.md`，直接在现有骨架内完成业务代码。

## Skill 的起点和终点

Skill 的起点是用户提出一个需要使用 LangGraph 实现的 Agent 业务需求。

Skill 的终点是 Coding Agent 已经：

1. 弄清业务目标、输入、输出、处理流程和关键约束；
2. 完成业务流程以及 Graph、State、Schema、Node、Tool、Subgraph 的设计；
3. 将设计方案清楚地汇报给用户；
4. 得到用户对设计方案的明确确认；
5. 按照 `TEMPLATE.md` 在现有 Template 中完成代码实现。

## Skill 必须约束的行为

Coding Agent 不得在刚收到业务需求时直接开始编写代码。

在设计得到确认之前，Coding Agent 必须：

- 识别会实质影响业务流程或 Graph 架构的缺失信息；
- 信息不足时向用户提出必要的问题，不自行虚构业务规则；
- 根据已经确认的信息完成整体设计；
- 说明各层 Graph 的职责、数据流、State 字段以及节点和工具的边界；
- 等待用户确认，不能用占位节点或默认假设跳过确认。

用户确认设计以后，Coding Agent 才能进入编码阶段。编码时必须读取并遵守
`TEMPLATE.md`，在已有固定文件中填写业务实现，不得自行创造另一套工程结构。

## Skill 与 Template 的边界

Skill 负责开发过程：

- 怎样理解业务需求；
- 什么时候必须提问；
- 怎样把业务转化为 LangGraph 系统设计；
- 怎样向用户汇报设计并取得确认；
- 什么时候可以开始编码。

`TEMPLATE.md` 负责最终代码约束：

- 固定目录和文件职责；
- State、Schema、Configuration、Graph、Node 和 Tool 的代码边界；
- LangGraph 的实现规则；
- Agent Server、PostgreSQL 和项目运行方式。

Skill 不重复 `TEMPLATE.md` 中的代码规范，而是在进入编码阶段时要求 Coding Agent
读取并遵守它。

## 不属于 Skill 的职责

这个 Skill 不负责：

- 安装到用户当前使用的 Codex 或 Claude Code；
- 创建、复制或重新生成 Template；
- 把模板复制脚本、依赖安装或项目启动作为核心能力；
- 替代用户决定业务规则和关键架构选择；
- 在用户确认设计之前直接修改业务代码。

具体的提问策略、设计汇报格式和阶段切换规则，需要结合真实 Coding Agent 任务的
测试结果继续设计。本文件当前只固定已经确认的职责和边界。
