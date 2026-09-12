"""创建同时支持控制台和文件输出的应用日志器。"""

import logging

from backend.config.settings import (
    PROJECT_ROOT,
    SERVER_LOGGER_FILE,
    SERVER_LOGGER_LEVEL,
    config_manager,
)


def setup_logging() -> logging.Logger:
    """按应用配置初始化日志器。"""

    logger = logging.getLogger("AgentCenter")
    level = logging.getLevelName(config_manager.get(SERVER_LOGGER_LEVEL, "INFO"))
    logger.setLevel(level)
    # 模块被重复导入时复用既有处理器，避免一条日志重复输出。
    if logger.handlers:
        return logger

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logger_file = config_manager.get(SERVER_LOGGER_FILE)
    if logger_file:
        # 仅在配置日志文件时启用文件输出，并自动创建父目录。
        log_file = PROJECT_ROOT / logger_file
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger


logger = setup_logging()
