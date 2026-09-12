from langgraph.graph import MessagesState


class RouteState(MessagesState):
    """
    天机路由状态。

    具体状态字段由路由图实现时补充。
    """
    intent: str
