from aiogram import types

from MainBot.utils.MyModule.message import MessageManager
from MainBot.keyboards import selector
from MainBot.base.models import Users


class Menu:

    async def main_menu(
        self,
        message: types.Message | types.CallbackQuery,
        user: Users
    ) -> None:
        """
        Отправляем сообщение с информацией о пользователе
        """
        await MessageManager(
            message,
            user.user_id
        ).send_or_edit(
            None,
            await selector.main_menu(user),
            "menu"
        )
