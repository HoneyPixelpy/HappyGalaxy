import asyncio
from datetime import timedelta, datetime
from typing import Dict
import uuid

from loguru import logger
import pytz

from MainBot.base.models import Users, Lumberjack_Game
from MainBot.base.forms import Lumberjack_GameForms
from MainBot.base.orm_requests import Lumberjack_GameMethods, Sigma_BoostsMethods
import texts
from MainBot.utils.MyModule import Func
from MainBot.utils import _active_tasks


class EnergyUpdateManager:
    _instance = None
    _lock = asyncio.Lock()  # Для потокобезопасности

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def check_pending_energy_updates(
        self
        ) -> None:
        """
        Запускается при старте приложения для проверки незавершённых обновлений
        """
        try:
            active_games: list[Lumberjack_Game] = await Lumberjack_GameMethods().get_active_games()
            # TODO можно получить сразу все данные о бустах к этим играм
        
            for game in active_games:
                if game.current_energy >= game.max_energy:
                    continue

                time_passed = datetime.now(pytz.timezone('Europe/Moscow')) - game.last_energy_update
                required_delay: timedelta = await Sigma_BoostsMethods().calculate_recovery_time(
                    user=game.user
                    )
                
                if time_passed >= required_delay:
                    # Немедленное обновление
                    await Lumberjack_GameForms().update_energy(game)
                else:
                    # Запуск отложенного обновления
                    remaining_time = (required_delay - time_passed).total_seconds()
                    await self.schedule_energy_update(
                        user=game.user,
                        game_user=game,
                        delay_minutes=remaining_time / 60
                    )
            else:
                await Func.send_error_to_developer(
                    "Задачи для восстановления энергии запустились!!!"
                )
        except:
            await Func.send_error_to_developer(
                "Задачи для восстановления энергии не запустились"
            )
            return

    async def schedule_energy_update(
        self,
        user: Users,
        game_user: Lumberjack_Game = None,
        delay_minutes: int = None
        ) -> None:
        """
        Запуск задачи для обновления энергии.
        """
        user_id = user.user_id

        async with self._lock:
            if user_id in _active_tasks:
                return  # Задача уже запущена
            
            if not game_user:
                game_user: Lumberjack_Game = await Lumberjack_GameMethods().get_by_user(
                    user=user
                    )
            
            if game_user.current_energy >= game_user.max_energy:
                return
            
            if delay_minutes is None:
                delay_minutes: timedelta = await Sigma_BoostsMethods().calculate_recovery_time(
                    user=user
                    )
                delay_minutes = delay_minutes.total_seconds() / 60

            key = str(uuid.uuid4())

            task = asyncio.create_task(
                self.wait_and_update_energy(user, key, delay_minutes)
            )
            _active_tasks[user_id] = {
                "key": key,
                "task": task
                }

    async def wait_and_update_energy(
        self,
        user: Users,
        key: str,
        delay_minutes: float
        ) -> None:
        """
        Обновляем энергию через заданное время.
        
        Args:
            - user: Users > от сюда используем только user_id;
            
        TODO если таска была удалена и после этого создалась новая для этого юзера, наша проверка не защищает, нужен дополнительно уникальный ключ помимо user_id
        """
        try:
            await asyncio.sleep(delay_minutes * 60)  # Ожидание в секундах
            
            async with self._lock:
                if user.user_id not in _active_tasks:
                    return # Задача уже выполнена (хотя такого не может быть)
                else:
                    if _active_tasks[user.user_id]["key"] != key:
                        return # Задача была запущена в другом потоке

            game_user: Lumberjack_Game = await Lumberjack_GameMethods().get_by_user(
                user=user
                )

            if game_user.current_energy >= game_user.max_energy:
                async with self._lock:
                    _active_tasks.pop(user.user_id, None)
                return
            
            await Lumberjack_GameForms().update_energy(game_user)

            await self._notify_user(user)

            # Удаляем задачу из списка активных
            async with self._lock:
                _active_tasks.pop(user.user_id, None)
            
        except asyncio.CancelledError:
            logger.debug("Задача была отменена через force_update_energy")
        except Exception as e:
            logger.error(f"Ошибка в wait_and_update_energy: {e}")
            raise

    async def force_update_energy(
        self, 
        user: Users,
        game_user: Lumberjack_Game = None,
        refrash: bool = True
        ) -> None:
        """
        Принудительно обновляет энергию и отменяет запланированную задачу.
        """
        user_id = user.user_id

        async with self._lock:
            # Отменяем текущую задачу, если она есть
            if _active_tasks.get(user_id):
                task_data = _active_tasks.pop(user_id)
                task_data["task"].cancel()  # Важно: отменяем задачу
                try:
                    await task_data["task"]  # Ожидаем завершения (обрабатываем CancelledError)
                except asyncio.CancelledError:
                    pass
            
            if refrash:
                if not game_user:
                    game_user = await Lumberjack_GameMethods().get_by_user(user=user)
                
                # Обновляем энергию
                if game_user.current_energy < game_user.max_energy:
                    await Lumberjack_GameForms().update_energy(game_user)

    async def _notify_user(
        self, 
        user: Users
        ) -> None:
        """
        Уведомляет пользователя о восстановленной энергии.
        """
        try:
            from MainBot.config import bot
            await bot.send_message(
                chat_id=user.user_id,
                text=texts.Game.Texts.notif
            )
        except Exception as e:
            logger.exception(f"Ошибка при отправке уведомления: {e}")

