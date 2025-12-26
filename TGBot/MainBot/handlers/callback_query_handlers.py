import texts
from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from config import bot_name, entry_threshold_geo_hunt
from loguru import logger
from MainBot.base.forms import Sigma_BoostsForms
from MainBot.base.models import Users
from MainBot.filters.chat_types import ChatTypeFilter
from MainBot.state.state import Auth_state, RegPersonal
from MainBot.utils.Forms import (
    Authorisation,
    BonusBoosters,
    Boosts,
    FamilyTies,
    PersonalForms,
    Profile,
    Quests,
    Shop,
)
from MainBot.utils.Forms.Season import Season
from MainBot.utils.Games import (
    GeoHunt,
    GeoHuntManager,
    LumberjackGame,
    LumberjackManager,
)
from MainBot.utils.Games.Interactive import InteractiveGame
from MainBot.utils.MyModule import Func

callback_router = Router(name=__name__)
callback_router.message.filter(ChatTypeFilter(["private"]))


@callback_router.callback_query(F.data == "ready_register")
async def why_are_you(call: types.CallbackQuery, state: FSMContext, user: Users):
    await call.message.delete()
    await Authorisation.why_are_you(call.message.bot, state, user)


@callback_router.callback_query(F.data == "start_hello", Auth_state.Start_query)
async def start_hello(call: types.CallbackQuery, state: FSMContext, user: Users):
    await call.message.delete()
    await Authorisation.register_preview(call.message.bot, state, user)


#  & ~F.data.startswith("back_set_format_")
@callback_router.callback_query(
    F.data.startswith("sure_role|"), Auth_state.why_are_you
)  # , StateFilter("*")
async def sure_role(call: types.CallbackQuery, state: FSMContext, user: Users):
    call_data = call.data.split("|")
    if call_data[1] == "back":
        await call.message.delete()
        await Authorisation.why_are_you(call.message.bot, state, user)
    # elif call_data[1] == "child":
    #     await Authorisation.gender_participant(
    #         call,
    #         state,
    #         user
    #     )
    elif call_data[1] in ["parent", "worker", "child"]:
        await Authorisation.gender_participant(call, state, user, call_data[1])


@callback_router.callback_query(F.data.startswith("gender|"), Auth_state.Gender)
async def gender(call: types.CallbackQuery, state: FSMContext, user: Users):
    call_data = call.data.split("|")[1]
    if call_data == "back":
        await call.message.delete()
        await Authorisation.why_are_you(call.message.bot, state, user)
    else:
        await Authorisation.age_participant(call, state, user)


@callback_router.callback_query(F.data.startswith("gender|"), RegPersonal.Gender)
async def gender(call: types.CallbackQuery, state: FSMContext, user: Users):
    await PersonalForms().age_worker(call, state, user)


@callback_router.callback_query(F.data.startswith("edit_age|"), Auth_state.Age)
async def edit_age(call: types.CallbackQuery, state: FSMContext, user: Users):
    call_data = call.data.split("|")

    if call_data[1] == "age":
        await Authorisation.age_participant(call, state, user)
    elif call_data[1] == "role":
        await call.message.delete()
        await Authorisation.why_are_you(call.message.bot, state, user)


@callback_router.callback_query(F.data.startswith("data_validation|"), Auth_state.final)
async def data_validation(call: types.CallbackQuery, state: FSMContext, user: Users):
    call_data = call.data.split("|")
    if call_data[1] == "go":
        await Authorisation.success_ruls(call, state, user)
    elif call_data[1] == "edit":
        await Authorisation.back_gender_participant(call.message, state)


@callback_router.callback_query(
    F.data.startswith("data_validation|"), RegPersonal.final
)
async def data_validation(call: types.CallbackQuery, state: FSMContext, user: Users):
    call_data = call.data.split("|")
    if call_data[1] == "go":
        await PersonalForms().success_ruls(call, state, user)
    elif call_data[1] == "edit":
        await PersonalForms().back_gender_worker(call.message, state)


# @callback_router.callback_query(F.data == "success_ruls", Auth_state.success_ruls)
# async def success_ruls(call: types.CallbackQuery, state: FSMContext, user: Users):
#     await Authorisation.final_regisration(
#         call,
#         state,
#         user
#     )

# @callback_router.callback_query(F.data == "success_ruls", RegPersonal.success_ruls)
# async def success_ruls(call: types.CallbackQuery, state: FSMContext, user: Users):
#     await PersonalForms().final_regisration(
#         call,
#         state,
#         user
#     )


@callback_router.callback_query(F.data.startswith("geo_hunt_click"))
async def geo_hunt_click(call: types.CallbackQuery, user: Users):
    await GeoHunt().speed_lock(call, user)


@callback_router.callback_query(F.data.startswith("lumberjack_click"))
async def lumberjack_click(call: types.CallbackQuery, user: Users):
    user = await Sigma_BoostsForms().add_passive_income(user)
    await LumberjackManager().schedule_energy_update(user)
    await LumberjackGame.handle_click(call, user)


@callback_router.callback_query(F.data == "lumberjack_refresh")
async def lumberjack_refresh(call: types.CallbackQuery, user: Users):
    user = await Sigma_BoostsForms().add_passive_income(user)
    await LumberjackManager().schedule_energy_update(user)
    await LumberjackGame.handle_refresh(call, user)


@callback_router.callback_query(F.data.startswith("game|"))
async def game(call: types.CallbackQuery, user: Users):
    await call.message.delete()
    if user.role_private in ["parent", "child"] and not await FamilyTies().info_parent(
        user, call.message
    ):
        return

    user = await Sigma_BoostsForms().add_passive_income(user)

    await LumberjackManager().schedule_energy_update(user)
    await GeoHuntManager().schedule_energy_update(user)
    game_type: str = call.data.split("|")[1]
    if game_type == "clicker":
        await LumberjackGame.send_call_game(call, user)
    elif game_type == "create":
        await InteractiveGame().create_info(user, call=call)
    elif game_type == "geo_hunt":  # TODO добавить переменную с этим числом
        if user.all_starcoins >= entry_threshold_geo_hunt:
            await GeoHunt().get_field(call, user)
        else:
            await call.message.answer(
                text=texts.Game.GeoHunt.young_to_geohunter.format(
                    bot_name=bot_name, msg_id=call.message.message_id + 1
                ),
                disable_web_page_preview=True,
            )
    else:
        await Func.send_error_to_developer(
            (
                "Пользователь не смог перейти в игру\n"
                f"{user.user_id} {user.tg_username}\n"
                f"All starcoins: {user.all_starcoins}\n"
                f"Call Data: {call.data}"
            )
        )


@callback_router.callback_query(F.data == "boosts")
async def boosts(call: types.CallbackQuery, user: Users):
    await Boosts().catalog(call, user)


@callback_router.callback_query(F.data == "games")
async def games(call: types.CallbackQuery):
    await call.message.delete()
    await LumberjackGame().msg_before_game(call.message)


@callback_router.callback_query(F.data.startswith("get_boost|"))
async def get_boost(call: types.CallbackQuery, user: Users):
    name = call.data.split("|")[1]
    if name == "back":
        await call.message.delete()
        user = await Sigma_BoostsForms().add_passive_income(user)
        await LumberjackManager().schedule_energy_update(user)
        await GeoHuntManager().schedule_energy_update(user)
        await LumberjackGame.msg_before_game(call.message)
    else:
        await Boosts().get_boost(call, user, name, True)


@callback_router.callback_query(F.data.startswith("upgrade_boost|"))
async def upgrade_boost(call: types.CallbackQuery, user: Users):
    name = call.data.split("|")[1]
    if name == "back":
        await Boosts().catalog(call, user)
    else:
        await Boosts().upgrade_boost(call, user, name)


@callback_router.callback_query(F.data.startswith("get_product|"))
async def get_product(call: types.CallbackQuery, user: Users):
    product_id = int(call.data.split("|")[1])
    await Shop().get_product(call.message, user, product_id)


@callback_router.callback_query(F.data.startswith("buy_product|"))
async def buy_product(call: types.CallbackQuery, user: Users, state: FSMContext):
    product_id = call.data.split("|")[1]
    instructions = bool(call.data.split("|")[2])
    if product_id == "back":
        await Shop().catalog(user, call=call)
    else:
        if instructions:
            await Shop().view_instructions(
                call, state, user, product_id
            )
        else:
            user = await Sigma_BoostsForms().add_passive_income(user)
            status, error_msg_or_product = await Shop().check_possibility_purchase(
                user, product_id
            )
            if status:
                await Shop().buy_product(call.message, user, error_msg_or_product)
            else:
                try:
                    await call.answer(text=error_msg_or_product, show_alert=True)
                except:
                    await call.message.bot.send_message(
                        chat_id=user.user_id, text=error_msg_or_product
                    )


@callback_router.callback_query(F.data.startswith("success_buy|"))
async def success_buy(call: types.CallbackQuery, user: Users, state: FSMContext):
    action = call.data.split("|")[1]
    purchases_id = call.data.split("|")[2]
    match action:
        case "cancel":
            await Shop().cancel_buy(
                call, user, purchases_id
                )
        case "success":
            await Shop().success_buy(
                call, user, purchases_id
            )


@callback_router.callback_query(F.data.startswith("get_quest|"))
async def get_quest(call: types.CallbackQuery, state: FSMContext, user: Users):
    type_quest = call.data.split("|")[1]
    quest_id = int(call.data.split("|")[2])
    if type_quest == "subscribe":
        await Quests().get_sub_quest(call, state, user, quest_id)
    elif type_quest == "idea":
        await Quests().get_idea_quest(call.message, user, quest_id)
    elif type_quest == "daily":
        await Quests().get_daily_quest(call.message, user, quest_id)
    else:
        logger.error(f"Что это: {type_quest=}")


@callback_router.callback_query(F.data.startswith("idea_quest|"))
async def idea_quest(call: types.CallbackQuery, state: FSMContext, user: Users):
    quest_id = int(call.data.split("|")[1])
    await Quests().action_idea_quest(call, state, user, quest_id)


@callback_router.callback_query(F.data.startswith("daily_quest|"))
async def daily_quest(call: types.CallbackQuery, state: FSMContext, user: Users):
    quest_id = int(call.data.split("|")[1])
    await Quests().action_daily_quest(call, state, user, quest_id)


@callback_router.callback_query(F.data.startswith("all_quests"))
async def all_quests(call: types.CallbackQuery, user: Users):
    await Quests().viue_all(
        user,
        call=call,
        pagination=int(call.data.split("|")[1]) if "|" in call.data else None,
    )


@callback_router.callback_query(F.data.startswith("all_products"))
async def all_products(call: types.CallbackQuery, user: Users):
    await Shop().catalog(
        user,
        call=call,
        pagination=int(call.data.split("|")[1]) if "|" in call.data else None,
    )


@callback_router.callback_query(F.data == "view_rangs")
async def view_rangs(call: types.CallbackQuery, user: Users):
    await Season().get_upgrade_msg(message=call.message, user=user)


@callback_router.callback_query(F.data.startswith("check_sub|"))
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
            except:
                await call.message.bot.send_message(
                    chat_id=user.user_id, text=error_msg_or_quest
                )


@callback_router.callback_query(F.data.startswith("activate_bonus|"))
async def activate_bonus(call: types.CallbackQuery, user: Users):
    await BonusBoosters().get_bonus(call, user, call.data.split("|")[1])


@callback_router.callback_query(F.data.startswith("write_offer|"))
async def write_offer(call: types.CallbackQuery, user: Users, state: FSMContext):
    _type = call.data.split("|")[1]
    if _type == "shop":
        await Shop().write_offer(call, user, state)


@callback_router.callback_query(F.data.startswith("activate_idea|"))
async def activate_idea(call: types.CallbackQuery, user: Users):
    _type = call.data.split("|")[1]
    quest_id = call.data.split("|")[2]
    user_id = call.data.split("|")[3]
    if _type == "success":
        await Quests().success_idea(call, user, quest_id, user_id)
    elif _type == "delete":
        await Quests().delete_idea(call, user, quest_id, user_id)


@callback_router.callback_query(F.data == "back_to_profile")
async def back_to_profile(call: types.CallbackQuery, user: Users):
    await call.message.delete()
    user = await Sigma_BoostsForms().add_passive_income(user)
    await Profile().user_info_msg(call.message.bot, user, call.message.message_id)


@callback_router.callback_query(F.data == "null")
async def null(call: types.CallbackQuery, user: Users):
    pass


@callback_router.callback_query(F.data.startswith("update_game|"))
async def update_game(call: types.CallbackQuery, user: Users, state: FSMContext):
    await InteractiveGame().update(user, call, state)


@callback_router.callback_query(F.data == "create_game")
async def create_game(call: types.CallbackQuery, user: Users, state: FSMContext):
    await InteractiveGame().create_game(user, call)


@callback_router.callback_query(F.data.startswith("verif_interactive_game|"))
async def verif_interactive_game(call: types.CallbackQuery, user: Users):
    if call.data.split("|")[1] == "success":
        await InteractiveGame().success_create_game(user, call, call.data.split("|")[2])
    elif call.data.split("|")[1] == "delete":
        await InteractiveGame().delete_create_game(user, call, call.data.split("|")[2])
    else:
        logger.exception(f"Error: verif_interactive_game - {call.data}")
        await call.answer("Error: verif_interactive_game", show_alert=True)


@callback_router.callback_query(F.data.startswith("refresh_interactive_game|"))
async def refresh_interactive_game(
    call: types.CallbackQuery, user: Users, state: FSMContext
):
    game_id = int(call.data.split("|")[1])
    await InteractiveGame().refresh_ready_info(user, call, game_id)


@callback_router.callback_query(F.data.startswith("login_interactive_game|"))
async def login_interactive_game(
    call: types.CallbackQuery, user: Users, state: FSMContext
):
    game_id = int(call.data.split("|")[1])
    await InteractiveGame().invite_game(user, call, game_id)


@callback_router.callback_query(F.data.startswith("delete_interactive_game|"))
async def delete_interactive_game(
    call: types.CallbackQuery, user: Users, state: FSMContext
):
    game_id = int(call.data.split("|")[1])
    await InteractiveGame().delete_game(user, call, game_id)


@callback_router.callback_query(F.data.startswith("refresh_info_game|"))
async def refresh_info_game(call: types.CallbackQuery, user: Users, state: FSMContext):
    game_id = int(call.data.split("|")[1])
    await InteractiveGame().refresh_info(user, call, game_id)
    # NOTE если прошло больше 10 минут, столько скольно надо для принятия приглашения, то удаляется сообщение и игра


@callback_router.callback_query(F.data.startswith("start_interactive_game|"))
async def start_interactive_game(
    call: types.CallbackQuery, user: Users, state: FSMContext
):
    game_id = int(call.data.split("|")[1])
    await InteractiveGame().start_game(user, call, game_id)


@callback_router.callback_query(F.data.startswith("players_end_game|"))
async def players_end_game(call: types.CallbackQuery, user: Users, state: FSMContext):
    game_id = int(call.data.split("|")[1])
    pagination = int(call.data.split("|")[2])
    await InteractiveGame().finally_game(user, call, game_id, pagination)


@callback_router.callback_query(F.data.startswith("s_player_end_game|"))
async def s_player_end_game(call: types.CallbackQuery, user: Users, state: FSMContext):
    user_id = call.data.split("|")[1]
    game_id = int(call.data.split("|")[2])
    pagination = int(call.data.split("|")[3])
    await InteractiveGame().finally_game(user, call, game_id, pagination, user_id)


@callback_router.callback_query(F.data.startswith("end_game|"))
async def end_game(call: types.CallbackQuery, user: Users, state: FSMContext):
    game_id = int(call.data.split("|")[1])
    await InteractiveGame().end_game(user, call, game_id)


@callback_router.callback_query(
    F.data.in_(
        [
            F.data == "exit",
            F.data.startswith("data_validation|"),
            F.data.startswith("edit_age|"),
            F.data.startswith("success_fio|"),
            F.data.startswith("gender|"),
            F.data.startswith("sure_role|"),
        ]
    )
)
async def delete_no_state(call: types.CallbackQuery):
    await call.message.delete()
