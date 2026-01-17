import asyncio
import datetime
import json
import os
import random
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple, Union

import pycountry
import texts
from aiogram import types
from config import BASE_DIR
from deep_translator import GoogleTranslator
from loguru import logger
from MainBot.base.forms import Sigma_BoostsForms
from MainBot.base.models import GeoHunter, Users
from MainBot.base.orm_requests import GeoHunter_GameMethods
from MainBot.config import bot
from MainBot.utils.MyModule import Func
from MainBot.utils.Rabbitmq import RabbitMQ
from redis import Redis
from Redis.main import RedisManager


class FlagProcessor:
    def __init__(self):
        self.flags_path = BASE_DIR / "Data/Flags"
        self.output_file = "MainBot/utils/Games/GeoHunt/Data/geo.json"
        self.cache_file = "message_ids.json"
        self.translation_cache_file = "translations_cache.json"
        self.message_ids_cache = self._load_cache(self.cache_file)
        self.translation_cache = self._load_cache(self.translation_cache_file)
        self.translator = GoogleTranslator(source="auto", target="ru")

    def _load_cache(self, file_path: str) -> Dict:
        """Загружаем кэш из файла"""
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_cache(self, data: Dict, file_path: str):
        """Сохраняем кэш в файл"""
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    @lru_cache(maxsize=500)
    def _get_country_info_cached(
        self, country_code: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """Кэшированное получение информации о стране"""
        try:
            country = pycountry.countries.get(alpha_2=country_code.upper())
            flag_emoji = "".join(chr(ord(c) + 127397) for c in country.alpha_2)
            title = getattr(country, "common_name", country.name)
            return flag_emoji, title
        except (AttributeError, KeyError):
            return None, None

    async def get_country_info(
        self, country_code: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """Получаем информацию о стране с кэшированием"""
        return self._get_country_info_cached(country_code)

    async def get_localized_name(self, english_name: str) -> Optional[str]:
        """Переводим название страны на русский с кэшированием"""
        if english_name in self.translation_cache:
            return self.translation_cache[english_name]

        try:
            translated = self.translator.translate(english_name)
            if len(translated) <= 14 and any(
                "\u0400" <= c <= "\u04ff" for c in translated
            ):
                self.translation_cache[english_name] = translated
                self._save_cache(self.translation_cache, self.translation_cache_file)
                return translated
        except Exception as e: # Translation
            logger.error(f"Translation error for '{english_name}': {e}")

        return None

    async def get_message_id(self, flag_path: str) -> Optional[str]:
        """
        Загружает изображение флага в Telegram и возвращает file_id
        :param flag_path: Путь к файлу флага
        :return: file_id изображения или None при ошибке
        """
        if flag_path in self.message_ids_cache:
            return self.message_ids_cache[flag_path]

        try:
            # Отправляем фото в специальный чат (можно использовать свой ID)
            photo: types.PhotoSize = await self._upload_media(flag_path)

            if photo:
                file_id = photo.file_id
                self.message_ids_cache[flag_path] = file_id
                self._save_cache(self.message_ids_cache, self.cache_file)
                return file_id
        except Exception as e: # File
            logger.error(f"Error uploading media {flag_path}: {e}")

        return None

    async def _upload_media(self, file_path: str) -> Optional[types.PhotoSize]:
        """
        Внутренний метод для загрузки медиа
        :param file_path: Путь к файлу
        :return: Объект PhotoSize или None
        """
        try:
            await asyncio.sleep(2)
            # Отправляем в специальный чат (можно использовать свой ID)
            message = await bot.send_photo(
                chat_id=1894909159, photo=types.FSInputFile(path=file_path)
            )
            # Возвращаем наибольшее доступное фото (последний элемент в списке)
            return message.photo[-1] if message.photo else None
        except Exception as e: # exceptions.TelegramBadRequest
            logger.error(f"Error in _upload_media: {e}")
            return None

    async def process_all_flags(self):
        """Обрабатываем все флаги и сохраняем результат"""
        await asyncio.sleep(30)
        flags_data = []

        for index, flag_file in enumerate(os.listdir(self.flags_path), start=1):
            if not flag_file.endswith(".png"):
                continue

            country_code = flag_file[:-4]  # Удаляем .png
            emoji, english_name = await self.get_country_info(country_code)

            if not emoji or not english_name:
                logger.error(f"Skipping {flag_file} - country info not found")
                continue

            russian_name = await self.get_localized_name(english_name)
            if not russian_name:
                logger.error(f"Skipping {flag_file} - translation failed")
                continue

            flag_path = os.path.join(self.flags_path, flag_file)
            message_id = await self.get_message_id(flag_path)

            data = {
                "title": russian_name,
                "emoji": emoji,
                "correct": "",
                "path": flag_path,
                "media_id": message_id,
            }
            logger.debug(data)

            flags_data.append(data)

            # if index >= 20:
            #     break

        # Сохраняем в файл
        with open(BASE_DIR / self.output_file, "w", encoding="utf-8") as f:
            json.dump(flags_data, f, ensure_ascii=False, indent=4)

        logger.info(f"Processed {len(flags_data)} flags. Saved to {self.output_file}")
        return flags_data


class Flag:

    def __init__(self):
        self.output_file = "MainBot/utils/Games/GeoHunt/Data/geo.json"
        self.flags_path = "Data/Flags"
        self.count_var_respons = 4

    async def get_all_flags(self) -> list[str]:
        """
        Получаем все флаги
        """
        with open(BASE_DIR / self.output_file, "r", encoding="utf-8") as file:
            # return json.loads(file.read())
            datas = json.loads(file.read())

        if not datas[0].get("id"):
            ids: List[int] = []
            for data in datas:
                while True:
                    _id = random.randint(1000000000, 9999999999)
                    if _id not in ids:
                        break

                data["id"] = _id
                ids.append(_id)
            else:
                del ids

            with open(BASE_DIR / self.output_file, "w", encoding="utf-8") as file:
                file.write(json.dumps(datas, indent=4, ensure_ascii=False))

            return datas
        else:
            return datas

    async def get_step_flags(self) -> list[str]:
        """
        Получаем все флаги
        """
        list_flags = await self.get_all_flags()
        random.shuffle(list_flags)
        return list_flags

    async def get_flag_data(self, user: Users, redis_client: Redis) -> Dict:
        """
        Получаем наименование флага
        """
        data = []
        true_var = random.randint(1, 4)
        for index, step_flag_path in enumerate(await self.get_step_flags(), start=1):
            if len(data) == self.count_var_respons:
                break

            if index == true_var:
                step_flag_path["correct"] = "1"
                true_emoji = step_flag_path["emoji"]
                await redis_client.set(
                    f"geo_hunt_true_var:{user.user_id}",
                    json.dumps(
                        {"id": step_flag_path["id"], "title": step_flag_path["title"]},
                        ensure_ascii=False,
                    ),
                    ex=60,
                )
                photo_id = step_flag_path["media_id"]

            # NOTE можно добавить pydantic модель
            data.append(step_flag_path)

        return data, photo_id, true_emoji


class Build(Flag):

    def __init__(self):
        super().__init__()

    async def text(self, user_balance: float, energy: int, emoji: str) -> str:
        """
        Создаем текст для Игры
        """
        return texts.Game.GeoHunt.main.format(
            user_balance=user_balance, energy=energy, emoji=emoji
        )

    async def keyboard(self, datas: list[dict]) -> types.InlineKeyboardMarkup:
        """
        Создаем клавиатуру для Игры
        """
        inline_keyboard = []
        btns = []
        for data in datas:
            btns.append(
                types.InlineKeyboardButton(
                    text=data["title"],
                    callback_data="geo_hunt_click|{}".format(data["id"]),
                )
            )
            if len(btns) == 2:
                inline_keyboard.append(btns.copy())
                btns.clear()
        else:
            if btns:
                inline_keyboard.append(btns.copy())
            inline_keyboard.append(
                [
                    types.InlineKeyboardButton(
                        text=texts.Game.Btns.boosts, callback_data="boosts"
                    )
                ]
            )
            inline_keyboard.append(
                [
                    types.InlineKeyboardButton(
                        text=texts.Btns.back, callback_data="games"
                    )
                ]
            )

        return types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    async def media(self, path: str) -> Any:
        """
        Создаем объект медиа для Игры

        TODO пока что через файл, потом нужно сделать через id медиафайла
        """
        return types.FSInputFile(path=path)

    async def send(
        self,
        user: Users,
        message: types.Message,
        text: str,
        photo,
        keyboard: types.InlineKeyboardMarkup,
        new_msg: bool,
    ) -> int:
        """
        Отправляем сообщения
        """
        try:
            try:
                if new_msg:
                    raise Exception(
                        "Хотим сразу отправить сообщение без попытки изменить его"
                    )
                await message.edit_media(
                    media=types.InputMediaPhoto(media=photo, caption=text),
                    reply_markup=keyboard,
                )
                return message.message_id
            except: # exceptions.TelegramBadRequest
                message_data = await message.bot.send_photo(
                    chat_id=user.user_id,
                    photo=photo,
                    caption=text,
                    reply_markup=keyboard,
                )
                return message_data.message_id
        except: # exceptions.TelegramBadRequest
            logger.exception("2")
            return message.message_id


class GeoHuntMain(Build):

    def __init__(self):
        super().__init__()

    async def get_field(
        self,
        call: types.CallbackQuery,
        user: Users,
        redis_client: Redis,
        geo_hunter: Optional[GeoHunter] = None,
        new_msg: bool = False,
    ) -> int:
        """
        Собираем клавиатуру, текст и изображения
        """
        if not geo_hunter:
            geo_hunter = await GeoHunter_GameMethods().get_by_user(user)

        data, photo_id, true_emoji = await super().get_flag_data(user, redis_client)
        text = await super().text(user.starcoins, geo_hunter.current_energy, true_emoji)
        keyboard = await super().keyboard(data)
        return await super().send(user, call.message, text, photo_id, keyboard, new_msg)

    async def handle_click(
        self, call: types.CallbackQuery, user: Users, redis_client: Redis
    ) -> GeoHunter:
        """
        Обрабатывает клик по стране
        """
        _id = call.data.split("|")[1]

        # NOTE тут из редис получаем верный вариант и спавниваем с выбранным
        true_var = await redis_client.get(f"geo_hunt_true_var:{user.user_id}")
        true_var = json.loads(true_var)

        user_choice: bool = _id == str(true_var.get("id"))
        logger.debug(f"{call.from_user.id}: {_id} -> {user_choice}")

        data: dict = await GeoHunter_GameMethods().game_state(user=user)
        game_user = data["game_user"]

        if data["force_update_energy"]:
            from MainBot.utils.Games import GeoHuntManager

            await GeoHuntManager().force_update_energy(user)
            await Func.send_error_to_developer(
                "В ГЕОХантере Энергия пользователя {user_id} {tg_username} не восстановилось после истечения времени".format(
                    user_id=user.user_id,
                    tg_username=(
                        f"@{str(user.tg_username)}" if user.tg_username else "-"
                    ),
                )
            )

        # Проверяем энергию
        if game_user.current_energy <= 0:
            await call.answer(
                texts.Game.Error.no_energy.format(left_time=data["time_str"]),
                show_alert=True,
            )
            return

        # Обрабатываем клик
        game_user = await GeoHunter_GameMethods().process_click(user, user_choice)

        if game_user:
            await RabbitMQ().track_game(
                user.user_id,
                (
                    round((game_user.user.starcoins - user.starcoins), 2)
                    if user_choice
                    else 0
                ),
                "geohunter",
            )

        if user_choice:
            try:
                win_starcoins = round((game_user.user.starcoins - user.starcoins), 2)
                await call.answer(texts.Game.GeoHunt.yes.format(win=win_starcoins))
            except: # exceptions.TelegramBadRequest
                pass

            if data["first_click"]:
                from MainBot.utils.Games import GeoHuntManager

                await GeoHuntManager().schedule_energy_update(user)

        else:
            try:
                await call.answer(
                    texts.Game.GeoHunt.no.format(name=true_var.get("title"))
                )
            except: # exceptions.TelegramBadRequest
                pass

        return game_user


class GeoHuntMonitoring(GeoHuntMain):

    def __init__(self):
        self.redis = RedisManager()
        super().__init__()
        self.GEO_HUNT_TIMEOUT = 15
        self.MAX_TIMEOUT_COUNT = 3

    async def _game_session_timeout(
        self,
        call: types.CallbackQuery,
        user: Users,
        geo_hunter: Optional[GeoHunter],
        message_id: int,
    ) -> None:
        user_id = user.user_id
        bot = call.bot
        redis_client = await self.redis.get_redis()

        await asyncio.sleep(self.GEO_HUNT_TIMEOUT)

        session_data = await redis_client.hgetall(f"geo_hunt_session:{user_id}")
        if session_data:
            timeout_counter = (
                int(session_data.get(b"timeout_counter", b"0").decode()) + 1
            )

            await bot.delete_message(chat_id=user_id, message_id=message_id)
            await bot.send_message(
                chat_id=user_id, text=texts.Game.GeoHunt.time_over
            )

            await redis_client.delete(f"geo_hunt_session:{user_id}")

            # Проверяем, достигнут ли лимит
            if timeout_counter >= self.MAX_TIMEOUT_COUNT:
                from .. import LumberjackGame

                await LumberjackGame().msg_before_game(user, call)
            else:
                await self.get_field(
                    call,
                    user,
                    geo_hunter,
                    new_msg=True,
                    timeout_counter=timeout_counter,
                )  # передаем обновленный счетчик


    async def get_field(
        self,
        call: types.CallbackQuery,
        user: Users,  # TODO должен быть обновленным после добавления старкоинов
        geo_hunter: Optional[
            GeoHunter
        ] = None,  # TODO должен быть обновленным после вычета энергии
        new_msg: bool = False,
        timeout_counter: int = 0,
    ) -> None:
        """
        Удаляем существующую задачу если есть
        и создаем новую
        """
        user_id = user.user_id
        redis_client = await self.redis.get_redis()

        old_task_data = await redis_client.hgetall(f"geo_hunt_session:{user_id}")

        # Отменяем старую сессию, если есть
        if old_task_data and b"task_id" in old_task_data:
            try:
                # Получаем идентификатор задачи из Redis
                task_id = int(old_task_data[b"task_id"].decode())

                # Находим задачу среди текущих задач (это требует дополнительной реализации)
                for task in asyncio.all_tasks():
                    if id(task) == task_id:
                        task.cancel()
                        try:
                            await task  # Ожидаем завершения отменённой задачи
                        except asyncio.CancelledError:
                            pass
                        break

            except Exception as e:
                logger.error(f"Failed to cancel task {old_task_data[b'task_id']}: {e}")

        await redis_client.delete(f"geo_hunt_session:{user_id}")

        message_id = await super().get_field(
            call, user, redis_client, geo_hunter, new_msg
        )

        # Создаём задачу с таймаутом
        task = asyncio.create_task(
            self._game_session_timeout(call, user, geo_hunter, message_id)
        )
        expiry_time = datetime.datetime.now() + datetime.timedelta(
            seconds=self.GEO_HUNT_TIMEOUT
        )
        await redis_client.hset(
            f"geo_hunt_session:{user_id}",
            mapping={
                "task_id": str(id(task)),  # Идентификатор задачи
                "message_id": str(message_id),
                "expiry_time": expiry_time.isoformat(),
                "timeout_counter": str(timeout_counter),
            },
        )
        await redis_client.expire(
            f"geo_hunt_session:{user_id}", self.GEO_HUNT_TIMEOUT + 10
        )

    async def handle_click(self, call: types.CallbackQuery, user: Users) -> None:
        """
        Обрабатывает клик по стране
        """
        game_user = None
        user_id = user.user_id
        redis_client = await self.redis.get_redis()

        session_data = await redis_client.hgetall(f"geo_hunt_session:{user_id}")

        if not session_data:
            await call.answer(texts.Game.GeoHunt.time_over, show_alert=True)
        else:
            expiry_time = datetime.datetime.fromisoformat(
                session_data[b"expiry_time"].decode()  # что значит b
            )

            if datetime.datetime.now() > expiry_time:
                await call.answer(texts.Game.GeoHunt.time_over, show_alert=True)
            else:
                game_user = await super().handle_click(call, user, redis_client)

        await self.get_field(call, game_user.user if game_user else user, game_user)


class LockManager(GeoHuntMonitoring):
    def __init__(self):
        super().__init__()
        self.MIN_CLICK_INTERVAL = datetime.timedelta(seconds=1)
        self.cleanup_interval = datetime.timedelta(minutes=5)

    @asynccontextmanager
    async def user_lock(self, user_id: int) -> AsyncIterator[None]:
        """Контекстный менеджер для блокировки по user_id с использованием Redis"""
        redis_client = await self.redis.get_redis()
        lock_key = f"user_lock:{user_id}"
        last_used_key = f"last_used:{user_id}"

        try:
            # Пытаемся получить блокировку
            lock_acquired = await redis_client.set(
                lock_key,
                "locked",
                nx=True,  # NOTE означет что создаем только если его уже нет
                ex=int(self.cleanup_interval.total_seconds()),
            )

            if not lock_acquired:
                raise asyncio.TimeoutError("User is already locked")

            # Обновляем время последнего использования
            await redis_client.set(
                last_used_key,
                datetime.datetime.now().isoformat(),
                ex=int(self.cleanup_interval.total_seconds()),
            )

            yield
        finally:
            # Освобождаем блокировку
            await redis_client.delete(lock_key)

    async def speed_lock(
        self, call: types.CallbackQuery, user: Users
    ) -> Optional[bool]:
        user_id = user.user_id
        redis_client = await self.redis.get_redis()
        last_click_key = f"last_click:{user_id}"

        try:
            async with self.user_lock(user_id):
                now = datetime.datetime.now()

                # Проверяем последний клик
                last_click_str = await redis_client.get(last_click_key)
                if last_click_str:
                    last_click = datetime.datetime.fromisoformat(
                        last_click_str.decode()
                    )
                    if (now - last_click) < self.MIN_CLICK_INTERVAL:
                        await call.answer("⌛️")
                        return

                # Обновляем время последнего клика
                await redis_client.set(
                    last_click_key,
                    now.isoformat(),
                    ex=int(self.MIN_CLICK_INTERVAL.total_seconds() * 2),
                )

                # Ваша бизнес-логика
                user = await Sigma_BoostsForms().add_passive_income(user)
                from MainBot.utils.Games import GeoHuntManager

                await GeoHuntManager().schedule_energy_update(user)
                await super().handle_click(call, user)

        except asyncio.TimeoutError:
            await call.answer("⌛️")


class GeoHunt(LockManager):

    def __init__(self):
        super().__init__()
