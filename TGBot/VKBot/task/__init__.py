__all__ = ["task_check"]

import asyncio

from loguru import logger
from VKBot.task.tg import TelegramSubscriptionChecker
from VKBot.task.vk import VkSubscriptionChecker


async def task_check():
    try:
        await asyncio.sleep(20)
        # Создаем оба проверяльщика
        vk_checker = VkSubscriptionChecker()
        tg_checker = TelegramSubscriptionChecker()

        try:
            # Запускаем обе проверки параллельно
            await asyncio.gather(vk_checker.start(), tg_checker.start())

            # Бесконечный цикл, чтобы task_check не завершался
            while True:
                await asyncio.sleep(3600)

        except asyncio.CancelledError:
            pass
        finally:
            # Корректное завершение
            await asyncio.gather(vk_checker.stop(), tg_checker.stop())
    except: # Safe
        logger.exception("Что-то с задачами на проверку подписок")


if __name__ == "__main__":
    try:
        asyncio.run(task_check())
    except KeyboardInterrupt:
        logger.info("Приложение остановлено")
