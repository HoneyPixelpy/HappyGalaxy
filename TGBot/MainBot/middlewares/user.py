import asyncio
from typing import Any, Awaitable, Callable, Dict, Optional

import texts
from aiogram import BaseMiddleware, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject, User
from config import admins
from loguru import logger
from MainBot.base.models import Users
from MainBot.base.orm_requests import UserMethods
from MainBot.utils.errors import InternalServerError
from MainBot.utils.Forms import Authorisation, FamilyTies, UTMLinksForm
from MainBot.utils.Rabbitmq import RabbitMQ


class UserDataSession(BaseMiddleware):
    """
    Нету работы с персоналом !!!

    Args:
        BaseMiddleware (_type_): _description_
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        try:
            logger.debug(event.event.chat.id)
        except:
            pass

        try:
            logger.debug(event.message.reply_to_message.message_id)
        except:
            pass

        if event.event_type == "callback_query":
            message = event.callback_query.message
            from_user = event.callback_query.from_user
        else:
            message = event.message
            from_user = event.message.from_user

        state: FSMContext = data["state"]
        state_now: Optional[str] = await state.get_state()

        if (
            message.text
            and (message.text == "/start" or message.text == "/work")
            and message.chat.type == "private"
        ):
            if await self.check_registration_mode(state_now):
                return
            await state.clear()

        try:
            user = await self.check_registration(from_user.id)
        except InternalServerError:
            await message.bot.send_message(from_user.id, texts.Error.Notif.server_error)
            return

        if user and user.ban:
            return

        if not user:
            try:
                ref_str = message.text[7:]
                if "add_family_" in ref_str:
                    ref_str = ref_str.replace("add_family_", "")
            except:
                ref_str = ""

            user = await self.registration_user(from_user, ref_str)
        else:
            await self.update_tg_username(user, from_user)

        # NOTE тут собираем данные о действии
        asyncio.create_task(RabbitMQ().track_action(event, message, from_user))

        if message.text and "/start" in message.text and message.text[7:]:
            await self.utm_activate(user, message.text[7:])

        try:
            if "add_family_" in message.text[7:]:
                await FamilyTies().add_parent(
                    message=message,
                    user=user,
                    parent_user_id=message.text[7:].replace("add_family_", ""),
                )
        except Exception as ex:
            # logger.exception(str(ex))
            pass

        if (
            not await self.check_registration_mode(state_now)
            and not user.authorised
            and (message.text and "/work" not in message.text)
            and message.chat.type == "private"
            and event.event_type != "callback_query"  # and
            # not await self.check_admins(from_user.id)
        ):
            bot: Bot = data["bot"]
            await Authorisation.hello(bot, state, user)
            return

        data["user"] = user
        await state.update_data(user=user)
        return await handler(event, data)

    async def update_tg_username(self, user: Users, from_user: User) -> None:
        if from_user.username and user.tg_username != from_user.username:
            await UserMethods().update_username(user, from_user.username)

    async def utm_activate(self, user: Users, url_data: str) -> None:
        await UTMLinksForm().activate(user, url_data)

    async def check_admins(self, user_id: int) -> Optional[bool]:
        if user_id in admins:
            return True

    async def check_registration(self, user_id: int) -> Optional[Users]:
        return await UserMethods().get_by_user_id(user_id=user_id)

    async def registration_user(self, user_data: User, referral_user_id: str) -> Users:
        result_referral = None
        if (
            referral_user_id
            and referral_user_id.isdigit()
            and int(referral_user_id) != user_data.id
        ):
            result_referral = int(referral_user_id)

        return await UserMethods().create(user_data, result_referral)

    async def check_registration_mode(self, state_now: Optional[str]) -> Optional[bool]:
        if state_now and (
            "Auth_state" in state_now
            or "RegPersonal" in state_now
            or "RegPersonal_state" in state_now
        ):
            return True
