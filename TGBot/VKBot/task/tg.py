import asyncio
from datetime import datetime, timedelta

import aiohttp
from loguru import logger
from MainBot.base.models import Quests, Users
from MainBot.base.orm_requests import QuestsMethods, UseQuestsMethods, UserMethods
from MainBot.config import bot
from MainBot.utils.MyModule import Func


class TelegramSubscriptionChecker:
    def __init__(self):
        self._task = None
        self._running = False
        self._session = None
        self._request_delay = 1
        self._max_retries = 3

    async def start(self):
        """Запускает фоновую задачу"""
        if self._running:
            return

        self._running = True
        self._session = aiohttp.ClientSession()
        self._task = asyncio.create_task(self._run_daily_check())

    async def stop(self):
        """Останавливает фоновую задачу"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._session:
            await self._session.close()

    async def _run_daily_check(self):
        """Основной цикл проверки"""
        while self._running:
            now = datetime.now()
            target_time = now.replace(hour=2, minute=30, second=0, microsecond=0)

            # Если текущее время уже после 3:00, планируем на завтра
            if now > target_time:
                target_time += timedelta(days=1)

            # Сколько осталось до следующей проверки?
            sleep_seconds = (target_time - now).total_seconds()

            logger.info(
                f"Следующая проверка полписки телеграмм чатов в {target_time} (через {sleep_seconds / 3600:.1f} часов)"
            )
            await asyncio.sleep(sleep_seconds)  # Спим до 3:00 ночи

            # Запускаем проверку
            await self._check_all_subscribers()

    async def _check_all_subscribers(self):
        """Получает и проверяет всех подписчиков"""
        try:
            quests = [
                quest
                for quest in await QuestsMethods().get_quests()
                if quest.quest_data.type == "tg"
            ]

            for quest in quests:
                users = await UseQuestsMethods().get_all_users_sub_tg_chat(quest.id)

                for user in users:
                    if not await self.get_chat_member(
                        quest.quest_data.chat_id_name, user.user_id
                    ):
                        await self._handle_unsubscribed(user, quest)

                    await asyncio.sleep(self._request_delay)

        except Exception as e:
            logger.exception(f"Ошибка при проверке подписчиков Telegram: {e}")

    async def get_chat_member(self, chat_name: str, user_id: int) -> bool:
        try:
            chat_member = await bot.get_chat_member(chat_name, user_id)
            logger.debug(chat_member)
            if chat_member.status in ("left", "kicked", "restricted"):
                return False
            else:
                return True
        except:
            logger.exception(
                "chat_member = await bot.get_chat_member(chat_name, user_id)"
            )
            return False

    async def _handle_unsubscribed(self, user: Users, quest: Quests):
        """Обрабатывает отписавшихся пользователей"""
        logger.info(
            f"Пользователь Telegram {user.user_id} @{str(user.tg_username)} отписался"
        )
        await UseQuestsMethods().back_tg_quest(user, quest)
        await Func.send_error_to_developer(
            f"Пользователь Telegram {user.user_id} @{str(user.tg_username)} отписался от телеграмма {quest.quest_data.chat_id_name}"
        )
