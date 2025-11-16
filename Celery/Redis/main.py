import os
from loguru import logger

from redis import Redis
import redis as redis


REDIS_URL = os.getenv("REDIS_URL")

class RedisManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Явно указываем параметры для избежания проблем
            cls._instance.redis = redis.from_url(
                REDIS_URL,
                decode_responses=False,  # для автоматического декодирования из bytes в str
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                max_connections=10
            )
        return cls._instance

    def get_redis(self) -> redis.Redis:
        try:
            # Проверяем подключение
            self._instance.redis.ping()
            return self._instance.redis
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error: {e}")
            raise
        except Exception as e:
            logger.error(f"Redis error: {e}")
            raise

    def close(self):
        if self._instance and self._instance.redis:
            self._instance.redis.close()