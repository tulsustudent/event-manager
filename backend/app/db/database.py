from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv  # опционально, но рекомендуется

# Загружаем переменные окружения (если используешь .env)
load_dotenv()

# Лучше брать из переменной окружения, а не хардкодить
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:admin@localhost:5432/event_master"
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Создаём движок
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,                    # Поставь True при отладке
    pool_pre_ping=True,            # Проверка соединения
    pool_size=10,
    max_overflow=20
)

# Фабрика сессий
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Базовый класс
Base = declarative_base()