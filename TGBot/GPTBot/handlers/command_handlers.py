from aiogram import types, Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from loguru import logger

from GPTBot.keyboards.inline import main_menu
from MainBot.filters.chat_types import ChatTypeFilter


command_router = Router(name=__name__)
command_router.message.filter(ChatTypeFilter(["private"]))

@command_router.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext):
    # reset_limits(message.from_user.id)
    await state.clear()
    await message.answer(
        "<b>💡 Выберите тип генерации:</b>",
        reply_markup=main_menu()
    )
