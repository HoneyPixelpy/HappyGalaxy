from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from loguru import logger
from MainBot.base.forms import Sigma_BoostsForms
from MainBot.base.models import Users
from MainBot.filters.chat_types import ChatTypeFilter
from MainBot.utils.Forms import (
    FamilyTies,
    Quests,
)

quest_router = Router(name=__name__)
quest_router.message.filter(ChatTypeFilter(["private"]))


@quest_router.callback_query(F.data.startswith("all_quests"))
async def all_quests(call: types.CallbackQuery, user: Users):
    await Quests().viue_all(
        user,
        call=call,
        pagination=int(call.data.split("|")[1]) if "|" in call.data else None,
    )


@quest_router.callback_query(F.data.startswith("get_quest|"))
async def get_quest(call: types.CallbackQuery, state: FSMContext, user: Users):
    await state.clear()
    if familyTies := FamilyTies(user.role_private).need:
        if not await familyTies.check_parent(user):
            await familyTies.info_parent(user, call)
            return
    
    type_quest = call.data.split("|")[1]
    quest_id = int(call.data.split("|")[2])
    if type_quest == "subscribe":
        await Quests().get_sub_quest(call, state, user, quest_id)
    elif type_quest == "idea":
        await Quests().get_idea_quest(call, user, quest_id)
    elif type_quest == "daily":
        await Quests().get_daily_quest(call, user, quest_id)
    else:
        logger.error(f"Что это: {type_quest=}")


@quest_router.callback_query(F.data.startswith("idea_quest|"))
async def idea_quest(call: types.CallbackQuery, state: FSMContext, user: Users):
    quest_id = int(call.data.split("|")[1])
    await Quests().action_idea_quest(call, state, user, quest_id)


@quest_router.callback_query(F.data.startswith("daily_quest|"))
async def daily_quest(call: types.CallbackQuery, state: FSMContext, user: Users):
    quest_id = int(call.data.split("|")[1])
    await Quests().action_daily_quest(call, state, user, quest_id)


@quest_router.callback_query(F.data.startswith("check_sub|"))
async def check_sub(call: types.CallbackQuery, state: FSMContext, user: Users):
    quest_id = call.data.split("|")[1]
    user = await Sigma_BoostsForms().add_passive_income(user)
    status, error_msg_or_quest = await Quests().check_subscribe_quest(
        call, state, user, int(quest_id)
    )
    if status:
        await Quests().success_subscribe_quest(call, user, error_msg_or_quest)
    else:
        if error_msg_or_quest:
            try:
                await call.answer(text=error_msg_or_quest, show_alert=True)
            except: # exceptions.TelegramBadRequest
                await call.message.bot.send_message(
                    chat_id=user.user_id, text=error_msg_or_quest
                )


@quest_router.callback_query(F.data.startswith("activate_idea|"))
async def activate_idea(call: types.CallbackQuery, user: Users):
    _type = call.data.split("|")[1]
    quest_id = call.data.split("|")[2]
    user_id = call.data.split("|")[3]
    if _type == "success":
        await Quests().success_idea(call, user, quest_id, user_id)
    elif _type == "delete":
        await Quests().delete_idea(call, user, quest_id, user_id)

