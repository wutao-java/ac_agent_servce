"""创建 OpenAI-compatible 聊天模型。"""

from typing import Any

from langchain.chat_models import init_chat_model

from backend.config.settings import (
    AI_OPENAI_API_KEY,
    AI_OPENAI_BASE_URL,
    AI_OPENAI_MODEL,
    AI_OPENAI_TEMPERATURE,
    AI_OPENAI_TIMEOUT,
    config_manager,
)


def create_chat_model() -> Any:
    """根据应用配置创建聊天模型客户端。"""

    api_key = config_manager.get(AI_OPENAI_API_KEY)
    if not api_key:
        raise RuntimeError("AGENT_CENTER_AI_API_KEY 未配置")

    # 使用 OpenAI-compatible 协议，模型名和服务地址均由部署配置决定。
    return init_chat_model(
        model=config_manager.get(AI_OPENAI_MODEL),
        model_provider="openai",
        api_key=api_key,
        base_url=config_manager.get(AI_OPENAI_BASE_URL),
        temperature=float(config_manager.get(AI_OPENAI_TEMPERATURE, 0.3)),
        timeout=int(config_manager.get(AI_OPENAI_TIMEOUT, 60)),
        tags=["XiaozheAgent"],
    )
