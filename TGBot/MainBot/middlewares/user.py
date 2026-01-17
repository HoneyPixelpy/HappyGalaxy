import asyncio
from typing import Any, Awaitable, Callable, Dict, Optional, Union

import texts
from aiogram import BaseMiddleware, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject, User, Message
from config import admins
from loguru import logger
from MainBot.base.models import Users
from MainBot.base.orm_requests import IdempotencyKeyMethods, UserMethods
from MainBot.utils.errors import (
    DuplicateOperationError, InternalServerError, ServerError, UndefinedError)
from MainBot.utils.Forms import Authorisation, FamilyTies, UTMLinksForm
from MainBot.utils.Rabbitmq import RabbitMQ


class UserDataSession(BaseMiddleware):
    """
    Нету работы с персоналом !!!
    """
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        return await CustomMiddleware(handler, event, data).start()


class CustomMiddleware:
    
    def __init__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
        ):
        self.handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]] = handler
        self.event: TelegramObject = event
        self.data: Dict[str, Any] = data
        
        if self.event.event_type == "callback_query":
            self.message: Message = self.event.callback_query.message
            self.from_user: User = self.event.callback_query.from_user
        else:
            self.message: Message = self.event.message
            self.from_user: User = self.event.message.from_user
        
        super().__init__()

    async def start(self) -> Any:
        await self.debug()
        
        state: FSMContext = self.data["state"]
        state_now: Optional[str] = await state.get_state()

        user = await self.check_reg(state_now, state)
        
        if isinstance(user, bool) and user == False: return

        if user and user.ban:
            return

        user = await self.username(user)

        # NOTE тут собираем данные о действии
        asyncio.create_task(RabbitMQ().track_action(self.event, self.message, self.from_user))

        await self.utm(user)

        await self.add_family(user)

        if await self.authorisation(state_now, user, state): return

        self.data["user"] = user
        await state.update_data(user=user)
        
        await self.main()

    async def main(self) -> Any:
        try:
            return await self.handler(self.event, self.data)
        except (UndefinedError, ServerError) as ex:
            await ex.send(self.message)
        except DuplicateOperationError:
            if self.event.event_type == "callback_query":
                await self.event.callback_query.answer(
                    text=texts.Error.Notif.loading
                )
            else:
                new_message = await self.message.answer(
                    text=texts.Error.Notif.loading
                )
                await asyncio.sleep(5)
                await new_message.delete()
        except Exception as ex:
            await UndefinedError(
                ex,
                "Поймали в самом низу"
            ).send(self.message)

    async def check_reg(self, state_now, state) -> Union[Optional[Users],bool]:
        if (
            self.message.text
            and (self.message.text == "/start" or self.message.text == "/work")
            and self.message.chat.type == "private"
        ):
            if await self.check_registration_mode(state_now):
                return False
            await state.clear()

        try:
            return await self.check_registration(self.from_user.id)
        except InternalServerError:
            await self.message.bot.send_message(self.from_user.id, texts.Error.Notif.server_error)
            return False

    async def authorisation(self, state_now, user, state) -> Optional[bool]:
        if (
            not await self.check_registration_mode(state_now)
            and not user.authorised
            and (self.message.text and "/work" not in self.message.text)
            and self.message.chat.type == "private"
            and self.event.event_type != "callback_query"  # and
            # not await self.check_admins(from_user.id)
        ):
            bot: Bot = self.data["bot"]
            await Authorisation.hello(bot, state, user)
            return True
        
    async def debug(self) -> None:
        try:
            logger.debug(self.event.event.chat.id)
        except: pass
        try:
            logger.debug(self.event.message.reply_to_message.message_id)
        except: pass
        try:
            logger.debug(self.message.edit_date)
        except: pass
        try:
            logger.debug(self.message.date.timestamp())
        except: pass
        
    async def username(self, user) -> Users:
        if not user:
            try:
                ref_str = self.message.text[7:]
                if "add_family_" in ref_str:
                    ref_str = ref_str.replace("add_family_", "")
            except:
                ref_str = ""

            return await self.registration_user(self.from_user, ref_str)
        else:
            await self.update_tg_username(user, self.from_user)
            return user
        
    async def add_family(self, user: Users) -> None:
        try:
            if "add_family_" in self.message.text[7:]:
                await FamilyTies(user.role_private).add_parent(
                    message=self.message,
                    user=user,
                    parent_user_id=self.message.text[7:].replace("add_family_", ""),
                )
        except Exception as ex:
            # logger.error(str(ex))
            pass
        
    async def utm(self, user: Users) -> None:
        if self.message.text and "/start" in self.message.text and self.message.text[7:]:
            await self.utm_activate(user, self.message.text[7:])
        
    async def update_tg_username(self, user: Users, from_user: User) -> None:
        if from_user.username and user.tg_username != from_user.username:
            await UserMethods().update_username(user, from_user.username)

    async def utm_activate(self, user: Users, url_data: str) -> None:
        await UTMLinksForm().activate(
            user,
            self.message,
            url_data
        )

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

        return await UserMethods().create(
            user_data,
            result_referral,
            idempotency_key=await IdempotencyKeyMethods.IKgenerate(user_data.id, self.message)
            )

    async def check_registration_mode(self, state_now: Optional[str]) -> Optional[bool]:
        if state_now and (
            "Auth_state" in state_now
            or "RegPersonal" in state_now
            or "RegPersonal_state" in state_now
        ):
            return True
