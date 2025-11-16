import asyncio
from vkbottle import API
from loguru import logger
import asyncio
from typing import Optional


max_retries = 3

class VKGroup:
    """Класс для работы с группой VK
    
    Нужен токен группы Дополнительно - работа с апи - ключ доступа
    Название или id канала
    """
    @classmethod
    async def get_group_members(
        cls,
        group_id: int,
        group_token: str
        ) -> list[int]:
        """Получает список подписчиков группы"""
        for attempt in range(max_retries):
            try:
                members = await API(token=group_token).groups.get_members(
                    group_id=str(group_id)
                )
                logger.debug(members.items)
                return set(members.items)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
        
        return []

    @classmethod
    async def check_subscription(
        cls,
        user_id: int,
        group_id: int,
        group_token: str
        ) -> bool:
        try:
            # Проверка подписки через API
            result = await API(token=group_token).groups.is_member(
                group_id=str(group_id),
                user_id=user_id
            )
            logger.debug(result)
            return True if result else False
        except Exception as e:
            logger.exception(str(e))
            return False

    @classmethod
    async def get_user_id(
        cls,
        username: str,
        group_token: str
        ) -> Optional[int]:
        users = await API(token=group_token).users.get(user_ids=username)
        # logger.debug(users)
        return users[0].id if users else None
    
    @classmethod
    async def strip_url(
        cls,
        user_link: str
        ) -> str:
        if "http" in user_link or "vk.com" in user_link:
            return user_link.split("/")[-1]
        elif "vk:" in user_link:
            return user_link.replace("vk:")
        elif "@" in user_link:
            return user_link.split("@")[-1]
        else:
            logger.warning(user_link)
            return user_link

    @classmethod
    async def check_invite(
        cls, 
        vk_id: int,
        group_id: int,
        group_token: str
        ) -> bool:
        return False if not await cls.check_subscription(vk_id, group_id, group_token) else True
        



