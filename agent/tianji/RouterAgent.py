from typing import Optional

from langgraph.graph.state import CompiledStateGraph

from agent.BaseAgent import *


class RouterAgent(BaseAgent):
    """
    RouterAgent 是整个天机系统的核心路由智能体。

    负责：
    - 构建和维护 LangGraph 的推理状态图
    - 管理意图识别与路由逻辑
    - 以流式 SSE 输出最终结果
    - 持久化每个会话的状态（使用 LangGraph + Postgres Checkpointer）
    """

    def __init__(self):
        self.graph: Optional[CompiledStateGraph] = None

    async def init(self):
        """
        初始化 RouterAgent
        """
        self.init_graph()

    # ---------------- Graph 初始化 ----------------
    def init_graph(self):
        # TODO 待实现
        pass

    async def execute(self, question: str, session_id: str, user_token: str) -> AsyncIterable[str]:
        pass

    def id(self) -> int:
        """
        RouterAgent 的固定 ID。
        """
        return 1001

    async def session_detail(self, user_id: int, session_id: str) -> list:
        """暂不实现"""
        pass

    async def delete_session(self, session_id: str):
        """暂不实现"""
        pass


# 全局 RouterAgent 实例
router_agent = RouterAgent()