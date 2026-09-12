import unittest
from unittest.mock import AsyncMock, Mock, patch

from fastapi.testclient import TestClient

from web import app


class SessionRouterTest(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    @patch("web.router.SessionRouter.chat_session_dao.query_history_session")
    def test_query_history_session(self, query_history_session):
        query_history_session.return_value = {"当天": []}

        response = self.client.get(
            "/session/history",
            params={"agent_id": 1001, "user_id": 1},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"当天": []})
        query_history_session.assert_called_once_with(1001, 1)

    @patch("web.router.SessionRouter.chat_session_dao.delete_history_session")
    @patch("web.router.SessionRouter.AGENTS")
    def test_delete_history_session(self, agents, delete_history_session):
        agent = Mock()
        agent.delete_session = AsyncMock()
        agents.get.return_value = agent
        delete_history_session.return_value = {"status": "ok"}

        response = self.client.delete(
            "/session/history",
            params={
                "agent_id": 1001,
                "user_id": 1,
                "session_id": "session-1",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        agent.delete_session.assert_awaited_once_with("session-1")
        delete_history_session.assert_called_once_with(1001, 1, "session-1")

    @patch("web.router.SessionRouter.chat_session_dao.update_history_session")
    def test_update_history_session(self, update_history_session):
        update_history_session.return_value = {"status": "ok"}

        response = self.client.put(
            "/session/history",
            params={
                "agent_id": 1001,
                "user_id": 1,
                "session_id": "session-1",
                "title": "新标题",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        update_history_session.assert_called_once_with(
            1001,
            1,
            "session-1",
            "新标题",
        )


if __name__ == "__main__":
    unittest.main()
