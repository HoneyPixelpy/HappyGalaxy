import texts
from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from loguru import logger
from MainBot.base.forms import Sigma_BoostsForms
from MainBot.base.models import Users
from MainBot.base.orm_requests import Lumberjack_GameMethods
from MainBot.filters.chat_types import ChatTypeFilter
from MainBot.utils.Forms import (
    FamilyTies,
    Profile,
    Quests,
    Shop,
    Menu,
    RatingForms
)
from MainBot.utils.Forms.Season import Season
from MainBot.utils.Games import (
    GeoHuntManager,
    LumberjackGame,
    LumberjackManager,
)

main_router = Router(name=__name__)
main_router.message.filter(ChatTypeFilter(["private"]))


@main_router.callback_query(F.data.startswith("main_menu|"))
async def main_menu(call: types.CallbackQuery, state: FSMContext, user: Users):
    if user.authorised:
        chapter = call.data.split("|")[1]
        logger.debug(chapter)
        await state.clear()
        match chapter:
            case "profile":
                user = await Sigma_BoostsForms().add_passive_income(user)
                await Profile().user_info_msg(
                    call,
                    user
                )
            case "rang":
                await Season().edit_upgrade_msg(call=call, user=user)
            case "game":
                if familyTies := FamilyTies(user.role_private).need:
                    if not await familyTies.check_parent(user):
                        await familyTies.info_parent(user, call)
                        return

                if await Lumberjack_GameMethods().get_max_energy(user):
                    user = await Sigma_BoostsForms().add_passive_income(user)
                    await LumberjackManager().schedule_energy_update(user)
                    await GeoHuntManager().schedule_energy_update(user)
                    await LumberjackGame.msg_before_game(user, call)
            case "quests":
                if familyTies := FamilyTies(user.role_private).need:
                    if not await familyTies.check_parent(user):
                        await familyTies.info_parent(user, call)
                        return
                
                user = await Sigma_BoostsForms().add_passive_income(user)
                await Quests().viue_all(user, call=call)
            case "rating":
                user = await Sigma_BoostsForms().add_passive_income(user)
                await RatingForms().main(user, call)
            case "help":
                await Profile().user_help_msg(user, call.message)
            case "shop":
                user = await Sigma_BoostsForms().add_passive_income(user)                
                await Shop().catalog(user, call=call)
            case "invite_friend":
                await Profile().invite_friend_info(
                    call,
                    user
                )
            case "back":
                await Menu().main_menu(
                    call,
                    user
                )
    else:
        await call.answer(
            texts.Error.Notif.undefined_error
        )


