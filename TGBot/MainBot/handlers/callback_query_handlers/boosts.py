from aiogram import F, Router, types
from MainBot.base.forms import Sigma_BoostsForms
from MainBot.base.models import Users
from MainBot.filters.chat_types import ChatTypeFilter
from MainBot.utils.Forms import (
    Boosts,
)
from MainBot.utils.Games import (
    GeoHuntManager,
    LumberjackGame,
    LumberjackManager,
)

boosts_router = Router(name=__name__)
boosts_router.message.filter(ChatTypeFilter(["private"]))


@boosts_router.callback_query(F.data == "boosts")
async def boosts(call: types.CallbackQuery, user: Users):
    await Boosts().catalog(call, user)


@boosts_router.callback_query(F.data.startswith("get_boost|"))
async def get_boost(call: types.CallbackQuery, user: Users):
    name = call.data.split("|")[1]
    if name == "back":
        user = await Sigma_BoostsForms().add_passive_income(user)
        await LumberjackManager().schedule_energy_update(user)
        await GeoHuntManager().schedule_energy_update(user)
        await LumberjackGame.msg_before_game(user, call)
    else:
        await Boosts().get_boost(call, user, name, True)


@boosts_router.callback_query(F.data.startswith("upgrade_boost|"))
async def upgrade_boost(call: types.CallbackQuery, user: Users):
    name = call.data.split("|")[1]
    if name == "back":
        await Boosts().catalog(call, user)
    else:
        await Boosts().upgrade_boost(call, user, name)




