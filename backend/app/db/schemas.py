from pydantic import BaseModel
from datetime import datetime
from typing import Optional

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