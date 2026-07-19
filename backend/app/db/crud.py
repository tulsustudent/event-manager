from sqlalchemy.orm import Session
import bcrypt
from backend.app.db import models, schemas

# --- Авторизация ---

def get_password_hash(password: str) -> str:
    # Используем срез [:72], чтобы избежать ограничений bcrypt
    return bcrypt.hashpw(password[:72].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password[:72].encode('utf-8'), hashed_password.encode('utf-8'))

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- События ---

def create_user_event(db: Session, event: schemas.EventCreate, user_id: int):
    db_event = models.Event(**event.model_dump(), creator_id=user_id)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

# Получение созданных пользователем событий
def get_user_created_events(db: Session, user_id: int):
    return db.query(models.Event).filter(models.Event.creator_id == user_id).all()

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

    for key, value in event_update.model_dump().items():
        setattr(db_event, key, value)

    db.commit()
    db.refresh(db_event)
    return db_event

def get_user_profile_data(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    return {
        "created": user.events,
        "participated": user.participated_events
    }

def get_events(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    # Возвращаем все события (или фильтруй, если нужно только свои)
    return db.query(models.Event).offset(skip).limit(limit).all()