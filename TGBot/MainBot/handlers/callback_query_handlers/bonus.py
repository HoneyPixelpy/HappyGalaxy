from aiogram import F, Router, types
from MainBot.base.models import Users
from MainBot.filters.chat_types import ChatTypeFilter
from MainBot.utils.Forms import (
    BonusBoosters,
)

bonus_router = Router(name=__name__)
bonus_router.message.filter(ChatTypeFilter(["private"]))


@bonus_router.callback_query(F.data.startswith("activate_bonus|"))
async def activate_bonus(call: types.CallbackQuery, user: Users):
    await BonusBoosters().get_bonus(call, user, call.data.split("|")[1])

