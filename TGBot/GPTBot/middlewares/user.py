from typing import Any, Awaitable, Callable, Dict, Optional

import texts
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from GPTBot.utils import check_tg_invite
from loguru import logger
from MainBot.base.models import Users
from MainBot.base.orm_requests import UserMethods
from MainBot.utils.errors import InternalServerError


class UserDataSession(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        try:
            print(event.event.chat.id)
        except:
            pass

        if event.event_type == "callback_query":
            message: Message = event.callback_query.message
            from_user = event.callback_query.from_user
        else:
            message: Message = event.message
            from_user = event.message.from_user

        try:
            user = await self.check_registration(from_user.id)
        except InternalServerError:
            await message.bot.send_message(from_user.id, texts.Error.Notif.server_error)
            return

        logger.debug(user)

        if not user or not user.authorised or not await check_tg_invite(user.user_id):
            await message.bot.send_message(
                chat_id=message.from_user.id,
                text=(
                    "<b>"
                    "⚠️ Для бесплатного использования бота «Счастливый GPT» необходимо иметь"
                    " <a href='https://t.me/happiness34vlz/47'>Галактический Паспорт</a>"
                    " и быть подписанным на <a href='https://t.me/happiness34vlz'>Телеграм-Канал</a>:\n"
                    "\n"
                    "Проще говоря:\n"
                    "1️⃣ Подпишитесь на канал @happiness34vlz\n"
                    "2️⃣ Зарегистрируйтесь в игре @happygalaxy_bot\n"
                    "\n"
                    "После выполненных действий нажмите или напишите /start\n"
                    "</b>"
                ),
                disable_web_page_preview=True,
            )
            return

        if user.ban:
            return

        data["user"] = user
        return await handler(event, data)

    async def check_registration(self, user_id: int) -> Optional[Users]:
        return await UserMethods().get_by_user_id(user_id=user_id)
