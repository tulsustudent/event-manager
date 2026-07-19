from tests.base import ApiTestCase


class HealthCheckTestCase(ApiTestCase):
    def test_health_check_no_auth_required(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)

    def test_health_check_reports_database_ok(self):
        res = self.client.get("/health")
        body = res.json()
        self.assertEqual(body["database"], "ok")
        self.assertEqual(body["status"], "ok")

    def test_health_check_reports_redis_status(self):
        # В тестах Redis подменён на fakeredis (см. tests/base.py), так что ping должен проходить
        res = self.client.get("/health")
        self.assertEqual(res.json()["redis"], "ok")


if __name__ == "__main__":
    import unittest
    unittest.main()
