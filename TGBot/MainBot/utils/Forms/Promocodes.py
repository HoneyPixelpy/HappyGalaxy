import asyncio
from datetime import datetime
import json
import math
import random
from typing import Optional, Tuple, Union
from collections import namedtuple

from aiogram.fsm.context import FSMContext
from aiogram import Bot, types
from loguru import logger
import pytz

from MainBot.base.models import SubscribeQuest, Users, Quests, IdeaQuests, DailyQuests
from MainBot.state.state import Daily, Idea, SPromocodes
from MainBot.utils.errors import ListLengthChangedError, NoDesiredTypeError
from Redis.aggregator import QuestAggregator
import texts, config
from MainBot.keyboards.inline import IKB as inline
from MainBot.keyboards.reply import KB as reply
from MainBot.base.orm_requests import PromocodesMethods
from MainBot.utils.MyModule import Func
from config import debug


class Promocodes:
    
    async def wait_promo(
        self,
        user: Users,
        state: FSMContext,
        *,
        call: types.CallbackQuery = None,
        message: types.Message = None
        ) -> None:
        if call:
            message = call.message
            await message.delete()
            
        await message.bot.send_message(
            chat_id=user.user_id,
            text=texts.Promocodes.Text.wait,
            reply_markup=await reply.back("Введите промокод")
        )
            
        await state.set_state(SPromocodes.wait)
    
    async def activate(
        self,
        message: types.Message,
        state: FSMContext,
        user: Users
        ) -> None:
        promocode = await PromocodesMethods().activate(user.id, message.text)
        if isinstance(promocode, str):
            if promocode == "server_error":
                await Func.send_error_to_developer(
                    text=(
                        "Пользователь не смог активировать промокод\n"
                        f"{user.user_id} {user.tg_username}\n"
                        f"Promocode: {message.text}"
                    )
                )
            await message.bot.send_message(
                chat_id=user.user_id,
                text=texts.Promocodes.Errors.__dict__[promocode],
                reply_markup=await reply.back("Введите промокод")
            )
        else:
            text = texts.Promocodes.Text.promo_starcoins.format(
                name=f'{promocode.title}\n\n{promocode.description}' if promocode.description else promocode.title,
                reward_starcoins=promocode.reward_starcoins
            )
            await message.bot.send_message(
                chat_id=user.user_id,
                text=text,
                reply_markup=await reply.main_menu(user),
                disable_web_page_preview=True
            )
            await message.delete()
            await state.clear()


