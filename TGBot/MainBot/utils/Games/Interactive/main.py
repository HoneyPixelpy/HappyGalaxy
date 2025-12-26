import asyncio
import json
import math
from collections import namedtuple
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import config
import pytz
import redis.asyncio as redis
import texts
from aiogram import Bot, exceptions, types
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger
from MainBot.base.models import (
    GameType,
    InteractiveGameAllInfo,
    InteractiveGameBase,
    InteractiveGameData,
    InteractiveGameInfo,
    RewardType,
    Users,
)
from MainBot.base.orm_requests import InteractiveGameMethods, UserMethods
from MainBot.keyboards.inline import IKB as inline
from MainBot.keyboards.reply import KB as reply
from MainBot.state.state import SInteractiveGame
from MainBot.utils.MyModule.Functions import Func
from Redis.main import RedisManager

lock = asyncio.Lock()


class SupportInteractiveGame:

    async def check_key(self, key: str) -> bool:
        return key in ["clear", "delete"] + list(
            InteractiveGameBase.model_fields.keys()
        )

    async def check_required_data(self, data: dict) -> Optional[bool]:
        if (
            isinstance(data, dict)
            and data.get("title")
            and data.get("description")
            and data.get("reward_starcoins")
            and data.get("type_game")
        ):
            return True


class InteractiveGameStorage:

    def __init__(self):
        self._redis: redis.Redis = None

    async def set(
        self, user: Users, key: str, value: Any, prymary_key: str = "interactive_game"
    ) -> None:
        async with lock:
            if not self._redis:
                self._redis = await RedisManager().get_redis()

            # Сериализуем значение в JSON
            if not isinstance(value, (str, int, float, bool)) or value is None:
                value = json.dumps(value, ensure_ascii=False)

            await self._redis.hset(f"{prymary_key}:{user.user_id}", key, value)
            await self._redis.expire(f"{prymary_key}:{user.user_id}", 3600)

    async def get(
        self,
        user: Users,
        key: Optional[str] = None,
        prymary_key: str = "interactive_game",
    ) -> Optional[Union[str, dict]]:
        async with lock:
            if not self._redis:
                self._redis = await RedisManager().get_redis()
            if key:
                value = await self._redis.hget(f"{prymary_key}:{user.user_id}", key)

                if value is None:
                    return None

                value_str = value.decode("utf-8") if isinstance(value, bytes) else value

                # Пытаемся десериализовать JSON
                try:
                    return json.loads(value_str)
                except (json.JSONDecodeError, TypeError):
                    # Если не JSON, возвращаем как есть
                    return value_str
            else:
                data = await self._redis.hgetall(f"{prymary_key}:{user.user_id}")
                # Декодируем все байты в строки
                decoded_data = {}
                for k, v in data.items():
                    if isinstance(k, bytes):
                        k = k.decode("utf-8")

                    if isinstance(v, bytes):
                        v_str = v.decode("utf-8")
                    else:
                        v_str = str(v)

                    # Пытаемся десериализовать каждое значение
                    try:
                        decoded_data[k] = json.loads(v_str)
                    except (json.JSONDecodeError, TypeError):
                        decoded_data[k] = v_str

                return decoded_data

    async def clear(self, user: Users, prymary_key: str = "interactive_game") -> None:
        async with lock:
            if not self._redis:
                self._redis = await RedisManager().get_redis()
            await self._redis.delete(f"{prymary_key}:{user.user_id}")


class InteractiveGameDB:

    async def get_game(self, game_id: int) -> Optional[InteractiveGameBase]:
        return await InteractiveGameMethods().get(game_id)

    async def get_game_info(self, game_id: int) -> Optional[InteractiveGameInfo]:
        return await InteractiveGameMethods().get_info(game_id)

    async def create_game(
        self, user: Users, data: dict
    ) -> Optional[InteractiveGameBase]:
        return await InteractiveGameMethods().create(user, data)

    async def delete_rejected_game(self, game_id: int) -> Optional[InteractiveGameBase]:
        return await InteractiveGameMethods().delete_rejected(game_id)

    async def delete_pending_game(self, game_id: int) -> Optional[InteractiveGameInfo]:
        return await InteractiveGameMethods().delete_pending(game_id)

    async def success_game(self, game_id: int) -> Optional[InteractiveGameBase]:
        return await InteractiveGameMethods().success_game(game_id)

    async def active_users(self, game: InteractiveGameBase) -> List[Users]:
        active_users = await UserMethods().active_users(game.min_rang, game.max_rang)
        for active_user in active_users:
            if active_user.user_id == game.user.user_id:
                active_users.remove(active_user)
        return active_users

    async def invite_game(
        self, game_id: int, user: Users
    ) -> Optional[InteractiveGameBase]:
        return await InteractiveGameMethods().invite_game(game_id, user)

    async def start_game(self, game_id: int) -> Optional[InteractiveGameInfo]:
        return await InteractiveGameMethods().start_game(game_id)

    async def end_game(
        self, game_id: int, winers: List[str]
    ) -> Optional[InteractiveGameAllInfo]:
        return await InteractiveGameMethods().end_game(game_id, winers)


class NotificationInteractiveGame(InteractiveGameStorage, SupportInteractiveGame):

    def __init__(self):
        super().__init__()

    async def send_moderation(
        self, user: Users, call: CallbackQuery, game: InteractiveGameBase
    ) -> None:
        """
        Отправляем на модерацию
        """
        await call.message.delete()
        result_worker_game = texts.InteractiveGame.Create.result_worker_game.format(
            type_game=game.type_game,
            title=game.title,
            description=game.description,
            reward_starcoins=game.reward_starcoins,
            reward_type=game.reward_type,
            min_rang=game.min_rang,
            max_rang=game.max_rang,
            min_players=game.min_players,
            max_players=game.max_players,
        )
        await call.bot.send_message(
            chat_id=user.user_id,
            text=result_worker_game,
            reply_markup=await reply.main_menu(user),
        )
        await call.bot.send_message(
            chat_id=config.game_chat,
            text=result_worker_game
            + texts.InteractiveGame.Create.user_info_game.format(
                role=user.role_name,
                tg_info=await Func.format_tg_info(user.user_id, user.tg_username),
                gender=await Func.gender_name(user.gender, user.role_private),
                age=(datetime.now(pytz.timezone("Europe/Moscow")) - user.age).days
                // 365,
                title="Имя" if user.role_private == "child" else "ФИО",
                supername=user.supername,
                name=user.name,
                nickname=user.nickname,
                phone=user.phone,
                created_at=await Func.format_date(user.created_at),
                referral_count=await UserMethods().get_referral_count(user.user_id),
            ),
            reply_markup=await inline.verif_interactive_game(game.id),
        )
        await super().clear(user)

    async def send_delete(
        self, user: Users, call: CallbackQuery, game: InteractiveGameBase
    ) -> None:
        await call.answer("Game deleted", show_alert=True)
        await call.bot.send_message(
            chat_id=user.user_id,
            text=texts.InteractiveGame.Create.delete_game.format(title=game.title),
        )

    async def send_success(
        self, user: Users, call: CallbackQuery, game: InteractiveGameBase
    ) -> None:
        await call.answer("Game created", show_alert=True)
        await call.bot.send_message(
            chat_id=user.user_id,
            text=texts.InteractiveGame.Create.success_game.format(title=game.title),
        )

    async def send_no_active_users(self, user: Users, call: CallbackQuery) -> None:
        await call.bot.send_message(
            chat_id=user.user_id, text=texts.InteractiveGame.Ready.no_active_users
        )

    async def send_new_try_start(
        self, user: Users, call: CallbackQuery, game: InteractiveGameBase
    ) -> None:
        await call.bot.send_message(
            chat_id=user.user_id,
            text=texts.InteractiveGame.Ready.new_try_start.format(
                type_game=game.type_game, title=game.title
            ),
            reply_markup=await inline.new_try_interactive_game(game.id),
        )

    async def false_invite(self, call: CallbackQuery) -> None:
        await call.answer(text=texts.InteractiveGame.Invite.false)
        await call.message.delete()

    async def true_invite(
        self, user: Users, call: CallbackQuery, game: InteractiveGameBase
    ) -> None:
        # алерт для приглашенного
        await call.answer(text=texts.InteractiveGame.Invite.true)
        await call.message.delete()
        # сообщение для приглашенного
        await call.bot.send_message(
            chat_id=user.user_id,
            text=texts.InteractiveGame.Invite.notif_player.format(
                type_game=game.type_game,
                title=game.title,
                description=game.description,
                reward_starcoins=game.reward_starcoins,
                reward_type=game.reward_type,
            ),
        )
        # информируем админа
        await call.bot.send_message(
            chat_id=game.user.user_id,
            text=texts.InteractiveGame.Invite.notif_admin.format(
                user=await Func.format_tg_info(user.user_id, user.tg_username),
                title=game.title,
            ),
        )

    async def fail_delete_pending(self, call: CallbackQuery) -> None:
        await call.answer(text=texts.InteractiveGame.Ready.fail_delete_pending)

    async def send_delete_pending(
        self, user: Users, bot: Bot, game: InteractiveGameBase
    ) -> None:
        await bot.send_message(
            chat_id=user.user_id,
            text=texts.InteractiveGame.Invite.cancel.format(title=game.title),
        )

    async def send_error_activate_game(self, user: Users, bot: Bot) -> None:
        await bot.send_message(
            chat_id=user.user_id, text=texts.InteractiveGame.Activate.error
        )

    async def send_game_info(
        self,
        user: Users,
        game: InteractiveGameBase,
        bot: Bot,
        *,
        call: CallbackQuery = None,
    ) -> None:
        logger.debug(game.start_game_at)
        logger.debug(datetime.now(pytz.timezone("Europe/Moscow")))
        logger.debug(datetime.now(pytz.timezone("Europe/Moscow")) - game.start_game_at)
        text = texts.InteractiveGame.Activate.info.format(
            owner=await Func.format_nickname(
                user.user_id, game.user.nickname, game.user.name, game.user.supername
            ),
            type_game=game.type_game,
            title=game.title,
            description=game.description,
            reward_starcoins=game.reward_starcoins,
            reward_type=game.reward_type,
            start_time=game.start_game_at.strftime("%H:%M"),
            current_time=(
                datetime.now(pytz.timezone("Europe/Moscow")) - game.start_game_at
            ).seconds
            // 60,
        )
        keyboard = await inline.game_info(game.id, user.user_id == game.user.user_id)
        try:
            if not call:
                raise Exception("Надо просто отправить сообщение")
            await call.message.edit_text(text=text, reply_markup=keyboard)
        except:
            await bot.send_message(
                chat_id=user.user_id, text=text, reply_markup=keyboard
            )

    async def send_error_finally_game(self, user: Users, bot: Bot) -> None:
        await bot.send_message(
            chat_id=user.user_id, text=texts.InteractiveGame.Error._finally
        )

    async def send_error_end_game(self, user: Users, bot: Bot) -> None:
        await bot.send_message(
            chat_id=user.user_id, text=texts.InteractiveGame.End.error
        )

    async def send_result_game_creator(
        self,
        user: Users,
        bot: Bot,
        call: CallbackQuery,
        game_all_info: InteractiveGameAllInfo,
    ) -> None:
        text = texts.InteractiveGame.End.creator.format(
            title=game_all_info.game.title,
            count_winers=len(
                [
                    game_data
                    for game_data in game_all_info.game_datas
                    if game_data.result == "win"
                ]
            ),
            calc_starcoins=sum(
                [
                    game_data.reward_starcoins
                    for game_data in game_all_info.game_datas
                    if game_data.result == "win"
                ]
            ),
            count_losers=len(
                [
                    game_data
                    for game_data in game_all_info.game_datas
                    if game_data.result == "lose"
                ]
            ),
        )
        try:
            await call.message.edit_text(text=text)
        except:
            await bot.send_message(chat_id=user.user_id, text=text)

    async def send_result_game_logs_chat(
        self, bot: Bot, game_all_info: InteractiveGameAllInfo
    ) -> None:
        await bot.send_message(
            chat_id=config.game_chat,
            text=texts.InteractiveGame.End.logs.format(
                title=game_all_info.game.title,
                count_winers=len(
                    [
                        game_data
                        for game_data in game_all_info.game_datas
                        if game_data.result == "win"
                    ]
                ),
                calc_starcoins=sum(
                    [
                        game_data.reward_starcoins
                        for game_data in game_all_info.game_datas
                        if game_data.result == "win"
                    ]
                ),
                count_losers=len(
                    [
                        game_data
                        for game_data in game_all_info.game_datas
                        if game_data.result == "lose"
                    ]
                ),
            ),
        )

    async def send_result_game_win(
        self,
        user: Users,
        bot: Bot,
        game: InteractiveGameBase,
        game_data: InteractiveGameData,
    ) -> None:
        await bot.send_message(
            chat_id=user.user_id,
            text=texts.InteractiveGame.End.win.format(
                title=game.title, reward_starcoins=game_data.reward_starcoins
            ),
        )

    async def send_result_game_lose(
        self, user: Users, bot: Bot, game: InteractiveGameBase
    ) -> None:
        await bot.send_message(
            chat_id=user.user_id,
            text=texts.InteractiveGame.End.lose.format(title=game.title),
        )

    async def send_result_game_draw(
        self, user: Users, bot: Bot, game: InteractiveGameBase
    ) -> None:
        await bot.send_message(
            chat_id=user.user_id,
            text=texts.InteractiveGame.End.draw.format(title=game.title),
        )


class MainInteractiveGame(InteractiveGameDB, NotificationInteractiveGame):

    def __init__(self):
        super().__init__()


class CreateInteractiveGame(MainInteractiveGame):

    def __init__(self):
        super().__init__()

    async def create_text(self, data: dict) -> None:
        if data.get("reward_type"):
            reward_type = RewardType.items().get(data.get("reward_type"))
        else:
            reward_type = "..."

        if data.get("type_game"):
            type_game = GameType.items().get(data.get("type_game"))
        else:
            type_game = "..."

        return texts.InteractiveGame.Create.worker_game.format(
            title=data.get("title", "..."),
            description=data.get("description", "..."),
            reward_starcoins=data.get("reward_starcoins", "..."),
            reward_type=reward_type,
            min_rang=data.get("min_rang", "0"),
            max_rang=data.get("max_rang", "999999"),
            min_players=data.get("min_players", "0"),
            max_players=data.get("max_players", "999999"),
            type_game=type_game,
        )

    async def create_info_msg(
        self,
        user: Users,
        data: dict,
        *,
        call: Optional[CallbackQuery] = None,
        message: Optional[Message] = None,
    ) -> None:
        text = await self.create_text(data)
        if call:
            await call.message.edit_text(
                text,
                reply_markup=await inline.create_game(
                    await self.check_required_data(data)
                ),
            )
        else:
            await message.bot.send_message(
                chat_id=user.user_id,
                text=text,
                reply_markup=await inline.create_game(
                    await self.check_required_data(data)
                ),
            )

    async def request_title(
        self,
        user: Users,
        *,
        call: Optional[CallbackQuery] = None,
        message: Optional[Message] = None,
    ) -> None:
        try:
            if call:
                message = call.message

            await message.bot.send_message(
                chat_id=user.user_id,
                text=texts.InteractiveGame.Create.title,
                reply_markup=await reply.back(),
            )
        except Exception as ex:
            error_text = f"{__name__} -> {ex.__class__.__name__} -> {ex}"
            logger.exception(error_text)
            await Func.send_error_to_developer(error_text)

    async def request_description(
        self,
        user: Users,
        *,
        call: Optional[CallbackQuery] = None,
        message: Optional[Message] = None,
    ) -> None:
        try:
            if call:
                message = call.message

            await message.bot.send_message(
                chat_id=user.user_id,
                text=texts.InteractiveGame.Create.description,
                reply_markup=await reply.back(),
            )
        except Exception as ex:
            error_text = f"{__name__} -> {ex.__class__.__name__} -> {ex}"
            logger.exception(error_text)
            await Func.send_error_to_developer(error_text)

    async def request_reward_starcoins(
        self,
        user: Users,
        *,
        call: Optional[CallbackQuery] = None,
        message: Optional[Message] = None,
    ) -> None:
        try:
            if call:
                message = call.message

            await message.bot.send_message(
                chat_id=user.user_id,
                text=texts.InteractiveGame.Create.reward_starcoins,
                reply_markup=await reply.back(),
            )
        except Exception as ex:
            error_text = f"{__name__} -> {ex.__class__.__name__} -> {ex}"
            logger.exception(error_text)
            await Func.send_error_to_developer(error_text)

    async def request_reward_type(
        self,
        user: Users,
        *,
        call: Optional[CallbackQuery] = None,
        message: Optional[Message] = None,
    ) -> None:
        try:
            if call:
                message = call.message

            await message.bot.send_message(
                chat_id=user.user_id,
                text=texts.InteractiveGame.Create.reward_type,
                reply_markup=await reply.interactive_game_reward_type(),
            )
        except Exception as ex:
            error_text = f"{__name__} -> {ex.__class__.__name__} -> {ex}"
            logger.exception(error_text)
            await Func.send_error_to_developer(error_text)

    async def request_min_rang(
        self,
        user: Users,
        *,
        call: Optional[CallbackQuery] = None,
        message: Optional[Message] = None,
    ) -> None:
        try:
            if call:
                message = call.message

            await message.bot.send_message(
                chat_id=user.user_id,
                text=texts.InteractiveGame.Create.min_rang,
                reply_markup=await reply.back(),
            )
        except Exception as ex:
            error_text = f"{__name__} -> {ex.__class__.__name__} -> {ex}"
            logger.exception(error_text)
            await Func.send_error_to_developer(error_text)

    async def request_max_rang(
        self,
        user: Users,
        *,
        call: Optional[CallbackQuery] = None,
        message: Optional[Message] = None,
    ) -> None:
        try:
            if call:
                message = call.message

            await message.bot.send_message(
                chat_id=user.user_id,
                text=texts.InteractiveGame.Create.max_rang,
                reply_markup=await reply.back(),
            )
        except Exception as ex:
            error_text = f"{__name__} -> {ex.__class__.__name__} -> {ex}"
            logger.exception(error_text)
            await Func.send_error_to_developer(error_text)

    async def request_min_players(
        self,
        user: Users,
        *,
        call: Optional[CallbackQuery] = None,
        message: Optional[Message] = None,
    ) -> None:
        try:
            if call:
                message = call.message

            await message.bot.send_message(
                chat_id=user.user_id,
                text=texts.InteractiveGame.Create.min_players,
                reply_markup=await reply.back(),
            )
        except Exception as ex:
            error_text = f"{__name__} -> {ex.__class__.__name__} -> {ex}"
            logger.exception(error_text)
            await Func.send_error_to_developer(error_text)

    async def request_max_players(
        self,
        user: Users,
        *,
        call: Optional[CallbackQuery] = None,
        message: Optional[Message] = None,
    ) -> None:
        try:
            if call:
                message = call.message

            await message.bot.send_message(
                chat_id=user.user_id,
                text=texts.InteractiveGame.Create.max_players,
                reply_markup=await reply.back(),
            )
        except Exception as ex:
            error_text = f"{__name__} -> {ex.__class__.__name__} -> {ex}"
            logger.exception(error_text)
            await Func.send_error_to_developer(error_text)

    async def request_type_game(
        self,
        user: Users,
        *,
        call: Optional[CallbackQuery] = None,
        message: Optional[Message] = None,
    ) -> None:
        try:
            if call:
                message = call.message

            await message.bot.send_message(
                chat_id=user.user_id,
                text=texts.InteractiveGame.Create.type_game,
                reply_markup=await reply.interactive_game_type_game(),
            )
        except Exception as ex:
            error_text = f"{__name__} -> {ex.__class__.__name__} -> {ex}"
            logger.exception(error_text)
            await Func.send_error_to_developer(error_text)

    async def set_state(
        self, user: Users, call: CallbackQuery, key: str, state: FSMContext
    ) -> None:
        await state.set_state(SInteractiveGame.wait_data)
        await state.update_data(key=key)
        if key == "title":
            await self.request_title(user, call=call)
        elif key == "description":
            await self.request_description(user, call=call)
        elif key == "reward_starcoins":
            await self.request_reward_starcoins(user, call=call)
        elif key == "reward_type":
            await self.request_reward_type(user, call=call)
        elif key == "min_rang":
            await self.request_min_rang(user, call=call)
        elif key == "max_rang":
            await self.request_max_rang(user, call=call)
        elif key == "min_players":
            await self.request_min_players(user, call=call)
        elif key == "max_players":
            await self.request_max_players(user, call=call)
        elif key == "type_game":
            await self.request_type_game(user, call=call)

    async def edit_state(
        self, user: Users, message: Message, key: str, value: str, state: FSMContext
    ) -> None:
        logger.debug(key)
        logger.debug(value)
        if key == "title":
            if len(value) > 255:
                await message.answer(
                    texts.InteractiveGame.Error.title_too_long,
                    reply_markup=await reply.back(),
                )
                return
        elif key == "description":
            if len(value) > 1024:
                await message.answer(
                    texts.InteractiveGame.Error.description_too_long,
                    reply_markup=await reply.back(),
                )
                return
        elif key in [
            "reward_starcoins",
            "min_rang",
            "max_rang",
            "min_players",
            "max_players",
        ]:
            try:
                float(value)
            except ValueError:
                await message.answer(
                    texts.InteractiveGame.Error.reward_starcoins_not_number,
                    reply_markup=await reply.back(),
                )
                return
        elif key == "reward_type":
            if value not in RewardType.items().values():
                await message.answer(
                    texts.InteractiveGame.Error.reward_type_not_valid,
                    reply_markup=await reply.interactive_game_reward_type(),
                )
                return
            value = [k for k, v in RewardType.items().items() if v == value].pop()
        elif key == "type_game":
            if value not in GameType.items().values():
                await message.answer(
                    texts.InteractiveGame.Error.type_game_not_valid,
                    reply_markup=await reply.interactive_game_type_game(),
                )
                return
            value = [k for k, v in GameType.items().items() if v == value].pop()

        await super().set(user, key, value)
        await state.clear()
        data = await super().get(user)
        message_id = data.get("message_id")
        if message_id:
            try:
                await message.bot.delete_message(
                    chat_id=user.user_id, message_id=message_id
                )
            except:
                logger.warning(f"Не смогли удалить сообщение {__name__}")

        await self.create_info_msg(user, data, message=message)

    async def update(self, user: Users, call: CallbackQuery, state: FSMContext) -> None:
        """
        Здесь будем по инлайн кнопкам переходить в
        редактирование определенного поля нашей игры
        """
        key = call.data.split("|")[1]
        if not await super().check_key(key):
            await call.message.delete()
            return

        await super().set(user, "message_id", call.message.message_id)

        if key == "clear":
            await super().clear(user)
            await self.create_info_msg(user, {}, call=call)
        elif key == "delete":
            await call.message.delete()
            await super().clear(user)
            await call.bot.send_message(
                chat_id=user.user_id,
                text=texts.Texts.start,
                reply_markup=await reply.main_menu(user),
            )
        else:
            await call.message.delete_reply_markup()
            await self.set_state(user, call, key, state)

    async def edit(self, user: Users, message: Message, state: FSMContext) -> None:
        """
        Здесь принимаем значение для изменения
        """
        data = await state.get_data()
        key = data.get("key")
        logger.debug(key)

        await self.edit_state(user, message, key, message.text, state)

    async def create_game(self, user: Users, call: CallbackQuery) -> None:
        """
        Создаем игру
        Отправляем ее на модерацию
        """
        data = await super().get(user)
        if await super().check_required_data(data):
            if data.get("message_id"):
                del data["message_id"]
            game = await super().create_game(user, data)
            if game:
                await super().send_moderation(user, call, game)
            else:
                await call.answer(texts.Error.Notif.server_error)
        else:
            await call.answer(texts.InteractiveGame.Error.not_all_fields)


class ReadyInteractiveGame(MainInteractiveGame):

    async def mailing_text(self, game: InteractiveGameBase) -> None:
        return texts.InteractiveGame.Ready.mailing_text.format(
            title=game.title, description=game.description
        )

    async def login_game_kb(self, game: InteractiveGameBase) -> None:
        return await inline.login_game(game.id)

    async def invite_mailing(
        self,
        user: Users,
        bot: Bot,
        active_users: List[Users],
        game: InteractiveGameBase,
    ) -> None:
        mailing_fun = await Func.constructor_func_to_mailing_one_msg(
            bot,
            "",
            "",
            False,
            await self.mailing_text(game),
            await self.login_game_kb(game),
        )
        received = 0
        for active_user in active_users:
            # if active_user.user_id == game.user.user_id: continue
            if not await super().get(user, prymary_key=f"mailing_new_game:{game.id}"):
                break
            try:
                await mailing_fun(active_user)
                received += 1
                await super().set(
                    user, "received", received, f"mailing_new_game:{game.id}"
                )

                await asyncio.sleep(1)

            except exceptions.TelegramRetryAfter as ex:
                logger.error(f"Сработало исключение!!!\n!!!{ex}")
            except Exception as ex:
                logger.error(f"Сработало исключение!!!\n!!!{ex}")

        else:
            await bot.send_message(
                chat_id=user.user_id, text="💡 <b>ВСЕ ПРИГЛАШЕНИЯ БЫЛИ РАЗОСЛАНЫ</b>\n"
            )
            await super().set(
                user,
                "received",
                f"Завершена на {received} пользователей",
                f"mailing_new_game:{game.id}",
            )

    async def progress_text(
        self,
        game: InteractiveGameBase,
        in_users: int,
        received: Union[int, str],
        all_users: int,
    ) -> None:
        return texts.InteractiveGame.Ready.ready_game.format(
            type_game=game.type_game,
            title=game.title,
            progress=(
                received if isinstance(received, str) else f"{received}/{all_users}"
            ),
            _in=in_users,
            _all=min(all_users, game.max_players),
        )

    async def ready_kb(
        self, game: InteractiveGameBase, end_mailing: bool = False
    ) -> types.InlineKeyboardMarkup:
        return await inline.ready_game(game.id, end_mailing)

    async def refresh_ready_info(
        self, user: Users, call: CallbackQuery, game: Union[InteractiveGameBase, int]
    ) -> None:
        """
        Обновляем информацию об игре
        """
        if isinstance(game, int):
            game = await super().get_game(game)

        if not game:
            await call.answer(texts.InteractiveGame.Error.delete_already)
            await call.message.delete()
            return

        in_users = await super().get(user, "in_users", f"mailing_new_game:{game.id}")
        received = await super().get(user, "received", f"mailing_new_game:{game.id}")
        all_users = await super().get(user, "all_users", f"mailing_new_game:{game.id}")

        text = await self.progress_text(game, in_users, received, all_users)
        keyboard = await self.ready_kb(game, isinstance(received, str))

        await call.bot.send_message(
            chat_id=user.user_id, text=text, reply_markup=keyboard
        )
        await call.message.delete()

    async def invite_action(
        self, user: Users, call: CallbackQuery, game: InteractiveGameBase
    ) -> None:
        """
        Принимаем приглашение
        """
        received = await super().get(
            game.user, "in_users", f"mailing_new_game:{game.id}"
        )
        await super().set(
            game.user, "in_users", int(received) + 1, f"mailing_new_game:{game.id}"
        )
        await super().true_invite(user, call, game)

    async def delete_game_mailing(
        self, bot: Bot, game: InteractiveGameBase, users: List[Users]
    ) -> None:
        for user in users:
            try:
                await super().send_delete_pending(user, bot, game)
                await asyncio.sleep(1)
            except exceptions.TelegramRetryAfter as ex:
                logger.error(f"Сработало исключение!!!\n!!!{ex}")
            except Exception as ex:
                logger.error(f"Сработало исключение!!!\n!!!{ex}")

    async def delete_pending(
        self, user: Users, call: CallbackQuery, game_info: InteractiveGameInfo
    ) -> None:
        """
        Удаляем во время инвайтов
        """
        try:
            await call.message.delete()
        except:
            pass
        await super().clear(user, f"mailing_new_game:{game_info.game.id}")
        await self.delete_game_mailing(call.bot, game_info.game, game_info.users)


class StartInteractiveGame(MainInteractiveGame):

    async def mailing_start_game(
        self, bot: Bot, users: List[Users], game: InteractiveGameBase
    ) -> None:
        for user in users:
            if not await super().get(user, prymary_key=f"mailing_start_game:{game.id}"):
                break
            try:
                await super().send_game_info(user, game, bot)
                await asyncio.sleep(1)
            except exceptions.TelegramRetryAfter as ex:
                logger.error(f"Сработало исключение!!!\n!!!{ex}")
            except Exception as ex:
                logger.error(f"Сработало исключение!!!\n!!!{ex}")

        else:
            await super().clear(user, f"mailing_start_game:{game.id}")

    async def activate_game(
        self, user: Users, call: CallbackQuery, game_info: InteractiveGameInfo
    ) -> None:
        """
        Активируем игру
        Делаем рассылку о начале игры
        """
        await super().clear(user, f"mailing_new_game:{game_info.game.id}")

        await super().send_game_info(user, game_info.game, call.bot, call=call)

        await super().set(user, "status", 1, f"mailing_start_game:{game_info.game.id}")

        await self.mailing_start_game(call.bot, game_info.users, game_info.game)


class PlayersPanel(MainInteractiveGame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.buttons_line = 4

    async def players_text(
        self,
        user: Users,
        selected: List[int],
        users: List[Users],
        pagination: int = 1,
        title: str = "distribution_reward",
    ) -> str:
        # NOTE Протестировать на нескольких юзерах
        text = texts.InteractiveGame.Players.__dict__[title]
        text += texts.InteractiveGame.Players.title

        lp = pagination * self.buttons_line
        sp = lp - self.buttons_line
        for index, user in enumerate(users):
            if index >= sp and index < lp:
                text += texts.InteractiveGame.Players.user.format(
                    emoji=(
                        texts.InteractiveGame.Players.Emoji.cgreen
                        if str(user.user_id) in selected
                        else texts.InteractiveGame.Players.Emoji.cgrey
                    ),
                    name=await Func.format_nickname(
                        user.user_id, user.nickname, user.name, user.supername
                    ),
                )
        return text

    async def markup_data(
        self,
        users: List[Users],
        game: InteractiveGameBase,
        callback_data: str,
        pagination: int = 1,
    ) -> List[Dict]:
        # NOTE Протестировать на нескольких юзерах
        data = []
        lp = pagination * self.buttons_line
        sp = lp - self.buttons_line
        for index, user in enumerate(users):
            if index >= sp and index < lp:
                data.append(
                    {
                        "title": await Func.get_emoji_number(index + 1),
                        "callback_data": f"{callback_data}|{user.user_id}|{game.id}|{pagination}",
                    }
                )
        return data

    async def build_reply_markup(
        self,
        game_info: InteractiveGameInfo,
        selected: List[int],
        callback_data: str,
        pagination: int = 1,
    ) -> types.InlineKeyboardMarkup:
        # NOTE Протестировать на нескольких юзерах
        inline_keyboard = []
        data = await self.markup_data(
            game_info.users, game_info.game, callback_data, pagination
        )
        inline_keyboard.extend(
            [
                [
                    types.InlineKeyboardButton(
                        text=(
                            texts.InteractiveGame.Btns.calculate_victory
                            if selected
                            else "✖️"
                        ),
                        callback_data=(
                            f"end_game|{game_info.game.id}" if selected else "null"
                        ),
                    )
                ]
            ]
        )

        inline_keyboard.extend(
            [
                [
                    types.InlineKeyboardButton(
                        text=texts.InteractiveGame.Btns.in_all,
                        callback_data=f"s_player_end_game|all|{game_info.game.id}|{pagination}",
                    ),
                    types.InlineKeyboardButton(
                        text=texts.InteractiveGame.Btns.clear,
                        callback_data=f"s_player_end_game|clear|{game_info.game.id}|{pagination}",
                    ),
                ]
            ]
        )

        keyboard = await inline.buttons(data, self.buttons_line)
        pagboard = await inline.pagination(
            f"players_end_game|{game_info.game.id}",
            pagination,
            math.ceil(len(game_info.users) / self.buttons_line),
        )
        inline_keyboard.extend(keyboard.inline_keyboard)
        inline_keyboard.extend(pagboard.inline_keyboard)
        inline_keyboard.extend(
            [
                [
                    types.InlineKeyboardButton(
                        text=texts.Btns.back,
                        callback_data=f"refresh_info_game|{game_info.game.id}",
                    )
                ]
            ]
        )
        return types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    async def players_info(
        self,
        user: Users,
        bot: Bot,
        game_info: InteractiveGameInfo,
        pagination: int = 1,
        call: Optional[CallbackQuery] = None,
    ) -> None:
        selected = await super().get(
            user, "selected", prymary_key=f"s_player_end_game|{game_info.game.id}"
        )
        if not selected:
            selected = []

        text = await self.players_text(user, selected, game_info.users, pagination)
        kb = await self.build_reply_markup(
            game_info, selected, "s_player_end_game", pagination
        )
        if call:
            await call.message.edit_text(text, reply_markup=kb)
        else:
            await bot.send_message(user.user_id, text, reply_markup=kb)


class FinallyInteractiveGame(PlayersPanel):

    async def finally_game(
        self,
        user: Users,
        call: CallbackQuery,
        game_info: InteractiveGameInfo,
        pagination: int = 1,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Завершаем игру
        """
        if user_id:
            selected = await super().get(
                user, "selected", prymary_key=f"s_player_end_game|{game_info.game.id}"
            )
            if not selected:
                selected = []

            if user_id == "clear":
                selected.clear()
            elif user_id == "all":
                selected.clear()
                selected.extend([str(u.user_id) for u in game_info.users])
            elif user_id not in selected:
                selected.append(user_id)
            else:
                selected.remove(user_id)

            await super().set(
                user, "selected", selected, f"s_player_end_game|{game_info.game.id}"
            )

        await super().players_info(user, call.bot, game_info, pagination, call=call)

    async def result_game(
        self, user: Users, call: CallbackQuery, game_all_info: InteractiveGameAllInfo
    ) -> None:
        """
        Уведомляем создателя
        Уведомляем базу результатами
        Уведомляем участников
        """
        bot = call.bot
        await super().send_result_game_creator(user, bot, call, game_all_info)
        await super().send_result_game_logs_chat(bot, game_all_info)

        for game_data in game_all_info.game_datas:
            try:
                if game_data.creator:
                    continue

                if game_data.result == "win":
                    await super().send_result_game_win(
                        game_data.user, bot, game_all_info.game, game_data
                    )
                elif game_data.result == "lose":
                    await super().send_result_game_lose(
                        game_data.user, bot, game_all_info.game
                    )
                elif game_data.result == "draw":
                    await super().send_result_game_draw(
                        game_data.user, bot, game_all_info.game
                    )

                await asyncio.sleep(1)

            except exceptions.TelegramRetryAfter as ex:
                logger.error(f"Сработало исключение!!!\n!!!{ex}")
            except Exception as ex:
                logger.error(f"Сработало исключение!!!\n!!!{ex}")


class InteractiveGame(
    CreateInteractiveGame,
    ReadyInteractiveGame,
    StartInteractiveGame,
    FinallyInteractiveGame,
):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def create_info(
        self,
        user: Users,
        *,
        call: Optional[CallbackQuery] = None,
        message: Optional[Message] = None,
    ) -> None:
        """
        Здесь будем определять может ли пользователь создавать игры или нет

        Надо проверить есть ли активная игра у пользователя
        Может ли он вообще их создавать
        """
        if call:
            message = call.message
            try:
                await message.delete()
            except:
                pass

        await super().set(user, "type_game", "all")
        await super().set(user, "title", "Шахматы")
        await super().set(user, "description", "Дефолт")
        await super().set(user, "reward_starcoins", 5)
        await super().set(user, "reward_type", "from_all_wins")

        data = await self.get(user)
        if data.get("key"):
            del data["key"]
        await self.create_info_msg(user, data, message=message)

    async def success_create_game(
        self, user: Users, call: CallbackQuery, game_id: int
    ) -> None:
        """
        Создание игры успешно
        """
        success_game = await super().success_game(game_id)
        if success_game:
            # NOTE тут можно убрать повторное сообщение об одобрении при попытке повторно начать игру
            await super().send_success(user, call, success_game)
            await self.ready_info(user, call, success_game)
        else:
            logger.warning(f"RESULT: {str(success_game)}")
            await Func.send_error_to_developer(
                f"Пользователь Telegram {user.user_id} @{str(user.tg_username)} не смог Подтвердить игру {game_id}"
            )
            await call.answer(texts.Error.Notif.server_error)

    async def delete_create_game(
        self, user: Users, call: CallbackQuery, game_id: int
    ) -> None:
        """Удаление игры
        Удаляем запись
        Уведомляем создателя
        """
        try:
            delete_game = await super().delete_rejected_game(game_id)
            if delete_game:
                await super().clear(user)
                await super().send_delete(user, call, delete_game)
            else:
                logger.warning(f"RESULT: {str(delete_game)}")
                await Func.send_error_to_developer(
                    f"Пользователь Telegram {user.user_id} @{str(user.tg_username)} не смог Удалить игру {game_id}"
                )
                await call.answer(texts.Error.Notif.server_error)
        finally:
            await call.message.delete_reply_markup()

    async def ready_info(
        self, user: Users, call: CallbackQuery, game: InteractiveGameBase
    ) -> None:
        """Инфа после подтверждения
        Делаем рассылку по активным пользователям которые подходят по рангу и роли
        Создатель получает панель с пользователями которые получили приглашение, приняли его и инфа по принятым
        """
        active_users: List[Users] = await super().active_users(game)
        if not active_users:
            await super().send_no_active_users(user, call)
            await super().send_new_try_start(user, call, game)
            return

        await super().set(user, "in_users", 0, f"mailing_new_game:{game.id}")
        await super().set(user, "received", 0, f"mailing_new_game:{game.id}")
        await super().set(
            user, "all_users", len(active_users), f"mailing_new_game:{game.id}"
        )

        await super().refresh_ready_info(game.user, call, game)
        await super().invite_mailing(game.user, call.bot, active_users, game)

    async def invite_game(self, user: Users, call: CallbackQuery, game_id: int) -> None:
        game = await super().invite_game(game_id, user)
        if game:
            await super().invite_action(user, call, game)
        else:
            await super().false_invite(call)

    async def delete_game(self, user: Users, call: CallbackQuery, game_id: int) -> None:
        game_info = await super().delete_pending_game(game_id)
        if game_info:
            await super().delete_pending(user, call, game_info)
        else:
            await super().fail_delete_pending(call)

    async def start_game(self, user: Users, call: CallbackQuery, game_id: int) -> None:
        game_info = await super().start_game(game_id)
        if game_info:
            await super().activate_game(user, call, game_info)
        else:
            await super().send_error_activate_game(user, call.bot)

    async def refresh_info(
        self, user: Users, call: CallbackQuery, game_id: int
    ) -> None:
        game = await super().get_game(game_id)
        if not game:
            await call.answer(texts.InteractiveGame.Error.delete_already)
            await call.message.delete()
            return

        await call.message.delete()
        await super().send_game_info(user, game, call.bot, call=call)

    async def finally_game(
        self,
        user: Users,
        call: CallbackQuery,
        game_id: int,
        pagination: int = 1,
        user_id: Optional[str] = None,
    ) -> None:
        game_info = await super().get_game_info(game_id)
        if game_info:
            await super().finally_game(user, call, game_info, pagination, user_id)
        else:
            await super().send_error_finally_game(user, call.bot)

    async def end_game(self, user: Users, call: CallbackQuery, game_id: int) -> None:
        game_info = await super().get_game_info(game_id)
        if game_info:
            winers = await super().get(
                user, "selected", prymary_key=f"s_player_end_game|{game_info.game.id}"
            )

            game_result = await super().end_game(game_id, winers)
            if game_result:
                await super().clear(user, f"s_player_end_game|{game_info.game.id}")
                await super().result_game(user, call, game_result)
            else:
                await super().send_error_end_game(user, call.bot)
        else:
            await super().send_error_finally_game(user, call.bot)

    # async def kik_player(
    #     self,
    #     user: Users,
    #     call: CallbackQuery,
    #     game: InteractiveGameBase
    #     ) -> None:
    #     pass

    # async def invite_player(
    #     self,
    #     user: Users,
    #     call: CallbackQuery,
    #     game: InteractiveGameBase
    #     ) -> None:
    #     pass

    async def more_players(
        self, user: Users, call: CallbackQuery, game: InteractiveGameBase
    ) -> None:
        pass

    async def comment_game(
        self, user: Users, call: CallbackQuery, game: InteractiveGameBase
    ) -> None:
        pass

    async def evaluate_player(
        self, user: Users, call: CallbackQuery, game: InteractiveGameBase
    ) -> None:
        pass
