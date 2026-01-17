import asyncio
import json
import re
import threading
from functools import wraps
from typing import Any, Callable

from loguru import logger
from rest_framework import status
from rest_framework.response import Response

from bot.service.exceptions import DuplicateOperationException
from bot.service.idempotency import Idempotency

from .error import RaisesResponse


class DatabaseQueue:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Классическая реализация синглтона"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # Двойная проверка для потокобезопасности
                    cls._instance = super().__new__(cls)
                    cls.queue = []
                    cls.condition = threading.Condition()
                    cls._worker_thread = None
                    cls._stop_event = threading.Event()
        return cls._instance

    def __del__(self):
        """Автоматическое завершение при удалении объекта"""
        self.stop()

    def start(self):
        """Запуск фонового worker"""
        with self._lock:
            if self._worker_thread is None:
                self._stop_event.clear()
                self._worker_thread = threading.Thread(
                    target=self._worker_loop, daemon=True, name="DatabaseQueueWorker"
                )
                self._worker_thread.start()
                logger.info("DatabaseQueue worker started")

    def _worker_loop(self):
        """Основной цикл обработки задач"""
        while not self._stop_event.is_set():
            with self.condition:
                if not self.queue:
                    self.condition.wait(timeout=0.1)
                    continue

                func, args, kwargs, future = self.queue.pop(0)

            try:
                result = func(*args, **kwargs)
                future.set_result(result)
            except Exception as e:
                logger.error(f"Database error: {e}", exc_info=True)
                future.set_exception(e)

    def stop(self) -> None:
        """Корректное завершение worker"""
        with self._lock:
            if self._worker_thread and self._worker_thread.is_alive():
                self._stop_event.set()
                with self.condition:
                    self.condition.notify_all()
                self._worker_thread.join(timeout=1.0)
                if self._worker_thread.is_alive():
                    logger.warning("Worker thread did not stop gracefully")
                self._worker_thread = None
                logger.info("DatabaseQueue worker stopped")

    def request(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Добавление задачи в очередь"""
        if self._worker_thread is None:
            self.start()

        future = Future()
        with self.condition:
            self.queue.append((func, args, kwargs, future))
            self.condition.notify()

        return future.result()


class Future:
    """Потокобезопасная Future с таймаутом"""

    def __init__(self, timeout: float = None):
        self._condition = threading.Condition()
        self._result = None
        self._exception = None
        self._done = False
        self._timeout = timeout

    def __del__(self):
        """Очистка ресурсов"""
        with self._condition:
            self._condition.notify_all()

    def set_result(self, result):
        with self._condition:
            self._result = result
            self._done = True
            self._condition.notify_all()

    def set_exception(self, exception):
        with self._condition:
            self._exception = exception
            self._done = True
            self._condition.notify_all()

    def result(self, timeout: float = None) -> Any:
        with self._condition:
            if not self._done:
                self._condition.wait(timeout or self._timeout)
                if not self._done:
                    raise TimeoutError("Future result timed out")

            if self._exception:
                raise self._exception
            return self._result


def queue_request(func):
    """
    Декоратор для последовательной обработки запросов к БД
    """
    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        """
        Декорируем обработчики запросов для
        отловли частых ошибок

        WARNING:
            Для SQLite дополнительно используем очередь
            для того чтобы с базов в одно время
            работал только один поток
        """
        try:
            # NOTE с переходом на PostgreSQL уберем на простое выполнение метода
            return func(self, request, *args, **kwargs)
            # return DatabaseQueue().request(func, *args, **kwargs)
        except DuplicateOperationException as e:
            logger.error(e)
            return Response(data=e.detail, status=status.HTTP_409_CONFLICT)
        except RaisesResponse as e:
            # NOTE почти всегда ответ возвращается через эту ошибку
            logger.error(e)
            return Response(data=e.data, status=e.status)
        except Exception as e:
            error = "\n{}: {}\n{}".format(str(func), e.__class__.__name__, str(e))
            logger.exception(error)
            return Response(
                {"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    return wrapper


def idempotency_request(func):
    """
    Декоратор для работы с idempotency_key
    """
    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        """
        Декорируем обработчики запросов для
        проверки и автовозврата ответов на запросы
        которые уже отработали или в работе

        WARNING:
            Для POST запросов
            которые могут продублироваться
            
            Для использования обязательно первым аргументом
            должен быть request
        """
        """
        Проверка перед обработкой
        """
        ttl = 300
        idempotency_key = (
            request.META.get('HTTP_IDEMPOTENCY_KEY') or 
            request.headers.get('IDEMPOTENCY-KEY', None)
        )
        logger.debug(idempotency_key)
        if not idempotency_key:
            return Response(
                {'error': 'Idempotency-Key header required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        idempotency_key = request.path.replace('/api/v1/', '') + idempotency_key
        logger.debug(idempotency_key)

        Idempotency.start(
            idempotency_key=idempotency_key,
            ttl=ttl
        )
                    
        try:
            """
            Выполняем обработку запроса
            """
            response: Response = func(self, request, *args, **kwargs)
            
            status_code = response.status_code
            data = response.data
            
            return response
        except RaisesResponse as e:
            status_code = e.status
            data = e.data
            raise
        except Exception as e:
            status_code = 400
            data = str(e)
            raise
        finally:
            """
            Сохраняем результат в Redis с TTL 24ч
            """
            """Отмечаем операцию как выполненную"""
            logger.debug(status_code)
            logger.debug(data)
            
            Idempotency.end(
                idempotency_key=idempotency_key,
                ttl=ttl,
                status_code=status_code,
                data=data
            )
    return wrapper


class QueryData:
    @classmethod
    def check_params(cls, request, key: str) -> Any:
        value = request.data.get(key, "no key")
        if value == "no key":
            value = request.query_params.get(key, "no key")
            if value == "no key":
                logger.warning(f"\n{key} parameter is required\n")
                raise RaisesResponse(
                    data={"error": f"{key} parameter is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return value


def check_sql_injection(value: str) -> bool:
    if not re.match(r"^[a-zA-Zа-яА-Я0-9_-]{3,50}$", value):
        raise RaisesResponse(
            data={
                "error": "undefined",  # NOTE для выдачи пользователю информации об неопределенной ошибке
                "message": "SQL Injection detected",
            },
            status=status.HTTP_200_OK,
        )
