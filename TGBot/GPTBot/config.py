import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from config import BASE_DIR, debug

if debug:
    TOKEN = os.getenv("GPTBOT_TEST_TOKEN")
else:
    TOKEN = os.getenv("GPTBOT_BASE_TOKEN")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

DAILY_LIMIT = 10
TIMEOUT = 20  # в секундах
LIMITS_FILE = f"{BASE_DIR}/GPTBot/limits.json"
proxy_url = os.getenv("OPENAI_PROXY")
