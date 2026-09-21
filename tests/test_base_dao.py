import unittest
from unittest.mock import patch

from dao.BaseDAO import BaseDAO


class BaseDAOTest(unittest.TestCase):

    @patch("dao.BaseDAO.SessionLocal")
    def test_execute_commits_and_removes_scoped_session(self, session_local):
        db_session = unittest.mock.Mock()
        session_local.return_value = db_session

        result = BaseDAO()._execute(lambda session: "ok")

        self.assertEqual(result, "ok")
        db_session.commit.assert_called_once_with()
        db_session.rollback.assert_not_called()
        session_local.remove.assert_called_once_with()

    @patch("dao.BaseDAO.logger")
    @patch("dao.BaseDAO.SessionLocal")
    def test_execute_rolls_back_and_removes_scoped_session_on_error(
        self,
        session_local,
        _logger,
    ):
        db_session = unittest.mock.Mock()
        session_local.return_value = db_session

        def raise_error(_session):
            raise RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            BaseDAO()._execute(raise_error)

        db_session.commit.assert_not_called()
        db_session.rollback.assert_called_once_with()
        session_local.remove.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
