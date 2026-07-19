from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from passlib.context import CryptContext

from . import models, schemas

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


# ====================== USER CRUD ======================
def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """Создание пользователя с хешированием пароля."""
    db_user = models.User(
        username=user.username,
        password_hash=hash_password(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# ====================== EVENT CRUD ======================
def get_event_by_id(db: Session, event_id: int):
    # Загружаем участников сразу
    return db.query(models.Event).options(joinedload(models.Event.participants)).filter(
        models.Event.id == event_id
    ).first()


def create_user_event(db: Session, event: schemas.EventCreate, user_id: int):
    """Создание события через CRUD"""
    db_event = models.Event(
        title=event.title,
        description=event.description,
        is_private=event.is_private,
        event_date=event.event_date,
        category=event.category,
        creator_id=user_id
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def update_event(db: Session, event_id: int, event_update: schemas.EventUpdate):
    """Частичное обновление события — меняются только переданные поля."""
    db_event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not db_event:
        return None

    update_data = event_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_event, field, value)

    db.commit()
    db.refresh(db_event)
    return db_event


def delete_event(db: Session, event_id: int) -> bool:
    """Удаление события"""
    db_event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if db_event:
        db.delete(db_event)
        db.commit()
        return True
    return False


# ====================== PARTICIPANT CRUD ======================
def add_participant(db: Session, event_id: int, user_id: int):
    """Добавление участника"""
    exists = db.query(models.EventParticipant).filter(
        models.EventParticipant.event_id == event_id,
        models.EventParticipant.user_id == user_id
    ).first()
    if exists:
        return exists

    db_participant = models.EventParticipant(
        event_id=event_id,
        user_id=user_id,
        username=get_user_by_id(db, user_id).username
    )
    db.add(db_participant)
    db.commit()
    db.refresh(db_participant)
    return db_participant


def remove_participant(db: Session, event_id: int, user_id: int) -> bool:
    """Удаление участника"""
    db_participant = db.query(models.EventParticipant).filter(
        models.EventParticipant.event_id == event_id,
        models.EventParticipant.user_id == user_id
    ).first()

    if db_participant:
        db.delete(db_participant)
        db.commit()
        return True
    return False