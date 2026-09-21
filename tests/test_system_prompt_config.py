import unittest
from unittest.mock import patch

from agent.prompts.SystemPromptConfig import SystemPromptConfig
from common import (
    NACOS_CONFIG_GROUP,
    PROMPT_BUY_CHAT_DATA_ID,
    PROMPT_CONSULT_CHAT_DATA_ID,
    PROMPT_KNOWLEDGE_CHAT_DATA_ID,
    PROMPT_RECOMMEND_CHAT_DATA_ID,
    PROMPT_ROUTE_CHAT_DATA_ID,
    PROMPT_TEXT_CHAT_DATA_ID,
    PROMPT_UNKNOWN_CHAT_DATA_ID,
)


class FakeNacosClient:

    def __init__(self, values):
        self.values = values

    def get_config(self, data_id, group, timeout=5):
        return self.values[data_id]


class SystemPromptConfigTest(unittest.TestCase):

    def test_loads_prompt_data_ids_from_nacos(self):
        config_values = {
            NACOS_CONFIG_GROUP: "DEFAULT_GROUP",
            PROMPT_ROUTE_CHAT_DATA_ID: "route.txt",
            PROMPT_RECOMMEND_CHAT_DATA_ID: "recommend.txt",
            PROMPT_BUY_CHAT_DATA_ID: "buy.txt",
            PROMPT_CONSULT_CHAT_DATA_ID: "consult.txt",
            PROMPT_KNOWLEDGE_CHAT_DATA_ID: "knowledge.txt",
            PROMPT_UNKNOWN_CHAT_DATA_ID: "unknown.txt",
            PROMPT_TEXT_CHAT_DATA_ID: "text.txt",
        }

        with patch(
            "agent.prompts.SystemPromptConfig.config_manager.get",
            side_effect=lambda key, default=None: config_values.get(key, default),
        ):
            prompt_config = SystemPromptConfig()
            prompt_config.client = FakeNacosClient({
                "route.txt": "route prompt",
                "recommend.txt": "recommend prompt",
                "buy.txt": "buy prompt",
                "consult.txt": "consult prompt",
                "knowledge.txt": "knowledge prompt",
                "unknown.txt": "unknown prompt",
                "text.txt": "text prompt",
            })

            prompt_config.load_all_configs()

        self.assertEqual(prompt_config._values["chat_route_message"], "route prompt")
        self.assertEqual(prompt_config._values["chat_buy_message"], "buy prompt")
        self.assertEqual(prompt_config._values["chat_text_message"], "text prompt")

    def test_check_updates_refreshes_changed_prompt(self):
        config_values = {
            NACOS_CONFIG_GROUP: "DEFAULT_GROUP",
            PROMPT_ROUTE_CHAT_DATA_ID: "route.txt",
        }

        with patch(
            "agent.prompts.SystemPromptConfig.config_manager.get",
            side_effect=lambda key, default=None: config_values.get(key, default),
        ):
            prompt_config = SystemPromptConfig()
            prompt_config._config_map = {PROMPT_ROUTE_CHAT_DATA_ID: "chat_route_message"}
            prompt_config.client = FakeNacosClient({"route.txt": "old prompt"})
            prompt_config.load_all_configs()
            prompt_config.client.values["route.txt"] = "new prompt"

            prompt_config._check_updates()

        self.assertEqual(prompt_config._values["chat_route_message"], "new prompt")


if __name__ == "__main__":
    unittest.main()
