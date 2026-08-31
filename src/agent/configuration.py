"""定义整棵 Graph 树共享的通用运行参数。"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True, kw_only=True, slots=True)
class Configuration:
    """定义整棵 Graph 树共享的不可变运行参数。"""

    model_name: str = "deepseek-v4-flash"
    model_temperature: float = 0.0
    model_timeout_seconds: float = 60.0
    model_max_retries: int = 2
    recursion_limit: int = 100

    @classmethod
    def from_env(cls) -> "Configuration":
        """读取允许通过环境变量覆盖的个人默认模型。"""
        load_dotenv()
        defaults = cls()
        return cls(
            model_name=os.getenv("MODEL_NAME", defaults.model_name),
        )

    def __post_init__(self) -> None:
        """拒绝会让模型调用或 Graph 执行失去边界的配置。"""
        positive_values = {
            "model_timeout_seconds": self.model_timeout_seconds,
            "model_max_retries": self.model_max_retries,
            "recursion_limit": self.recursion_limit,
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
