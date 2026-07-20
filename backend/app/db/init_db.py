from backend.app.db.database import Base, SQLALCHEMY_DATABASE_URL
# Импортируем из того же файла db/models.py
from backend.app.db.models import User, Event, EventParticipant
from sqlalchemy import create_engine

def init_db(drop_all: bool = False):
    # Создаем синхронную версию строки подключения (заменяем асинхронный драйвер на psycopg2)
    sync_url = SQLALCHEMY_DATABASE_URL.replace("+asyncpg", "+psycopg2")

    # Создаем временный СИНХРОННЫЙ движок
    sync_engine = create_engine(sync_url)

    print("🛠 Создание таблиц (синхронный режим)...")
    if drop_all:
        Base.metadata.drop_all(bind=sync_engine)

    Base.metadata.create_all(bind=sync_engine)
    print("✅ База данных успешно инициализирована!")


if __name__ == "__main__":
    # Для удобства — спрашиваем подтверждение
    answer = input("Удалить все данные перед созданием таблиц? (y/N): ")
    drop = answer.lower() == 'y'
    init_db(drop_all=drop)