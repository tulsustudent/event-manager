from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from backend.app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    events = relationship("Event", back_populates="owner")


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