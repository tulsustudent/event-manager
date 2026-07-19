from sqlalchemy import Column, Integer, String, Boolean, DateTime
from backend.app.db.database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    category = Column(String, index=True)
    is_private = Column(Boolean, default=False)
    event_date = Column(DateTime)
    creator_id = Column(Integer)  # Пока заглушка: просто ID создателя