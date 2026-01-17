from aiogram import F, Router, types
from loguru import logger
from MainBot.base.models import Users
from MainBot.filters.chat_types import ChatTypeFilter
from MainBot.utils.Forms import (
    RatingForms
)

rating_router = Router(name=__name__)
rating_router.message.filter(ChatTypeFilter(["private"]))


@rating_router.callback_query(F.data.startswith("rating_menu|"))
async def rating_menu(call: types.CallbackQuery, user: Users):
    chapter = call.data.split("|")[1]
    logger.debug(chapter)
    await RatingForms().section(user, call, chapter)


