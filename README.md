# Менеджер событий

десктоп-приложение для управления событиями (ивентами) и пользователями. позволяет создавать события с заданным названием и описанием, одной из возможных категорий и временем начала (с точностью до минуты). пользователи могут записаться на созданное событие, и тогда в его карточке будет указано количество участников. удалить событие может только его создатель. доступно окно профиля пользователя, в котором видны события, созданные им, и все те, на которые он записан. в главном окне отображены все доступные события, а также есть поиск по названию и категории и сортировка (по названию или времени проведения). по умолчанию для события видны только название и категория, при нажатии на карточку она раскрывается и показывает описание, время проведения и кнопку для записи (или удаления).

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

#Альтернативный способ: создание файла через параметры команд в терминале
"DATABASE_URL=postgresql://user:password@localhost:5432/db_name" | Out-File -FilePath .env -Encoding utf8
"REDIS_URL=redis://localhost:6379/0" | Out-File -FilePath .env -Append -Encoding utf8
"SECRET_KEY=your_secret_key" | Out-File -FilePath .env -Append -Encoding utf8
"ACCESS_TOKEN_EXPIRE_MINUTES=30" | Out-File -FilePath .env -Append -Encoding utf8
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

# В другом окне терминала:
python client/app.py

# Обратите внимание: при регистрации пользователя минимальная длина пароля - 6 символов, логина - 3 символа
```
### 5. Тестирование
```bash
# Запуск тестов с генерацией отчета
coverage run -m unittest discover -s tests -p "test_*.py"
coverage report -m
```
### 6. Демонстрация работы программы
<img width="440" height="600" alt="image" src="https://github.com/user-attachments/assets/a42cc403-ec04-4c51-8d3f-c6563330c0d5" />

<img width="666" height="785" alt="image" src="https://github.com/user-attachments/assets/f5141bf0-d9a6-41b4-a931-eea4d9281ba9" />

<img width="439" height="706" alt="image" src="https://github.com/user-attachments/assets/48167850-191d-4106-8ec3-80d2d52a4b47" />


