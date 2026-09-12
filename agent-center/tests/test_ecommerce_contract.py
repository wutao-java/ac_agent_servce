"""验证 AgentCenter 与电商后端之间的 HTTP 接口契约。"""

import os
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

os.environ.setdefault("AGENT_SERVICE_AUTH_TOKEN", "test-service-token")

from web import app


class EcommerceContractTest(unittest.TestCase):
    """覆盖客服接口的请求结构、鉴权和能力边界。"""

    def setUp(self):
        """为每个用例创建隔离的 Agent 模拟对象和测试客户端。"""

        self.agent_patcher = patch("web.router.ChatRouter.xiaozhe_agent")
        self.agent = self.agent_patcher.start()
        self.client = TestClient(app)

    def tearDown(self):
        """停止 Agent 模拟补丁，避免影响后续用例。"""

        self.agent_patcher.stop()

    def test_chat_accepts_ecommerce_backend_contract(self):
        """对话接口应接受电商后端约定的完整请求。"""

        self.agent.chat = AsyncMock(return_value={
            "session_id": "cs-1",
            "answer": "订单正在运输中。",
            "session_state": {"message_count": 1},
        })

        response = self.client.post(
            "/chat",
            headers={"X-Agent-Service-Token": "test-service-token"},
            json={
                "session_id": "cs-1",
                "runtime_user_id": "user-1",
                "runtime_nickname": "小哲用户",
                "runtime_member_level": "GOLD",
                "runtime_risk_level": "LOW",
                "user_message": "查询我的订单",
                "agent_mode": "production_react",
                "reasoning_view": "off",
                "debug": False,
                "runtime_context": {"relatedOrderNo": "SO-1"},
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["session_id"], "cs-1")
        self.assertEqual(response.json()["answer"], "订单正在运输中。")
        request = self.agent.chat.await_args.args[0]
        self.assertEqual(request.runtime_user_id, "user-1")
        self.assertEqual(request.runtime_context["relatedOrderNo"], "SO-1")

    def test_resume_accepts_ecommerce_backend_contract(self):
        """恢复接口应接受电商后端约定的审核请求。"""

        self.agent.resume = AsyncMock(return_value={
            "session_id": "cs-1",
            "workflow_id": "wf-1",
            "status": "not_found",
            "message": "当前会话没有待恢复工作流。",
            "answer": "当前会话没有待恢复工作流。",
            "workflow": None,
            "session_state": None,
        })

        response = self.client.post(
            "/chat/resume",
            headers={"X-Agent-Service-Token": "test-service-token"},
            json={
                "session_id": "cs-1",
                "workflow_id": "wf-1",
                "resume_token": "resume-1",
                "decision": "approved",
                "reviewer_note": "用户已确认",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "not_found")
        self.agent.resume.assert_awaited_once()

    def test_chat_rejects_invalid_service_token(self):
        """对话接口应拒绝错误的服务令牌。"""

        response = self.client.post(
            "/chat",
            headers={"X-Agent-Service-Token": "wrong-token"},
            json={
                "session_id": "cs-1",
                "runtime_user_id": "user-1",
                "user_message": "你好",
            },
        )

        self.assertEqual(response.status_code, 401)
        self.agent.chat.assert_not_called()

    def test_health_does_not_require_external_services(self):
        """健康检查不应依赖模型、数据库等外部服务。"""

        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_legacy_routes_are_not_exposed(self):
        """当前版本不应继续暴露已移除的旧接口。"""

        self.assertEqual(self.client.post("/auth/token").status_code, 404)
        self.assertEqual(self.client.get("/session/history").status_code, 404)
        self.assertEqual(self.client.post("/chat/stop").status_code, 404)


if __name__ == "__main__":
    unittest.main()
