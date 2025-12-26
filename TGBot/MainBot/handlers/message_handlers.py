import texts
from aiogram import F, Router, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from loguru import logger
from MainBot.base.forms import Sigma_BoostsForms
from MainBot.base.models import Users
from MainBot.base.orm_requests import Lumberjack_GameMethods
from MainBot.filters.chat_types import ChatTypeFilter
from MainBot.utils.Forms import FamilyTies, Profile, Promocodes, Quests, Shop
from MainBot.utils.Games import LumberjackGame

texts_router = Router(name=__name__)
texts_router.message.filter(ChatTypeFilter(["private"]))


@texts_router.message(StateFilter(None), F.text)
async def text_over(message: types.Message, state: FSMContext, user: Users):
    """Все обработки с текстом"""
    logger.debug(message.text)
    match message.text:
        case texts.Btns.back:
            """Вернуться назад"""
            user = await Sigma_BoostsForms().add_passive_income(user)
            await Profile().user_info_msg(message.bot, user, message.message_id)
        case texts.Btns.help:
            """Раздел поддержки"""
            await Profile().user_help_msg(message.bot, user)
        case texts.Btns.game:
            """Раздел игр"""
            if user.role_private in [
                "parent",
                "child",
            ] and not await FamilyTies().info_parent(user, message):
                return

            if await Lumberjack_GameMethods().get_max_energy(user):
                await LumberjackGame.msg_before_game(message)
        case texts.Btns.profile:
            """Раздел профиля"""
            user = await Sigma_BoostsForms().add_passive_income(user)
            await Profile().user_info_msg(message.bot, user, message.message_id)
        case texts.Btns.shop:
            """Раздел магазина"""
            await Shop().catalog(user, message=message)
        case texts.Btns.quests:
            """Раздел квестов"""
            await Quests().viue_all(user, message=message)
        case texts.Btns.promocodes:
            """Раздел промокодов"""
            await Promocodes().wait_promo(user, state, message=message)
    # await message.delete()
