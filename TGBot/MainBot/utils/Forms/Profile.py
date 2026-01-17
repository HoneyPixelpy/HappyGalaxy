import asyncio
from datetime import datetime
from html import escape
from typing import Any, AsyncGenerator, Coroutine, List, Optional, Tuple

import pytz
from MainBot.utils.MyModule.message import MessageManager
import texts
from aiogram import Bot, exceptions, types
from config import bot_name, log_chat
from loguru import logger
from MainBot.base.models import RewardData, Users
from MainBot.base.orm_requests import DataMethods, PurchasesMethods, UserMethods
from MainBot.keyboards import inline, reply, selector
from MainBot.utils.Forms.Season import Season
from MainBot.utils.MyModule import Func


class Profile:

    async def new_user_in_log(self, bot: Bot, user: Users) -> None:
        """
        Отправляем сообщение с информацией о пользователе
        """
        await bot.send_message(
            chat_id=log_chat,
            text=texts.Profile.Texts.log_info.format(
                user_id=str(user.user_id),
                username=str(user.tg_username),
                names=await Func.format_tg_names(
                    escape(user.tg_first_name),
                    escape(user.tg_last_name) if user.tg_last_name else None,
                ),
                gender=await Func.gender_name(user.gender, user.role_private),
                age=(datetime.now(pytz.timezone("Europe/Moscow")) - user.age).days
                // 365,
                title="Имя" if user.role_private == "child" else "ФИО",
                supername=str(user.supername),
                name=str(user.name),
                nickname=user.nickname,
                phone=str(user.phone),
                referal_id=(
                    user.referral_user_id if user.referral_user_id else "Без реферала"
                ),
                role=user.role,
            ),
            disable_web_page_preview=True,
        )

    async def user_info_msg(
        self,
        message: types.Message | types.CallbackQuery,
        user: Users
    ) -> None:
        """
        Отправляем сообщение с информацией о пользователе
        """
        user_upgrade: dict = await Season().get_upgrade_point(user)
        
        if isinstance(message, types.Message):
            message_id = message.message_id
        else:
            message_id = message.message.message_id

        await MessageManager(
            message,
            user.user_id
        ).send_or_edit(
            texts.Profile.Texts.info.format(
                upgrade_emoji=user_upgrade.emoji,
                upgrade_name=user_upgrade.name,
                msg_id=message_id + 1,
                type_name=user.role_name.replace(" Галактики", ""),
                nickname=await Func.format_nickname(
                    user.user_id, user.nickname, user.name, user.supername
                ),
                starcoins=user.starcoins,
                bot_name=bot_name
            ) + (
                texts.Profile.Texts.buy_false if user.purch_ban else texts.Profile.Texts.buy_true
            ) + texts.Profile.Texts.minultiacc,
            await inline.back_to_main(),
            "profile"
        )

    async def invite_friend_info(
        self,
        call: types.CallbackQuery,
        user: Users
        ) -> None:
        reward_data: RewardData = await DataMethods().reward()

        await MessageManager(
            call,
            user.user_id
        ).send_or_edit(
            texts.Profile.Texts.referal.format(
                add_referal=reward_data.starcoins_for_referal,
                add_referer=reward_data.starcoins_for_referer,
                referral_count=await UserMethods().get_referral_count(user.user_id),
                user_id=user.user_id,
                bot_name=bot_name
            ),
            await inline.back_to_main(),
            "invite_friend"
        )

    async def user_help_msg(self, user: Users, message: types.Message) -> None:
        """
        Отправляем сообщение с информацией о пользователе
        """
        await MessageManager(
            message,
            user.user_id
        ).send_or_edit(
            texts.Texts.help,
            await inline.back_to_main() if user.authorised else None,
            "help"
        )
        # await bot.send_message(
        #     chat_id=user.user_id,
        #     text=texts.Texts.help,
        #     reply_markup=await selector.main_menu(user) if user.authorised else None,
        #     disable_web_page_preview=True,
        # )

    async def find_user(
        self, user_id: int
    ) -> Tuple[Optional[str], Optional[types.InlineKeyboardMarkup]]:
        """
        Отправляем сообщение с информацией о пользователе
        """
        target_user = await UserMethods().get_by_user_id(user_id)
        if not target_user:
            return (texts.Error.Notif.user_not_found, await reply.amdin_markup())

        ban_text = "Разбанить" if target_user.ban else "Забанить"
        inline_keyboard_list = [
            [
                types.InlineKeyboardButton(
                    text="Написать пользователю",
                    callback_data=f"send_msg_user|{target_user.user_id}",
                ),
                types.InlineKeyboardButton(
                    text="Изменить Старкоины",
                    callback_data=f"change_balance|{target_user.user_id}",
                ),
            ],
            [
                types.InlineKeyboardButton(
                    text="Покупки",
                    callback_data=f"purchases_tasks|{target_user.user_id}",
                ),
                types.InlineKeyboardButton(
                    text=ban_text, callback_data=f"ban_user|{target_user.user_id}"
                ),
            ],
            [
                types.InlineKeyboardButton(
                    text="Откатить регистрацию",
                    callback_data=f"rollback_registration|{target_user.user_id}",
                )
            ],
        ]

        purchases = await PurchasesMethods().get_user_purchases(target_user, True)

        text = str(texts.Admin.Texts.info).format(
            user_id=target_user.user_id,
            username=target_user.tg_username,
            first_name=escape(target_user.tg_first_name),
            last_name=(
                escape(target_user.tg_last_name) if target_user.tg_last_name else None
            ),
            role=target_user.role,
            nickname=target_user.nickname,
            title="Имя" if target_user.role_private == "child" else "ФИО",
            supername=target_user.supername,
            name=target_user.name,
            gender=await Func.gender_name(
                target_user.gender, str(target_user.role_private)
            ),
            age=(datetime.now(pytz.timezone("Europe/Moscow")) - target_user.age).days
            // 365,
            phone=target_user.phone,
            starcoins=target_user.starcoins,
            all_purchases=len(purchases),
            active_purchases=len(
                [purchase for purchase in purchases if not purchase.completed]
            ),
            count_referrers=await UserMethods().get_referral_count(target_user.user_id),
            created_at=await Func.format_date(target_user.created_at),
            authorised_at=(
                await Func.format_date(target_user.authorised_at)
                if target_user.authorised_at
                else "Не авторизован"
            ),
            ban_emoji="⛔️" if target_user.ban else "✖️",
        )

        return text, types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard_list)

    async def rollback_registration(
        self, call: types.CallbackQuery, target_user_id: int
    ) -> str:
        """
        Откатываем регистрацию.
        """
        user = await UserMethods().get_by_user_id(target_user_id)
        user = await UserMethods().complete_registration(
            user,
            state_data={
                "role": user.role_private,
                "gender": user.gender,
                "age": user.age,
                "name": None,
                "supername": None,
                "nickname": None,
                "phone": None,
                "authorised": False,
                "authorised_at": None,
            },
            rollback=True,
        )

        text, keyboard = await self.find_user(target_user_id)
        try:
            await call.message.edit_text(text=text, reply_markup=keyboard)
        except: # exceptions.TelegramBadRequest
            await call.message.bot.send_message(
                chat_id=call.from_user.id, text=text, reply_markup=keyboard
            )
            await call.message.delete()

    async def change_user_balance(self, user_id: int, new_balance: float) -> str:
        """
        Изменяем баланс старкоинов пользователя.
        """
        new_starcoins = await UserMethods().update_balance(user_id, new_balance)
        if not new_starcoins:
            raise Exception(f"Response = {str(new_starcoins)}")
        return str(texts.Admin.Texts.new_balance_this).format(new_starcoins)

    async def get_banned_users(
        self,
    ) -> List[int]:
        """
        Получаем забаненных пользователей.
        """
        banned_users = await UserMethods().get_banned_users()
        logger.debug(banned_users)
        return banned_users

    async def change_ban_user(self, user_id: int, ban: bool) -> None:
        """
        Снимаем бан.
        """
        result = await UserMethods().update_ban(user_id, ban)
        if result:
            if ban:
                logger.info(f"Забанили Юзера: {user_id}")
            else:
                logger.info(f"Разбанили Юзера: {user_id}")
        else:
            logger.error(f"Бан не изменен: {user_id}")

    async def get_purchases_by_user(
        self, target_user_id: int
    ) -> List[Tuple[Optional[str], Optional[types.InlineKeyboardMarkup]]]:
        """
        Получаем таски юзера на выплату.
        """
        user = await UserMethods().get_by_user_id(target_user_id)
        purchases = await PurchasesMethods().get_user_purchases(user)
        if not purchases:
            return [(texts.Admin.Texts.no_tasks, None)]

        result = []
        for purchas in purchases:
            result.append(
                (
                    str(texts.Admin.FindUser.purchas).format(
                        title=purchas.title,
                        description=purchas.description,
                        price=purchas.cost,
                        purchase_date=(
                            purchas.purchase_date.strftime("%d %m %Y")
                            if purchas.purchase_date
                            else "..."
                        ),
                    ),
                    types.InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                types.InlineKeyboardButton(
                                    text="Закрыть заказ и Уведомить",
                                    callback_data=f"delete_purchas|{purchas.id}|{target_user_id}|yes",
                                )
                            ],
                            [
                                types.InlineKeyboardButton(
                                    text="Закрыть заказ",
                                    callback_data=f"delete_purchas|{purchas.id}|{target_user_id}|",
                                )
                            ],
                            [
                                types.InlineKeyboardButton(
                                    text="Удалить сообщение", callback_data="exit"
                                )
                            ],
                        ]
                    ),
                )
            )
        else:
            return result

    async def delete_output_task(
        self,
        call: types.CallbackQuery,
        target_user_id: int,
        task_id: int,
        bool_send_msg: bool,
    ) -> None:
        """
        Удаляем эту таску.
        """
        purchas = await PurchasesMethods().confirm_purchase(task_id)
        if purchas:
            if bool_send_msg:
                try:
                    await call.message.bot.send_message(
                        chat_id=target_user_id,
                        text=str(texts.Admin.FindUser.confirm_purchas).format(
                            title=purchas.title, description=purchas.description
                        ),
                    )
                except Exception as ex: # exceptions.TelegramBadRequest
                    logger.exception(str(ex))
        else:
            logger.error(f"Response = {purchas}")

    async def get_all_output_tasks(
        self,
    ) -> AsyncGenerator[
        Tuple[Optional[str], Optional[types.InlineKeyboardMarkup]], None
    ]:
        """
        Получаем все таски.
        """
        purchases = await PurchasesMethods().get_all_purchases()

        tasks_found = False
        for purchas in purchases:
            tasks_found = True
            yield (
                texts.Admin.FindUser.purchas.format(
                    title=purchas.title,
                    description=purchas.description,
                    price=purchas.cost,
                    purchase_date=(
                        purchas.purchase_date.strftime("%d %m %Y")
                        if purchas.purchase_date
                        else "..."
                    ),
                ),
                types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(
                                text="Закрыть заказ и Уведомить",
                                callback_data=f"delete_purchas|{purchas.id}|{purchas.user.user_id}|yes",
                            )
                        ],
                        [
                            types.InlineKeyboardButton(
                                text="Закрыть заказ",
                                callback_data=f"delete_purchas|{purchas.id}|{purchas.user.user_id}|",
                            )
                        ],
                        [
                            types.InlineKeyboardButton(
                                text="Удалить сообщение", callback_data="exit"
                            )
                        ],
                    ]
                ),
            )
        else:
            if tasks_found:
                yield (texts.Admin.Texts.this_all_tasks, None)
            else:
                yield (texts.Admin.Texts.all_no_tasks, None)

    async def notification_referal(
        self, message: types.Message, user: Users
    ) -> Optional[bool]:
        """
        Уведомляем реферера о регистрации
        пользователя по его реферальной ссылке
        Даем бонус за регистрацию рефереру
        """
        referal_user = await UserMethods().process_referral(user.user_id)
        if referal_user:
            if referal_user["new_ref_connection"]:
                reward_data: RewardData = await DataMethods().reward()
                await message.bot.send_message(
                    chat_id=referal_user["user_id"],
                    text=texts.Profile.Texts.success_referal.format(
                        starcoins=reward_data.starcoins_for_referer
                    ),
                )
            return True

    async def notification_parent(
        self, message: types.Message, user: Users, parent_user: Optional[Users] = None
    ) -> Optional[bool]:
        """
        После сохнарения в базе для семьи
        уведомляем пригласившего и того кто пригласил
        """
        await message.bot.send_message(
            chat_id=user.user_id, text=texts.Family_Ties.Texts.success_parent
        )

        await message.bot.send_message(
            chat_id=parent_user.user_id, text=texts.Family_Ties.Texts.success_parent
        )
        return True

    async def mailing(
        self,
        message: types.Message,
        mailing_func: Coroutine[Any, Any, types.Message],
        **kwargs,
    ):
        await message.answer(
            "Рассылка запущена", reply_markup=await reply.amdin_markup()
        )
        msg = await message.answer("Гоу")

        users = await UserMethods().get_all_users(**kwargs)
        number = 0

        for user in users:
            if not user.authorised or user.ban:
                continue
            try:
                await mailing_func(user)
                number += 1
                if number % 10 == 0:
                    await message.bot.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=msg.message_id,
                        text=f"Юзеров получило уже - {number}",
                    )
                await asyncio.sleep(0.3)
            except exceptions.TelegramRetryAfter as ex:
                logger.error(f"Сработало исключение!!!\n!!!{ex}")
                # await asyncio.sleep(ex.retry_after)
                continue
            except Exception as ex: # exceptions.TelegramBadRequest
                logger.error(f"Сработало исключение!!!\n!!!{ex}")
                continue
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=msg.message_id,
            text=f"💡 <b>РАССЫЛКА ВЫПОЛНЕНА</b> 💡\n\n<i>Рассылку получило: {number} /челбанов</i>",
        )
