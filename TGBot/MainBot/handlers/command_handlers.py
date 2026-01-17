from MainBot.utils.errors import DuplicateOperationError
import texts
from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart
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
    Menu,
)
from MainBot.utils.Games import GeoHuntManager, LumberjackGame, LumberjackManager
from MainBot.utils.MyModule import Func

command_router = Router(name=__name__)
command_router.message.filter(ChatTypeFilter(["private"]))


# NOTE /profile
@command_router.message(Command(commands="profile"))
async def profile(message: types.Message, state: FSMContext, user: Users):
    if user.authorised:
        await state.clear()
        user = await Sigma_BoostsForms().add_passive_income(user)
        await Profile().user_info_msg(message, user)


@command_router.message(CommandStart())
async def cmd_start(message: types.Message, user: Users, state: FSMContext):
    url_data = message.text[7:]
    logger.debug(url_data)
    if url_data:
        if "upgrade_list_" in url_data:
            await Season().get_upgrade_msg(message=message, user=user)
            return

        elif await GiveLinksForm().activate(message, user, url_data):
            return

    await state.clear()
    await Menu().main_menu(
        message,
        user
    )


@command_router.message(Command(commands="work"))
async def work(message: types.Message, state: FSMContext, user: Users):
    key: str = message.text.replace("/work", "").strip()
    logger.info(key)
    if key and await PersonalForms().check_key(key):
        await PersonalForms().gender_worker(user, message, state, key)


@command_router.message(Command(commands="quests"))
async def quests(message: types.Message, state: FSMContext, user: Users):
    if user.authorised:
        await state.clear()
        if familyTies := FamilyTies(user.role_private).need:
            if not await familyTies.check_parent(user):
                await familyTies.info_parent(user, message)
                return
        
        user = await Sigma_BoostsForms().add_passive_income(user)
        await Quests().viue_all(user, message=message)


@command_router.message(Command(commands="game"))
async def game(message: types.Message, state: FSMContext, user: Users):
    if user.authorised:
        await state.clear()
        if familyTies := FamilyTies(user.role_private).need:
            if not await familyTies.check_parent(user):
                await familyTies.info_parent(user, message)
                return
        
        if await Lumberjack_GameMethods().get_max_energy(user):
            user = await Sigma_BoostsForms().add_passive_income(user)
            await LumberjackManager().schedule_energy_update(user)
            await GeoHuntManager().schedule_energy_update(user)
            await LumberjackGame.msg_before_game(user, message)
        else:
            await message.delete()


@command_router.message(Command(commands="shop"))
async def shop(message: types.Message, state: FSMContext, user: Users):
    if user.authorised:
        await state.clear()
        user = await Sigma_BoostsForms().add_passive_income(user)
        await Shop().catalog(user, message=message)


@command_router.message(Command(commands="help"))
async def profile(message: types.Message, state: FSMContext, user: Users):
    await state.clear()
    await Profile().user_help_msg(user, message)


