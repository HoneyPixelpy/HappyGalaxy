from typing import List, Optional

import texts
from aiogram import types
from config import bot_name
from MainBot.base.models import Family_Ties, RewardData, Users
from MainBot.base.orm_requests import DataMethods, Family_TiesMethods, IdempotencyKeyMethods, UserMethods
from MainBot.utils.MyModule.message import MessageManager
from MainBot.utils.Forms.Profile import Profile
from MainBot.keyboards import inline


class FamilyTies:
    """ Сюда попадают только РОДИТЕЛИ и ДЕТИ
    Нету сообщения который бы постоянно информировал
    о ссылке для приглашения родственников
    """
    def __init__(self, role_private: str):
        self.role_private = role_private
        self.available_roles = ["parent", "child"]
        self.having_family = False
    
    @property
    def need(self) -> Optional['FamilyTies']:
        return self if self.role_private in self.available_roles else None

    async def search_ties(self, family: List[Family_Ties]) -> Optional[bool]:
        if self.role_private == "child":
            search = "parent"
        elif self.role_private == "parent":
            search = "child"

        for family_member in family:
            if (
                family_member.to_user.role_private == search
                or family_member.from_user.role_private == search
            ):
                return True

    async def check_parent(self, user: Users) -> Optional[bool]:
        """
        Потом надо разбить на два метода
        - один дает доступ к игре как щас
        - другой выдает инфу о родственниках
        """
        family: List[Family_Ties] = await Family_TiesMethods().get_family(user)

        if not family:
            return None

        self.having_family = True
        if not await self.search_ties(family):
            return None
        
        return True

    async def info_parent(
        self,
        user: Users,
        call: types.CallbackQuery | types.Message
        ) -> Optional[bool]:
        """
        Отправляем сообщение для приглашения родственников
        """
        text = ""
        reward_data: RewardData = await DataMethods().reward()
        match self.role_private:
            case "child":
                text += texts.Family_Ties.Texts.no_family_child
            case "parent":
                text += texts.Family_Ties.Texts.no_family_parent

        text += texts.Family_Ties.Texts.family_link.format(
            bot_name=bot_name, user_id=user.user_id
        )
        if not self.having_family:
            text += texts.Family_Ties.Texts.family_bonus.format(
                parent_bonus=reward_data.starcoins_parent_bonus
            )

        await MessageManager(
            call,
            user.user_id
        ).send_or_edit(
            text,
            await inline.back_to_main(),
            "game"
        )

        # await call.bot.send_message(
        #     chat_id=user.user_id,
        #     text=text,
        #     reply_markup=await selector.main_menu(user),
        #     disable_web_page_preview=True,
        # )

    async def add_parent(
        self, message: types.Message, user: Users, parent_user_id: str
    ) -> None:
        """
        Добавляем в семью пользователя по нашей ссылке
         - срабатывает сразу после перехода по ссылке
        """
        if (
            parent_user_id
            and parent_user_id.isdigit()
            and int(parent_user_id) != user.user_id
        ):
            parent_user: Users = await UserMethods().get_by_user_id(int(parent_user_id))

            if not parent_user:
                await message.answer(texts.Error.Notif.user_not_found)
            elif not parent_user.authorised:
                await message.answer(texts.Error.Family_Ties.you_try_later)
            elif not user.authorised:
                await message.answer(texts.Error.Family_Ties.me_try_later)
            elif parent_user.role_private not in [
                "child",
                "parent",
            ] or user.role_private not in ["child", "parent"]:
                await message.answer(texts.Error.Family_Ties.you_no_ties)
            else:
                if not await Family_TiesMethods().get_target_ties(
                    parent_user=parent_user, user=user
                ):
                    await Family_TiesMethods().create(
                        from_user=parent_user,
                        to_user=user,
                        idempotency_key=await IdempotencyKeyMethods.IKgenerate(user.user_id, message)
                    )
                    await Profile().notification_parent(message, user, parent_user)
                else:
                    await message.answer(texts.Family_Ties.Texts.already_family)
