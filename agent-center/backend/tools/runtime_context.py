"""定义 Agent 工具使用的可信运行时上下文。"""

from dataclasses import dataclass, field
from typing import Any

from backend.integrations.ecommerce_client import EcommerceClient


@dataclass
class AgentContext:
    """向工具注入电商客户端、可信用户身份和页面上下文。"""

    ecommerce_client: EcommerceClient
    user_id: str
    runtime_context: dict[str, Any] = field(default_factory=dict)
