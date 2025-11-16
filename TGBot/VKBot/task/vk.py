import asyncio
from typing import List
from datetime import datetime, timedelta
import aiohttp

from loguru import logger

from ..api import VKGroup
from MainBot.base.models import Users
from MainBot.utils.MyModule import Func
from MainBot.base.orm_requests import QuestsMethods, UseQuestsMethods, UserMethods



class VkSubscriptionChecker:
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
            target_time = now.replace(hour=2, minute=0, second=0, microsecond=0)

            # Если текущее время уже после 3:00, планируем на завтра
            if now > target_time:
                target_time += timedelta(days=1)

            # Сколько осталось до следующей проверки?
            sleep_seconds = (target_time - now).total_seconds()
            
            logger.info(f"Следующая проверка полписки ВК чатов в {target_time} (через {sleep_seconds / 3600:.1f} часов)")
            await asyncio.sleep(sleep_seconds)  # Спим до 3:00 ночи

            # Запускаем проверку
            await self._check_all_subscribers()

    async def _check_all_subscribers(self):
        """Получает и проверяет всех подписчиков"""
        try:
            """ TODO
            когда научимся добавлять интерактивно, нужно сделать так чтобы мы сначала получали
            все квесты для vk и с каждым квестом проводили эту работу
            """
            quests = [quest for quest in await QuestsMethods().get_quests() if quest.quest_data.type == "vk"]
            for quest in quests:
                members: set[int] = await VKGroup.get_group_members(
                    quest.quest_data.chat_id_name, 
                    quest.quest_data.group_token
                    )
                vk_users: List[Users] = await UseQuestsMethods().get_all_users_sub_vk_chat(quest.id)
                
                for vk_user in vk_users:
                    if vk_user.vk_id not in members:
                        await self._handle_unsubscribed(vk_user, quest.quest_data.chat_id_name)
                    
                    await asyncio.sleep(self._request_delay)
                
        except Exception as e:
            logger.error(f"Ошибка при проверке подписчиков: {e}")
            await Func.send_error_to_developer(
                f"Ошибка при проверке подписчиков: {e.__class__.__name__} - {e}"
            )

    async def _handle_unsubscribed(self, user: Users, chat_id_name: str):
        """Обрабатывает отписавшихся пользователей"""
        logger.info(f"Пользователь {user.user_id} @{str(user.tg_username)} отписался")
        await UserMethods().back_vk_id(user, chat_id_name)
        await Func.send_error_to_developer(
            f"Пользователь {user.user_id} @{str(user.tg_username)} отписался от ВК группы {chat_id_name}"
        )
