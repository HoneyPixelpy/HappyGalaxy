from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from GPTBot.keyboards.inline import main_menu
from GPTBot.state.state import DialogStates
from loguru import logger
from MainBot.filters.chat_types import ChatTypeFilter

callback_router = Router(name=__name__)
callback_router.message.filter(ChatTypeFilter(["private"]))

# @callback_router.callback_query(lambda c: c.data == "reset_dialog")
# async def reset_dialog_callback(call: types.CallbackQuery, state: FSMContext):
#     # reset_limits(call.from_user.id)
#     await state.clear()
#     try:
#         await call.message.edit_text(
#             "<b>Диалог успешно перезапущен!</b>\n\n<b>💡 Выберите тип генерации:</b>",
#             reply_markup=main_menu()
#         )
#     except:
#         await call.bot.send_message(
#             chat_id=call.from_user.id,
#             text="<b>Диалог успешно перезапущен!</b>\n\n<b>💡 Выберите тип генерации:</b>",
#             reply_markup=main_menu()
#         )
#         await call.message.delete()


@callback_router.callback_query(lambda c: c.data == "gen_text")
async def gen_text_callback(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(DialogStates.waiting_text_prompt)
    try:
        await call.message.edit_text(
            "<b>🚀 Генерация Текста\n\n✏️ Напишите Ваш запрос:</b>",
            reply_markup=main_menu(),
        )
    except: # exceptions.TelegramBadRequest
        await call.bot.send_message(
            chat_id=call.from_user.id,
            text="<b>🚀 Генерация Текста\n\n✏️ Напишите Ваш запрос:</b>",
            reply_markup=main_menu(),
        )
        await call.message.delete()


@callback_router.callback_query(lambda c: c.data == "gen_image")
async def gen_image_callback(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(DialogStates.waiting_image_prompt)
    try:
        await call.message.edit_text(
            "<b>🚀 Генерация Картинки\n\n✏️ Напишите Ваш запрос:</b>",
            reply_markup=main_menu(),
        )
    except: # exceptions.TelegramBadRequest
        await call.bot.send_message(
            chat_id=call.from_user.id,
            text="<b>🚀 Генерация Картинки\n\n✏️ Напишите Ваш запрос:</b>",
            reply_markup=main_menu(),
        )
        await call.message.delete()
