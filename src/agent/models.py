"""根据 Configuration 创建目标项目使用的模型实例。

模板保持厂商中立。Codex 应根据业务选择 Provider、添加对应依赖，并从环境变量
或部署环境读取密钥；模型创建逻辑不能放进 configuration.py。
"""
