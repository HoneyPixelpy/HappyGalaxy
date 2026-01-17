from aiogram import F, Router, types
from MainBot.base.models import Users
from MainBot.filters.chat_types import ChatTypeFilter
from MainBot.utils.Forms.Season import Season

rangs_router = Router(name=__name__)
rangs_router.message.filter(ChatTypeFilter(["private"]))


@rangs_router.callback_query(F.data == "view_rangs")
async def view_rangs(call: types.CallbackQuery, user: Users):
    await Season().edit_upgrade_msg(call=call, user=user)



