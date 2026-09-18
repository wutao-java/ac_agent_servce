import importlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


config_module = importlib.import_module("config.ConfigManager")


class ConfigManagerEnvTest(unittest.TestCase):

    def test_loads_env_from_project_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "application.yml").write_text(
                "db:\n  url: ${AGENT_CENTER_TEST_DB_URL}\n", encoding="utf-8"
            )
            (root / ".env").write_text(
                "AGENT_CENTER_TEST_DB_URL=mysql+pymysql://local/db\n", encoding="utf-8"
            )

            with patch.dict(os.environ):
                os.environ.pop("AGENT_CENTER_TEST_DB_URL", None)
                with patch.object(config_module, "get_project_root", return_value=root):
                    manager = config_module.ConfigManager()
                    with patch.object(manager, "_config", None):
                        manager.load_config()
                        self.assertEqual(
                            manager.get("db.url"), "mysql+pymysql://local/db"
                        )

    def test_process_environment_takes_precedence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "application.yml").write_text(
                "db:\n  url: ${AGENT_CENTER_TEST_DB_URL}\n", encoding="utf-8"
            )
            (root / ".env").write_text(
                "AGENT_CENTER_TEST_DB_URL=from-file\n", encoding="utf-8"
            )

            with patch.dict(os.environ, {"AGENT_CENTER_TEST_DB_URL": "from-process"}):
                with patch.object(config_module, "get_project_root", return_value=root):
                    manager = config_module.ConfigManager()
                    with patch.object(manager, "_config", None):
                        manager.load_config()
                        self.assertEqual(manager.get("db.url"), "from-process")


if __name__ == "__main__":
    unittest.main()
