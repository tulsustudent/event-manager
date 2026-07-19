import runpy
import unittest
from unittest import mock

from sqlalchemy import create_engine, inspect
from sqlalchemy.pool import StaticPool

from backend.app.db import init_db as init_db_module
from backend.app.db import database as database_module


class InitDbTestCase(unittest.TestCase):
    def setUp(self):
        # Подменяем реальный (postgres) engine на in-memory sqlite,
        # чтобы не тянуть настоящую БД в юнит-тестах.
        self.test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

    def tearDown(self):
        self.test_engine.dispose()

    def test_init_db_creates_expected_tables(self):
        with mock.patch.object(init_db_module, "engine", self.test_engine):
            init_db_module.init_db(drop_all=False)

        table_names = inspect(self.test_engine).get_table_names()
        self.assertIn("users", table_names)
        self.assertIn("events", table_names)
        self.assertIn("event_participants", table_names)

    def test_init_db_drop_all_then_recreate(self):
        with mock.patch.object(init_db_module, "engine", self.test_engine):
            init_db_module.init_db(drop_all=False)
            init_db_module.init_db(drop_all=True)  # не должно упасть на пустой БД

        table_names = inspect(self.test_engine).get_table_names()
        self.assertIn("users", table_names)


class InitDbMainBlockTestCase(unittest.TestCase):
    """
    Строки 23-25 (input() + drop + вызов init_db внутри if __name__ == '__main__')
    никогда не выполняются при обычном импорте модуля тестами — это и есть причина
    missing 23-25 в init_db.py. Запускаем модуль по-настоящему как скрипт через
    runpy, подменив input() и движок БД на тестовый sqlite.
    """

    def setUp(self):
        self.test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

    def tearDown(self):
        self.test_engine.dispose()

    def test_main_block_with_no_confirmation_creates_tables_without_dropping(self):
        with mock.patch.object(database_module, "engine", self.test_engine), \
             mock.patch("builtins.input", return_value="n"):
            runpy.run_module("backend.app.db.init_db", run_name="__main__")

        table_names = inspect(self.test_engine).get_table_names()
        self.assertIn("users", table_names)

    def test_main_block_with_confirmation_drops_then_recreates(self):
        with mock.patch.object(database_module, "engine", self.test_engine), \
             mock.patch("builtins.input", return_value="y"):
            runpy.run_module("backend.app.db.init_db", run_name="__main__")

        table_names = inspect(self.test_engine).get_table_names()
        self.assertIn("users", table_names)


if __name__ == "__main__":
    unittest.main()
