from typing import Optional
from MainBot.utils.MyModule import Func


class InternalServerError(Exception):
    """
    Ошибка в тех случаях когда сервер не ответил нам
    """
    pass


class ListLengthChangedError(Exception):
    """
    Длина списка с сообщениями изменилась
    """
    pass


class NoDesiredTypeError(Exception):
    """
    Тип контента не верный
    """
    pass


class InternalServerErrorClass:
    """
    Ошибка в тех случаях когда сервер не ответил нам
    """
    async def send(self, message: Optional[str] = None):
        await Func.send_error_to_developer(message)
        raise InternalServerError(message)




