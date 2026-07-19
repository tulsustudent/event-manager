from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Table # Добавили Table
from sqlalchemy.orm import relationship
from backend.app.db.database import Base

# Таблица для связи "участники - события"
event_participants = Table(
    "event_participants",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("event_id", ForeignKey("events.id"), primary_key=True),
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    events = relationship("Event", back_populates="owner")
    # Добавляем связь для участия
    participated_events = relationship(
        "Event", secondary=event_participants, back_populates="participants"
    )

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    category = Column(String)
    is_private = Column(Boolean, default=False)
    event_date = Column(DateTime)
    creator_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="events")
    # Добавляем связь для участников
    participants = relationship(
        "User", secondary=event_participants, back_populates="participated_events"
    )