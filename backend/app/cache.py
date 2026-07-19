"""
Тонкий слой кэширования поверх Redis.

Дизайн-решение: кэш никогда не должен ронять приложение. Если Redis недоступен
(не поднят, сеть отвалилась, таймаут) — все функции здесь молча "промахиваются"
(fail-open) и приложение просто работает напрямую с БД, как будто кэша нет.
Это сознательный компромисс: для учебного/пет-проекта важнее, чтобы API не падало
при недоступном Redis, чем чтобы кэш был гарантированно "жёстким".

Инвалидация сделана через версионирование пространств имён (namespace version),
а не через SCAN + DEL по маске: увеличили версию — все старые ключи с этой
версией в написании просто больше не запрашиваются и сами протухнут по TTL.
Это дешевле и безопаснее, чем SCAN по продакшен Redis.
"""
import json
import logging
import os
from typing import Any, Optional

import redis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "60"))

_redis_client: Optional["redis.Redis"] = None


def get_redis_client() -> "redis.Redis":
    """Ленивая инициализация клиента (создаётся один раз на процесс)."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis.from_url(
            REDIS_URL,
            socket_connect_timeout=1,
            socket_timeout=1,
            decode_responses=True,
        )
    return _redis_client


def reset_client() -> None:
    """Сбросить закэшированный клиент. Нужно только в тестах, чтобы подменять
    get_redis_client на fakeredis между тестами."""
    global _redis_client
    _redis_client = None


def cache_get(key: str) -> Optional[Any]:
    try:
        raw = get_redis_client().get(key)
    except Exception as e:  # redis.RedisError, ConnectionError, TimeoutError и т.п.
        logger.warning(f"Redis недоступен, кэш пропущен (get '{key}'): {e}")
        return None
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return None


def cache_set(key: str, value: Any, ttl: int = CACHE_TTL_SECONDS) -> None:
    try:
        get_redis_client().setex(key, ttl, json.dumps(value, default=str))
    except Exception as e:
        logger.warning(f"Redis недоступен, значение не закэшировано ('{key}'): {e}")


def get_version(namespace: str) -> int:
    try:
        v = get_redis_client().get(f"cache_version:{namespace}")
    except Exception as e:
        logger.warning(f"Redis недоступен, версия кэша '{namespace}' = 0: {e}")
        return 0
    return int(v) if v is not None else 0


def bump_version(namespace: str) -> None:
    """Инвалидировать всё пространство имён разом (например, все результаты
    поиска событий) — вызывается при любой мутации, влияющей на эти данные."""
    try:
        get_redis_client().incr(f"cache_version:{namespace}")
    except Exception as e:
        logger.warning(f"Redis недоступен, версия кэша '{namespace}' не увеличена: {e}")
