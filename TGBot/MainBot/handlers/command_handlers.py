import asyncio

import texts
from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from loguru import logger
from MainBot.base.forms import Sigma_BoostsForms
from MainBot.base.models import Users
from MainBot.base.orm_requests import Lumberjack_GameMethods
from MainBot.filters.chat_types import ChatTypeFilter
from MainBot.utils.Forms import (
    FamilyTies,
    GiveLinksForm,
    PersonalForms,
    Profile,
    Quests,
    Season,
    Shop,
)
from MainBot.utils.Games import GeoHuntManager, LumberjackGame, LumberjackManager
from MainBot.utils.MyModule import Func

command_router = Router(name=__name__)
command_router.message.filter(ChatTypeFilter(["private"]))


@command_router.message(CommandStart())
async def cmd_start(message: types.Message, user: Users):
    url_data = message.text[7:]
    logger.debug(url_data)
    if url_data:
        if "upgrade_list_" in url_data:
            await Season().get_upgrade_msg(message=message, user=user)
            return

        elif await GiveLinksForm().activate(message, user, url_data):
            return

    user = await Sigma_BoostsForms().add_passive_income(user)
    await Profile().user_info_msg(message.bot, user, message.message_id)


@command_router.message(Command(commands="work"))
async def profile(message: types.Message, state: FSMContext, user: Users):
    try:
        key: str = message.text.replace("/work", "").strip()
        logger.info(key)
        if key and await PersonalForms().check_key(key):
            await PersonalForms().gender_worker(user, message, state, key)
    except Exception as ex:
        logger.exception(f"{ex.__class__.__name__} {ex}")
        await Func.send_error_to_developer(f"{ex.__class__.__name__} {ex}")
        await message.answer(texts.Personal.Error.undefined_error)


@command_router.message(Command(commands="task"))
async def task(message: types.Message, state: FSMContext, user: Users):
    if user.authorised:
        await state.clear()
        user = await Sigma_BoostsForms().add_passive_income(user)
        await Quests().viue_all(user, message=message)


@command_router.message(Command(commands="shop"))
async def shop(message: types.Message, state: FSMContext, user: Users):
    if user.authorised:
        await state.clear()
        user = await Sigma_BoostsForms().add_passive_income(user)
        await Shop().catalog(user, message=message)


@command_router.message(Command(commands="help"))
async def profile(message: types.Message, state: FSMContext, user: Users):
    await state.clear()
    await Profile().user_help_msg(message.bot, user)


@command_router.message(Command(commands="game"))
async def game(message: types.Message, state: FSMContext, user: Users):
    if user.authorised:
        await state.clear()
        if user.role_private in [
            "parent",
            "child",
        ] and not await FamilyTies().info_parent(user, message):
            return
        if await Lumberjack_GameMethods().get_max_energy(user):
            user = await Sigma_BoostsForms().add_passive_income(user)
            await LumberjackManager().schedule_energy_update(user)
            await GeoHuntManager().schedule_energy_update(user)
            await LumberjackGame.msg_before_game(message)
        else:
            await message.delete()
