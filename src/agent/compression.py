"""提供与具体业务 State 解耦的 Thread 内上下文压缩能力。"""

from collections.abc import Sequence

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AnyMessage, HumanMessage, RemoveMessage
from langchain_core.messages.utils import count_tokens_approximately
from langgraph.graph.message import REMOVE_ALL_MESSAGES

from agent.configuration import Configuration
from agent.state import State


def estimate_context_tokens(messages: Sequence[AnyMessage]) -> int:
    """使用厂商中立的近似算法估算消息 Token 数量。"""
    return count_tokens_approximately(messages)


def should_compress(state: State, configuration: Configuration) -> bool:
    """判断当前消息历史是否达到统一压缩阈值。"""
    return (
        estimate_context_tokens(state.get("messages", []))
        >= configuration.compression_trigger_tokens
    )


def select_recent_messages(
    messages: Sequence[AnyMessage],
    *,
    keep_count: int,
) -> list[AnyMessage]:
    """保留最近消息，并尽量从一条 HumanMessage 开始形成有效对话。"""
    recent_messages = list(messages[-keep_count:])
    while recent_messages and not isinstance(recent_messages[0], HumanMessage):
        recent_messages.pop(0)
    return recent_messages


async def summarize_messages(
    state: State,
    *,
    model: BaseChatModel,
) -> str:
    """根据完整消息历史创建或扩展滚动摘要。"""
    messages = list(state.get("messages", []))
    existing_summary = state.get("conversation_summary", "").strip()
    if not messages:
        return existing_summary

    if existing_summary:
        instruction = (
            "下面是此前的对话摘要：\n"
            f"{existing_summary}\n\n"
            "请结合当前完整对话更新摘要，保留事实、决定、未完成事项和重要约束。"
        )
    else:
        instruction = "请总结当前完整对话，保留事实、决定、未完成事项和重要约束。"

    response = await model.ainvoke([*messages, HumanMessage(content=instruction)])
    return str(response.text)


def build_compression_update(
    state: State,
    *,
    summary: str,
    configuration: Configuration,
) -> dict[str, object]:
    """用滚动摘要替换旧消息，并保留最近的有效对话。"""
    recent_messages = select_recent_messages(
        state.get("messages", []),
        keep_count=configuration.compression_keep_messages,
    )
    return {
        "conversation_summary": summary,
        "messages": [
            RemoveMessage(id=REMOVE_ALL_MESSAGES),
            *recent_messages,
        ],
    }


async def compress_context(
    state: State,
    *,
    model: BaseChatModel,
    configuration: Configuration,
) -> dict[str, object]:
    """执行一次完整压缩，供具体项目的压缩 Node 调用。"""
    summary = await summarize_messages(state, model=model)
    return build_compression_update(
        state,
        summary=summary,
        configuration=configuration,
    )
