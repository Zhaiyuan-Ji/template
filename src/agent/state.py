"""定义所有目标项目共享的最低 State 约定。"""

from langgraph.graph import MessagesState


class State(MessagesState, total=False):
    """保存 Thread 内消息和滚动上下文摘要。

    具体项目在这个 State 中继续增加真实业务字段。State 只保存可序列化的原始
    业务数据，不保存配置、密钥、连接对象、模型实例或格式化 Prompt。
    """

    conversation_summary: str
