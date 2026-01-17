"""Работаем с idempotency key"""

from enum import Enum
import json
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from loguru import logger
from rest_framework.response import Response

from bot.views.error import RaisesResponse
from Redis.main import RedisManager
from .exceptions import DuplicateOperationException


class StatusIdempotencyKey(str, Enum):
    """Статусы для процессов через idempotency key"""
    PROCESSING = "processing"
    COMPLETED  = "completed"
    FAIL       = "fail"


def json_serializable(obj: Any) -> str:
    """Сериализация UUID и datetime для JSON"""
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class CacheLock:
    """Базовый класс для работы с Redis Lock"""
    @staticmethod
    def lock(
        key: str
    ) -> Any:
        """
        Создаем запись для блокировки
        """
        return RedisManager().get_redis().set(
            f"lock:{key}",
            "1",
            nx=True, # NOTE создает только если ее нет
            ex=300
            )
    
    @staticmethod
    def unlock(
        key: str
    ) -> Any:
        """
        Удаляем запись для блокировки
        """
        return RedisManager().get_redis().delete(
            f"lock:{key}"
            )
    

class CacheIdempotencyKey:
    """Базовые методы для работы с кэшом"""
    @classmethod
    def get(
        cls,
        key: str
    ) -> Optional[Dict[str, Any] | Any]:
        """
        Получение idempotency key из Redis.
        """
        data = RedisManager().get_redis().get(f"idempotency:{key}")
        if data:
            return json.loads(data)
        return None

    @classmethod
    def set(
        cls,
        key: str,
        data: Dict[str, Any],
        ttl: int
    ) -> None:
        """
        Сохранение idempotency key в Redis.
        """
        RedisManager().get_redis().set(
            f"idempotency:{key}",
            json.dumps(data, default=json_serializable),
            ex=ttl
        )


class IdempotencyKey(CacheIdempotencyKey):
    """Расширенные методы для работы с idempotency key"""
    @classmethod
    def check(
        cls,
        idempotency_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Проверка idempotency key.
        """
        key_data = super().get(idempotency_key)

        if key_data:
            match key_data.get("status", ""):
                case "completed":
                    return key_data
                case "processing":
                    raise DuplicateOperationException("Operation in progress")
                case "fail":
                    return key_data
        return None

    @classmethod
    def processing(
        cls,
        idempotency_key: str,
        ttl: int,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Сохранение idempotency key как processing.
        """
        if not data:
            data = {}

        data["status"] = StatusIdempotencyKey.PROCESSING

        super().set(idempotency_key, data=data, ttl=ttl)

    @classmethod
    def complete(
        cls,
        idempotency_key: str,
        ttl: int,
        data: Dict[str, Any]
    ) -> None:
        """
        Изменение idempotency key как completed.
        """
        data["status"] = StatusIdempotencyKey.COMPLETED

        super().set(idempotency_key, data=data, ttl=ttl)

    @classmethod
    def fail(
        cls,
        idempotency_key: str,
        ttl: int,
        data: Dict[str, Any]
    ) -> None:
        """
        Изменение idempotency key как completed.
        """
        data["status"] = StatusIdempotencyKey.FAIL

        super().set(idempotency_key, data=data, ttl=ttl)


class Idempotency:
    @classmethod
    def start(
        cls,
        idempotency_key: str,
        ttl: int
    ) -> None:
        key_data = IdempotencyKey.check(idempotency_key)
        logger.debug(key_data)
        if key_data:
            raise RaisesResponse(
                data=key_data["data"],
                status=key_data["status_code"]
            )
        
        if CacheLock.lock(idempotency_key):
            try:
                IdempotencyKey.processing(
                    idempotency_key=idempotency_key,
                    ttl=ttl
                )
            finally:
                CacheLock.unlock(idempotency_key)
        
    @classmethod
    def end(
        cls,
        idempotency_key: str,
        ttl: int,
        status_code: int,
        data: str
    ) -> None:
        response_data = {
            'status_code': status_code,
            'data': data
        }
        if status_code < 400:
            """
            Помечаем запрос как успешный
            """
            IdempotencyKey.complete(
                idempotency_key=idempotency_key,
                data=response_data,
                ttl=ttl
            )
        else:
            """
            Помечаем как не успешен
            """
            IdempotencyKey.fail(
                idempotency_key=idempotency_key,
                data=response_data,
                ttl=ttl
            )
