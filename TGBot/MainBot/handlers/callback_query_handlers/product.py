from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from loguru import logger
from MainBot.base.forms import Sigma_BoostsForms
from MainBot.base.models import Users
from MainBot.filters.chat_types import ChatTypeFilter
from MainBot.state.state import Offer
from MainBot.utils.Forms import (
    Shop,
)

product_router = Router(name=__name__)
product_router.message.filter(ChatTypeFilter(["private"]))


@product_router.callback_query(F.data.startswith("all_products"))
async def all_products(call: types.CallbackQuery, user: Users, state: FSMContext):
    await state.clear()
    await Shop().catalog(
        user,
        call=call,
        pagination=int(call.data.split("|")[1]) if "|" in call.data else None,
    )


@product_router.callback_query(F.data.startswith("get_product|"))
async def get_product(call: types.CallbackQuery, user: Users, state: FSMContext):
    await state.clear()
    product_id = int(call.data.split("|")[1])
    await Shop().get_product(call.message, user, product_id)


@product_router.callback_query(F.data.startswith("buy_product|"))
async def buy_product(call: types.CallbackQuery, user: Users, state: FSMContext):
    product_id = call.data.split("|")[1]
    logger.debug(product_id)
    if product_id == "back":
        await Shop().catalog(user, call=call)
    else:
        instructions = bool(call.data.split("|")[2])
        logger.debug(instructions)
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
                except: # exceptions.TelegramBadRequest
                    await call.message.bot.send_message(
                        chat_id=user.user_id, text=error_msg_or_product
                    )


@product_router.callback_query(F.data.startswith("success_buy|"))
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


@product_router.callback_query(F.data.startswith("rollback_buy|"))
async def rollback_buy(call: types.CallbackQuery, user: Users, state: FSMContext):
    purchases_id = call.data.split("|")[1]
    await Shop().rollback_buy(
        call, user, purchases_id
        )


@product_router.callback_query(F.data.startswith("confirm_buy|"), Offer.confirm)
async def confirm_buy(call: types.CallbackQuery, user: Users, state: FSMContext):
    solution = call.data.split("|")[1]
    data = await state.get_data()
    await state.clear()
    
    match solution:
        case "yes":
            user = await Sigma_BoostsForms().add_passive_income(user)
            status, error_msg_or_product = await Shop().check_possibility_purchase(
                user, data["product_id"]
            )
            if status:
                await Shop().buy_product(call.message, user, error_msg_or_product, data["instructions"], data["delivery_data"])
            else:
                try:
                    await call.message.answer(text=error_msg_or_product)
                except: # exceptions.TelegramBadRequest
                    await call.bot.send_message(
                        chat_id=user.user_id, text=error_msg_or_product
                    )
        case "no":
            await Shop().get_product(call.message, user, data["product_id"])


@product_router.callback_query(F.data.startswith("write_offer|"))
async def write_offer(call: types.CallbackQuery, user: Users, state: FSMContext):
    _type = call.data.split("|")[1]
    if _type == "shop":
        await Shop().write_offer(call, user, state)


