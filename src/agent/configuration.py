"""定义整棵 Graph 树共享的 Runtime Context。

这里只描述功能开关、并发限制、循环上限和模型名称等运行参数，并提供明确默认值
和有效范围。生成项目时应为业务循环提供明确上限，并设置 recursion_limit 作为
最后保护；durability 不作为可变配置，统一固定为 async。

不要在这里创建模型、数据库连接、Checkpointer，读取业务 State 或保存 API Key。
"""
