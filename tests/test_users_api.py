from tests.base import ApiTestCase


class RegisterTestCase(ApiTestCase):
    def test_register_success(self):
        res = self.register("alice", "password123")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "User registered successfully")

    def test_register_duplicate_username_rejected(self):
        self.register("alice", "password123")
        res = self.register("alice", "password123")
        self.assertEqual(res.status_code, 400)

    def test_register_password_too_short_rejected(self):
        res = self.register("alice", "12345")  # 5 символов, минимум — 6
        self.assertEqual(res.status_code, 422)

    def test_register_username_too_short_rejected(self):
        res = self.register("ab", "password123")  # 2 символа, минимум — 3
        self.assertEqual(res.status_code, 422)


class LoginTestCase(ApiTestCase):
    def test_login_success_returns_token(self):
        self.register("alice", "password123")
        res = self.login("alice", "password123")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertIn("access_token", body)
        self.assertEqual(body["username"], "alice")
        self.assertEqual(body["token_type"], "bearer")

    def test_login_wrong_password_rejected(self):
        self.register("alice", "password123")
        res = self.login("alice", "wrong-password")
        self.assertEqual(res.status_code, 401)

    def test_login_nonexistent_user_rejected(self):
        res = self.login("ghost", "whatever")
        self.assertEqual(res.status_code, 401)


if __name__ == "__main__":
    import unittest
    unittest.main()
