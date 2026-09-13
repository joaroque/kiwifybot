import unittest

import app as web_app


class AppSecurityTests(unittest.TestCase):
    def setUp(self):
        web_app.app.config.update(TESTING=True)
        self.client = web_app.app.test_client()

    def test_login_post_without_csrf_token_is_rejected(self):
        response = self.client.post(
            "/login", data={"email": "user@example.com", "password": "secret"}
        )
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
