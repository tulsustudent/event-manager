from .database import engine, Base
# Импортируем ВСЕ модели, чтобы они зарегистрировались
from .models import User, Event, EventParticipant


def init_db(drop_all: bool = False):
    """
    Инициализация базы данных.
    drop_all=True — опасно, только для разработки!
    """
    if drop_all:
        print("⚠️ Удаление всех таблиц...")
        Base.metadata.drop_all(bind=engine)
        print("✅ Таблицы удалены.")

    print("🛠 Создание таблиц...")
    Base.metadata.create_all(bind=engine)
    print("✅ База данных успешно инициализирована!")


if __name__ == "__main__":
    # Для удобства — спрашиваем подтверждение
    answer = input("Удалить все данные перед созданием таблиц? (y/N): ")
    drop = answer.lower() == 'y'
    init_db(drop_all=drop)