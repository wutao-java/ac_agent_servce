from typing import AsyncIterable, Optional

import asyncio
import uuid

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import StateSnapshot

from agent.BaseAgent import BaseAgent, STOP_EVENT, format_sse_data, make_sse_event
from agent.tianji.RouteState import RouteState
from agent.tianji.node import IntentAgent, RecommendAgent, BuyAgent, ConsultAgent, UnknownAgent, KnowledgeAgent
from agent.tianji.node.BaseNodeAgent import ToolContext
from agent.tianji.tools.result import CourseInfo, PrePlaceOrder
from common import INTENT_TO_AGENT
from config import logger
from config.ConnectionPool import get_async_pg_pool
from dao import chat_session_dao
from util import JsonUtil


class RouterAgent(BaseAgent):
    """
    RouterAgent 是整个天机系统的核心路由智能体。

    负责：
    - 构建和维护 LangGraph 的推理状态图
    - 管理意图识别与路由逻辑
    - 以流式 SSE 输出最终结果
    - 持久化每个会话的状态（使用 LangGraph + Postgres Checkpointer）
    """

    # 声明用于 Graph 的所有节点智能体（节点 = 子 Agent）
    AGENTS = {
        "intent_agent": IntentAgent(),
        "recommend_agent": RecommendAgent(),
        "buy_agent": BuyAgent(),
        "consult_agent": ConsultAgent(),
        "knowledge_agent": KnowledgeAgent(),
        "unknown_agent": UnknownAgent(),
    }

    def __init__(self):
        self.graph: Optional[CompiledStateGraph] = None
        self.checkpointer: Optional[AsyncPostgresSaver] = None  # 用于保存会话状态的 Postgres Checkpointer

    async def init(self):
        """
        初始化 RouterAgent
        """
        # 检查会话记忆所需要的表是否存在
        await self.check_table()

        # 获取异步数据库连接池实例
        async_pg_pool = await get_async_pg_pool()
        # 创建checkpointer是用于实现会话记忆的
        self.checkpointer = AsyncPostgresSaver(conn=async_pg_pool)

        self.init_graph()

    async def check_table(self):
        """
        检查数据库中是否存在会话记忆相关的表，如果不存在则创建
        """
        async_pg_pool = await get_async_pg_pool()
        conn = None
        try:
            # 先创建一个临时checkpointer，用于检查数据库中相关的表是否存在，如果不存在则创建
            conn = await async_pg_pool.getconn()
            await conn.set_autocommit(True) # 设置自动提交，不使用显式事务块
            checkpointer = AsyncPostgresSaver(conn=conn)
            await checkpointer.setup()  # 如果会话记忆相关的表不存在，会自动创建
        finally:
            if conn is not None:
                await async_pg_pool.putconn(conn)

    # ---------------- Graph 初始化 ----------------
    def init_graph(self):
        """
        构建 RouterAgent 的状态图（LangGraph StateGraph）

        图结构：
        START → intent_agent → <条件路由> → recommend / buy / consult / knowledge / unknown → END
        """
        builder = StateGraph(RouteState)  # RouteState 用于定义 Graph 中的状态结构

        # 添加所有节点到 Graph（每个节点绑定对应智能体的 execute()）
        for name, agent in self.AGENTS.items():
            builder.add_node(name, agent.execute)

        # 设置图的起点：首先进入意图识别
        builder.add_edge(START, "intent_agent")

        # 定义意图路由函数
        def intent_router_gate(state: RouteState):
            raw_intent = state.get("intent", "UNKNOWN")
            intent = self._normalize_intent(raw_intent)
            logger.debug(f"【IntentAgent】智能体识别到的意图：{intent}")
            return intent

        # 基于意图值进行条件跳转（INTENT_TO_AGENT 负责映射）
        builder.add_conditional_edges("intent_agent", intent_router_gate, INTENT_TO_AGENT)

        # 所有目标节点最终都结束于 END
        for target in INTENT_TO_AGENT.values():
            builder.add_edge(target, END)

        # 编译 Graph，并启用 Checkpointer
        self.graph = builder.compile(checkpointer=self.checkpointer)

    @staticmethod
    def _normalize_intent(raw_intent) -> str:
        intent = str(raw_intent).strip().upper()
        if intent in INTENT_TO_AGENT:
            return intent
        logger.warning("【IntentAgent】无法识别意图输出：%r，回退到 UNKNOWN", raw_intent)
        return "UNKNOWN"

    @staticmethod
    def _parse_tool_result(message: ToolMessage) -> dict:
        """将工具消息转换为前端卡片参数。"""
        if getattr(message, "status", "success") != "success":
            return {}
        if not message.content:
            return {}

        try:
            if message.name == "query_course_by_id":
                course_info = JsonUtil.to_obj(message.content, CourseInfo)
                if course_info.id is None:
                    return {}
                return {f"courseInfo_{course_info.id}": course_info}

            if message.name == "pre_place_order":
                order = JsonUtil.to_obj(message.content, PrePlaceOrder)
                return {"prePlaceOrder": order}
        except Exception:
            logger.exception("解析工具结果失败，tool=%s", message.name)

        return {}

    async def execute(self, question: str, session_id: str, user_token: str) -> AsyncIterable[str]:
        try:
            request_id = uuid.uuid4().hex

            self.reset_stop(session_id)
            chat_session_dao.update_title(session_id, self.id(), question)

            # 构建 Graph 执行上下文
            config = RunnableConfig(configurable={
                "thread_id": session_id,
                # 对象类型不会被 LangGraph 写入 checkpoint metadata，避免令牌落库
                "tool_context": ToolContext(
                    user_token=user_token,
                    request_id=request_id,
                ),
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

            tool_result = {}

            try:
                async for node_info, (message, metadata) in res:
                    if self.is_stop(session_id):
                        await res.aclose()
                        break

                    # 获取消息 tags（例如 IntentAgent）
                    tags = metadata.get("tags", [])

                    # 主动跳过 IntentAgent 阶段输出
                    if "IntentAgent" in tags:
                        continue

                    if isinstance(message, ToolMessage):
                        tool_result.update(self._parse_tool_result(message))
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

            if tool_result:
                yield make_sse_event(1003, tool_result)

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
        """
        查询指定 session 的消息历史（从 LangGraph 的 Checkpointer 中恢复）。
        """
        config = RunnableConfig(configurable={"thread_id": session_id})
        state_snapshot: StateSnapshot = await self.graph.aget_state(config)
        messages = state_snapshot.values.get("messages", [])

        result = []
        pending_params = {}

        for message in messages:
            msg_type = ""
            content = message.content

            if isinstance(message, ToolMessage):
                pending_params.update(self._parse_tool_result(message))
                continue

            # 用户消息
            if isinstance(message, HumanMessage):
                msg_type = "USER"

            # 模型回复消息
            elif isinstance(message, AIMessage):
                msg_type = "ASSISTANT"

            # 将有效消息加入结果结构
            if msg_type and content:
                params = pending_params if msg_type == "ASSISTANT" else {}
                result.append({
                    "type": msg_type,
                    "content": content,
                    "params": params.copy(),
                })
                if msg_type == "ASSISTANT":
                    pending_params.clear()

        return result

    async def delete_session(self, session_id: str):
        """删除指定会话的全部 checkpoint 数据。"""
        if self.checkpointer is None:
            raise RuntimeError("RouterAgent 尚未初始化")
        await self.checkpointer.adelete_thread(session_id)

# 全局 RouterAgent 实例
router_agent = RouterAgent()
