__all__ = [
    "inline",
    "reply",
    "selector"
]

from typing import Union

from aiogram import types
from loguru import logger

from MainBot.base.models import Users
from .inline import IKB
from .reply import KB


class KeyBoardType:
    """
    Через этот класс будем определять тип клавы
    выбранный пользователем
    
    Думаю через отдельную таблицу в бд
    где просто для каждого пользователя в виде
    строки "reply" или "inline" хранится выбор
    """
    
    async def get_kb_type(cls, *args, **kwargs) -> str:
        return "inline"

class inline(IKB):
    def __init__(self):
        super().__init__()

class reply(KB):
    def __init__(self):
        super().__init__()

class selector:
    """
    Класс который будет возвращать клаву в зависимости
    от выбора пользователя
    """
    @classmethod
    async def main_menu(
        cls, user: Users, *args, **kwargs
    ) -> Union[
        types.InlineKeyboardMarkup,
        types.ReplyKeyboardMarkup
    ]:
        kb_type = await KeyBoardType.get_kb_type(user)
        logger.debug(kb_type)
        match kb_type:
            case "reply":
                return await reply.main_menu(user, *args, **kwargs)
            case "inline":
                # NOTE Удаляем встроенную клаву
                return await inline.main_menu(user, *args, **kwargs)
        
    
    
