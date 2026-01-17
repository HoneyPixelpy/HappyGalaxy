from datetime import datetime
from typing import Optional, Union

from aiogram import types
from loguru import logger

from MainBot.utils.MyModule import Func
import texts


class ListLengthChangedError(Exception):
    """
    Длина списка с сообщениями изменилась
    """


class NoDesiredTypeError(Exception):
    """
    Тип контента не верный
    """


class InternalServerError(Exception):
    """
    Ошибка в тех случаях когда сервер не ответил нам
    """


class DuplicateOperationError(Exception):
    """
    Ошибка дублирования запроса
    """


class UndefinedError(Exception):
    """
    Неопределенная ошибка
    """
    def __init__(self, ex: Exception, text: str):
        self.text = text
        logger.exception(f"{ex.__class__.__name__} {ex}")
        super().__init__(text)

    async def send(
        self,
        message: Union[types.Message, types.CallbackQuery]
        ):
        await Func.send_error_to_developer("UndefinedError:\n" + self.text)
        await message.answer(
            texts.Error.Notif.undefined_error
            )


class ServerError(Exception):
    """
    Ошибка сервера
    """
    def __init__(self, ex: Exception, text: str):
        self.text = text
        logger.exception(f"{ex.__class__.__name__} {ex}")
        super().__init__(text)

    async def send(
        self,
        message: Union[types.Message, types.CallbackQuery]
        ):
        await Func.send_error_to_developer("ServerError:\n" + self.text)
        await message.answer(
            texts.Error.Notif.server_error
            )


class InternalServerErrorClass:
    async def send(self, message: Optional[str] = None):
        await Func.send_error_to_developer(message)
        raise InternalServerError(message)


class RelevanceError(Exception):
    """
    Работаем не с актальным сообщением
    """
    def __init__(self, new: datetime, old: datetime):
        self.message = f"Ожидалось изменение сообщения созданного в {new}, но сообщение было изменено уже в {old}"


