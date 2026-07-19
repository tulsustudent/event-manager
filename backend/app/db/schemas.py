from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr

class EventBase(BaseModel):
    title: str
    description: str
    category: str
    is_private: bool = False
    event_date: datetime

class EventCreate(EventBase):
    pass

class Event(EventBase):
    id: int
    creator_id: int

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    events: List[Event] = []

    class Config:
        from_attributes = True