import datetime
import json
import os

from GPTBot.config import DAILY_LIMIT, LIMITS_FILE, TIMEOUT
from loguru import logger
from VKBot.task.tg import TelegramSubscriptionChecker


# --- ХЕЛПЕРЫ ДЛЯ ЛИМИТОВ ---
def load_limits():
    if not os.path.exists(LIMITS_FILE):
        return {}
    with open(LIMITS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_limits(data):
    with open(LIMITS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


async def check_tg_invite(user_id):
    data = load_limits()
    user_id = str(user_id)
    now = datetime.datetime.now()
    now_timestamp = now.timestamp()
    today_str = now.strftime("%Y-%m-%d")

    # Получаем информацию о пользователе или создаем новую запись
    user_data: dict = data.get(
        user_id,
        {"usage": {}, "privilege": {"last_check": None, "is_subscribed": False}},
    )

    # Проверяем, нужно ли выполнять проверку подписки
    last_check_str = user_data["privilege"].get("last_check")
    need_check = True

    if last_check_str:
        last_check = datetime.datetime.strptime(last_check_str, "%Y-%m-%d")
        if (now - last_check) < datetime.timedelta(days=1):
            need_check = False

    if need_check or not user_data["privilege"]["is_subscribed"]:
        try:
            # Проверяем подписку пользователя
            is_subscribed = await TelegramSubscriptionChecker().get_chat_member(
                "@happiness34vlz", user_id
            )
            logger.debug(is_subscribed)
            # Обновляем данные о подписке
            user_data["privilege"].update(
                {
                    "is_subscribed": is_subscribed,
                    "last_check": today_str,
                    "last_check_timestamp": now_timestamp,
                }
            )

            # Сохраняем обновленные данные
            data[user_id] = user_data
            save_limits(data)

            return is_subscribed

        except Exception as e:
            logger.error(f"Error checking subscription: {e}")
            return user_data["privilege"].get("is_subscribed", False)
    else:
        return user_data["privilege"].get("is_subscribed", False)


def get_today():
    return datetime.datetime.now().strftime("%Y-%m-%d")


def check_and_inc(user_id, typ):
    data = load_limits()
    today = get_today()
    user_id = str(user_id)

    user: dict = data.get(user_id, {})
    usage = user.get("usage", {}).get(today, {}).get(typ, 0)

    if usage >= DAILY_LIMIT:
        return False

    user.setdefault("usage", {}).setdefault(today, {})[typ] = usage + 1
    data[user_id] = user
    save_limits(data)
    return True


def set_timeout(user_id):
    data = load_limits()
    user_id = str(user_id)
    now = datetime.datetime.now().timestamp()

    user = data.get(user_id, {})
    user["timeout"] = now
    data[user_id] = user
    save_limits(data)


def is_timeout(user_id):
    data = load_limits()
    user_id = str(user_id)
    user = data.get(user_id, {})
    last = user.get("timeout")

    if not last:
        return False

    now = datetime.datetime.now().timestamp()
    return (now - last) < TIMEOUT


def reset_limits(user_id):
    data = load_limits()
    user_id = str(user_id)

    if user_id in data:
        data[user_id]["usage"] = {}
        data[user_id]["timeout"] = None
        save_limits(data)
