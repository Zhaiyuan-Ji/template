"""根据已经解析好的运行上下文创建 DeepSeek Chat Model。"""

from langchain_core.language_models import BaseChatModel
from langchain_deepseek import ChatDeepSeek

from agent.configuration import Configuration


def create_model(configuration: Configuration) -> BaseChatModel:
    """创建一个符合 LangGraph 消息、工具和结构化输出接口的模型。"""
    return ChatDeepSeek(
        model=configuration.model_name,
        temperature=configuration.model_temperature,
        timeout=configuration.model_timeout_seconds,
        max_retries=configuration.model_max_retries,
    )
