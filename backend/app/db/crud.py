from sqlalchemy.orm import Session
import bcrypt
from passlib.context import CryptContext
from backend.app.db import models, schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    # Используем срез [:72], чтобы избежать ValueError из-за длины пароля
    return bcrypt.hashpw(password[:72].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# create_event (без user_id) лучше удалить, чтобы не было конфликтов

def create_user_event(db: Session, event: schemas.EventCreate, user_id: int):
    # Используем model_dump() вместо dict()
    db_event = models.Event(**event.model_dump(), creator_id=user_id)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def get_events(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Event).filter(models.Event.creator_id == user_id).offset(skip).limit(limit).all()


def delete_event(db: Session, event_id: int, user_id: int):
    event = db.query(models.Event).filter(
        models.Event.id == event_id,
        models.Event.creator_id == user_id
    ).first()
    if event:
        db.delete(event)
        db.commit()
        return True
    return False


def update_event(db: Session, event_id: int, user_id: int, event_update: schemas.EventCreate):
    db_event = db.query(models.Event).filter(
        models.Event.id == event_id,
        models.Event.creator_id == user_id
    ).first()
    if not db_event:
        return None

    # Обновляем поля через model_dump()
    for key, value in event_update.model_dump().items():
        setattr(db_event, key, value)

    db.commit()
    db.refresh(db_event)
    return db_event