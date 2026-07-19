import unittest
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db.database import Base
from backend.app.db import crud, schemas


class CrudTestCase(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = Session()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def _make_event_schema(self, **overrides):
        payload = dict(
            title="Party",
            description="Fun times",
            category="Музыка",
            is_private=False,
            event_date=datetime.now(timezone.utc) + timedelta(days=1),
        )
        payload.update(overrides)
        return schemas.EventCreate(**payload)

    # ---- Пароли ----
    def test_hash_password_differs_from_plain(self):
        hashed = crud.hash_password("secret123")
        self.assertNotEqual(hashed, "secret123")

    def test_verify_password_correct(self):
        hashed = crud.hash_password("secret123")
        self.assertTrue(crud.verify_password("secret123", hashed))

    def test_verify_password_incorrect(self):
        hashed = crud.hash_password("secret123")
        self.assertFalse(crud.verify_password("wrong-password", hashed))

    # ---- Пользователи ----
    def test_create_user_and_lookup_by_username(self):
        user = crud.create_user(self.db, schemas.UserCreate(username="bob", password="pw12345"))
        found = crud.get_user_by_username(self.db, "bob")
        self.assertEqual(found.id, user.id)

    def test_get_user_by_id(self):
        user = crud.create_user(self.db, schemas.UserCreate(username="carol", password="pw12345"))
        found = crud.get_user_by_id(self.db, user.id)
        self.assertEqual(found.username, "carol")

    def test_get_user_by_username_not_found_returns_none(self):
        self.assertIsNone(crud.get_user_by_username(self.db, "ghost"))

    # ---- События ----
    def test_create_user_event(self):
        user = crud.create_user(self.db, schemas.UserCreate(username="dave", password="pw12345"))
        event = crud.create_user_event(self.db, self._make_event_schema(), user_id=user.id)
        self.assertEqual(event.creator_id, user.id)
        self.assertEqual(event.title, "Party")

    def test_update_event_partial_fields(self):
        user = crud.create_user(self.db, schemas.UserCreate(username="erin", password="pw12345"))
        event = crud.create_user_event(self.db, self._make_event_schema(), user_id=user.id)

        updated = crud.update_event(self.db, event.id, schemas.EventUpdate(title="Renamed"))
        self.assertEqual(updated.title, "Renamed")
        self.assertEqual(updated.description, "Fun times")  # не переданное поле не меняется

    def test_update_event_not_found_returns_none(self):
        result = crud.update_event(self.db, 9999, schemas.EventUpdate(title="X"))
        self.assertIsNone(result)

    def test_delete_event_true_then_false(self):
        user = crud.create_user(self.db, schemas.UserCreate(username="frank", password="pw12345"))
        event = crud.create_user_event(self.db, self._make_event_schema(), user_id=user.id)

        self.assertTrue(crud.delete_event(self.db, event.id))
        self.assertFalse(crud.delete_event(self.db, event.id))  # уже удалено

    def test_get_event_by_id_not_found(self):
        self.assertIsNone(crud.get_event_by_id(self.db, 9999))

    # ---- Участники ----
    def test_add_participant_is_idempotent(self):
        creator = crud.create_user(self.db, schemas.UserCreate(username="grace", password="pw12345"))
        participant = crud.create_user(self.db, schemas.UserCreate(username="heidi", password="pw12345"))
        event = crud.create_user_event(self.db, self._make_event_schema(), user_id=creator.id)

        first = crud.add_participant(self.db, event.id, participant.id)
        second = crud.add_participant(self.db, event.id, participant.id)
        self.assertEqual(first.id, second.id)

    def test_remove_participant_true_then_false(self):
        creator = crud.create_user(self.db, schemas.UserCreate(username="ivan", password="pw12345"))
        participant = crud.create_user(self.db, schemas.UserCreate(username="judy", password="pw12345"))
        event = crud.create_user_event(self.db, self._make_event_schema(), user_id=creator.id)
        crud.add_participant(self.db, event.id, participant.id)

        self.assertTrue(crud.remove_participant(self.db, event.id, participant.id))
        self.assertFalse(crud.remove_participant(self.db, event.id, participant.id))


if __name__ == "__main__":
    unittest.main()
