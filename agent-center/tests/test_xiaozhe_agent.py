"""验证小哲 Agent 对可信身份及运行时上下文的处理。"""

import unittest

from langchain_core.messages import AIMessage

from agent.xiaozhe.models import ChatRequest
from agent.xiaozhe.service import XiaozheAgent


class StubGraph:
    """记录调用参数并返回固定模型回复的测试图。"""

    def __init__(self):
        """初始化待记录的上下文与消息。"""

        self.context = None
        self.messages = None

    async def ainvoke(self, payload, *, config, context):
        """模拟 Agent 图调用并保存本轮输入。"""

        self.context = context
        self.messages = payload["messages"]
        return {"messages": [*self.messages, AIMessage(content="查询完成。")]}


class XiaozheAgentTest(unittest.IsolatedAsyncioTestCase):
    """覆盖小哲 Agent 的核心会话安全约束。"""

    async def test_chat_uses_trusted_identity_and_filters_sensitive_context(self):
        """对话应使用可信用户身份，并过滤未列入白名单的敏感字段。"""

        agent = XiaozheAgent()
        graph = StubGraph()
        agent._graph = graph
        self.addAsyncCleanup(agent.close)

        response = await agent.chat(ChatRequest(
            session_id="cs-1",
            runtime_user_id="user-1",
            user_message="查询订单",
            runtime_context={
                "relatedOrderNo": "SO-1",
                "mobile": "13800000000",
            },
        ))

        self.assertEqual(response.answer, "查询完成。")
        self.assertEqual(graph.context.user_id, "user-1")
        self.assertIn("SO-1", graph.messages[0].content)
        self.assertNotIn("13800000000", graph.messages[0].content)


if __name__ == "__main__":
    unittest.main()
