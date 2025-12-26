import json
from typing import Any, Callable, List, Optional, Tuple

from django.db.models import Q
from loguru import logger
from Redis.main import RedisManager


class RangService:

    def get_user_rang(self, user: "Users") -> Optional["Rangs"]:  # type: ignore
        """Получить текущий ранг пользователя"""
        from bot.models import Rangs

        try:
            return (
                Rangs.objects.filter(  # type: ignore
                    Q(_role=user._role) | Q(_role__isnull=True),
                    all_starcoins__lte=user.all_starcoins,
                )
                .order_by("-level")
                .first()
            )
        except Rangs.DoesNotExist:  # type: ignore
            return None

    def send_rang_notification(
        self,
        user: "Users",  # type: ignore
        current_rang: "Rangs",  # type: ignore
        previous_rang: "Rangs",  # type: ignore
        new_quests: bool,
    ):
        """Отправить уведомление о новом ранге через Redis"""
        redis_client = RedisManager().get_redis()
        notification_data = {
            "user_id": user.user_id,
            "new_rang_level": previous_rang.level,
            "new_rang_name": previous_rang.name,
            "new_rang_emoji": previous_rang.emoji,
            "old_level": current_rang.level,
            "all_starcoins": user.all_starcoins,
            "new_quests": new_quests,
        }

        # Сохраняем в Redis для обработки ботом
        redis_client.rpush("rang_notifications", json.dumps(notification_data))
        redis_client.publish("rang_updates", f"user:{user.user_id}:rang_upgraded")
