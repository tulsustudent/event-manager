@echo off
chcp 65001 >nul
cd /d "%~dp0"
setlocal

:: 1. Создание .env
if not exist ".env" (
    if exist ".env.example" (
        echo [ИНФО] Создаю .env из примера...
        copy .env.example .env >nul
    )
)

:: 2. ЗАПУСК DOCKER
echo [ИНФО] Запуск Docker контейнеров...
docker compose up -d
if %errorlevel% neq 0 (
    echo [ОШИБКА] Docker не запущен! Проверь Docker Desktop. & pause & exit /b 1
)

:: 3. Ожидание готовности БД
echo [ИНФО] Ожидание готовности базы данных...
:wait_db
docker inspect -f "{{.State.Health.Status}}" eventmaster-postgres | find "healthy" >nul
if %errorlevel% neq 0 (
    timeout /t 2 >nul
    goto wait_db
)

:: 4. Установка зависимостей
if not exist "venv" (
    echo [ИНФО] Создаю venv...
    py -m venv venv
)
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install -r requirements.txt >nul

:: 5. Инициализация базы
echo [ИНФО] Инициализация базы данных...
venv\Scripts\python.exe -c "from backend.app.db.init_db import init_db; init_db()"

:: 6. Запуск бэкенда
echo [ИНФО] Запуск бэкенда...
start "EventMaster Backend" cmd /k "venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload"

:: 7. Запуск клиента
echo [ИНФО] Запуск клиента...
if exist "client\app.py" (
    venv\Scripts\python.exe client\app.py
) else (
    echo [ВНИМАНИЕ] Файл клиента не найден, приложение не запустится! & pause
)

endlocal