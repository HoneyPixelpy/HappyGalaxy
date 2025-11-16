import asyncio
import os
from pathlib import Path

admins = [1894909159, 467011044] # 1894909159 , 467011044

bot_name = os.getenv("BOT_NAME") # GalaxyBot Second_Tests_Scripts_Bot happygalaxy_bot
photo_id = os.getenv("PHOTO_ID") # "AgACAgIAAxkBAAIIKGh9WAhIH8wkPBhxi4og3jSB2MBOAAKS-jEbmprpS9WUQI65t7QrAQADAgADeQADNgQ" # TEST "AgACAgIAAxkBAAI-O2h9Xo7e725pBopmLy4OnUijFcftAAKS-jEbmprpS8oGhSxDDj6JAQADAgADeQADNgQ"
debug = os.getenv("DEBUG")

log_chat = "-1002565986205" if not debug else "1894909159"
quests_chat = "-1002933684603" if not debug else "1894909159"
smm_chat = "-1003000387263" if not debug else "1894909159"
game_chat = "-1003000387263" if not debug else "1894909159"

BASE_DIR = Path(__file__).resolve().parent

file_lock = asyncio.Lock()
base_lock = asyncio.Lock()

entry_threshold_geo_hunt = 100 # NOTE сколько всего должно быть нафармлено старкоинов для вхождения в Гео Хантер
REDIS_URL = os.getenv("REDIS_URL")
