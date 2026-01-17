from typing import Any, Coroutine

import texts
from aiogram import F, Router, exceptions, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from loguru import logger
from MainBot.base.forms import Sigma_BoostsForms
from MainBot.base.models import Users
from MainBot.filters.chat_types import ChatTypeFilter, IsAdmin
from MainBot.handlers.message_handlers import text_over
from MainBot.keyboards import reply
from MainBot.state.state import CreateBonus, FindUser, Mailing
from MainBot.utils.Forms import BonusBoosters, PersonalForms, Profile, Menu
from MainBot.utils.MyModule import Func


admin_router = Router(name=__name__)
admin_router.message.filter(IsAdmin(), ChatTypeFilter(["private"]))


@admin_router.message(
    StateFilter(None),
    F.content_type.in_(
        {
            "animation",
            "audio",
            "document",
            "photo",
            "sticker",
            "video",
            "video_note",
            "voice",
            "contact",
            "location",
            "venue",
            "poll",
            "dice",
            "game",
            "emoji",
        }
    ),
)
async def cmd_animation(message: types.Message) -> None:
    logger.info(message)
    logger.info(message.message_id)
    try:
        if message.photo:
            """
            Фото с текстом
            """
            media_content = message.photo[-1].file_id
            media_type = "photo"
            await message.answer_photo(photo=media_content)
        elif message.animation:
            """
            Гифка с текстом
            """
            media_content = message.animation.file_id
            media_type = "animation"
            await message.answer_animation(animation=media_content)
        elif message.video:
            """
            Видео с текстом
            """
            media_content = message.video.file_id
            media_type = "video"
            await message.answer_video(video=media_content)
        elif message.document:
            """
            Документ с текстом
            """
            media_content = message.document.file_id
            media_type = "document"
            await message.answer_document(document=media_content)
        elif message.audio:
            """
            Аудио файл с текстом
            """
            media_content = message.audio.file_id
            media_type = "audio"
            await message.answer_audio(audio=media_content)
        elif message.sticker:
            """
            Без текста, просто стикер БЕЗ анимации
            """
            media_content = message.sticker.file_id
            media_type = "sticker"
            await message.answer_sticker(sticker=media_content)
        elif message.voice:
            """
            Голосовуха с текстом
            """
            media_content = message.voice.file_id
            media_type = "voice"
            await message.answer_voice(voice=media_content)
        elif message.video_note:
            """
            Без текста, только кружок
            """
            media_content = message.video_note.file_id
            media_type = "video_note"
            await message.answer_video_note(video_note=media_content)
        else:
            media_content = None
            media_type = None
            await message.answer(str(texts.Admin.Mailing.skip_media))
    except exceptions.TelegramBadRequest as ex:
        await message.answer(str(f"Error: {ex}"))
        return
    await message.answer(f"Идентификатор: {str(media_content)}")


@admin_router.message(FindUser.user_id)
async def find_user_id(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if data.get("message_id"):
        try:
            await message.bot.delete_message(
                message.from_user.id, data.get("message_id")
            )
        except: # exceptions.TelegramBadRequest
            pass
    if message.text == str(texts.Admin.Btns.back_to_admin):
        await message.answer(
            texts.Admin.Texts.main, reply_markup=await reply.amdin_markup()
        )
        await state.clear()
        return
    try:
        find_user_id = int(message.text)
    except: # TypeError
        await message.answer(str(texts.Error.Notif.get_number))
        return

    text, keyboard = await Profile().find_user(find_user_id)

    await message.bot.send_message(
        message.from_user.id, text=text, reply_markup=keyboard
    )
    await message.answer(
        texts.Admin.Texts.main, reply_markup=await reply.amdin_markup()
    )
    await state.clear()


@admin_router.callback_query(F.data.startswith("send_msg_user|"))
async def find_send_msg_user(call: types.CallbackQuery, state: FSMContext):
    find_user_id = int(call.data.split("|")[1])
    await call.message.delete()

    message_now = await call.message.bot.send_message(
        call.from_user.id,
        text=texts.Admin.Texts.go_send_msg,
        reply_markup=await reply.back_to_amdin_markup(),
    )
    await state.update_data(
        find_user_id=find_user_id, message_id=message_now.message_id
    )
    await state.set_state(FindUser.send_msg)


@admin_router.message(FindUser.send_msg)
async def find_send_msg(message: types.Message, state: FSMContext):
    data = await state.get_data()
    find_user_id = data["find_user_id"]
    if data.get("message_id"):
        try:
            await message.bot.delete_message(
                message.from_user.id, data.get("message_id")
            )
        except: # exceptions.TelegramBadRequest
            pass
    if message.text == str(texts.Admin.Btns.back_to_admin):
        await state.clear()
        text, keyboard = await Profile().find_user(find_user_id)

        await message.bot.send_message(
            message.from_user.id, text=text, reply_markup=keyboard
        )
        await message.answer(
            texts.Admin.Texts.main, reply_markup=await reply.amdin_markup()
        )
        return

    # TODO можем отправить только текст

    try:
        await message.bot.send_message(chat_id=find_user_id, text=message.html_text)
        await message.answer(str(texts.Admin.FindUser.message_send))
    except Exception as ex:
        logger.exception(str(ex))
        await message.answer(
            str(texts.Error.Notif.no_send_msg).format(str(ex.__class__.__name__))
        )

    text, keyboard = await Profile().find_user(find_user_id)

    await message.bot.send_message(
        message.from_user.id, text=text, reply_markup=keyboard
    )
    await message.answer(
        texts.Admin.Texts.main, reply_markup=await reply.amdin_markup()
    )
    await state.clear()


@admin_router.callback_query(F.data.startswith("change_balance|"))
async def find_change_balance(call: types.CallbackQuery, state: FSMContext):
    find_user_id = int(call.data.split("|")[1])
    await call.message.delete_reply_markup()

    message_now = await call.message.bot.send_message(
        call.from_user.id,
        text=str(texts.Admin.Texts.go_change_balance),
        reply_markup=await reply.back_to_amdin_markup(),
    )
    await state.update_data(
        find_user_id=find_user_id, message_id=message_now.message_id
    )
    await state.set_state(FindUser.change_balance)


@admin_router.message(FindUser.change_balance)
async def find_change_balance(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if data.get("message_id"):
        try:
            await message.bot.delete_message(
                message.from_user.id, data.get("message_id")
            )
        except: # exceptions.TelegramBadRequest
            pass
    if message.text == str(texts.Admin.Btns.back_to_admin):
        await state.clear()
        text, keyboard = await Profile().find_user(find_user_id)

        await message.bot.send_message(
            message.from_user.id, text=text, reply_markup=keyboard
        )
        await message.answer(
            texts.Admin.Texts.main, reply_markup=await reply.amdin_markup()
        )
        return

    find_user_id = data["find_user_id"]

    try:
        new_balance = float(message.text.replace(",", "."))
    except: # TypeError
        await message.answer(str(texts.Error.Notif.get_number))
        return

    answer_text = await Profile().change_user_balance(find_user_id, new_balance)
    await message.answer(answer_text)

    text, keyboard = await Profile().find_user(find_user_id)

    await message.bot.send_message(
        message.from_user.id, text=text, reply_markup=keyboard
    )
    await message.answer(
        texts.Admin.Texts.main, reply_markup=await reply.amdin_markup()
    )
    await state.clear()


@admin_router.callback_query(F.data.startswith("ban_user|"))
async def find_ban_user(call: types.CallbackQuery):
    find_user_id = int(call.data.split("|")[1])

    await Profile().change_ban_user(
        find_user_id,
        ban=False if find_user_id in await Profile().get_banned_users() else True,
    )

    text, keyboard = await Profile().find_user(find_user_id)

    await call.message.edit_text(text=text, reply_markup=keyboard)


@admin_router.callback_query(F.data.startswith("purchases_tasks|"))
async def find_purchases(call: types.CallbackQuery):
    find_user_id = int(call.data.split("|")[1])

    for task in await Profile().get_purchases_by_user(find_user_id):
        await call.message.bot.send_message(
            call.from_user.id, text=task[0], reply_markup=task[1]
        )


@admin_router.callback_query(F.data.startswith("delete_purchas|"))
async def delete_purchas(call: types.CallbackQuery):
    task_id = int(call.data.split("|")[1])
    target_user_id = int(call.data.split("|")[2])
    bool_send_msg = bool(call.data.split("|")[3])

    await Profile().delete_output_task(call, target_user_id, task_id, bool_send_msg)

    await call.message.bot.send_message(
        chat_id=call.from_user.id, text=str(texts.Admin.Texts.task_delete)
    )

    await call.message.delete()


@admin_router.callback_query(F.data.startswith("rollback_registration|"))
async def delete_purchas(call: types.CallbackQuery):
    target_user_id = int(call.data.split("|")[1])
    await Profile().rollback_registration(call, target_user_id)


@admin_router.message(Mailing.Pin)
async def Mailing_Pin(message: types.Message, state: FSMContext):
    if message.text == str(texts.Admin.Btns.back_to_admin):
        await message.answer(
            texts.Admin.Texts.main, reply_markup=await reply.amdin_markup()
        )
        await state.clear()
        return
    elif message.text == str(texts.Admin.Btns.yes_pin):
        await state.update_data(pin_bool=True)
    elif message.text == str(texts.Admin.Btns.no_pin):
        await state.update_data(pin_bool=False)
    else:
        await message.answer(str(texts.Error.Notif.no_btn))
        return
    data = await state.get_data()
    if data.get("message_id"):
        try:
            await message.bot.delete_message(
                message.from_user.id, data.get("message_id")
            )
        except: # exceptions.TelegramBadRequest
            pass
    message_now = await message.bot.send_message(
        chat_id=message.from_user.id,
        text=str(texts.Admin.Mailing.step_two),
        reply_markup=await reply.back_to_amdin_markup(no_media_btn=True),
    )
    await state.set_state(Mailing.Media)
    await state.update_data(message_id=message_now.message_id)


@admin_router.message(Mailing.Media)
async def Mailing_Media(message: types.Message, state: FSMContext):
    if message.text == texts.Btns.back:
        await message.answer(
            str(texts.Admin.Mailing.step_one),
            reply_markup=await reply.Pin_Mailing_markup(),
        )
        await state.set_state(Mailing.Pin)
    else:
        try:
            if message.photo:
                """
                Фото с текстом
                """
                media_content = message.photo[-1].file_id
                media_type = "photo"
                await message.answer_photo(photo=media_content)
            elif message.animation:
                """
                Гифка с текстом
                """
                media_content = message.animation.file_id
                media_type = "animation"
                await message.answer_animation(animation=media_content)
            elif message.video:
                """
                Видео с текстом
                """
                media_content = message.video.file_id
                media_type = "video"
                await message.answer_video(video=media_content)
            elif message.document:
                """
                Документ с текстом
                """
                media_content = message.document.file_id
                media_type = "document"
                await message.answer_document(document=media_content)
            elif message.audio:
                """
                Аудио файл с текстом
                """
                media_content = message.audio.file_id
                media_type = "audio"
                await message.answer_audio(audio=media_content)
            elif message.sticker:
                """
                Без текста, просто стикер БЕЗ анимации
                """
                media_content = message.sticker.file_id
                media_type = "sticker"
                await message.answer_sticker(sticker=media_content)
            elif message.voice:
                """
                Голосовуха с текстом
                """
                media_content = message.voice.file_id
                media_type = "voice"
                await message.answer_voice(voice=media_content)
            elif message.video_note:
                """
                Без текста, только кружок
                """
                media_content = message.video_note.file_id
                media_type = "video_note"
                await message.answer_video_note(video_note=media_content)
            else:
                media_content = None
                media_type = None
                await message.answer(str(texts.Admin.Mailing.skip_media))
        except exceptions.TelegramBadRequest as ex:
            await message.answer(str(f"Error: {ex}"))
            return
        data = await state.get_data()
        if data.get("message_id"):
            try:
                await message.bot.delete_message(
                    message.from_user.id, data.get("message_id")
                )
            except: # exceptions.TelegramBadRequest
                pass

        message_now = await message.bot.send_message(
            chat_id=message.from_user.id,
            text=str(texts.Admin.Mailing.step_three),
            reply_markup=await reply.back(),
        )
        await state.update_data(
            message_id=message_now.message_id,
            media_content=media_content,
            media_type=media_type,
        )
        await state.set_state(Mailing.Text)


@admin_router.message(Mailing.Text)
async def Mailing_Text(message: types.Message, state: FSMContext, user: Users):
    if message.text == texts.Btns.back:
        await message.answer(
            str(texts.Admin.Mailing.step_two),
            reply_markup=await reply.back_to_amdin_markup(no_media_btn=True),
        )
        await state.set_state(Mailing.Media)
    else:
        logger.info(len(message.html_text))
        await state.update_data(text=message.html_text)

        data = await state.get_data()
        if data.get("message_id"):
            try:
                await message.bot.delete_message(
                    message.from_user.id, data.get("message_id")
                )
            except: # exceptions.TelegramBadRequest
                pass
        mailing_func: Coroutine[Any, Any, None] = (
            await Func.constructor_func_to_mailing_one_msg(
                message.bot,
                data["media_content"],
                data["media_type"],
                data["pin_bool"],
                message.html_text,
            )
        )
        try:
            await mailing_func(user)
        except Exception as ex:
            logger.exception(str(ex))
            await message.answer(str(texts.Error.Notif.text_is_big))
            await Func.send_error_to_developer(f"{ex.__class__.__name__} {ex}")
            return

        message_now = await message.bot.send_message(
            chat_id=message.from_user.id,
            text=str(texts.Admin.Mailing.step_four),
            reply_markup=await reply.Confirm_Mailing_markup(),
        )
        await state.set_state(Mailing.Confirm)
        await state.update_data(
            mailing_func=mailing_func, message_id=message_now.message_id
        )


@admin_router.message(Mailing.Confirm)
async def Mailing_Confirm(message: types.Message, state: FSMContext):
    if message.text == texts.Btns.back:
        await message.answer(
            str(texts.Admin.Mailing.step_three), reply_markup=await reply.back()
        )
        await state.set_state(Mailing.Text)
    elif message.text == str(texts.Admin.Mailing.start_mailing):
        data = await state.get_data()
        if data.get("message_id"):
            try:
                await message.bot.delete_message(
                    message.from_user.id, data.get("message_id")
                )
            except: # exceptions.TelegramBadRequest
                pass
        mailing_func = data["mailing_func"]

        await state.clear()

        await Profile().mailing(message, mailing_func)


@admin_router.message(CreateBonus.type_bonus)
async def CreateBonus_type_bonus(
    message: types.Message, state: FSMContext, user: Users
):
    if message.text == texts.Admin.Btns.back_to_admin:
        await message.answer(
            texts.Admin.Texts.main, reply_markup=await reply.amdin_markup()
        )
        await state.clear()
    else:
        if message.text == texts.Admin.Bonus.add_starcoins_bonus:
            await BonusBoosters().size_starcoins_bonus(message, user, state)
        elif message.text == texts.Admin.Bonus.scale_clicks_bonus:
            await BonusBoosters().scale_clicks_bonus(message, user, state)
        elif message.text == texts.Admin.Bonus.energy_renewal_bonus:
            await BonusBoosters().energy_renewal_bonus(message, user, state)
        else:
            await message.answer(str(texts.Error.Notif.no_btn))


@admin_router.message(CreateBonus.size_starcoins)
async def CreateBonus_size_starcoins(
    message: types.Message, state: FSMContext, user: Users
):
    if message.text == texts.Btns.back:
        await BonusBoosters().type_bonus(message, user, state)
        return
    elif message.text.isdigit():
        await BonusBoosters().max_quantity_bonus(
            message, user, state, {"size_starcoins": int(message.text)}
        )
    else:
        await message.answer(str(texts.Error.Notif.get_number))
        return


@admin_router.message(CreateBonus.max_quantity)
async def CreateBonus_max_quantity(
    message: types.Message, state: FSMContext, user: Users
):
    if message.text == texts.Btns.back:
        await BonusBoosters().size_starcoins_bonus(message, user, state)
        return
    elif message.text.isdigit():
        await BonusBoosters().expires_at_hours_bonus(
            message, user, state, {"max_quantity": int(message.text)}
        )
    else:
        await message.answer(str(texts.Error.Notif.get_number))
        return


@admin_router.message(CreateBonus.click_scale)
async def CreateBonus_click_scale(
    message: types.Message, state: FSMContext, user: Users
):
    if message.text == texts.Btns.back:
        await BonusBoosters().type_bonus(message, user, state)
        return
    else:
        try:
            await BonusBoosters().expires_at_hours_bonus(
                message, user, state, {"click_scale": float(message.text)}
            )
        except ValueError:
            await message.answer(str(texts.Error.Notif.get_number))
            return


@admin_router.message(CreateBonus.expires_at_hours)
async def CreateBonus_expires_at_hours(
    message: types.Message, state: FSMContext, user: Users
):
    if message.text == texts.Btns.back:
        await BonusBoosters().type_bonus(message, user, state)
        return
    else:
        try:
            await BonusBoosters().create_bonus(
                message, user, state, float(message.text)
            )
        except ValueError:
            await message.answer(str(texts.Error.Notif.get_number))
            return


@admin_router.message(StateFilter(None), F.text)
async def text_admin(message: types.Message, state: FSMContext, user: Users):
    # Админка
    logger.info(message.text)
    if message.text.lower() in ["admin", "/admin", "админ", "админка"]:
        await message.answer(
            texts.Admin.Texts.main, reply_markup=await reply.amdin_markup()
        )
    match message.text:
        case str(texts.Admin.Btns.back_to_main):
            await Menu().main_menu(
                message,
                user
            )
        case str(texts.Admin.Btns.back_to_admin):
            await message.answer(
                texts.Admin.Texts.main, reply_markup=await reply.amdin_markup()
            )
        case str(texts.Admin.Btns.find_user):
            await state.set_state(FindUser.user_id)
            message_now = await message.bot.send_message(
                message.from_user.id,
                text=str(texts.Admin.FindUser.start_text),
                reply_markup=await reply.back_to_amdin_markup(),
            )
            await state.update_data(message_id=message_now.message_id)
        case str(texts.Admin.Btns.mailing):
            message_now = await message.bot.send_message(
                chat_id=message.from_user.id,
                text=str(texts.Admin.Mailing.step_one),
                reply_markup=await reply.Pin_Mailing_markup(),
            )
            await state.set_state(Mailing.Pin)
            await state.update_data(message_id=message_now.message_id)
        case str(texts.Admin.Btns.all_tasks):
            async for text, keyboard in Profile().get_all_output_tasks():
                await message.bot.send_message(
                    message.from_user.id, text=text, reply_markup=keyboard
                )
        case str(texts.Admin.Btns.generate_key):
            text = await PersonalForms().generate_key()
            await message.answer(text)
        case str(texts.Admin.Btns.bonus_boost):
            await BonusBoosters().type_bonus(message, user, state)

    await text_over(message, user)
