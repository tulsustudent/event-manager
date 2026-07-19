from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import logging
from backend.app.db import models, schemas, crud
from backend.app.db.database import engine, get_db
from backend.app.auth import verify_password, create_access_token, get_current_user

models.Base.metadata.create_all(bind=engine)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI()


# Регистрация
@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        logger.warning(f"Registration attempt failed: {user.email} is already registered")
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = crud.create_user(db=db, user=user)
    logger.info(f"New user registered: {user.email}")
    return new_user


# Получение токена
@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Login failed for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    logger.info(f"User logged in: {form_data.username}")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


# Создание события
@app.post("/events/", response_model=schemas.Event)
def create_event(
        event: schemas.EventCreate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    logger.info(f"User {current_user.email} is creating a new event: {event.title}")
    return crud.create_user_event(db=db, event=event, user_id=current_user.id)


# Чтение событий текущего пользователя (созданных им)
@app.get("/events/", response_model=List[schemas.Event])
def read_events(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    logger.info(f"User {current_user.email} requested their events list")
    return crud.get_events(db, user_id=current_user.id, skip=skip, limit=limit)


# Удаление события
@app.delete("/events/{event_id}")
def delete_event(
        event_id: int,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    success = crud.delete_event(db=db, event_id=event_id, user_id=current_user.id)
    if not success:
        logger.warning(f"User {current_user.email} failed to delete event {event_id}: Not found")
        raise HTTPException(status_code=404, detail="Event not found")

    logger.info(f"User {current_user.email} deleted event {event_id}")
    return {"detail": "Event deleted successfully"}


# Обновление события
@app.put("/events/{event_id}", response_model=schemas.Event)
def update_event(
        event_id: int,
        event_update: schemas.EventCreate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    updated_event = crud.update_event(db=db, event_id=event_id, user_id=current_user.id, event_update=event_update)
    if not updated_event:
        logger.warning(f"User {current_user.email} failed to update event {event_id}: Not found")
        raise HTTPException(status_code=404, detail="Event not found")

    logger.info(f"User {current_user.email} updated event {event_id}")
    return updated_event


# Новый эндпоинт профиля
@app.get("/users/me/events/")
def read_my_events(current_user: models.User = Depends(get_current_user)):
    logger.info(f"User {current_user.email} accessed their profile events")
    return {
        "created": current_user.events,
        "participated": current_user.participated_events
    }