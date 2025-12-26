import asyncio
import re
from datetime import datetime
from typing import List, Optional, Tuple, Union

import aiofiles
import pytz
import texts
from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from config import BASE_DIR
from loguru import logger
from MainBot.base.forms import UsersForms
from MainBot.base.models import Users
from MainBot.base.orm_requests import UserMethods
from MainBot.keyboards.inline import IKB as inline
from MainBot.keyboards.reply import KB as reply
from MainBot.state.state import Auth_state
from MainBot.utils.MyModule import Func, load_config_from_forwards

from .Profile import Profile


class Authorisation:

    bad_words_file = BASE_DIR / "Settings/bad_words.txt"

    @classmethod
    async def forward_msgs(cls, key: str, bot: Bot, user: Users) -> None:
        """
        Пересылаем приветственные сообщения
        """
        json_data = await load_config_from_forwards()

        messages = json_data[key]["messages"]
        user_id = user.user_id

        for message_data in messages:
            # if user_id == 1894909159: continue
            if message_data["type"] == "sticker":
                try:
                    await bot.send_sticker(
                        chat_id=user_id, sticker=message_data["message_key"]
                    )
                except Exception as e:
                    logger.error(f"No {e.__class__.__name__}: {e}")
            elif message_data["type"] == "text":
                try:
                    await bot.send_message(
                        chat_id=user_id, text=message_data["message_key"]
                    )
                except Exception as e:
                    logger.error(f"No {e.__class__.__name__}: {e}")
            await asyncio.sleep(message_data["time"])

    @classmethod
    async def hello(cls, bot: Bot, state: FSMContext, user: Users) -> None:
        """
        Начинаем работу с новым пользователем
        """
        await state.set_state(Auth_state.No)

        await cls.forward_msgs("First", bot, user)

        await bot.send_message(
            chat_id=user.user_id,
            text=texts.Start.Texts.time_changes,
            reply_markup=await inline.start_hello(),
        )

        await state.set_state(Auth_state.Start_query)

    @classmethod
    async def let_do_it_later(
        cls,
        bot: Bot,
        state: FSMContext,
        user: Users,
    ) -> None:
        """
        Если мы хотим позже зарегаться
        """
        await state.set_state(Auth_state.No)

        await cls.forward_msgs("Second", bot, user)

        await bot.send_message(
            chat_id=user.user_id,
            text=texts.Start.Texts.time_wait,
            reply_markup=await reply.start_wait(),
        )

        await state.clear()

    @classmethod
    async def register_preview(
        cls,
        bot: Bot,
        state: FSMContext,
        user: Users,
    ) -> None:
        """
        Начинаем регистрацию нового пользователя
        """
        await state.set_state(Auth_state.No)

        await cls.forward_msgs("Three", bot, user)

        await cls.ready_register(bot, user)

    @classmethod
    async def ready_register(cls, bot: Bot, user: Users) -> None:
        """Auth_state.No
        Прызваем назать на кнопку создать паспорт
        """
        await bot.send_message(
            chat_id=user.user_id,
            text=texts.Start.Texts.ready_register,
            reply_markup=await inline.ready_register(),
            disable_web_page_preview=True,
        )

    @classmethod
    async def why_are_you(
        cls,
        bot: Bot,
        state: FSMContext,
        user: Users,
    ) -> None:
        """
        Начинаем регистрацию нового пользователя
        """
        await bot.send_message(
            chat_id=user.user_id,
            text=texts.Start.Texts.why_are_you,
            reply_markup=await reply.why_are_you(),
        )

        await state.set_state(Auth_state.why_are_you)

    @classmethod
    async def sure_role(
        cls,
        bot: Bot,
        user: Users,
        role: str,
    ) -> None:
        """
        Спрашиваем уверен ли участний в своем выборе
        """
        if role == "child":
            text = texts.Start.Texts.sure_participant
        elif role == "parent":
            text = texts.Start.Texts.sure_parent
        elif role == "worker":
            text = texts.Start.Texts.sure_worker

        await bot.send_message(
            chat_id=user.user_id, text=text, reply_markup=await inline.sure_role(role)
        )

    @classmethod
    async def gender_participant(
        cls, call: types.CallbackQuery, state: FSMContext, user: Users, role: str
    ) -> None:
        """
        Отправляем еще несколько сообщений
        для детей после чего даем выбор пола
        """
        await call.message.delete()
        await state.set_state(Auth_state.No)

        await state.update_data(role=role)

        last_msg = await call.message.bot.send_message(
            chat_id=user.user_id, text=texts.Start.Texts.child_reg_msg_1
        )

        for msg_text in [texts.Start.Texts.child_reg_msg_3]:
            last_msg = await call.message.bot.send_message(
                chat_id=user.user_id,
                text="...",
            )
            await asyncio.sleep(2.5)
            await call.bot.edit_message_text(
                text=msg_text, chat_id=user.user_id, message_id=last_msg.message_id
            )
            await asyncio.sleep(0.5)

        await call.message.bot.send_message(
            chat_id=user.user_id,
            text=texts.Start.Texts.gender,
            reply_markup=await inline.gender(role),
        )
        await state.set_state(Auth_state.Gender)

    # @classmethod
    # async def gender_parent(
    #     cls,
    #     call: types.CallbackQuery,
    #     state: FSMContext,
    #     user: Users,
    #     role: str = "parent"
    #     ) -> None:
    #     """
    #     Даем выбор пола
    #     """
    #     await call.message.delete()
    #     await state.update_data(
    #         role=role
    #     )

    #     await call.message.bot.send_message(
    #         chat_id=user.user_id,
    #         text=texts.Start.Texts.gender,
    #         reply_markup=await inline.gender(role)
    #     )
    #     await state.set_state(Auth_state.Gender)

    @classmethod
    async def back_gender_participant(
        cls,
        message: types.Message,
        state: FSMContext,
    ) -> None:
        """
        Отправляем еще несколько сообщений
        для детей после чего даем выбор пола
        """
        data = await state.get_data()
        await message.answer(
            text=texts.Start.Texts.gender,
            reply_markup=await inline.gender(data.get("role", "")),
        )
        await message.delete()
        await state.set_state(Auth_state.Gender)

    @classmethod
    async def age_participant(
        cls,
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

        await state.set_state(Auth_state.Age)

    @classmethod
    async def check_age(
        cls,
        birthday: str,
        state: FSMContext,
    ) -> Tuple[bool, Union[str, datetime]]:
        """
        Проверяем возраст
        Проверяем в опредленном диапазоне
        Для детей и родителей разные диапазоны
        при несоответсвии выбиваем ошибку
        """
        try:
            if len(birthday.strip().split(".")) == 3:
                tz = pytz.timezone("Europe/Moscow")
                date_now = datetime.now(tz)
                birthdate = datetime.strptime(birthday, "%d.%m.%Y")
                birthdate = tz.localize(birthdate)  # Добавляем временную зону
                human_years = (date_now - birthdate).days // 365

                state_data = await state.get_data()
                if state_data["role"] == "child":
                    if human_years < 10:
                        return False, texts.Error.Age.young
                    elif human_years > 16:
                        return False, texts.Error.Age.old
                    else:
                        return True, birthdate
                elif state_data["role"] == "parent":
                    if human_years < 18:
                        return False, texts.Error.Age.parent
                    else:
                        return True, birthdate
                elif state_data["role"] == "worker":
                    if human_years < 16:
                        return False, texts.Error.Age.parent
                    else:
                        return True, birthdate
                else:
                    return True, birthdate
            else:
                raise Exception("Неправильный формат даты рождения")
        except:
            return False, texts.Error.Age.wrong

    @classmethod
    async def back_age_participant(
        cls,
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

        await state.set_state(Auth_state.Age)

    @classmethod
    async def fio_participant(
        cls, message: types.Message, state: FSMContext, user: Users, age: datetime
    ) -> None:
        """
        Вводим Фамилия Имя
        """
        data = await state.get_data()
        await state.update_data(age=age)
        await message.delete()

        await message.bot.send_message(
            chat_id=user.user_id,
            text=(
                texts.Start.Texts.first_name
                if data["role"] == "child"
                else texts.Start.Texts.fio
            ),
            reply_markup=await reply.back(
                "Имя" if data["role"] == "child" else "Фамилия Имя"
            ),
        )

        await state.set_state(Auth_state.FIO)

    @classmethod
    async def check_fio(
        cls, user_fio: str, role: str = ""
    ) -> Tuple[bool, Union[str, list[str]]]:
        """
        Проверяем введенное ФИО с расширенной валидацией
        Возвращает (статус_валидности, сообщение_об_ошибке)
        """
        # Удаляем лишние пробелы и приводим к нормальной форме
        cleaned_fio = " ".join(user_fio.strip().split())

        # Разбиваем на компоненты
        parts = cleaned_fio.split()

        bad_words = await cls.banned_words()

        # Базовые проверки
        if role == "child":
            if len(parts) != 1:
                return False, texts.Error.FIO.dont_first_name

            # Проверка на кириллицу (можно расширить для других языков)
            if not re.fullmatch(r"[а-яёА-ЯЁ-]+", parts[0]):
                return False, texts.Error.FIO.bad_symbols_first_name

            # Проверка заглавных букв
            if not parts[0][0].isupper():
                return False, texts.Error.FIO.upper_start_symbol_first_name

            # Проверка минимальной/максимальной длины
            if len(parts[0]) < 2:
                return False, texts.Error.FIO.min_two_symbol_first_name

            if len(parts[0]) > 30:
                return False, texts.Error.FIO.very_big_first_name

            if any(bad_word in parts[0].lower() for bad_word in bad_words):
                return False, texts.Error.Nickname.bad_words

            parts = ["", parts[0]]

        else:
            if len(parts) != 2:
                return False, texts.Error.FIO.dont_full

            last_name, first_name = parts

            # Проверка на кириллицу (можно расширить для других языков)
            if not all(re.fullmatch(r"[а-яёА-ЯЁ-]+", part) for part in parts):
                return False, texts.Error.FIO.bad_symbols

            # Проверка заглавных букв
            if not (last_name[0].isupper() and first_name[0].isupper()):
                return False, texts.Error.FIO.upper_start_symbol

            # Проверка минимальной/максимальной длины
            if any(len(part) < 2 for part in parts):
                return False, texts.Error.FIO.min_two_symbol

            if any(len(part) > 30 for part in parts):
                return False, texts.Error.FIO.very_big

            for part in parts:
                if any(bad_word in part.lower() for bad_word in bad_words):
                    return False, texts.Error.Nickname.bad_words

        # Проверка на дефисы (например, для двойных фамилий)
        if any(
            "--" in part or part.startswith("-") or part.endswith("-") for part in parts
        ):
            return False, texts.Error.FIO.uncorrect_symbol

        # if await UserMethods().check_fio(last_name, first_name, middle_name):
        #     return False, texts.Error.FIO.uniq

        return True, parts

    # @classmethod
    # async def success_fio_participant(
    #     cls,
    #     message: types.Message,
    #     state: FSMContext,
    #     user: Users,
    #     role: str,
    #     parts: list[str]
    #     ) -> None:
    #     """
    #     Вводим Фамилия Имя
    #     """
    #     await state.update_data(
    #         supername=parts[0],
    #         name=parts[1]
    #     )
    #     await message.delete()

    #     await message.bot.send_message(
    #         chat_id=user.user_id,
    #         text=texts.Start.Texts.success_first_name.format(
    #             name=parts[1]
    #         ) if role == "child" else texts.Start.Texts.success_fio.format(
    #             supername=parts[0],
    #             name=parts[1]
    #         ),
    #         reply_markup=await inline.success_fio()
    #     )
    #     await state.set_state(Auth_state.Success_FIO)

    @classmethod
    async def back_fio_participant(
        cls, message: types.Message, state: FSMContext, user: Users
    ) -> None:
        """
        Вводим Фамилия Имя
        """
        data = await state.get_data()
        await message.delete()

        await message.bot.send_message(
            chat_id=user.user_id,
            text=(
                texts.Start.Texts.first_name
                if data["role"] == "child"
                else texts.Start.Texts.fio
            ),
            reply_markup=await reply.back(
                "Имя" if data["role"] == "child" else "Фамилия Имя"
            ),
        )
        await state.set_state(Auth_state.FIO)

    @classmethod
    async def create_nickname(
        cls,
        message: types.Message,
        state: FSMContext,
        user: Users,
        role: str,
        parts: list[str],
    ) -> None:
        """
        Вводим Никнейм
        """
        await state.update_data(supername=parts[0], name=parts[1])
        await message.delete()

        await message.bot.send_message(
            chat_id=user.user_id,
            text=texts.Start.Texts.nickname,
            reply_markup=await reply.nickname(role),
        )

        await state.set_state(Auth_state.nickname)

    @classmethod
    async def back_create_nickname(
        cls, message: types.Message, state: FSMContext, user: Users, role: str
    ) -> None:
        """
        Вводим Никнейм
        """
        await message.delete()

        await message.bot.send_message(
            chat_id=user.user_id,
            text=texts.Start.Texts.nickname,
            reply_markup=await reply.nickname(role),
        )

        await state.set_state(Auth_state.nickname)

    @classmethod
    async def banned_words(cls) -> list[str]:
        async with aiofiles.open(cls.bad_words_file, "r", encoding="utf-8") as f:
            lines = await f.read()
            return lines.splitlines()

    @classmethod
    async def check_nickname(cls, nickname: str) -> Tuple[bool, Union[str, List[str]]]:
        """
        Проверяет валидность псевдонима пользователя.

        Правила:
        1. Длина: 1-30 символов
        2. Допустимые символы: русские буквы, цифры, пробелы и дефисы
        3. Нельзя:
        - Только цифры
        - Нецензурные слова
        - Спецсимволы (кроме дефиса)
        - Повторяющиеся пробелы/дефисы

        Возвращает:
        - (True, nickname) если валидно
        - (False, error_messages) если невалидно (список ошибок)
        """
        errors = []
        normalized_nick = nickname.strip()

        # 1. Проверка длины
        if len(normalized_nick) < 1:
            errors.append(texts.Error.Nickname.small_len)
        elif len(normalized_nick) > 25:
            errors.append(texts.Error.Nickname.big_len)

        # 2. Проверка допустимых символов
        if not re.fullmatch(r"^[а-яёА-ЯЁ0-9\s-]+$", normalized_nick):
            errors.append(texts.Error.Nickname.bad_symbols)

        # 3. Проверка на только цифры
        if normalized_nick.isdigit():
            errors.append(texts.Error.Nickname.only_digit)

        # 4. Проверка нецензурных слов (упрощенная версия)
        if any(
            bad_word in normalized_nick.lower() for bad_word in await cls.banned_words()
        ):
            errors.append(texts.Error.Nickname.bad_words)

        # 5. Проверка повторяющихся символов
        if "  " in normalized_nick or "--" in normalized_nick:
            errors.append(texts.Error.Nickname.double_symbols)

        # 6. Проверка начального/конечного символа
        if normalized_nick.startswith("-") or normalized_nick.endswith("-"):
            errors.append(texts.Error.Nickname.start_end_symbols)

        # 7. Проверка регистра (опционально)
        if normalized_nick.lower() != normalized_nick and not normalized_nick.isupper():
            if not any(c.isupper() for c in normalized_nick if c.isalpha()):
                errors.append(texts.Error.Nickname.lower_case)

        # Нормализация (убираем лишние пробелы, приводим к единому регистру)
        final_nick = " ".join(normalized_nick.split()).title()

        if await UserMethods().check_nickname(final_nick):
            errors.append(texts.Error.Nickname.uniq)

        if errors:
            return False, errors

        return True, final_nick

    @classmethod
    async def phone_participant(
        cls,
        message: types.Message,
        state: FSMContext,
        user: Users,
        nickname: Optional[str],
    ) -> None:
        """
        Вводим Нормер телефона
        """
        await state.update_data(nickname=nickname)
        await message.delete()

        await message.bot.send_message(
            chat_id=user.user_id,
            text=texts.Start.Texts.phone,
            reply_markup=await reply.send_phone(),
        )

        await state.set_state(Auth_state.phone)

    @classmethod
    async def check_phone(cls, phone: str) -> Tuple[bool, Union[str, List[str]]]:
        """
        Проверяет валидность российского номера телефона.

        Базовые правила для русских номеров:
        1. Начинается с +7 или 8
        2. Содержит 11 цифр (включая код страны)
        3. Допустимые форматы:
           +7XXXYYYZZWW
           8XXXYYYZZWW
           8 (XXX) YYY-ZZ-WW
           +7 (XXX) YYY-ZZ-WW
        """
        errors = []
        cleaned_phone = re.sub(r"[^\d]", "", phone)  # Удаляем всё, кроме цифр
        # if os.getenv("DEBUG"):
        #     cleaned_phone = f"7961058{random.randint(1000, 9999)}"

        # Проверка длины
        if len(cleaned_phone) != 11:
            errors.append(texts.Error.Phone.eleven)

        # Проверка начала номера
        if not (cleaned_phone.startswith("7") or cleaned_phone.startswith("8")):
            errors.append(texts.Error.Phone.seven)

        # Проверка кода оператора (первые цифры после 7/8)
        operator_codes = ["9", "4", "8"]  # Основные начальные цифры операторов
        if len(cleaned_phone) > 1 and cleaned_phone[1] not in operator_codes:
            errors.append(texts.Error.Phone.standart)

        # Нормализация к формату +7XXXYYYZZWW
        normalized = f"+7{cleaned_phone[1:]}"

        if await UserMethods().check_phone(normalized):
            errors.append(texts.Error.Phone.uniq)

        if errors:
            return False, errors

        return True, normalized

    @classmethod
    async def data_validation(
        cls, message: types.Message, state: FSMContext, user: Users, phone: str
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
                title="Имя" if state_data["role"] == "child" else "ФИО",
                name=state_data["name"],
                supername=state_data["supername"],
                nickname=(
                    state_data["nickname"] if state_data["nickname"] else "Не указано"
                ),
                phone=state_data["phone"],
            ),
            reply_markup=await inline.data_validation(state_data["role"]),
        )

        await state.set_state(Auth_state.final)

    @classmethod
    async def success_ruls(
        cls, call: types.CallbackQuery, state: FSMContext, user: Users
    ) -> None:
        """
        Выдаем сообщение с подтверждением правил
        """
        await call.message.delete()

        await call.message.bot.send_message(
            chat_id=user.user_id, text=texts.Start.Texts.wait_passport
        )
        await asyncio.sleep(4)

        await cls.final_regisration(call, state, user)

        # await call.message.bot.send_message(
        #     chat_id=user.user_id,
        #     text=texts.Start.Texts.success_ruls,
        #     reply_markup=await inline.success_ruls(),
        #     disable_web_page_preview=True
        # )

        # await state.set_state(Auth_state.success_ruls)

    @classmethod
    async def final_regisration(
        cls, call: types.CallbackQuery, state: FSMContext, user: Users
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

        if user.referral_user_id:
            if await Profile().notification_referal(call.message, user):
                user = await UserMethods().get_by_user_id(user.user_id)

        await Profile().new_user_in_log(call.message.bot, user)
        await Profile().user_info_msg(call.message.bot, user, call.message.message_id)

        await state.clear()
