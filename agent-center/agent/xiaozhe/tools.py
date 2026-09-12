"""定义小哲电商 Agent 可调用的只读业务工具。"""

import json
from dataclasses import dataclass, field
from typing import Any

from langchain.tools import ToolRuntime, tool

from .client import EcommerceClient


@dataclass
class AgentContext:
    """向工具注入电商客户端、可信用户身份和运行时上下文。"""

    ecommerce_client: EcommerceClient
    user_id: str
    runtime_context: dict[str, Any] = field(default_factory=dict)


def _json(data: Any) -> str:
    """将工具结果序列化为保留中文的 JSON 文本。"""

    return json.dumps(data, ensure_ascii=False, default=str)


@tool
async def search_products(keyword: str, runtime: ToolRuntime) -> str:
    """按商品名称或描述关键词搜索商品、价格、库存和活动。"""
    return _json(await runtime.context.ecommerce_client.list_products(keyword or None))


@tool
async def get_product(product_id: int, runtime: ToolRuntime) -> str:
    """按商品 ID 查询商品详情、价格、库存和售后限制。"""
    return _json(await runtime.context.ecommerce_client.get_product(product_id))


@tool
async def get_current_user_order(order_no: str, runtime: ToolRuntime) -> str:
    """查询当前用户自己的订单详情。"""
    return _json(await runtime.context.ecommerce_client.get_order(order_no, runtime.context.user_id))


@tool
async def get_current_user_logistics(order_no: str, runtime: ToolRuntime) -> str:
    """查询当前用户指定订单的物流轨迹。"""
    return _json(await runtime.context.ecommerce_client.get_logistics(order_no, runtime.context.user_id))


@tool
async def get_current_user_preferences(runtime: ToolRuntime) -> str:
    """查询当前用户的购物偏好。"""
    return _json(await runtime.context.ecommerce_client.get_user_preferences(runtime.context.user_id))


@tool
async def get_current_user_coupons(runtime: ToolRuntime) -> str:
    """查询当前用户可见的优惠券。"""
    return _json(await runtime.context.ecommerce_client.get_user_coupons(runtime.context.user_id))


@tool
async def search_after_sale_policies(scene_key: str, runtime: ToolRuntime) -> str:
    """按场景查询退款、退货和换货规则。"""
    return _json(await runtime.context.ecommerce_client.list_after_sale_policies(scene_key or None))


@tool
async def search_faq(keyword: str, runtime: ToolRuntime) -> str:
    """查询发票、配送和售后常见问题。"""
    return _json(await runtime.context.ecommerce_client.list_faq(keyword or None))


ECOMMERCE_TOOLS = [
    search_products,
    get_product,
    get_current_user_order,
    get_current_user_logistics,
    get_current_user_preferences,
    get_current_user_coupons,
    search_after_sale_policies,
    search_faq,
]
if __name__ == '__main__':
    get_current_user_order()

