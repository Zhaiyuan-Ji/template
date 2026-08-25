"""定义整棵 Graph 树共享的通用运行参数。"""

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True, slots=True)
class Configuration:
    """提供所有目标项目一致的安全默认值。"""

    recursion_limit: int = 100
    compression_trigger_tokens: int = 12_000
    compression_keep_messages: int = 12
    max_retry_attempts: int = 3

    def __post_init__(self) -> None:
        """拒绝会让循环、压缩或重试失去边界的配置。"""
        positive_values = {
            "recursion_limit": self.recursion_limit,
            "compression_trigger_tokens": self.compression_trigger_tokens,
            "compression_keep_messages": self.compression_keep_messages,
            "max_retry_attempts": self.max_retry_attempts,
        }
        for name, value in positive_values.items():
            if value < 1:
                msg = f"{name} 必须大于 0，当前值为 {value}。"
                raise ValueError(msg)
