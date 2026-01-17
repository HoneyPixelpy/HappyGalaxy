from datetime import datetime
from typing import List

import texts as tx
from aiogram import types
from MainBot.base.models import Rangs, Users
from MainBot.base.orm_requests import RangsMethods
from MainBot.utils.MyModule.message import MessageManager
from MainBot.keyboards import inline


class Season:

    async def get_upgrade_list(self, user: Users) -> List[Rangs]:
        """
        Получаем список с улучшениями
        """
        try:
            return await RangsMethods().get_by_role(user.role_private)
        except: # Safe
            return [
                Rangs(
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    id=1,
                    all_starcoins=0,
                    role_private=None,
                    role=None,
                    role_name=None,
                    emoji="❔",
                    name="Незнакомец",
                )
            ]

    async def get_upgrade_point(self, user: Users) -> dict:
        """
        Показываем данные о нашем уровне.
        """
        season_data = await self.get_upgrade_list(user)
        user_data = season_data[0]
        for value in season_data:
            if user.all_starcoins >= value.all_starcoins:
                user_data = value
            else:
                return user_data
        else:
            return user_data

    async def text(
        self,
        user: Users,
    ) -> str:
        season_data = await self.get_upgrade_list(user)

        text = "<b>"
        text += tx.Season.Texts.title
        text += tx.Season.Texts.all_starcoins.format(
            starcoins=(
                int(user.all_starcoins)
                if int(user.all_starcoins) == user.all_starcoins
                else user.all_starcoins
            )
        )
        for value in season_data[1:]:
            text += "{} {} - {}\n\n".format(
                value.emoji,
                value.name,
                (
                    "✅"
                    if user.all_starcoins >= value.all_starcoins
                    else (
                        str(
                            int(value.all_starcoins)
                            if int(value.all_starcoins) == value.all_starcoins
                            else value.all_starcoins
                        )
                        + "★"
                    )
                ),
            )
        text += "</b>"
        return text

    async def keyboard(
        self
    ) -> None:
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=tx.Btns.back, callback_data="main_menu|back"
                    )
                ]
            ]
        )

    async def edit_upgrade_msg(
        self,
        call: types.CallbackQuery,
        user: Users,
    ) -> None:
        """
        Показываем список с улучшениями
        """        
        text = await self.text(user)

        await MessageManager(
            call,
            user.user_id
        ).send_or_edit(
            text,
            await self.keyboard(),
            "rang"
        )

    async def get_upgrade_msg(
        self,
        message: types.Message,
        user: Users,
    ) -> None:
        """
        Показываем список с улучшениями
        """
        try:
            await message.bot.delete_message(
                chat_id=user.user_id,
                message_id=int(message.text[7:].replace("upgrade_list_", "")) + 1
            )
        except: # exceptions.TelegramBadRequest
            pass

        await message.delete()
        
        text = await self.text(user)

        await MessageManager(
            message,
            user.user_id
        ).send_or_edit(
            text,
            await inline.back_to_profile(),
            "rang"
        )

        # await message.bot.send_message(
        #     chat_id=user.user_id,
        #     text=text,
        #     reply_markup=await self.keyboard()
        # )
