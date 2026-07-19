from sqlalchemy.orm import Session
from backend.app.db import models, schemas

def create_event(db: Session, event: schemas.EventCreate, user_id: int):
    db_event = models.Event(**event.model_dump(), creator_id=user_id)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def get_events(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Event).offset(skip).limit(limit).all()