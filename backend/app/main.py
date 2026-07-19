from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.app.db import models, schemas, crud
from backend.app.db.database import engine, get_db
from backend.app.auth import verify_password, create_access_token, get_current_user

# Создание таблиц в БД
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Вспомогательная функция для поиска пользователя (можно также импортировать из crud)
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

# Регистрация
@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

# Получение токена
@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# Создание события (привязывается к текущему пользователю)
@app.post("/events/", response_model=schemas.Event)
def create_event(
        event: schemas.EventCreate,
        db: Session = Depends(get_db),
        current_user_email: str = Depends(get_current_user)
):
    user = get_user_by_email(db, email=current_user_email)
    return crud.create_user_event(db=db, event=event, user_id=user.id)

# Чтение событий текущего пользователя
@app.get("/events/", response_model=List[schemas.Event])
def read_events(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user_email: str = Depends(get_current_user)
):
    user = get_user_by_email(db, email=current_user_email)
    return crud.get_events(db, user_id=user.id, skip=skip, limit=limit)

# Удаление события
@app.delete("/events/{event_id}")
def delete_event(
        event_id: int,
        db: Session = Depends(get_db),
        current_user_email: str = Depends(get_current_user)
):
    user = get_user_by_email(db, email=current_user_email)
    success = crud.delete_event(db=db, event_id=event_id, user_id=user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found or you don't have permission to delete it"
        )
    return {"detail": "Event deleted successfully"}

# Обновление события
@app.put("/events/{event_id}", response_model=schemas.Event)
def update_event(
        event_id: int,
        event_update: schemas.EventCreate,
        db: Session = Depends(get_db),
        current_user_email: str = Depends(get_current_user)
):
    user = get_user_by_email(db, email=current_user_email)
    updated_event = crud.update_event(db=db, event_id=event_id, user_id=user.id, event_update=event_update)
    if not updated_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found or permission denied"
        )
    return updated_event