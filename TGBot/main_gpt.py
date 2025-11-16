import asyncio
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

from GPTBot import start_bot as start_gpt_bot

base_dir = Path(__file__).resolve().parent

logger.add(
    sink=f'{base_dir}/logs_gpt/debug.log',
    format="| TIME:{time:HH:mm:ss} | LVL:{level} | FILE:{file} | LINE:{line} | FUNC:{function} |\n:::{message}",
    level="DEBUG",
    rotation="1000 KB"
)

async def run_bot():
    """Асинхронный запуск Telegram бота"""
    await start_gpt_bot()

if __name__ == '__main__':
    asyncio.run(run_bot())

