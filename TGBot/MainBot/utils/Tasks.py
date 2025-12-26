import asyncio
import datetime
import sys
import typing

import pytz
from loguru import logger
from MainBot.utils.Base import CopyBase

#############################################################################################
# LEGACY
#############################################################################################


class WaitingTask:

    @classmethod
    async def pre_task_waiting(
        cls, now: datetime.datetime, target_time: datetime.datetime
    ) -> None:
        wait_time: int = (target_time - now).total_seconds()
        if wait_time > 0:
            logger.debug(
                f"Waiting for {wait_time} seconds until {target_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"
            )
            await asyncio.sleep(wait_time)
            logger.debug("Подождали!")
            return True
        else:
            logger.error(
                "Заданное время находится в прошлом. Пожалуйста, установите будущее время."
            )
            return False

    @classmethod
    async def get_now_and_target_time_in_time_zone(
        cls,
        *,
        hour: int = 0,
        minute: int = 0,
        second: int = 0,
        target_tz: str = "Europe/Moscow",
    ) -> typing.Union[datetime.datetime, datetime.datetime]:
        # Определяем часовой пояс
        tz = pytz.timezone(target_tz)
        # Определяем текущее время и целевое время (2:00 по Москве)
        now = datetime.datetime.now(tz)
        target_time = now.replace(
            hour=hour, minute=minute, second=second, microsecond=0
        )
        return now, target_time


class Tasks:

    async def create_task_from_database_copy(self):
        while True:
            now, target_time = await WaitingTask.get_now_and_target_time_in_time_zone(
                hour=2
            )

            # Если текущее время после 3:00, установите цель на следующий день
            if "--copy_bd" in sys.argv:
                target_time = now + datetime.timedelta(seconds=5)
            else:
                if now >= target_time:
                    target_time += datetime.timedelta(days=1)

            # Ожидаем до целевого времени
            if await WaitingTask.pre_task_waiting(now, target_time):

                # Создаем задачу для отправки копии базы данных
                await CopyBase.copy_bd(target_time)

                await asyncio.sleep(1000)
            else:
                logger.error("Ошибка в ожидании!")
                break


#############################################################################################
# LEGACY
#############################################################################################
