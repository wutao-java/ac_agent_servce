import inspect
import unittest

from sqlalchemy import select

from dao.pojo import AppInfo


class AppInfoImportTest(unittest.TestCase):

    def test_package_exports_orm_model_class(self):
        self.assertTrue(inspect.isclass(AppInfo))

        statement = select(AppInfo)

        self.assertIs(statement.column_descriptions[0]["entity"], AppInfo)


if __name__ == "__main__":
    unittest.main()
