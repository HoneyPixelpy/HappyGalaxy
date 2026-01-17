# В вашем Telegram боте добавьте обработчик Redis
import asyncio
import json
from typing import Any, Coroutine, Dict, List

import texts
from aiogram import exceptions, types
from loguru import logger
from MainBot.config import bot
from MainBot.keyboards import inline
from MainBot.utils.Rabbitmq import RabbitMQ
from redis import Redis

from .main import RedisManager


async def handle_rang_notifications(*args, **kwargs) -> None:
    """Фоновая задача для обработки уведомлений о рангах"""
    redis_obj = RedisManager()
    redis_client: Redis = await redis_obj.get_redis()
    while True:
        try:
            # Проверяем Redis на наличие уведомлений
            notification_json = await redis_client.lpop("rang_notifications")

            if notification_json:
                notification = json.loads(notification_json)
                await send_rang_upgrade_message(
                    notification["user_id"],
                    notification["new_rang_name"],
                    notification["new_rang_emoji"],
                    notification["new_quests"],
                )

            await asyncio.sleep(1)

        except Exception as e: # exceptions.TelegramBadRequest
            logger.error(f"Error in rang notification handler: {e}")
            await asyncio.sleep(3)


async def send_rang_upgrade_message(
    user_id: int, new_name: str, new_emoji: str, new_quests: bool
) -> None:
    """Отправить сообщение о повышении ранга"""
    try:
        if new_quests:
            text = texts.Season.Texts.new_rang_new_quests.format(
                emoji=new_emoji, name=new_name
            )
        else:
            text = texts.Season.Texts.new_rang_no_quests.format(
                emoji=new_emoji, name=new_name
            )

        await bot.send_message(
            chat_id=user_id, text=text, reply_markup=await inline.new_rang(new_quests)
        )

    except Exception as e: # exceptions.TelegramBadRequest
        logger.error(f"Failed to send rang upgrade message to {user_id}: {e}")


async def handle_continue_registration_mailing(*args, **kwargs) -> None:
    """
    Делаем рассылку для того чтобы пользователи продолжали регу
    """
    redis_obj = RedisManager()
    redis_client: Redis = await redis_obj.get_redis()
    while True:
        try:
            # Проверяем Redis на наличие уведомлений
            continue_registration_json = await redis_client.lpop(
                "bot:continue_registration"
            )

            if continue_registration_json:
                continue_registration = json.loads(continue_registration_json)
                await continue_registration_mailing(continue_registration["user_ids"])
            await asyncio.sleep(1)

        except Exception as e: # Redis
            logger.error(f"Error in rang notification handler: {e}")
            await asyncio.sleep(3)


async def continue_registration_mailing(
    user_ids: List[int],
) -> None:
    """Отправить сообщение о повышении ранга"""
    number = 0

    for user_id in user_ids:
        try:
            await bot.send_message(
                chat_id=user_id, text=texts.Profile.Texts.continue_registration
            )
            number += 1
            if number % 10 == 0:
                logger.debug(
                    f"Юзеров получило уже - {number} о предложении продолжить регистарцию"
                )
            await asyncio.sleep(0.3)
        except exceptions.TelegramRetryAfter as ex:
            logger.error(f"Сработало исключение!!!\n!!!{ex}")
            # await asyncio.sleep(ex.retry_after)
            continue
        except Exception as ex: # exceptions.TelegramBadRequest
            logger.error(f"Сработало исключение!!!\n!!!{ex}")
            continue

    logger.info(
        f"💡 РАССЫЛКА ВЫПОЛНЕНА 💡\nПредложение продолжить регистрацию получило: {number} /челбанов"
    )


async def handle_auto_reject_old_quest_attempts(*args, **kwargs) -> None:
    redis_obj = RedisManager()
    redis_client: Redis = await redis_obj.get_redis()
    while True:
        try:
            # Проверяем Redis на наличие уведомлений
            old_quests_data = await redis_client.lpop("bot:old_quests")

            if old_quests_data:
                auto_reject_attempts = json.loads(old_quests_data)
                await auto_reject_old_quest_attempts(
                    auto_reject_attempts["mailing_data"]
                )
            await asyncio.sleep(1)

        except Exception as e: # Redis
            logger.error(f"Error in rang notification handler: {e}")
            await asyncio.sleep(3)


async def auto_reject_old_quest_attempts(
    mailing_datas: List[Dict],
) -> None:
    """
    Отправить сообщение об отказе в апруве квеста
    """
    number = 0

    for mailing_data in mailing_datas:
        await RabbitMQ().track_quest(  # NOTE в приоритете перекинуть работу с kafka на сторону django
            mailing_data["user_id"],
            mailing_data["quest_id"],
            action="auto_rejected",
        )

        try:
            await bot.send_message(
                chat_id=mailing_data["user_id"],
                text=texts.Quests.Texts.idea_deny.format(mailing_data["title"]),
                reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(
                                text=texts.Quests.Btns.go_activate,
                                callback_data=f"get_quest|{mailing_data['type_quest']}|{mailing_data['quest_id']}",
                            )
                        ]
                    ]
                ),
                disable_notification=True,
            )
            number += 1
            if number % 10 == 0:
                logger.debug(
                    f"Юзеров получило уже - {number} о просроченном квесте"
                )
            await asyncio.sleep(0.3)
        except exceptions.TelegramRetryAfter as ex:
            logger.error(f"Сработало исключение!!!\n!!!{ex}")
            # await asyncio.sleep(ex.retry_after)
            continue
        except Exception as ex: # exceptions.TelegramBadRequest
            logger.exception(f"Сработало исключение!!!\n!!!{ex}")
            continue

    logger.info(
        f"💡 РАССЫЛКА ВЫПОЛНЕНА 💡\nО просроченном кве получило: {number} /челбанов"
    )

