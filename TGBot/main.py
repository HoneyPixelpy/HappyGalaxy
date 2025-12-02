import asyncio
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

# from UnitTest.utils.Forms.test_quests import run_check_idea_quest_test

load_dotenv()

from MainBot import start_bot as start_main_bot
from MainBot.utils.Games.Lumberjack.manager import EnergyUpdateManager as LumberjackEUM
from MainBot.utils.Games.GeoHunt.manager import EnergyUpdateManager as GeoHuntEUM
from Redis.notification import handle_rang_notifications, handle_continue_registration_mailing, \
    handle_auto_reject_old_quest_attempts
from VKBot import task_check

base_dir = Path(__file__).resolve().parent

logger.add(
    sink=f'{base_dir}/logs/debug.log',
    format="| TIME:{time:HH:mm:ss} | LVL:{level} | FILE:{file} | LINE:{line} | FUNC:{function} |\n:::{message}",
    level="DEBUG",
    rotation="1000 KB"
)

async def test():
    """Метод для тестирования"""
    # from MainBot.utils.Statistics import Statistics
    from MainBot.utils.Games.GeoHunt.main import FlagProcessor
    await FlagProcessor().process_all_flags()
    await asyncio.gather(
        start_main_bot(),
        FlagProcessor().process_all_flags()
    )
    # stats = Statistics()
    # await stats.get_all()

async def run_bot():
    """Асинхронный запуск Telegram бота"""
    # asyncio.create_task(Tasks().create_task_from_database_copy()) # NOTE копируем базу данных
    """
    Эти таски должны убраться в Celery и RabbitMQ
    """
    asyncio.create_task(handle_rang_notifications())
    asyncio.create_task(handle_continue_registration_mailing())
    asyncio.create_task(handle_auto_reject_old_quest_attempts())
    asyncio.create_task(task_check()) # NOTE проверяем не отписался ли пользователь от телеграмм и вк чатов
    asyncio.create_task(LumberjackEUM().check_pending_energy_updates()) # NOTE обновление энергии кликера
    asyncio.create_task(GeoHuntEUM().check_pending_energy_updates()) # NOTE обновление энергии геохантера
    # await test()
    await start_main_bot()

if __name__ == '__main__':
    asyncio.run(run_bot())

