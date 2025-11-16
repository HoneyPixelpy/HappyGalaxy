from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from loguru import logger

from MainBot.base.models import Users
import texts
from MainBot.base.forms import Sigma_BoostsForms
from MainBot.base.orm_requests import Lumberjack_GameMethods
from MainBot.filters.chat_types import ChatTypeFilter
from MainBot.utils.Forms import FamilyTies, Quests, \
    Shop, Profile, Promocodes
from MainBot.utils.Games import LumberjackGame


texts_router = Router(name=__name__)
texts_router.message.filter(ChatTypeFilter(["private"]))

@texts_router.message(StateFilter(None), F.text)
async def text_over(message: types.Message, state: FSMContext, user: Users):
	# Основные команды
    logger.debug(message.text)
    if message.text == texts.Btns.back:
        user = await Sigma_BoostsForms().add_passive_income(user)
        await Profile().user_info_msg(message.bot, user, message.message_id)
    elif message.text == texts.Btns.help:
        await Profile().user_help_msg(message.bot, user)
    elif message.text == texts.Btns.game:
        if (
            user.role_private in ["parent", "child"] and
            not await FamilyTies().info_parent(user, message)
            ):
            return
        
        if await Lumberjack_GameMethods().get_max_energy(user):
            await LumberjackGame.msg_before_game(message)
    elif message.text == texts.Btns.profile:
        user = await Sigma_BoostsForms().add_passive_income(user)
        await Profile().user_info_msg(message.bot, user, message.message_id)
    elif message.text == texts.Btns.shop:
        await Shop().catalog(
            user, 
            message=message
            )
    elif message.text == texts.Btns.quests:
        await Quests().viue_all(user, message=message)
    elif message.text == texts.Btns.promocodes:
        await Promocodes().wait_promo(user, state, message=message)
    await message.delete()

