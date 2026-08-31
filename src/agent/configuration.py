"""定义整棵 Graph 树共享的运行上下文和默认运行配置。"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv
from langgraph.runtime import Runtime

DEFAULT_MODEL_NAME = "deepseek-v4-flash"
DEFAULT_RECURSION_LIMIT = 100


@dataclass(frozen=True, kw_only=True, slots=True)
class Configuration:
    """定义整棵 Graph 树共享的不可变运行参数。"""

    model_name: str = DEFAULT_MODEL_NAME
    model_temperature: float = 0.0
    model_timeout_seconds: float = 60.0
    model_max_retries: int = 2

    def __post_init__(self) -> None:
        """拒绝会让模型调用失去边界的配置。"""
        positive_values = {
            "model_timeout_seconds": self.model_timeout_seconds,
            "model_max_retries": self.model_max_retries,
        }
        for name, value in positive_values.items():
            if value < 1:
                msg = f"{name} 必须大于 0，当前值为 {value}。"
                raise ValueError(msg)

        for name, value in {"model_name": self.model_name}.items():
            if not value.strip():
                msg = f"{name} 不能为空。"
                raise ValueError(msg)

        if not 0 <= self.model_temperature <= 2:
            msg = "model_temperature 必须位于 0 到 2 之间。"
            raise ValueError(msg)


def get_configuration(runtime: Runtime[Configuration]) -> Configuration:
    """优先使用本次 Run 的 Context，没有传入时读取环境默认值。"""
    if runtime.context is not None:
        return runtime.context

    load_dotenv()
    return Configuration(
        model_name=os.getenv("MODEL_NAME", DEFAULT_MODEL_NAME),
    )
