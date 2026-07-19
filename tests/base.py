import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

import fakeredis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.app.db.database import Base, get_db
from backend.app.main import app
from backend.app import cache


class ApiTestCase(unittest.TestCase):
    """Базовый TestCase для тестов через HTTP-эндпоинты.

    Каждый тест получает свою чистую in-memory SQLite БД, и app.dependency_overrides
    переопределяет ИМЕННО ту функцию get_db, которую реально использует main.py
    (раньше main.py объявлял свою собственную копию get_db, и override не срабатывал —
    это было исправлено при рефакторинге main.py).

    Redis тоже подменяется на fakeredis (in-memory имитация), чтобы тесты не зависели
    от реально поднятого Redis-сервера и не тормозили на таймаутах подключения.
    """

    def setUp(self):
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

        def override_get_db():
            db = self.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

        cache.reset_client()
        self.fake_redis = fakeredis.FakeRedis(decode_responses=True)
        self._cache_patcher = mock.patch.object(cache, "get_redis_client", return_value=self.fake_redis)
        self._cache_patcher.start()

    def tearDown(self):
        self._cache_patcher.stop()
        cache.reset_client()
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    # ==================== Вспомогательные методы ====================
    def register(self, username="alice", password="password123"):
        return self.client.post("/register", json={"username": username, "password": password})

    def login(self, username="alice", password="password123"):
        return self.client.post("/login", json={"username": username, "password": password})

    def auth_headers(self, username="alice", password="password123"):
        """Регистрирует и логинит пользователя, возвращает (headers, user_id)."""
        self.register(username, password)
        res = self.login(username, password)
        body = res.json()
        return {"Authorization": f"Bearer {body['access_token']}"}, body["user_id"]

    def create_event(self, headers, **overrides):
        payload = {
            "title": "Test Event",
            "description": "Описание",
            "category": "IT",
            "is_private": False,
            "event_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        }
        payload.update(overrides)
        return self.client.post("/events/", json=payload, headers=headers)
