from typing import Optional
from aiogram import types

from MainBot.keyboards.reply import KB as reply
from MainBot.utils.Forms.Profile import Profile
from MainBot.base.orm_requests import DataMethods, Family_TiesMethods, UserMethods
from MainBot.base.models import RewardData, Users, Family_Ties
import texts
from config import bot_name


class FamilyTies:
    """
    Нету сообщения который бы постоянно информировал
    о ссылке для приглашения родственников
    """

    async def search_ties(
        self,
        family: list[Family_Ties],
        role: str
        ) -> Optional[bool]:
        if role == "child": search = "parent"
        elif role == "parent": search = "child"
            
        for family_member in family:
            if (
                family_member.to_user.role_private == search or
                family_member.from_user.role_private == search
                ):
                return True
        
    async def info_parent(
        self,
        user: Users,
        message: types.Message
        ) -> Optional[bool]:
        """
        Сюда попадают только РОДИТЕЛИ и ДЕТИ
        
        Отправляем сообщение для приглашения родственников

        Здесь могут отображаться не зарегестрированные пользователи
        нужно учитывать тот факт что некоторых данных в базе
        может не быть
        
        Потом надо разбить на два метода
        - один дает доступ к игре как щас
        - другой выдает инфу о родственниках
        
        """
        family: list[Family_Ties] = await Family_TiesMethods().get_family(user)
        text = ""
        if not family or not await self.search_ties(family, user.role_private):
            reward_data: RewardData = await DataMethods().reward()
            if user.role_private == "child":
                text += texts.Family_Ties.Texts.no_family_child
            elif user.role_private == "parent":
                text += texts.Family_Ties.Texts.no_family_parent
            # elif user.role_private == "worker":
            #     text += texts.Family_Ties.Texts.no_family_worker
            
            text += texts.Family_Ties.Texts.family_link.format(
                bot_name=bot_name,
                user_id=user.user_id
            )
            if not family:
                text += texts.Family_Ties.Texts.family_bonus.format(
                    parent_bonus=reward_data.starcoins_parent_bonus
                )
            
            await message.bot.send_message(
                chat_id=user.user_id,
                text=text,
                reply_markup=await reply.main_menu(user),
                disable_web_page_preview=True
            )
            return
        # else:
        #     for family_member in family:
        #         if await sync_to_async(lambda: family_member.to_user)() == user:
        #             fm_user = await sync_to_async(lambda: family_member.from_user)()
        #         else:
        #             fm_user = await sync_to_async(lambda: family_member.to_user)()
        #         text += texts.Family_Ties.Texts.family_member_info.format(
        #             role=fm_user.role,
        #             supername=fm_user.supername,
        #             name=fm_user.name,
        #             starcoins=fm_user.starcoins
        #         )
        #     else:
        #         text += texts.Family_Ties.Texts.footer_family.format(
        #             bot_name=bot_name,
        #             user_id=user.user_id
        #         )

        # await message.bot.send_message(
        #     chat_id=user.user_id,
        #     text=text,
        #     reply_markup=await reply.main_menu(user),
        #     disable_web_page_preview=True
        # )
        return True

    async def add_parent(
        self,
        message: types.Message,
        user: Users,
        parent_user_id: str
        ) -> None:
        """
        Добавляем в семью пользователя по нашей ссылке
         - срабатывает сразу после перехода по ссылке
        """
        if (parent_user_id and
            parent_user_id.isdigit() and 
            int(parent_user_id) != user.user_id
            ):
            parent_user: Users = await UserMethods().get_by_user_id(int(parent_user_id))
            
            if not parent_user:
                await message.answer(
                    texts.Error.Notif.user_not_found
                )
            elif not parent_user.authorised:
                await message.answer(
                    texts.Error.Family_Ties.you_try_later
                )
            elif not user.authorised:
                await message.answer(
                    texts.Error.Family_Ties.me_try_later
                )
            elif (
                parent_user.role_private not in ["child", "parent"] or
                user.role_private not in ["child", "parent"]
                ):
                await message.answer(
                    texts.Error.Family_Ties.you_no_ties
                )
            else:
                if not await Family_TiesMethods().get_target_ties(
                        parent_user=parent_user, 
                        user=user
                        ):
                    await Family_TiesMethods().create(
                        from_user=parent_user,
                        to_user=user
                    )
                    await Profile().notification_parent(message, user, parent_user)
                else:
                    await message.answer(
                        texts.Family_Ties.Texts.already_family
                    )
        