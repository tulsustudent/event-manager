from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


# ====================== USER SCHEMAS ======================
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    """Отдельная схема для логина — здесь мы не проверяем стойкость пароля,
    а только то, что оба поля переданы. Проверка длины пароля уместна при
    регистрации (политика для новых паролей), но не при входе — иначе
    пользователь с уже существующим (гипотетически более старым, коротким)
    паролем не смог бы залогиниться вовсе."""
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


# ====================== PARTICIPANT SCHEMAS ======================
class EventParticipantResponse(BaseModel):
    id: int
    event_id: int
    user_id: int
    username: Optional[str] = None

    class Config:
        from_attributes = True


# ====================== EVENT SCHEMAS ======================
class EventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., max_length=1000)
    is_private: bool = False
    category: str = Field(..., min_length=1, max_length=100)
    event_date: datetime = Field(...)  # Обязательная дата в будущем


class EventResponse(BaseModel):
    id: int
    title: str
    description: str
    is_private: bool
    creator_id: int
    event_date: datetime
    category: Optional[str] = None

    # Участники
    participants: List[EventParticipantResponse] = []

    class Config:
        from_attributes = True


class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    is_private: Optional[bool] = None
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    event_date: Optional[datetime] = None


# Для статистики и других ответов
class EventSimpleResponse(BaseModel):
    id: int
    title: str
    event_date: datetime
    category: Optional[str] = None

    class Config:
        from_attributes = True