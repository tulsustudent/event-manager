import unittest
from unittest import mock

import fakeredis

from backend.app import cache


class CacheTestCase(unittest.TestCase):
    def setUp(self):
        cache.reset_client()
        self.fake = fakeredis.FakeRedis(decode_responses=True)
        self._patcher = mock.patch.object(cache, "get_redis_client", return_value=self.fake)
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()
        cache.reset_client()

    def test_set_then_get_roundtrip(self):
        cache.cache_set("key1", {"a": 1, "b": [1, 2, 3]})
        self.assertEqual(cache.cache_get("key1"), {"a": 1, "b": [1, 2, 3]})

    def test_get_missing_key_returns_none(self):
        self.assertIsNone(cache.cache_get("does-not-exist"))

    def test_get_version_starts_at_zero(self):
        self.assertEqual(cache.get_version("fresh-namespace"), 0)

    def test_bump_version_increments(self):
        v0 = cache.get_version("ns")
        cache.bump_version("ns")
        v1 = cache.get_version("ns")
        cache.bump_version("ns")
        v2 = cache.get_version("ns")
        self.assertEqual(v1, v0 + 1)
        self.assertEqual(v2, v0 + 2)

    def test_get_redis_client_is_memoized(self):
        cache.reset_client()
        self._patcher.stop()
        with mock.patch("backend.app.cache.redis.Redis.from_url", return_value=self.fake) as from_url:
            client_a = cache.get_redis_client()
            client_b = cache.get_redis_client()
            self.assertIs(client_a, client_b)
            from_url.assert_called_once()
        self._patcher.start()

    # ---- fail-open поведение: недоступный Redis не должен ронять приложение ----
    def test_cache_get_fails_open_on_redis_error(self):
        broken = mock.Mock()
        broken.get.side_effect = ConnectionError("Redis недоступен")
        with mock.patch.object(cache, "get_redis_client", return_value=broken):
            self.assertIsNone(cache.cache_get("k"))

    def test_cache_set_fails_open_on_redis_error(self):
        broken = mock.Mock()
        broken.setex.side_effect = ConnectionError("Redis недоступен")
        with mock.patch.object(cache, "get_redis_client", return_value=broken):
            cache.cache_set("k", {"a": 1})  # не должно бросать исключение

    def test_get_version_fails_open_on_redis_error(self):
        broken = mock.Mock()
        broken.get.side_effect = ConnectionError("Redis недоступен")
        with mock.patch.object(cache, "get_redis_client", return_value=broken):
            self.assertEqual(cache.get_version("ns"), 0)

    def test_bump_version_fails_open_on_redis_error(self):
        broken = mock.Mock()
        broken.incr.side_effect = ConnectionError("Redis недоступен")
        with mock.patch.object(cache, "get_redis_client", return_value=broken):
            cache.bump_version("ns")  # не должно бросать исключение

    def test_cache_get_ignores_corrupted_json(self):
        self.fake.set("bad-json", "{not valid json")
        self.assertIsNone(cache.cache_get("bad-json"))


if __name__ == "__main__":
    unittest.main()
