import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from web import app


class ChatRouterTest(unittest.TestCase):

    @patch("web.router.ChatRouter.AGENTS")
    def test_stop_marks_agent_session(self, agents):
        agent = Mock()
        agents.get.return_value = agent

        with patch.dict("os.environ", {"AGENT_CENTER_GATEWAY_SECRET": "test-gateway-secret"}):
            response = TestClient(app).post(
                "/chat/stop",
                headers={"X-Gateway-Token": "test-gateway-secret"},
                params={"session_id": "session-1", "agent_id": 1001},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        agent.stop.assert_called_once_with("session-1")


if __name__ == "__main__":
    unittest.main()
