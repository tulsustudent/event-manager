import unittest
from jose import jwt
from fastapi import HTTPException

from backend.app.auth import (
    create_access_token,
    get_current_user,
    get_current_user_optional,
    SECRET_KEY,
    ALGORITHM,
)


class CreateAccessTokenTestCase(unittest.TestCase):
    def test_token_contains_subject(self):
        token = create_access_token({"sub": "alice"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        self.assertEqual(payload["sub"], "alice")

    def test_token_has_expiry_claim(self):
        token = create_access_token({"sub": "alice"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        self.assertIn("exp", payload)


class GetCurrentUserOptionalTestCase(unittest.TestCase):
    def test_returns_none_without_token(self):
        self.assertIsNone(get_current_user_optional(token=None, db=None))

    def test_returns_none_for_invalid_token(self):
        self.assertIsNone(get_current_user_optional(token="not-a-valid-token", db=None))


class GetCurrentUserTestCase(unittest.TestCase):
    def test_raises_401_without_token(self):
        with self.assertRaises(HTTPException) as ctx:
            get_current_user(token=None, db=None)
        self.assertEqual(ctx.exception.status_code, 401)

    def test_raises_401_for_invalid_token(self):
        with self.assertRaises(HTTPException) as ctx:
            get_current_user(token="garbage.token.value", db=None)
        self.assertEqual(ctx.exception.status_code, 401)


if __name__ == "__main__":
    unittest.main()
