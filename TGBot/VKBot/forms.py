from typing import Tuple

import texts
from aiogram import types
from aiogram.fsm.context import FSMContext
from loguru import logger
from MainBot.keyboards.reply import KB as reply
from MainBot.state.state import VKProfile

from .api import VKGroup


class VKForms(VKGroup):

    @classmethod
    async def get_vk_profile_link(
        cls, state: FSMContext, quest_id: int
    ) -> Tuple[str, types.ReplyKeyboardMarkup]:
        await state.set_state(VKProfile.url)
        await state.update_data(quest_id=quest_id)
        return (texts.Quests.VK.get_url, await reply.back())

    # async def get_vk_chat(
    #     self,
    #     quest_id: str
    #     ) -> Tuple[
    #         str,
    #         types.ReplyKeyboardMarkup
    #     ]:
    #     quest = await QuestsMethods().get_by_id(user.user_id, quest_id)
    #     if not quest:
    #         return (texts.Shop.Error.no_quest, None)

    #     sub_quest = quest.quest_data

    #     text = texts.Quests.Texts.sub_quest.format(
    #             title=sub_quest.title if not sub_quest.description else f"{sub_quest.title}\n\n{sub_quest.description}",
    #             price=sub_quest.reward_starcoins,
    #             url=sub_quest.url
    #         )

    #     return (
    #         text,
    #         await inline.check_sub(sub_quest.id)
    #     )

    @classmethod
    async def verif_vk_chat(cls, vk_id: int, group_id: int, group_token: str) -> bool:
        result = await cls.check_invite(vk_id, group_id, group_token)
        logger.debug(result)

        return result
