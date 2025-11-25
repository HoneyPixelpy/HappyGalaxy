from aiogram import types

import texts
from MainBot.base.forms import Sigma_BoostsForms
from config import debug
from MainBot.base.models import Users
from MainBot.base.orm_requests import Sigma_BoostsMethods
from MainBot.utils.Games import LumberjackManager, GeoHuntManager


class Boosts:

    async def catalog(
        self,
        call: types.CallbackQuery,
        user: Users
        ) -> None:
        """
        Отправляем сообщение с каталогом бустов
        """
        boosts_data: list[dict] = await Sigma_BoostsMethods().catalog_boosts(user)
        
        inline_keyboard = []
        for boost_data in boosts_data:
            inline_keyboard.append(
                [types.InlineKeyboardButton(
                    text=texts.Boosts.Btns.__dict__[boost_data['name']].format(now=boost_data['value'], max=boost_data['max_level']),
                    callback_data="get_boost|{}".format(boost_data['name'])
                )]
            )
        else:
            inline_keyboard.append(
                [
                    types.InlineKeyboardButton(
                        text=texts.Btns.back,
                        callback_data="get_boost|back"
                    )
                ]
            )
        
        text = texts.Boosts.Texts.catalog.format(
            nickname=user.nickname,
            user_id=user.user_id,
            starcoins=user.starcoins
        )

        try:
            await call.message.edit_text(
                text=text,
                reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=inline_keyboard
                )
            )
        except:
            await call.message.bot.send_message(
                chat_id=user.user_id,
                text=text,
                reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=inline_keyboard
                )
            )
            await call.message.delete()

    async def build_boost_text(
        self,
        emoji: str,
        price: float,
        max_level: int,
        now_level: int,
        name: str,
        user: Users
        ) -> None:
        """
        Собираем текст для сообщения с бустом.
        """
        return texts.Boosts.Texts.info.format(
                title=texts.Boosts.Btns.__dict__[name].format(now=now_level, max=max_level),
                emoji=emoji,
                now_level=now_level,
                description=texts.Boosts.Descriptions.__dict__[name].format(next_level=max_level if now_level+1 > max_level else now_level+1),
                upgrade_cost=price,
                balance=user.starcoins
            )

    async def get_boost(
        self,
        call: types.CallbackQuery,
        user: Users,
        name: str,
        alert: bool = False
        ) -> None:
        """
        Отправляем сообщение с информацией о конкретном бусте
        """
        boost_info: dict = await Sigma_BoostsMethods().info_boost(user, name)
        
        inline_keyboard = []
        if boost_info['boost_level'] < boost_info['max_level']:
            text = await self.build_boost_text(
                boost_info['emoji'],
                boost_info['price'],
                boost_info['max_level'],
                boost_info['boost_level'],
                name,
                user
            )

            inline_keyboard.append(
                [
                    types.InlineKeyboardButton(
                        text=texts.Btns.buy,
                        callback_data=f"upgrade_boost|{name}"
                    )
                ]
            )
        else:
            text = "<b>"+texts.Boosts.Texts.max_level+"</b>"
            if alert:
                try:
                    await call.answer(
                        texts.Boosts.Texts.max_level,
                        show_alert=True
                    )
                    return
                except:
                    pass


        inline_keyboard.append(
            [
                types.InlineKeyboardButton(
                    text=texts.Btns.back,
                    callback_data="upgrade_boost|back"
                )
            ]
        )

        try:
            await call.message.edit_text(
                text=text,
                reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=inline_keyboard
                )
            )
        except:
            await call.message.bot.send_message(
                chat_id=user.user_id,
                text=text,
                reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=inline_keyboard
                )
            )
            await call.message.delete()

    async def upgrade_boost(
        self,
        call: types.CallbackQuery,
        user: Users,
        name: str
        ) -> None:
        """
        Отправляем сообщение с информацией о конкретном бусте
        """
        upgrade_data: dict = await Sigma_BoostsForms().upgrade(
            user=user,
            name=name
        )
        if not debug:
            if not upgrade_data:
                try:
                    await call.answer(
                        texts.Shop.Error.not_enough_starcoins,
                        show_alert=True
                    )
                except:
                    await call.message.bot.send_message(
                        chat_id=user.user_id,
                        text=texts.Shop.Error.not_enough_starcoins,
                    )
                return

        if upgrade_data:
            await LumberjackManager().force_update_energy(user)
            await GeoHuntManager().force_update_energy(user)
            try:
                await call.answer(
                    text=texts.Boosts.Texts.success.format(
                        emoji=upgrade_data['emoji'],
                        level=upgrade_data['level']
                        ),
                    show_alert=True
                )
            except:
                await call.message.bot.send_message(
                    chat_id=user.user_id,
                    text=texts.Boosts.Texts.success.format(
                        emoji=upgrade_data['emoji'],
                        level=upgrade_data['level']
                        )
                )
            await self.get_boost(call, upgrade_data['user'], name)
        else:
            await call.message.bot.send_message(
                chat_id=user.user_id,
                text=texts.Error.Notif.undefined_error
            )



