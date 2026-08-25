"""定义根 Graph 的业务节点和连接关系。

生成目标项目时，先根据业务确定节点和 State，再在这里组装 Graph。普通函数节点
的注册名称必须与函数名一致；固定路线使用 Edge，动态路由使用 Command。
需要人工输入时使用 interrupt，并把产生外部副作用的动作放到批准后的独立节点。
外部查询节点按错误类型配置 RetryPolicy；有副作用节点只有实现幂等后才能重试。

通过 Agent Server 运行时直接编译并导出 ``graph``，不在源码中重复创建
Checkpointer；直接运行模式按 persistence.py 的 PostgreSQL 生命周期编译 Graph。
"""
