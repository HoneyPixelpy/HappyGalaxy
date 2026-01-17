from aiogram import F, Router, types
from MainBot.base.forms import Sigma_BoostsForms
from MainBot.base.models import Users
from MainBot.filters.chat_types import ChatTypeFilter
from MainBot.utils.Forms import (
    Profile,
)

profile_router = Router(name=__name__)
profile_router.message.filter(ChatTypeFilter(["private"]))


@profile_router.callback_query(F.data == "back_to_profile") # NOTE DELETE
async def back_to_profile(call: types.CallbackQuery, user: Users):
    user = await Sigma_BoostsForms().add_passive_income(user)
    await Profile().user_info_msg(call, user)

