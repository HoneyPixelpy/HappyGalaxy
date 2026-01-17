from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from loguru import logger
from MainBot.filters.chat_types import IsAdmin
from MainBot.utils.Forms import Shop
from config import shop_chat


shop_router = Router(name=__name__)
shop_router.message.filter(IsAdmin(), F.chat.id == int(shop_chat))


@shop_router.message(F.reply_to_message)
async def admin_reply_handler(message: types.Message, state: FSMContext):
    answer_message_id = message.reply_to_message.message_id
    logger.debug(answer_message_id)
    await Shop().answer_buy(message, state, answer_message_id)
