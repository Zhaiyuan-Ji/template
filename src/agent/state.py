"""定义根 Graph 唯一的主要 State。

Coding Agent 必须根据业务选择 ``MessagesState`` 或 ``TypedDict``，不能默认假设
所有 Agent 都是对话型。State 只保存跨节点传递或需要从 Checkpoint 恢复的可序列化
业务数据；本空白模板不预设任何字段。
"""
