import unittest
from unittest.mock import patch

from agent.tianji.RouterAgent import RouterAgent


class BaseAgentStopTest(unittest.TestCase):

    @patch("agent.BaseAgent.redis")
    def test_stop_flag_lifecycle(self, redis_client):
        redis_client.exists.return_value = 1
        agent = RouterAgent()

        agent.stop("session-1")
        agent.reset_stop("session-1")
        stopped = agent.is_stop("session-1")

        key = "AGENT_CENTER_STOP_FLAGS:1001:session-1"
        redis_client.setex.assert_called_once_with(key, 120, "1")
        redis_client.delete.assert_called_once_with(key)
        redis_client.exists.assert_called_once_with(key)
        self.assertTrue(stopped)


if __name__ == "__main__":
    unittest.main()
