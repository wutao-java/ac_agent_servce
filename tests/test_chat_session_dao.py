import unittest
from unittest.mock import patch

from dao.ChatSessionDAO import ChatSessionDAO
from dao.vo.SessionVO import Example


class ChatSessionDAOTest(unittest.TestCase):

    @patch("dao.ChatSessionDAO.config_manager.get")
    def test_hot_examples_returns_example_value_objects(self, get_config):
        get_config.return_value = [
            {"title": "示例标题", "describe": "示例描述"},
        ]

        examples = ChatSessionDAO().hot_examples(num=1, agent_id=1001)

        self.assertEqual(
            examples,
            [Example(title="示例标题", describe="示例描述")],
        )
        get_config.assert_called_once_with("ai.1001.session.examples", [])


if __name__ == "__main__":
    unittest.main()
