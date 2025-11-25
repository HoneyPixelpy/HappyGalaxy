from datetime import timedelta, datetime
from typing import Union

from aiogram import types
from aiogram.fsm.context import FSMContext
import pytz

from MainBot.base.models import Lumberjack_Game, Users
import texts
from MainBot.base.orm_requests import BonusesMethods, Lumberjack_GameMethods
from MainBot.keyboards.reply import KB as reply
from MainBot.state.state import CreateBonus
from MainBot.utils.Forms.Profile import Profile
from config import base_lock
from MainBot.utils.Games import LumberjackManager, GeoHuntManager


class BonusDopClass:

    async def calculate_end_time(self, hours_duration: float) -> datetime:
        """
        Рассчитывает время окончания события по МСК.
        
        :param hours_duration: Продолжительность в часах (например, 2.5 = 2 часа 30 минут)

        # Форматируем результат
        return end_time.strftime('%d.%m.%Y %H:%M (MSK)')
        """
        # # Получаем текущее время в UTC
        # utc_now = datetime.now(pytz.utc)
        
        # # Конвертируем в московское время (MSK, UTC+3)
        # msk_tz = pytz.timezone('Europe/Moscow')
        # msk_now = utc_now.astimezone(msk_tz)
        utc_now = datetime.now(pytz.utc)
        
        # Рассчитываем продолжительность
        duration = timedelta(hours=hours_duration)
        return utc_now + duration


class CreateBonusBoosters(BonusDopClass):

    async def mailing_new_bonus(
        self,
        message: types.Message,
        text: str,
        keyboard: types.InlineKeyboardMarkup = None,
        *,
        type_bonus: str
        ) -> str:
        """
        Алгоритм рассылки бонуса.
        """
        async def send_msg(user: Users) -> None:
            if type_bonus in ["click_scale", "energy_renewal"]:
                if not await Lumberjack_GameMethods().get_max_energy(user):
                    return
            await message.bot.send_message(
                chat_id=user.user_id,
                text=text,
                reply_markup=keyboard
            )

        await Profile().mailing(
            message,
            send_msg
        )

    async def activate_bonus_keyboard(
        self,
        bonus_id: Union[str, int]
        ) -> types.InlineKeyboardMarkup:
        """
        Создаем клавиатуру для пуша.
        """
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=texts.Bonus.Btns.activate,
                        callback_data=f"activate_bonus|{bonus_id}"
                    )
                ]
            ]
        )

    async def go_game_keyboard(
        self
        ) -> types.InlineKeyboardMarkup:
        """
        Создаем клавиатуру для пуша.
        """
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=texts.Btns.game,
                        callback_data="games"
                    )
                ]
            ]
        )

    async def type_bonus(
        self,
        message: types.Message,
        user: Users,
        state: FSMContext
        ):
        """
        Начинаем создание бонуса
        Выбираем тип бонуса
        """
        await state.set_state(CreateBonus.type_bonus)
        await message.bot.send_message(
            chat_id=user.user_id,
            text=texts.Admin.Bonus.type_bonus,
            reply_markup=await reply.type_bonus()
        )

    async def size_starcoins_bonus(
        self,
        message: types.Message,
        user: Users,
        state: FSMContext
        ):
        await state.set_state(CreateBonus.size_starcoins)
        await state.update_data(
            type_bonus="add_starcoins"
        )
        await message.bot.send_message(
            chat_id=user.user_id,
            text=texts.Admin.Bonus.size_starcoins,
            reply_markup=await reply.back()
        )

    async def max_quantity_bonus(
        self,
        message: types.Message,
        user: Users,
        state: FSMContext,
        state_data: dict
        ):
        await state.set_state(CreateBonus.max_quantity)
        await state.update_data(
            **state_data
        )
        await message.bot.send_message(
            chat_id=user.user_id,
            text=texts.Admin.Bonus.max_quantity,
            reply_markup=await reply.back()
        )

    async def expires_at_hours_bonus(
        self,
        message: types.Message,
        user: Users,
        state: FSMContext,
        state_data: dict
        ):
        await state.set_state(CreateBonus.expires_at_hours)
        await state.update_data(
            **state_data
        )
        await message.bot.send_message(
            chat_id=user.user_id,
            text=texts.Admin.Bonus.expires_at_hours,
            reply_markup=await reply.back()
        )

    async def scale_clicks_bonus(
        self,
        message: types.Message,
        user: Users,
        state: FSMContext
        ):
        await state.set_state(CreateBonus.click_scale)
        await state.update_data(
            type_bonus="click_scale"
        )
        await message.bot.send_message(
            chat_id=user.user_id,
            text=texts.Admin.Bonus.click_scale,
            reply_markup=await reply.back()
        )

    async def energy_renewal_bonus(
        self,
        message: types.Message,
        user: Users,
        state: FSMContext
        ):
        await state.set_state(CreateBonus.expires_at_hours)
        await state.update_data(
            type_bonus="energy_renewal"
        )
        await message.bot.send_message(
            chat_id=user.user_id,
            text=texts.Admin.Bonus.expires_at_hours,
            reply_markup=await reply.back()
        )

    async def create_bonus(
        self,
        message: types.Message,
        user: Users,
        state: FSMContext,
        expires_at_hours: float
        ):
        state_data = await state.get_data()
        await state.clear()

        if state_data.get("type_bonus","") == "add_starcoins":
            size_starcoins = state_data.get("size_starcoins")
            max_quantity = state_data.get("max_quantity")
            
            bonus = await BonusesMethods().create_bonus(
                state_data.get("type_bonus"),
                expires_at=str(await self.calculate_end_time(expires_at_hours)),
                value=size_starcoins,
                max_quantity=max_quantity
            )
            text = texts.Bonus.Texts.add_starcoins_bonus.format(
                starcoins=bonus.bonus_data.value
            )
        elif state_data.get("type_bonus","") == "click_scale":
            click_scale = state_data.get("click_scale")
            
            bonus = await BonusesMethods().create_bonus(
                state_data.get("type_bonus"),
                expires_at=str(await self.calculate_end_time(expires_at_hours)),
                value=click_scale,
                duration_hours=expires_at_hours
            )
            text = texts.Bonus.Texts.click_scale_bonus.format(
                hours=bonus.bonus_data.duration_hours,
                scale=bonus.bonus_data.value
            )
        elif state_data.get("type_bonus","") == "energy_renewal":
            bonus = await BonusesMethods().create_bonus(
                state_data.get("type_bonus"),
                expires_at=str(await self.calculate_end_time(expires_at_hours)),
                duration_hours=expires_at_hours
            )
            text = texts.Bonus.Texts.energy_renewal_bonus.format(
                hours=bonus.bonus_data.duration_hours
            )
        else:
            await message.answer(str(texts.Error.Notif.undefined_error))
            return

        await self.mailing_new_bonus(
            message,
            text=text,
            keyboard=await self.go_game_keyboard() \
                if state_data.get("type_bonus") == "click_scale" else \
                    await self.activate_bonus_keyboard(
                        bonus_id=bonus.id
                    ),
            type_bonus=state_data.get("type_bonus")
        )


class ActivateBonusBoosters:

    async def get_bonus(
        self,
        call: types.CallbackQuery,
        user: Users,
        bonus_id: int
        ) -> None:
        """
        Проверяем и получаем бонус
        """
        async with base_lock: # TODO перекинуть на сторону сервера блокировку
            result = await BonusesMethods().claim_bonus(
                user,
                bonus_id
            )
            if (
                result and
                isinstance(result, dict) and
                "success_energy_renewal" == result.get("text", "")
                ):
                await LumberjackManager().force_update_energy(user)
                await GeoHuntManager().force_update_energy(user)
            try:
                text_name: str = result['text']
                if text_name == "not_active":
                    text = texts.Bonus.Texts.bonus_ended
                elif text_name == "already_used":
                    text = texts.Bonus.Texts.already_used
                elif text_name == "undefined_error":
                    text = texts.Bonus.Texts.undefined_error
                elif text_name == "success_energy_renewal":
                    text = texts.Bonus.Texts.success_energy_renewal
                elif "success_add_starcoins" in text_name:
                    text = texts.Bonus.Texts.success_add_starcoins.format(
                        starcoins=text_name.replace(
                            'success_add_starcoins=', ''
                        )
                    )
                
                await call.answer(
                    text=text,
                    show_alert=True
                )
            except:
                await call.message.bot.send_message(
                    chat_id=user.user_id,
                    text=text
                )
            
            await call.message.delete()


class BonusBoosters(CreateBonusBoosters, ActivateBonusBoosters):
    """
    Для всех.

    Пуш временный усилитель (
        Процент на который умножается прибыль с клика 
        время работы усилителя
    )

    Пуш раздача старкоинов (
        количества использований 
        число выданное каждому успевшему челику
    )

    Время валидности буста

    """

    def __init__(self):
        pass




