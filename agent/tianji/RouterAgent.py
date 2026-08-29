from pathlib import Path
from typing import Optional

import uuid
import asyncio
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from langgraph.graph import END, START, StateGraph
from agent.tianji.RouteState import RouteState
from common import *
from config import logger

from agent.BaseAgent import *
from agent.tianji.node import IntentAgent, RecommendAgent, BuyAgent, ConsultAgent, UnknownAgent, KnowledgeAgent


class RouterAgent(BaseAgent):
    """
    RouterAgent 是整个天机系统的核心路由智能体。

    负责：
    - 构建和维护 LangGraph 的推理状态图
    - 管理意图识别与路由逻辑
    - 以流式 SSE 输出最终结果
    - 持久化每个会话的状态（使用 LangGraph + Postgres Checkpointer）
    """

    GRAPH_PNG_DIR = Path(__file__).resolve().parents[2] / "graph_png"

    INTENT_MAPS = {
        "intent_agent": IntentAgent(),
        "recommend_agent": RecommendAgent(),
        "buy_agent": BuyAgent(),
        "consult_agent": ConsultAgent(),
        "knowledge_agent": KnowledgeAgent(),
        "unknown_agent": UnknownAgent(),
    }

    def __init__(self):
        self.graph: Optional[CompiledStateGraph] = None

    async def init(self):
        """
        初始化 RouterAgent
        """
        self.init_graph()

    # ---------------- Graph 初始化 ----------------
    def init_graph(self):
        """
        构建 RouterAgent 的状态图（LangGraph StateGraph）
        图结构： START → intent_agent → <条件路由> → recommend / buy / consult / knowledge / unknown → END
        """
        builder = StateGraph(RouteState)

        for name, agent in self.INTENT_MAPS.items():
            builder.add_node(name, agent.execute)

        # 设置图的起点：首先进入意图识别
        builder.add_edge(START, "intent_agent")

        # 定义意图路由函数
        def intent_router_gate(state: RouteState):
            intent = state.get("intent", "UNKNOWN")
            logger.debug(f"【IntentAgent】智能体识别到的意图：{intent}")
            return intent


        # 基于意图值进行条件跳转（INTENT_TO_AGENT 负责映射）
        builder.add_conditional_edges("intent_agent", intent_router_gate, INTENT_TO_AGENT)

        # 所有目标节点最终都结束于 END
        for target in INTENT_TO_AGENT.values():
            builder.add_edge(target, END)

        self.graph = builder.compile()

        # try:
        #     mermaid = self.graph.get_graph().draw_mermaid_png()
        #     self.GRAPH_PNG_DIR.mkdir(parents=True, exist_ok=True)
        #     (self.GRAPH_PNG_DIR / "router.jpg").write_bytes(mermaid)
        # except Exception as e:
        #     print(e)



    async def execute(self, question: str, session_id: str, user_token: str) -> AsyncIterable[str]:
        try:
            request_id = uuid.uuid4().hex

            # 构建 Graph 执行上下文
            config = RunnableConfig(configurable={
                "thread_id": session_id,
                "user_token": user_token, # 将自定义参数传递给子智能体
                "request_id": request_id  # 将自定义参数传递给子智能体
            })

            # 用户输入封装
            inputs = {"messages": HumanMessage(question)}

            # 开始图的流式执行
            res = self.graph.astream(
                input=inputs,
                config=config,
                subgraphs=True, # 需要得到子图的输出
                stream_mode="messages",
            )

            try:
                async for node_info, (message, metadata) in res:
                    # 获取消息 tags（例如 IntentAgent）
                    tags = metadata.get("tags", [])

                    # 主动跳过 IntentAgent 阶段输出
                    if "IntentAgent" in tags:
                        continue

                    # 提取 message 内容
                    content = getattr(message, "content", None)
                    if not content:
                        continue
                    # SSE 输出文本事件
                    yield make_sse_event(1001, content)
            except asyncio.CancelledError:
                # 客户端中断，也需要安全关闭流
                await res.aclose()
                raise

        except Exception as e:
            logger.exception("RouterAgent error")
            yield make_sse_event(2001, str(e))

        # SSE 最终停止事件（前端用于关闭流）
        yield format_sse_data(STOP_EVENT)

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
