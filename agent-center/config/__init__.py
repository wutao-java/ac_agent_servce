"""配置基础设施包，对外提供配置管理器和全局日志器。"""

from .ConfigManager import config_manager
from .Logger import logger

__all__ = ["config_manager", "logger"]
