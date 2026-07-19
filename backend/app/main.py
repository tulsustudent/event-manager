from fastapi import FastAPI, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import select, text
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta, timezone
from typing import Optional, Literal
import logging
import time

# Относительные импорты (все отталкиваются от текущей папки app)
from .db.database import get_db
from .db import models, schemas, crud
from .auth import get_current_user, get_current_user_optional, create_access_token
from .cache import cache_get, cache_set, get_version, bump_version, get_redis_client

# Пространства имён для инвалидации кэша (см. backend/app/cache.py)
EVENTS_CACHE_NS = "events"
STATS_CACHE_NS = "stats"

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

TAGS_METADATA = [
    {"name": "Auth", "description": "Регистрация и авторизация пользователей (JWT)."},
    {"name": "Events", "description": "CRUD события, поиск, участие, напоминания."},
    {"name": "Users", "description": "Профиль пользователя, статистика, его события."},
    {"name": "System", "description": "Служебные эндпоинты (health-check)."},
]

app = FastAPI(title="EventMaster API", openapi_tags=TAGS_METADATA)

# Схема БД создаётся отдельным скриптом backend/app/db/init_db.py — запусти его
# один раз перед первым стартом приложения. Раньше create_all вызывался прямо
# здесь при каждом импорте модуля, что било реальным подключением к Postgres
# и ломало импорт приложения (а значит и тесты) без поднятой БД.


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - Статус: {response.status_code} - Время: {process_time:.4f} сек")
    return response


@app.post("/register", tags=["Auth"], summary="Регистрация пользователя")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        logger.warning(f"Попытка регистрации существующего пользователя: {user.username}")
        raise HTTPException(status_code=400, detail="Username already registered")

    new_user = crud.create_user(db, user)
    logger.info(f"Пользователь зарегистрирован: {new_user.username}")
    return {"message": "User registered successfully"}


@app.post("/login", tags=["Auth"], summary="Авторизация")
def login(user_data: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user_data.username)
    if not db_user or not crud.verify_password(user_data.password, db_user.password_hash):
        logger.warning(f"Неудачная попытка входа: {user_data.username}")
        raise HTTPException(status_code=401, detail="Неверные данные")

    access_token = create_access_token(data={"sub": db_user.username})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": db_user.username,
        "user_id": db_user.id
    }


@app.post("/events/", tags=["Events"], summary="Создание события")
def create_event(
        event: schemas.EventCreate,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)
    if event.event_date < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Событие не может быть в прошлом")

    db_event = crud.create_user_event(db, event, user_id=current_user.id)
    bump_version(EVENTS_CACHE_NS)
    bump_version(STATS_CACHE_NS)
    logger.info(f"Ивент '{event.title}' создан пользователем {current_user.username}")
    return db_event


@app.patch("/events/{event_id}", tags=["Events"], summary="Обновление события")
def update_event(
        event_id: int,
        event_update: schemas.EventUpdate,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    db_event = crud.get_event_by_id(db, event_id)
    if not db_event or db_event.creator_id != current_user.id:
        logger.warning(f"Несанкционированное изменение ивента {event_id} от {current_user.username}")
        raise HTTPException(status_code=404, detail="Event not found or access denied")

    updated = crud.update_event(db, event_id, event_update)
    bump_version(EVENTS_CACHE_NS)
    logger.info(f"Ивент {event_id} обновлён пользователем {current_user.username}")
    return updated


@app.get("/events/search/", response_model=list[schemas.EventResponse], tags=["Events"], summary="Поиск событий")
def search_events(
    q: str = Query("", description="Поиск по названию"),
    category: str = Query("", description="Фильтр по категории"),
    sort_by: Literal["date", "name"] = Query("date", description="Сортировка: date или name"),
    current_user: Optional[models.User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    cache_key = (
        f"{EVENTS_CACHE_NS}:search:v{get_version(EVENTS_CACHE_NS)}:"
        f"{current_user.id if current_user else 'anon'}:{q}:{category}:{sort_by}"
    )
    cached = cache_get(cache_key)
    if cached is not None:
        logger.info("Поиск событий отдан из кэша")
        return cached

    query = select(models.Event).options(joinedload(models.Event.participants))
    query = query.where(
        (models.Event.is_private == False) |
        (models.Event.creator_id == (current_user.id if current_user else -1))
    )

    if q:
        query = query.where(models.Event.title.ilike(f"%{q}%"))
    if category:
        query = query.where(models.Event.category == category)

    if sort_by == "name":
        query = query.order_by(models.Event.title.asc())
    else:
        query = query.order_by(models.Event.event_date.asc())

    result = db.execute(query)
    logger.info(f"Поиск событий: запрос '{q}', категория '{category}', сортировка '{sort_by}'")
    events = result.unique().scalars().all()

    response_data = [
        schemas.EventResponse.model_validate(e).model_dump(mode="json") for e in events
    ]
    cache_set(cache_key, response_data)
    return response_data


@app.post("/events/{event_id}/join", tags=["Events"], summary="Присоединиться к событию")
def join_event(
    event_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    event = crud.get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    participation = crud.add_participant(db, event_id=event_id, user_id=current_user.id)
    bump_version(EVENTS_CACHE_NS)
    bump_version(STATS_CACHE_NS)
    logger.info(f"Пользователь {current_user.username} присоединился к ивенту {event_id}")
    return {"status": "success", "participation_id": participation.id}


@app.delete("/events/{event_id}", tags=["Events"], summary="Удалить событие")
def delete_event(
    event_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_event = crud.get_event_by_id(db, event_id)
    if not db_event or db_event.creator_id != current_user.id:
        logger.warning(f"Несанкционированное удаление ивента {event_id} от {current_user.username}")
        raise HTTPException(status_code=404, detail="Event not found or access denied")

    crud.delete_event(db, event_id)
    bump_version(EVENTS_CACHE_NS)
    bump_version(STATS_CACHE_NS)
    logger.info(f"Ивент {event_id} удален пользователем {current_user.username}")
    return {"status": "success"}


@app.get("/users/me/participating/", response_model=list[schemas.EventResponse], tags=["Users"], summary="События, в которых участвую")
def get_participating_events(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = select(models.Event).options(joinedload(models.Event.participants)).join(
        models.EventParticipant
    ).where(models.EventParticipant.user_id == current_user.id)

    result = db.execute(query)
    return result.unique().scalars().all()


@app.delete("/events/{event_id}/leave", tags=["Events"], summary="Покинуть событие")
def leave_event(
    event_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = crud.remove_participant(db, event_id=event_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Participation not found")

    bump_version(EVENTS_CACHE_NS)
    bump_version(STATS_CACHE_NS)
    logger.info(f"Пользователь {current_user.username} покинул ивент {event_id}")
    return {"status": "success"}


@app.get("/users/me/events/", tags=["Users"], summary="Мои события")
def get_my_events(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    created = db.query(models.Event).filter(models.Event.creator_id == current_user.id).all()
    participated_query = select(models.Event).options(joinedload(models.Event.participants)).join(
        models.EventParticipant
    ).where(models.EventParticipant.user_id == current_user.id)
    participated = db.execute(participated_query).unique().scalars().all()

    return {"created": created, "participated": participated}


@app.get("/users/{username}/stats/", tags=["Users"], summary="Статистика пользователя")
def get_user_stats(username: str, db: Session = Depends(get_db)):
    cache_key = f"{STATS_CACHE_NS}:v{get_version(STATS_CACHE_NS)}:{username}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    user = crud.get_user_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    data = {
        "id": user.id,
        "created_events": db.query(models.Event).filter(models.Event.creator_id == user.id).count(),
        "joined_events": db.query(models.EventParticipant).filter(
            models.EventParticipant.user_id == user.id
        ).count()
    }
    cache_set(cache_key, data)
    return data


@app.get("/events/reminders/", tags=["Events"], summary="Проверка напоминаний")
def check_reminders(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    query = select(models.Event).options(joinedload(models.Event.participants)).join(
        models.EventParticipant
    ).where(
        models.EventParticipant.user_id == current_user.id,
        models.Event.event_date >= now,
        models.Event.event_date <= now + timedelta(hours=1)
    )

    result = db.execute(query)
    return result.unique().scalars().all()


@app.get("/health", tags=["System"], summary="Проверка работоспособности сервиса")
def health_check(db: Session = Depends(get_db)):
    """
    Не требует авторизации. Проверяет БД и Redis независимо друг от друга —
    Redis недоступен => кэш просто не работает (см. cache.py), это НЕ должно
    считаться падением сервиса, поэтому статус БД и Redis не смешиваются
    в единый bool, а отдаются отдельно.
    """
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"

    try:
        get_redis_client().ping()
        redis_status = "ok"
    except Exception as e:
        redis_status = f"unavailable: {e}"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "redis": redis_status,
    }