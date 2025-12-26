from aiogram import types
from aiogram.filters import Filter
from aiogram.fsm.context import FSMContext
from config import admins
from MainBot.base.models import Users


class ChatTypeFilter(Filter):
    def __init__(self, chat_types: list[str]) -> None:
        self.chat_types = chat_types

    async def __call__(self, message: types.Message) -> bool:
        return message.chat.type in self.chat_types


class IsAdmin(Filter):

    async def __call__(self, message: types.Message, state: FSMContext) -> bool:
        data = await state.get_data()
        user: Users = data.get("user")
        if user and (
            user.user_id in admins or user.role_private in ["admin", "manager", "owner"]
        ):
            return True
        else:
            return False
