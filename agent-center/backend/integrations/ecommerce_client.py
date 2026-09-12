"""封装 Agent 访问电商后端受保护接口的异步客户端。"""

from typing import Any

import httpx


class EcommerceApiError(RuntimeError):
    """表示电商后端返回的接口或业务错误。"""

    def __init__(self, code: str, message: str, status_code: int):
        """保存业务错误码、提示消息和 HTTP 状态码。"""

        super().__init__(message)
        self.code = code
        self.status_code = status_code


class EcommerceClient:
    """通过服务令牌和可信用户身份访问电商后端。"""

    SERVICE_TOKEN_HEADER = "X-Agent-Service-Token"
    USER_ID_HEADER = "X-Agent-User-Id"

    def __init__(
        self,
        base_url: str,
        service_token: str | None,
        connect_timeout: float = 2.0,
        read_timeout: float = 20.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        """保存连接参数，并延迟创建可复用的异步 HTTP 客户端。"""

        self._base_url = base_url.rstrip("/")
        self._service_token = service_token or ""
        self._timeout = httpx.Timeout(read_timeout, connect=connect_timeout)
        self._transport = transport
        self._client: httpx.AsyncClient | None = None

    async def close(self) -> None:
        """关闭已创建的 HTTP 客户端。"""

        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def list_products(self, keyword: str | None = None) -> Any:
        """按可选关键词查询商品列表。"""

        params = {"keyword": keyword} if keyword else None
        return await self._request("GET", "/api/products", params=params)

    async def get_product(self, product_id: int) -> Any:
        """按商品 ID 查询商品详情。"""

        return await self._request("GET", f"/api/products/{product_id}")

    async def get_order(self, order_no: str, user_id: str) -> Any:
        """查询可信用户自己的指定订单。"""

        return await self._request("GET", f"/api/orders/{order_no}", user_id=user_id)

    async def get_logistics(self, order_no: str, user_id: str) -> Any:
        """查询可信用户指定订单的物流信息。"""

        return await self._request("GET", f"/api/orders/{order_no}/logistics", user_id=user_id)

    async def get_user_preferences(self, user_id: str) -> Any:
        """查询可信用户的购物偏好。"""

        return await self._request("GET", f"/api/users/{user_id}/preferences", user_id=user_id)

    async def get_user_coupons(self, user_id: str) -> Any:
        """查询可信用户可见的优惠券。"""

        return await self._request("GET", f"/api/users/{user_id}/coupons", user_id=user_id)

    async def list_after_sale_policies(self, scene_key: str | None = None) -> Any:
        """按可选场景查询售后政策。"""

        params = {"sceneKey": scene_key} if scene_key else None
        return await self._request("GET", "/api/after-sale/policies", params=params)

    async def list_faq(self, keyword: str | None = None) -> Any:
        """按可选关键词查询常见问题。"""

        params = {"keyword": keyword} if keyword else None
        return await self._request("GET", "/api/faq", params=params)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        user_id: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """发送请求并统一处理鉴权、响应解析和业务错误。"""

        headers = {}
        if self._service_token:
            headers[self.SERVICE_TOKEN_HEADER] = self._service_token
        if user_id:
            # 用户级接口必须同时携带服务令牌，不能单独信任用户 ID 请求头。
            if not self._service_token:
                raise EcommerceApiError(
                    "SERVICE_AUTH_NOT_CONFIGURED",
                    "Agent 服务令牌未配置",
                    503,
                )
            headers[self.USER_ID_HEADER] = user_id

        response = await self._get_client().request(
            method,
            path,
            params=params,
            headers=headers,
        )
        try:
            payload = response.json()
        except ValueError as exc:
            raise EcommerceApiError(
                "INVALID_RESPONSE",
                "电商后端返回了无法解析的响应",
                response.status_code,
            ) from exc

        # HTTP 错误和业务响应失败统一转换为调用方可处理的领域异常。
        if response.is_error or payload.get("success") is False:
            raise EcommerceApiError(
                str(payload.get("code", "ECOMMERCE_API_ERROR")),
                str(payload.get("message", "电商后端请求失败")),
                response.status_code,
            )
        return payload.get("data")

    def _get_client(self) -> httpx.AsyncClient:
        """延迟创建并复用异步 HTTP 客户端及其连接池。"""

        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                transport=self._transport,
            )
        return self._client
