import os
import logging
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# Импортируем явно через пакет
from backend.app.db.database import get_db
from backend.app.db import crud, models

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = "dev-only-insecure-secret-key"
    logger.warning(
        "SECRET_KEY не задан в окружении! Используется небезопасный дефолт — "
        "только для локальной разработки. Установи переменную окружения SECRET_KEY перед деплоем/сдачей."
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# auto_error=False — чтобы можно было построить опциональную авторизацию поверх той же схемы
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def _decode_user(token: str, db: Session) -> Optional[models.User]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

    username: str = payload.get("sub")
    if username is None:
        return None

    return crud.get_user_by_username(db, username=username)


def get_current_user(
        token: Optional[str] = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
):
    if not token:
        raise HTTPException(status_code=401, detail="Не авторизован")

    user = _decode_user(token, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    return user


def get_current_user_optional(
        token: Optional[str] = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
) -> Optional[models.User]:
    """Как get_current_user, но не требует токен — вернёт None, если его нет или он невалиден.
    Используется там, где эндпоинт доступен и анонимно (например, поиск событий)."""
    if not token:
        return None
    return _decode_user(token, db)