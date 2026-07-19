from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    # События, созданные пользователем
    events = relationship(
        "Event",
        back_populates="creator",
        cascade="all, delete-orphan",
        lazy="selectin"  # Улучшает загрузку
    )

    # Участие пользователя в событиях
    participations = relationship(
        "EventParticipant",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(String, nullable=False)
    is_private = Column(Boolean, default=False, nullable=False)

    # Новые поля
    event_date = Column(DateTime, nullable=False)  # Обязательное поле
    category = Column(String, index=True, nullable=False)  # Категория обязательна

    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Связи
    participants = relationship(
        "EventParticipant",
        back_populates="event",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    creator = relationship("User", back_populates="events")


class EventParticipant(Base):
    __tablename__ = "event_participants"

    id = Column(Integer, primary_key=True, index=True)

    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    username = Column(String, index=True, nullable=False)  # для удобства отображения

    # Связи
    event = relationship("Event", back_populates="participants")
    user = relationship("User", back_populates="participations")


# Индексы для производительности
from sqlalchemy import Index

Index('ix_event_date', Event.event_date)
Index('ix_event_category', Event.category)
Index('ix_participant_event_user', EventParticipant.event_id, EventParticipant.user_id, unique=True)