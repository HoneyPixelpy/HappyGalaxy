from aiogram import F, Router, types
from GPTBot.keyboards.inline import main_menu
from loguru import logger
from MainBot.filters.chat_types import ChatTypeFilter

texts_router = Router(name=__name__)
texts_router.message.filter(ChatTypeFilter(["private"]))


@texts_router.message()
async def fallback(message: types.Message):
    await message.reply(
        "<b>Пожалуйста, используйте меню для выбора типа генерации.</b>",
        reply_markup=main_menu(),
    )
