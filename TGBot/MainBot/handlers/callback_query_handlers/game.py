import texts
from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from loguru import logger
from config import bot_name, entry_threshold_geo_hunt
from MainBot.base.forms import Sigma_BoostsForms
from MainBot.base.models import Users
from MainBot.filters.chat_types import ChatTypeFilter
from MainBot.utils.Forms import (
    FamilyTies,
)
from MainBot.utils.Games import (
    GeoHunt,
    GeoHuntManager,
    LumberjackGame,
    LumberjackManager,
)
from MainBot.keyboards import inline
from MainBot.utils.Games.Interactive import InteractiveGame
from MainBot.utils.MyModule.message import MessageManager
from MainBot.utils.MyModule import Func

game_router = Router(name=__name__)
game_router.message.filter(ChatTypeFilter(["private"]))


@game_router.callback_query(F.data == "games")
async def games(call: types.CallbackQuery, user: Users):
    await LumberjackGame().msg_before_game(user, call)


@game_router.callback_query(F.data.startswith("game|"))
async def game(call: types.CallbackQuery, user: Users):
    if familyTies := FamilyTies(user.role_private).need:
        if not await familyTies.check_parent(user):
            await familyTies.info_parent(user, call)
            return

    user = await Sigma_BoostsForms().add_passive_income(user)

    await LumberjackManager().schedule_energy_update(user)
    await GeoHuntManager().schedule_energy_update(user)
    game_type: str = call.data.split("|")[1]
    match game_type:
        case "clicker":
            await LumberjackGame.send_call_game(call, user)
        case "create":
            await InteractiveGame().create_info(user, call=call)
        case "geo_hunt":  # TODO добавить переменную с этим числом
            if user.all_starcoins >= entry_threshold_geo_hunt:
                await GeoHunt().get_field(call, user)
            else:
                await MessageManager(
                    call,
                    user.user_id
                ).send_or_edit(
                    texts.Game.Texts.before_game + texts.Game.GeoHunt.young_to_geohunter,
                    await inline.before_game(),
                    "game"
                )
                # await call.message.answer(
                #     text=texts.Game.GeoHunt.young_to_geohunter.format(
                #         bot_name=bot_name, msg_id=call.message.message_id + 1
                #     ),
                #     disable_web_page_preview=True
                # )
        case _:
            await Func.send_error_to_developer(
                (
                    "Пользователь не смог перейти в игру\n"
                    f"{user.user_id} {user.tg_username}\n"
                    f"All starcoins: {user.all_starcoins}\n"
                    f"Call Data: {call.data}"
                )
            )


@game_router.callback_query(F.data.startswith("lumberjack_click"))
async def lumberjack_click(call: types.CallbackQuery, user: Users):
    user = await Sigma_BoostsForms().add_passive_income(user)
    await LumberjackManager().schedule_energy_update(user)
    await LumberjackGame.handle_click(call, user)


@game_router.callback_query(F.data == "lumberjack_refresh")
async def lumberjack_refresh(call: types.CallbackQuery, user: Users):
    user = await Sigma_BoostsForms().add_passive_income(user)
    await LumberjackManager().schedule_energy_update(user)
    await LumberjackGame.handle_refresh(call, user)


@game_router.callback_query(F.data.startswith("geo_hunt_click"))
async def geo_hunt_click(call: types.CallbackQuery, user: Users):
    await GeoHunt().speed_lock(call, user)


@game_router.callback_query(F.data.startswith("update_game|"))
async def update_game(call: types.CallbackQuery, user: Users, state: FSMContext):
    await InteractiveGame().update(user, call, state)


@game_router.callback_query(F.data == "create_game")
async def create_game(call: types.CallbackQuery, user: Users, state: FSMContext):
    await InteractiveGame().create_game(user, call)


@game_router.callback_query(F.data.startswith("verif_interactive_game|"))
async def verif_interactive_game(call: types.CallbackQuery, user: Users):
    if call.data.split("|")[1] == "success":
        await InteractiveGame().success_create_game(user, call, call.data.split("|")[2])
    elif call.data.split("|")[1] == "delete":
        await InteractiveGame().delete_create_game(user, call, call.data.split("|")[2])
    else:
        logger.exception(f"Error: verif_interactive_game - {call.data}")
        await call.answer("Error: verif_interactive_game", show_alert=True)


@game_router.callback_query(F.data.startswith("refresh_interactive_game|"))
async def refresh_interactive_game(
    call: types.CallbackQuery, user: Users, state: FSMContext
):
    game_id = int(call.data.split("|")[1])
    await InteractiveGame().refresh_ready_info(user, call, game_id)


@game_router.callback_query(F.data.startswith("login_interactive_game|"))
async def login_interactive_game(
    call: types.CallbackQuery, user: Users, state: FSMContext
):
    game_id = int(call.data.split("|")[1])
    await InteractiveGame().invite_game(user, call, game_id)


@game_router.callback_query(F.data.startswith("delete_interactive_game|"))
async def delete_interactive_game(
    call: types.CallbackQuery, user: Users, state: FSMContext
):
    game_id = int(call.data.split("|")[1])
    await InteractiveGame().delete_game(user, call, game_id)


@game_router.callback_query(F.data.startswith("refresh_info_game|"))
async def refresh_info_game(call: types.CallbackQuery, user: Users, state: FSMContext):
    game_id = int(call.data.split("|")[1])
    await InteractiveGame().refresh_info(user, call, game_id)
    # NOTE если прошло больше 10 минут, столько скольно надо для принятия приглашения, то удаляется сообщение и игра


@game_router.callback_query(F.data.startswith("start_interactive_game|"))
async def start_interactive_game(
    call: types.CallbackQuery, user: Users, state: FSMContext
):
    game_id = int(call.data.split("|")[1])
    await InteractiveGame().start_game(user, call, game_id)


@game_router.callback_query(F.data.startswith("players_end_game|"))
async def players_end_game(call: types.CallbackQuery, user: Users, state: FSMContext):
    game_id = int(call.data.split("|")[1])
    pagination = int(call.data.split("|")[2])
    await InteractiveGame().finally_game(user, call, game_id, pagination)


@game_router.callback_query(F.data.startswith("s_player_end_game|"))
async def s_player_end_game(call: types.CallbackQuery, user: Users, state: FSMContext):
    user_id = call.data.split("|")[1]
    game_id = int(call.data.split("|")[2])
    pagination = int(call.data.split("|")[3])
    await InteractiveGame().finally_game(user, call, game_id, pagination, user_id)


@game_router.callback_query(F.data.startswith("end_game|"))
async def end_game(call: types.CallbackQuery, user: Users, state: FSMContext):
    game_id = int(call.data.split("|")[1])
    await InteractiveGame().end_game(user, call, game_id)




