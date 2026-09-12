"""验证电商后端客户端的鉴权透传与错误处理。"""

import unittest

import httpx

from agent.xiaozhe.client import EcommerceApiError, EcommerceClient


class EcommerceClientTest(unittest.IsolatedAsyncioTestCase):
    """覆盖电商后端异步客户端的关键请求契约。"""

    async def test_protected_request_sends_service_and_user_headers(self):
        """受保护请求应同时携带服务令牌和可信用户身份。"""

        async def handler(request: httpx.Request):
            """模拟成功响应并断言客户端发送的鉴权请求头。"""

            self.assertEqual(request.url.path, "/api/orders/SO-1")
            self.assertEqual(request.headers["X-Agent-Service-Token"], "service-token")
            self.assertEqual(request.headers["X-Agent-User-Id"], "user-1")
            return httpx.Response(200, json={"success": True, "data": {"orderNo": "SO-1"}})

        client = EcommerceClient(
            base_url="http://ecommerce.test",
            service_token="service-token",
            transport=httpx.MockTransport(handler),
        )
        self.addAsyncCleanup(client.close)

        result = await client.get_order("SO-1", "user-1")

        self.assertEqual(result["orderNo"], "SO-1")

    async def test_business_error_is_raised_with_backend_message(self):
        """后端业务失败时应保留原始错误消息并抛出统一异常。"""

        async def handler(request: httpx.Request):
            """模拟电商后端返回无权访问订单的业务错误。"""

            return httpx.Response(403, json={
                "success": False,
                "code": "ORDER_ACCESS_DENIED",
                "message": "只能访问自己的订单",
            })

        client = EcommerceClient(
            base_url="http://ecommerce.test",
            service_token="service-token",
            transport=httpx.MockTransport(handler),
        )
        self.addAsyncCleanup(client.close)

        with self.assertRaisesRegex(EcommerceApiError, "只能访问自己的订单"):
            await client.get_order("SO-2", "user-1")


if __name__ == "__main__":
    unittest.main()
