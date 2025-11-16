import json
from typing import Any, Callable, Dict, List, Optional, Tuple
from loguru import logger

from Redis.main import RedisManager


class MainBotService:
    
    def __init__(self):
        self.redis_client = RedisManager().get_redis()
            
    def send_continue_registration(
        self,
        user_ids: List[int]
        ):
        """Отправить уведомление о новом ранге через Redis"""
        continue_registration_data = {
            'user_ids': user_ids
        }
        
        self.redis_client.rpush('bot:continue_registration', json.dumps(continue_registration_data))
        self.redis_client.publish('continue_registration_updates', "user:rang_upgraded")

    def send_old_quests(
        self,
        mailing_data: List[Dict]
        ):
        """Отправить уведомление о новом ранге через Redis"""
        old_quests_data = {
            'mailing_data': mailing_data
        }
        
        self.redis_client.rpush('bot:old_quests', json.dumps(old_quests_data))
        self.redis_client.publish('old_quests_deletes', "user:quests_deletes")


