"""加载应用配置、环境变量和 Agent 能力声明。"""

import json
import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APPLICATION_CONFIG_PATH = PROJECT_ROOT / "application.yml"
CAPABILITIES_PATH = PROJECT_ROOT / "backend" / "agent_capabilities.json"

# 本地环境变量文件位于 Agent 工程的上一级目录。
load_dotenv(dotenv_path=PROJECT_ROOT.parent / ".env")

# 服务配置
SERVER_PORT = "server.port"
SERVER_HOST = "server.host"
SERVER_LOGGER_FILE = "server.logger.file"
SERVER_LOGGER_LEVEL = "server.logger.level"

# 模型配置
AI_OPENAI_MODEL = "ai.openai.model"
AI_OPENAI_API_KEY = "ai.openai.api-key"
AI_OPENAI_BASE_URL = "ai.openai.base-url"
AI_OPENAI_TEMPERATURE = "ai.openai.temperature"
AI_OPENAI_TIMEOUT = "ai.openai.timeout"

# LangGraph 检查点配置
AI_AGENT_CHECKPOINTER_POSTGRES_MIN = "ai.agent.checkpointer.postgres.min"
AI_AGENT_CHECKPOINTER_POSTGRES_MAX = "ai.agent.checkpointer.postgres.max"
AI_AGENT_CHECKPOINTER_POSTGRES_URL = "ai.agent.checkpointer.postgres.url"

# 电商后端配置
ECOMMERCE_BASE_URL = "ecommerce.base-url"
ECOMMERCE_SERVICE_TOKEN = "ecommerce.service-token"
ECOMMERCE_CONNECT_TIMEOUT = "ecommerce.connect-timeout"
ECOMMERCE_READ_TIMEOUT = "ecommerce.read-timeout"

# 网关接入前，Nacos 配置保持隔离，不参与服务启动。
NACOS_SERVER_ADDR = "nacos.server-addr"
NACOS_USERNAME = "nacos.username"
NACOS_PASSWORD = "nacos.password"
NACOS_CONFIG_NAMESPACE = "nacos.config.namespace"
NACOS_CONFIG_GROUP = "nacos.config.group"
NACOS_DISCOVERY_NAME = "nacos.discovery.name"
NACOS_DISCOVERY_NAMESPACE = "nacos.discovery.namespace"
NACOS_DISCOVERY_IP = "nacos.discovery.ip"


class ConfigManager:
    """读取 YAML 配置，并解析其中的环境变量占位符。"""

    def __init__(self, file_path: Path = APPLICATION_CONFIG_PATH):
        """从指定 YAML 文件加载应用配置。"""

        self._config = self._load_yaml(file_path)

    @staticmethod
    def _load_yaml(file_path: Path) -> dict[str, Any]:
        """读取 YAML 文件，并将空文件规范化为空字典。"""

        if not file_path.exists():
            raise FileNotFoundError(f"配置文件缺失: {file_path}")
        try:
            with file_path.open(encoding="utf-8") as file:
                return yaml.safe_load(file) or {}
        except yaml.YAMLError as exc:
            raise ValueError(f"YAML 语法错误 ({file_path}): {exc}") from exc

    def get_config(self) -> dict[str, Any]:
        """返回完整配置。"""

        return self._config

    def get(self, key_path: str, default: Any = None) -> Any:
        """按点分路径读取配置，并解析 ``${ENV_VAR}``。"""

        current: Any = self._config
        try:
            # 逐层解析点分键，任一层缺失或类型不匹配时返回默认值。
            for key in key_path.split("."):
                current = current[key]
        except (KeyError, TypeError):
            return default

        # 完整的 ${ENV_VAR} 配置值由环境变量替换，不处理字符串内嵌占位符。
        if isinstance(current, str) and current.startswith("${") and current.endswith("}"):
            return os.getenv(current[2:-1], default)
        return current


def load_agent_capabilities() -> dict[str, Any]:
    """读取调试后台使用的 Agent 能力声明。"""

    with CAPABILITIES_PATH.open(encoding="utf-8") as file:
        return json.load(file)


config_manager = ConfigManager()
