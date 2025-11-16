import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from config import debug


if debug:
    TOKEN = os.getenv('MAIN_TEST_TOKEN')
else:
    TOKEN = os.getenv('MAIN_BASE_TOKEN')

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher()
