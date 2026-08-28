"""使用个人默认 DeepSeek Provider 创建通用 Chat Model。"""

import os

from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel
from langchain_deepseek import ChatDeepSeek

from agent.configuration import Configuration

DEEPSEEK_API_KEY_ENV = "DEEPSEEK_API_KEY"


def _require_deepseek_api_key() -> None:
    """在模型真正创建时检查 DeepSeek API Key。"""
    load_dotenv()
    if not os.getenv(DEEPSEEK_API_KEY_ENV, "").strip():
        msg = f"缺少环境变量 {DEEPSEEK_API_KEY_ENV}，无法创建 DeepSeek 模型。"
        raise RuntimeError(msg)


def _create_deepseek_model(
    model_name: str,
    configuration: Configuration,
) -> BaseChatModel:
    """创建一个符合 LangGraph 消息、工具和结构化输出接口的模型。"""
    _require_deepseek_api_key()
    return ChatDeepSeek(
        model=model_name,
        temperature=configuration.model_temperature,
        timeout=configuration.model_timeout_seconds,
        max_retries=configuration.model_max_retries,
    )


def create_model(configuration: Configuration) -> BaseChatModel:
    """创建默认业务模型。"""
    return _create_deepseek_model(configuration.model_name, configuration)
