import unittest
from unittest import mock

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db import database


class GetDbTestCase(unittest.TestCase):
    """
    get_db() никогда не выполняется в API-тестах: ApiTestCase (tests/base.py)
    полностью подменяет его через app.dependency_overrides[get_db], поэтому
    реальное тело функции (создание сессии, yield, закрытие в finally) не
    покрывалось ни одним тестом — это и есть причина missing 16-20 в database.py.
    Здесь вызываем сам генератор напрямую, без FastAPI, на тестовом sqlite-движке.
    """

    def setUp(self):
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def tearDown(self):
        self.engine.dispose()

    def test_get_db_yields_a_working_session(self):
        with mock.patch.object(database, "SessionLocal", self.TestSessionLocal):
            gen = database.get_db()
            db = next(gen)
            self.assertIsNotNone(db)
            # сессия рабочая — можно выполнить простой запрос
            result = db.execute(text("SELECT 1"))
            self.assertEqual(result.scalar(), 1)
            with self.assertRaises(StopIteration):
                next(gen)

    def test_get_db_closes_session_on_generator_exhaustion(self):
        with mock.patch.object(database, "SessionLocal", self.TestSessionLocal):
            gen = database.get_db()
            db = next(gen)
            with mock.patch.object(db, "close", wraps=db.close) as close_spy:
                with self.assertRaises(StopIteration):
                    next(gen)
                close_spy.assert_called_once()


if __name__ == "__main__":
    unittest.main()
