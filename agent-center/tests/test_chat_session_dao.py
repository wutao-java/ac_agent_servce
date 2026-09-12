import unittest
from datetime import date, datetime, time, timedelta
from types import SimpleNamespace
from unittest.mock import patch

from dao.ChatSessionDAO import (
    LAST_30_DAYS,
    LAST_YEAR,
    MORE_THAN_YEAR,
    NO_CHANGE_MESSAGE,
    SUCCESS_MESSAGE,
    TODAY,
    ChatSessionDAO,
)
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

    def test_query_history_session_groups_latest_thirty_sessions(self):
        today = date.today()
        sessions = [
            SimpleNamespace(
                session_id="today",
                title="今天",
                update_time=datetime.combine(today, time(hour=10)),
            ),
            SimpleNamespace(
                session_id="month",
                title="最近30天",
                update_time=datetime.combine(today - timedelta(days=10), time.min),
            ),
            SimpleNamespace(
                session_id="year",
                title="最近1年",
                update_time=datetime.combine(today - timedelta(days=100), time.min),
            ),
            SimpleNamespace(
                session_id="old",
                title="1年以上",
                update_time=datetime.combine(today - timedelta(days=400), time.min),
            ),
        ]
        db_session = unittest.mock.Mock()
        db_session.execute.return_value.scalars.return_value.all.return_value = sessions
        dao = ChatSessionDAO()

        with patch.object(
            dao,
            "_execute",
            side_effect=lambda operation: operation(db_session),
        ):
            result = dao.query_history_session(agent_id=1001, user_id=1)

        self.assertEqual(
            list(result),
            [MORE_THAN_YEAR, LAST_YEAR, LAST_30_DAYS, TODAY],
        )
        self.assertEqual(result[TODAY][0].session_id, "today")
        self.assertEqual(result[LAST_30_DAYS][0].session_id, "month")
        self.assertEqual(result[LAST_YEAR][0].session_id, "year")
        self.assertEqual(result[MORE_THAN_YEAR][0].session_id, "old")

    def test_update_title_only_sets_initial_title_and_refreshes_update_time(self):
        chat_session = SimpleNamespace(title=None, update_time=None)
        db_session = unittest.mock.Mock()
        db_session.execute.return_value.scalars.return_value.first.return_value = chat_session
        dao = ChatSessionDAO()

        with patch.object(
            dao,
            "_execute",
            side_effect=lambda operation: operation(db_session),
        ):
            result = dao.update_title("session-1", 1001, "a" * 120)

        self.assertEqual(result, SUCCESS_MESSAGE)
        self.assertEqual(chat_session.title, "a" * 100)
        self.assertIsInstance(chat_session.update_time, datetime)

    def test_delete_history_session_reports_no_change(self):
        db_session = unittest.mock.Mock()
        db_session.execute.return_value.rowcount = 0
        dao = ChatSessionDAO()

        with patch.object(
            dao,
            "_execute",
            side_effect=lambda operation: operation(db_session),
        ):
            result = dao.delete_history_session(1001, 1, "missing")

        self.assertEqual(result, NO_CHANGE_MESSAGE)


if __name__ == "__main__":
    unittest.main()
