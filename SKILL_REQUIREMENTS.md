# LangGraph Template Skill 职责

## 目标

这个 Skill 用于指导 Coding Agent 正确使用本项目的 `TEMPLATE.md`，把用户的业务
需求转化为结构清晰、职责明确的 LangGraph Agent 项目。

## 必须完成的工作

Coding Agent 在生成项目之前必须：

1. 和用户明确 Agent 的业务目标、输入、输出和主要处理流程；
2. 当关键信息不足或存在多种会明显影响架构的选择时，先向用户提问；
3. 根据已经确认的业务需求完成 Agent 和 Graph 设计；
4. 向用户说明设计方案，并等待用户确认；
5. 只有业务设计得到确认后，才能根据 `TEMPLATE.md` 生成项目代码。

不能使用假设业务、占位节点或未经用户确认的架构选择代替上述过程。

## 与 Template 的边界

Skill 负责 Coding Agent 如何理解需求、提出问题、完成设计、获取确认和执行生成。

`TEMPLATE.md` 负责规定最终 Agent 项目的目录结构、文件职责、代码组织方式、
LangGraph 使用规则和运行环境约束。

具体提问方式、设计输出格式和执行步骤，等后续正式设计 Skill 时再确定。
