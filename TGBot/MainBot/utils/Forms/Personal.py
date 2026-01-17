import asyncio
from datetime import datetime

import pytz
import texts
from aiogram import types
from aiogram.fsm.context import FSMContext
from MainBot.base.forms import UsersForms
from MainBot.base.models import Users, Work_Keys
from MainBot.base.orm_requests import Work_KeysMethods
from MainBot.keyboards import inline, reply
from MainBot.state.state import RegPersonal
from MainBot.utils.MyModule import Func

from .Profile import Profile


class PersonalForms:

    async def generate_key(self) -> str:
        """
        Создаем ключ для нового члена команды
        и выдаем его текстом для сообщения.
        """
        work_keys: Work_Keys = await Work_KeysMethods().create()
        return texts.Personal.Texts.new_key.format(key=work_keys.key)

    async def check_key(self, key: str) -> bool:
        """
        Возвращает True
            если ключ существует и не занят
        """
        return await Work_KeysMethods().check_by_key(key)

    async def gender_worker(
        self, user: Users, message: types.Message, state: FSMContext, key: str
    ):
        """
        Даем выбор пола
        """
        await message.delete()
        await message.bot.send_message(
            chat_id=user.user_id,
            text=texts.Start.Texts.gender,
            reply_markup=await inline.gender("manager", True),
        )

        await state.set_state(RegPersonal.Gender)
        await state.update_data(key=key, role="manager")

    async def back_gender_worker(
        self,
        message: types.Message,
        state: FSMContext,
    ) -> None:
        """
        Отправляем еще несколько сообщений
        для детей после чего даем выбор пола
        """
        await message.answer(
            text=texts.Start.Texts.gender,
            reply_markup=await inline.gender("manager", True),
        )
        await message.delete()
        await state.set_state(RegPersonal.Gender)

    async def age_worker(
        self,
        call: types.CallbackQuery,
        state: FSMContext,
        user: Users,
    ) -> None:
        """
        Вводим возраст
        """
        gender = call.data.split("|")[1]
        if gender in ["man", "woman"]:
            await state.update_data(gender=gender)
        await call.message.delete()

        await call.message.bot.send_message(
            chat_id=user.user_id,
            text=texts.Start.Texts.age,
            reply_markup=await reply.back(datetime.now().strftime("%d.%m.%Y")),
        )

        await state.set_state(RegPersonal.Age)

    async def fio_worker(
        self, message: types.Message, state: FSMContext, user: Users, age: datetime
    ) -> None:
        """
        Вводим Фамилия Имя
        """
        await state.update_data(age=age)
        await message.delete()

        await message.bot.send_message(
            chat_id=user.user_id,
            text=texts.Start.Texts.fio,
            reply_markup=await reply.back("Фамилия Имя"),
        )

        await state.set_state(RegPersonal.FIO)

    async def back_age_worker(
        self,
        message: types.Message,
        state: FSMContext,
        user: Users,
    ) -> None:
        """
        Вводим возраст
        """
        await message.delete()
        await message.bot.send_message(
            chat_id=user.user_id,
            text=texts.Start.Texts.age,
            reply_markup=await reply.back(datetime.now().strftime("%d.%m.%Y")),
        )

        await state.set_state(RegPersonal.Age)

    # async def success_fio_worker(
    #     self,
    #     message: types.Message,
    #     state: FSMContext,
    #     user: Users,
    #     parts: list[str]
    #     ) -> None:
    #     """
    #     Подтверждаем Фамилия Имя
    #     """
    #     await state.update_data(
    #         supername=parts[0],
    #         name=parts[1]
    #     )
    #     await message.delete()

    #     await message.bot.send_message(
    #         chat_id=user.user_id,
    #         text=texts.Start.Texts.success_fio.format(
    #             supername=parts[0],
    #             name=parts[1]
    #         ),
    #         reply_markup=await inline.success_fio()
    #     )
    #     await state.set_state(RegPersonal.Success_FIO)

    async def back_fio_worker(
        self, message: types.Message, state: FSMContext, user: Users
    ) -> None:
        """
        Вводим Фамилия Имя
        """
        await message.delete()

        await message.bot.send_message(
            chat_id=user.user_id,
            text=texts.Start.Texts.fio,
            reply_markup=await reply.back("Фамилия Имя"),
        )
        await state.set_state(RegPersonal.FIO)

    async def phone_worker(
        self,
        message: types.Message,
        state: FSMContext,
        user: Users,
        parts: list[str],
        nickname: str,
    ) -> None:
        """
        Вводим Нормер телефона
        """
        await state.update_data(nickname=nickname, supername=parts[0], name=parts[1])
        await message.delete()

        await message.bot.send_message(
            chat_id=user.user_id,
            text=texts.Start.Texts.phone,
            reply_markup=await reply.send_phone(),
        )

        await state.set_state(RegPersonal.phone)

    async def data_validation(
        self, message: types.Message, state: FSMContext, user: Users, phone: str
    ) -> None:
        """
        Даем данные пользователя на проверку
        """
        await state.update_data(phone=phone)
        await message.delete()

        state_data = await state.get_data()

        await message.bot.send_message(
            chat_id=user.user_id,
            text=str(state_data["phone"]),
            reply_markup=types.ReplyKeyboardRemove(),
        )

        await message.bot.send_message(
            chat_id=user.user_id,
            text=texts.Start.Texts.data_validation.format(
                gender=await Func.gender_name(state_data["gender"], state_data["role"]),
                age=(
                    datetime.now(pytz.timezone("Europe/Moscow")) - state_data["age"]
                ).days
                // 365,
                name=state_data["name"],
                supername=state_data["supername"],
                nickname=(
                    state_data["nickname"] if state_data["nickname"] else "Не указано"
                ),
                phone=state_data["phone"],
            ),
            reply_markup=await inline.data_validation(state_data["role"]),
        )

        await state.set_state(RegPersonal.final)

    async def success_ruls(
        self, call: types.CallbackQuery, state: FSMContext, user: Users
    ) -> None:
        """
        Выдаем сообщение с подтверждением правил
        """
        await call.message.delete()

        await call.message.bot.send_message(
            chat_id=user.user_id, text=texts.Start.Texts.wait_passport
        )
        await asyncio.sleep(1)

        await self.final_regisration(call, state, user)

        # await call.message.bot.send_message(
        #     chat_id=user.user_id,
        #     text=texts.Start.Texts.success_ruls,
        #     reply_markup=await inline.success_ruls(),
        #     disable_web_page_preview=True
        # )

        # await state.set_state(RegPersonal.success_ruls)

    async def final_regisration(
        self, call: types.CallbackQuery, state: FSMContext, user: Users
    ) -> None:
        """
        Регестрируем пользователя
        """
        # await call.message.delete()

        state_data = await state.get_data()

        await call.message.bot.send_message(
            chat_id=user.user_id, text=texts.Start.Texts.ready_passport
        )

        user = await UsersForms().registration(user, state_data)

        if not await Work_KeysMethods().register_with_key(user, state_data["key"]):
            await Func.send_error_to_developer(
                f"Не смогли привязать пользователя {user.user_id} к ключу {state_data['key']}"
            )
            await call.answer(texts.Personal.Error.undefined_error)
            await call.message.delete()
            await state.clear()
            return

        await Profile().new_user_in_log(call.message.bot, user)
        await Profile().user_info_msg(call, user)

        await state.clear()
