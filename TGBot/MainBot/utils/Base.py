import asyncio
import datetime
import os

import aiofiles
from aiogram import Bot, types
from config import BASE_DIR, log_chat
from loguru import logger
from MainBot.base.orm_requests import CopyBaseMethods
from MainBot.config import bot


class CopyBase:

    @classmethod
    async def copy_bd(cls, target_time: datetime.datetime) -> None:
        formatted_time = target_time.strftime("%d-%m-%Y_%H-%M")
        filename = f"db_copy_{formatted_time}.sqlite3"
        backup_path = BASE_DIR / filename

        try:

            content = await CopyBaseMethods().copy_base()

            async with aiofiles.open(backup_path, "wb") as f:
                await f.write(content)

            await bot.send_document(
                chat_id=1894909159,
                document=types.FSInputFile(path=backup_path, filename=filename),
                caption=f"Копия базы данных на {formatted_time}",
            )

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise  # Для retry в Celery
        finally:
            if os.path.exists(backup_path):
                os.remove(backup_path)
