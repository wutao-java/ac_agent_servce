import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from web import app


class AuthRouterTest(unittest.TestCase):

    def test_create_token_accepts_app_secret(self):
        expected = {
            "token": "test-token",
            "expire_hours": 720,
            "app_id": 1,
        }

        with patch(
            "web.router.AuthRouter.app_dao.create_token",
            return_value=expected,
        ) as create_token:
            response = TestClient(app).post(
                "/auth/token",
                json={
                    "app_key": "test-app-key",
                    "app_secret": "test-app-secret",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)
        create_token.assert_called_once_with("test-app-key", "test-app-secret")


if __name__ == "__main__":
    unittest.main()
