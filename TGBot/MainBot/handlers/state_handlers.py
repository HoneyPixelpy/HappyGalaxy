import asyncio

import texts
from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from loguru import logger
from MainBot.base.forms import Sigma_BoostsForms
from MainBot.base.models import Users
from MainBot.filters.chat_types import ChatTypeFilter
from MainBot.keyboards.inline import IKB as inline
from MainBot.keyboards.reply import KB as reply
from MainBot.state.state import (
    Auth_state,
    Daily,
    Idea,
    Msg_Delete,
    Offer,
    RegPersonal,
    SInteractiveGame,
    SPromocodes,
    VKProfile,
)
from MainBot.utils.Forms import (
    Authorisation,
    PersonalForms,
    Profile,
    Promocodes,
    Quests,
    Shop,
)
from MainBot.utils.Games.Interactive.main import InteractiveGame

# import humanize
# humanize.precisedelta(time_left, minimum_unit="minutes")

state_router = Router(name=__name__)
state_router.message.filter(ChatTypeFilter(["private"]))


# @state_router.message(Auth_state.Start_query)
# async def Auth_state_Start_query(message: types.Message, state: FSMContext, user: Users):
#     if message.text == texts.Start.Btns.go:
#         await Authorisation.register_preview(
#             message.bot,
#             state,
#             user
#         )
#     elif message.text == texts.Start.Btns.wait:
#         await Authorisation.let_do_it_later(
#             message.bot,
#             state,
#             user
#         )
#     else:
#         await message.answer(
#             texts.Error.Notif.no_btn,
#             reply_markup=await reply.start_hello()
#         )
#         await message.delete()


@state_router.message(Auth_state.why_are_you)
async def Auth_state_why_are_you(
    message: types.Message, state: FSMContext, user: Users
):
    await message.delete()
    if message.text == texts.Start.Btns.participant:
        role = "child"
    elif message.text == texts.Start.Btns.parent:
        role = "parent"
    elif message.text == texts.Start.Btns.worker:
        role = "worker"
    else:
        await message.answer(
            texts.Error.Notif.no_btn, reply_markup=await reply.why_are_you()
        )
        return
    await Authorisation.sure_role(message.bot, user, role=role)


@state_router.message(Auth_state.Age)
async def Auth_state_Age(message: types.Message, state: FSMContext, user: Users):
    if message.text == texts.Btns.back:
        await Authorisation.back_gender_participant(message, state)
    else:
        status, error_msg_or_age = await Authorisation.check_age(message.text, state)
        if status:
            await Authorisation.fio_participant(message, state, user, error_msg_or_age)
        else:
            await message.answer(error_msg_or_age, reply_markup=await inline.age())
            await message.delete()


@state_router.message(RegPersonal.Age)
async def RegPersonal_Age(message: types.Message, state: FSMContext, user: Users):
    if message.text == texts.Btns.back:
        await PersonalForms().back_gender_worker(message, state)
    else:
        status, error_msg_or_age = await Authorisation.check_age(message.text, state)
        if status:
            await PersonalForms().fio_worker(message, state, user, error_msg_or_age)
        else:
            await message.answer(error_msg_or_age, reply_markup=await inline.age())
            await message.delete()


@state_router.message(Auth_state.FIO)
async def Auth_state_FIO(message: types.Message, state: FSMContext, user: Users):
    data = await state.get_data()
    if message.text == texts.Btns.back:
        await Authorisation.back_age_participant(message, state, user)
    elif message.text:
        status, error_msg_or_parts = await Authorisation.check_fio(
            message.text, data["role"]
        )
        if status:
            await Authorisation.create_nickname(
                message, state, user, data["role"], error_msg_or_parts
            )
        else:
            await message.answer(
                error_msg_or_parts,
                reply_markup=await reply.back(
                    "Имя" if data["role"] == "child" else "Фамилия Имя"
                ),
            )
            await message.delete()

    else:
        await message.answer(
            texts.Error.Notif.no_str,
            reply_markup=await reply.back(
                "Имя" if data["role"] == "child" else "Фамилия Имя"
            ),
        )
        await message.delete()


@state_router.message(RegPersonal.FIO)
async def RegPersonal_FIO(message: types.Message, state: FSMContext, user: Users):
    if message.text == texts.Btns.back:
        await PersonalForms().back_age_worker(message, state, user)
    elif message.text:
        status, error_msg_or_parts = await Authorisation.check_fio(message.text)
        if status:
            await PersonalForms().phone_worker(
                message, state, user, error_msg_or_parts, ""
            )
        else:
            await message.answer(
                error_msg_or_parts, reply_markup=await reply.back("Фамилия Имя")
            )
            await message.delete()

    else:
        await message.answer(
            texts.Error.Notif.no_str, reply_markup=await reply.back("Фамилия Имя")
        )
        await message.delete()


@state_router.message(Auth_state.nickname)
async def Auth_state_nickname(message: types.Message, state: FSMContext, user: Users):
    if message.text == texts.Btns.back:
        await Authorisation.back_fio_participant(message, state, user)
    elif message.text == texts.Btns.select_later:
        await Authorisation.phone_participant(message, state, user, None)
    elif message.text:
        status, error_msg_or_final_nick = await Authorisation.check_nickname(
            message.text
        )
        if status:
            await Authorisation.phone_participant(
                message, state, user, error_msg_or_final_nick
            )
        else:
            await message.answer(
                "\n".join(error_msg_or_final_nick),
                reply_markup=await reply.back("Введите псевдоним"),
            )
            await message.delete()

    else:
        await message.answer(
            texts.Error.Notif.no_str, reply_markup=await reply.back("Введите псевдоним")
        )
        await message.delete()


@state_router.message(Auth_state.phone, F.content_type == types.ContentType.CONTACT)
async def Auth_state_phone(message: types.Message, state: FSMContext, user: Users):
    contact = message.contact

    if contact.user_id and contact.user_id == message.from_user.id:
        # Номер подтверждён через Telegram
        status, error_msg_or_phone = await Authorisation.check_phone(
            contact.phone_number
        )
        if status:
            await Authorisation.data_validation(
                message, state, user, error_msg_or_phone
            )
        else:
            await message.answer(
                "\n".join(error_msg_or_phone), reply_markup=await reply.send_phone()
            )
            await message.delete()
    else:
        # Требуется дополнительная проверка SMS
        await message.answer(
            "Отправьте свой номер, а не чужой!\n\nОбратитесь в нашу службу поддержки объяснив всю проблему",
            reply_markup=await reply.send_phone(),
        )


@state_router.message(RegPersonal.phone, F.content_type == types.ContentType.CONTACT)
async def RegPersonal_phone(message: types.Message, state: FSMContext, user: Users):
    contact = message.contact

    if contact.user_id and contact.user_id == message.from_user.id:
        # Номер подтверждён через Telegram
        # status, error_msg_or_phone = await Authorisation.check_phone(
        #     contact.phone_number
        #     )
        # if status:
        await PersonalForms().data_validation(
            message, state, user, contact.phone_number
        )
    # else:
    #     await message.answer(
    #         "\n".join(error_msg_or_phone),
    #         reply_markup=await reply.send_phone()
    #     )
    #     await message.delete()
    else:
        # Требуется дополнительная проверка SMS
        await message.answer(
            "Отправьте свой номер, а не чужой!\n\nОбратитесь в нашу службу поддержки объяснив всю проблему",
            reply_markup=await reply.send_phone(),
        )


@state_router.message(Auth_state.phone)
async def Auth_state_phone(message: types.Message, state: FSMContext, user: Users):
    if message.text == texts.Btns.back:
        state_data = await state.get_data()
        # if state_data['role'] in ["child", "worker"]:
        await Authorisation.back_create_nickname(
            message, state, user, state_data["role"]
        )
    # elif state_data['role'] == 'parent':
    #     await Authorisation.back_fio_participant(
    #         message,
    #         state,
    #         user
    #     )


@state_router.message(RegPersonal.phone)
async def RegPersonal_phone(message: types.Message, state: FSMContext, user: Users):
    if message.text == texts.Btns.back:
        await PersonalForms().back_fio_worker(message, state, user)


@state_router.message(Offer.shop)
async def Offer_shop(message: types.Message, state: FSMContext, user: Users):
    if message.text == texts.Btns.back:
        await state.clear()
        user = await Sigma_BoostsForms().add_passive_income(user)
        await Profile().user_info_msg(message.bot, user, message.message_id)
    else:
        await Shop().send_offer(message, state, user)


@state_router.message(
    Auth_state.Gender, Auth_state.Success_FIO, Auth_state.success_ruls, Auth_state.final
)
async def click_inline_kb(message: types.Message):
    await message.answer(texts.Error.Notif.no_btn + texts.Error.Notif.as_needed)
    await message.delete()


@state_router.message(Auth_state.No, Msg_Delete.Activate)
async def message_delete(message: types.Message):
    await message.delete()


@state_router.message(VKProfile.url)
async def VKProfile_url(message: types.Message, state: FSMContext, user: Users):
    if message.text == texts.Btns.back:
        await state.clear()
        await message.answer(
            text=texts.Texts.start, reply_markup=await reply.main_menu(user)
        )
        await Quests().viue_all(user, message=message)
    else:
        text, keyboard = await Quests().verif_vk_profile_link(state, user, message.text)
        for tx, kb in zip(text, keyboard):
            await message.bot.send_message(
                chat_id=user.user_id, text=tx, reply_markup=kb
            )
            await asyncio.sleep(0.2)
        # await message.delete()


@state_router.message(Idea.wait)
async def Idea_wait(message: types.Message, state: FSMContext, user: Users):
    data = await state.get_data()
    if message.text == texts.Btns.back:
        await state.clear()
        await Quests().get_idea_quest(message, user, data["id"])
    else:
        await Quests().check_idea_quest(message, state, user)


@state_router.message(Daily.wait)
async def Daily_wait(message: types.Message, state: FSMContext, user: Users):
    data = await state.get_data()
    if message.text == texts.Btns.back:
        await state.clear()
        await Quests().get_idea_quest(message, user, data["id"])
    else:
        await Quests().check_daily_quest(message, state, user)


@state_router.message(SPromocodes.wait)
async def SPromocodes_wait(message: types.Message, state: FSMContext, user: Users):
    if message.text == texts.Btns.back:
        await state.clear()
        await message.answer(
            text=texts.Texts.start, reply_markup=await reply.main_menu(user)
        )
    else:
        await Promocodes().activate(message, state, user)


@state_router.message(SInteractiveGame.wait_data)
async def SInteractiveGame_wait_data(
    message: types.Message, state: FSMContext, user: Users
):
    await message.bot.send_message(
        chat_id=user.user_id,
        text=texts.Texts.start,
        reply_markup=await reply.main_menu(user),
    )
    if message.text == texts.Btns.back:
        await state.clear()
        await message.delete()
        await InteractiveGame().create_info(user, message=message)
    else:
        await InteractiveGame().edit(user, message, state)


@state_router.message(Offer.instruction)
async def Offer_shop(message: types.Message, state: FSMContext, user: Users):
    if message.text == texts.Btns.back:
        data = await state.get_data()
        await state.clear()
        await Shop().get_product(message, user, data["product_id"])
    else:
        if len(message.text) > 600:
            await message.bot.send_message(
                chat_id=user.user_id,
                text=texts.Shop.Error.delivery_data_too_long,
                reply_markup=await reply.back()
            )
            return
        
        data = await state.get_data()
        await state.clear()
        
        user = await Sigma_BoostsForms().add_passive_income(user)
        status, error_msg_or_product = await Shop().check_possibility_purchase(
            user, data["product_id"]
        )
        if status:
            await Shop().buy_product(message, user, error_msg_or_product, message.text)
        else:
            try:
                await message.answer(text=error_msg_or_product)
            except:
                await message.bot.send_message(
                    chat_id=user.user_id, text=error_msg_or_product
                )
