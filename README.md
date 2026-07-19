# Менеджер событий

десктоп-приложение для управления событиями и пользователями

## Особенности архитектуры
* **Использование Redis для кэширования**
* **Мониторинг и логирование**
* **Клиентская часть через фреймворки FastAPI, Flet**
* **Документация Swagger**
* **Покрытие юнит-тестами более 90%**
* **Аутентификация на основе JWT**

## Сферы использования
* База для систем записи на мероприятия или управления событиями.
* Образец production-ready архитектуры на FastAPI.
* После доработки может использоваться как расписание для учебных заведений или транспортных компаний или календарь с записью событий

## Инструкция по развертыванию

### 1. Подготовка
```bash
python -m venv venv
source venv/bin/activate  # Для Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

### 2. Конфигурация
Создайте файл `.env` на основе `.env.example`:
```ini
DATABASE_URL=postgresql://user:password@localhost:5432/db_name
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. Запуск кэширования
Для работы кэша требуется Redis:
```bash
docker run --name my-redis -p 6379:6379 -d redis
```
### 4. Запуск
```bash
# Инициализация базы данных
python -m backend.app.db.init_db

# Запуск API
uvicorn backend.app.main:app --reload
```
### 5. Тестирование
```bash
# Запуск тестов с генерацией отчета
coverage run -m unittest discover -s tests -p "test_*.py"
coverage report -m
```
