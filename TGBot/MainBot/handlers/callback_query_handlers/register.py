from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from MainBot.base.models import Users
from MainBot.filters.chat_types import ChatTypeFilter
from MainBot.state.state import Auth_state, RegPersonal
from MainBot.utils.Forms import (
    Authorisation,
    PersonalForms,
)


register_router = Router(name=__name__)
register_router.message.filter(ChatTypeFilter(["private"]))


@register_router.callback_query(F.data == "ready_register")
async def why_are_you(call: types.CallbackQuery, state: FSMContext, user: Users):
    await call.message.delete()
    await Authorisation.why_are_you(call.message.bot, state, user)


@register_router.callback_query(F.data == "start_hello", Auth_state.Start_query)
async def start_hello(call: types.CallbackQuery, state: FSMContext, user: Users):
    await call.message.delete()
    await Authorisation.register_preview(call.message.bot, state, user)


#  & ~F.data.startswith("back_set_format_")
@register_router.callback_query(
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


@register_router.callback_query(F.data.startswith("gender|"), Auth_state.Gender)
async def gender(call: types.CallbackQuery, state: FSMContext, user: Users):
    call_data = call.data.split("|")[1]
    if call_data == "back":
        await call.message.delete()
        await Authorisation.why_are_you(call.message.bot, state, user)
    else:
        await Authorisation.age_participant(call, state, user)


@register_router.callback_query(F.data.startswith("gender|"), RegPersonal.Gender)
async def gender(call: types.CallbackQuery, state: FSMContext, user: Users):
    await PersonalForms().age_worker(call, state, user)


@register_router.callback_query(F.data.startswith("edit_age|"), Auth_state.Age)
async def edit_age(call: types.CallbackQuery, state: FSMContext, user: Users):
    call_data = call.data.split("|")

    if call_data[1] == "age":
        await Authorisation.age_participant(call, state, user)
    elif call_data[1] == "role":
        await call.message.delete()
        await Authorisation.why_are_you(call.message.bot, state, user)


@register_router.callback_query(F.data.startswith("data_validation|"), Auth_state.final)
async def data_validation(call: types.CallbackQuery, state: FSMContext, user: Users):
    call_data = call.data.split("|")
    if call_data[1] == "go":
        await Authorisation.success_ruls(call, state, user)
    elif call_data[1] == "edit":
        await Authorisation.back_gender_participant(call.message, state)


@register_router.callback_query(
    F.data.startswith("data_validation|"), RegPersonal.final
)
async def data_validation(call: types.CallbackQuery, state: FSMContext, user: Users):
    call_data = call.data.split("|")
    if call_data[1] == "go":
        await PersonalForms().success_ruls(call, state, user)
    elif call_data[1] == "edit":
        await PersonalForms().back_gender_worker(call.message, state)

