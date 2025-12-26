import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

import redis.asyncio as redis
import texts
from aiogram import types
from aiogram.fsm.context import FSMContext
from loguru import logger
from MainBot.state.state import Msg_Delete
from MainBot.utils.errors import ListLengthChangedError, NoDesiredTypeError
from MainBot.utils.MyModule import Func

from .main import RedisManager

lock = asyncio.Lock()


class RedisAggregator:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.timeout = 1  # seconds to wait for additional messages
        self.expire_time = 5
        self.aggregation_key = "user_aggregation:{}"

    async def add_message(self, user_id: int, message_data: Dict[str, Any]) -> int:
        """
        Собираем данные в redis
        Ждем

        return:
            len_data: int -> длина списка после добавления.
        """
        if not self.redis:
            self.redis = await RedisManager().get_redis()
        key = self.aggregation_key.format(user_id)

        await self.redis.rpush(key, json.dumps(message_data))

        len_data = await self.redis.llen(key)

        if len_data == 1:
            await self.redis.expire(key, self.expire_time)

        await asyncio.sleep(self.timeout)
        return len_data

    async def check_len_message(self, user_id: int, len_data: int) -> None:
        """
        Проверяем длину данных в redis
        Если не соответствует, вызываем ошибку
        """
        if not self.redis:
            self.redis = await RedisManager().get_redis()
        key = self.aggregation_key.format(user_id)

        if len_data != await self.redis.llen(key):
            raise ListLengthChangedError()

    async def get_message(self, user_id: int) -> Dict[str, List[Any]]:
        """
        Получаем данные которые успели сохранить
        """
        if not self.redis:
            self.redis = await RedisManager().get_redis()
        key = self.aggregation_key.format(user_id)

        messages = await self.redis.lrange(key, 0, -1)
        await self.redis.delete(key)

        msg_datas = [json.loads(msg) for msg in messages]

        return {
            "text": [msg_data["text"] for msg_data in msg_datas],
            "content_type": [msg_data["content_type"] for msg_data in msg_datas],
            "media_content": [msg_data["media_content"] for msg_data in msg_datas],
            "media_group_id": [msg_data["media_group_id"] for msg_data in msg_datas],
        }


class MessageAggregator(RedisAggregator):
    def __init__(self):
        super().__init__()

    async def add_message(
        self, user_id: int, message: types.Message, state: FSMContext, state_data: Dict
    ) -> Dict[str, List[Any]]:
        """
        Проверяем итоговые данные на контент
        """
        text, content_type, media_content, media_group_id = await Func.parsing_message(
            message
        )

        len_data = await super().add_message(
            user_id,
            {
                "text": text,
                "content_type": content_type,
                "media_content": media_content,
                "media_group_id": media_group_id,
            },
        )
        async with lock:
            await super().check_len_message(user_id, len_data)
            await state.set_state(Msg_Delete.Activate)

            msg_datas: Dict = await super().get_message(user_id)

        try:
            content_value = state_data["content"].value
        except AttributeError:
            content_value = state_data["content"]

        if content_value == "visible":
            visible_types: Set[str] = await Func.get_media_types("visible")

            desired_result = None
            for content_type in msg_datas["content_type"]:
                if content_type in visible_types:
                    desired_result = True

            if not desired_result:
                await message.answer(text=texts.Quests.Error.no_media)
                raise NoDesiredTypeError()
        elif content_value == "description":
            if not any(msg_datas["text"]):
                await message.answer(text=texts.Quests.Error.no_descr)
                raise NoDesiredTypeError()
        elif content_value == "any":
            pass
        else:
            logger.exception("Неизвестная ошибка")
            await message.answer(text=texts.Error.Notif.undefined_error)
            raise NoDesiredTypeError()

        return msg_datas


class QuestAggregator(MessageAggregator):
    def __init__(self):
        super().__init__()
