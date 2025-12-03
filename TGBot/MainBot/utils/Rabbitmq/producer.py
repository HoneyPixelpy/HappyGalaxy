# utils/rabbitmq_producer.py
import json

import pika
from loguru import logger

from .config import RabbitMQConfig
from MainBot.utils.MyModule.Functions import Func


class RabbitMQProducer:
        
    def produce_action(self, topic, backup_data):
        """Отправка backup в RabbitMQ с гарантией доставки"""
        try:
            with pika.BlockingConnection(RabbitMQConfig.connection_params) as connection:
                with connection.channel() as channel:
                    # channel.queue_declare(
                    #     queue=topic, 
                    #     durable=True,
                    #     arguments={
                    #         'x-message-ttl': 604800000,
                    #         'x-max-length': 100000
                    #     }
                    # ) 
                    
                    channel.basic_publish(
                        exchange='',
                        routing_key=topic,
                        body=json.dumps(backup_data, ensure_ascii=False)
                    )
            
        except Exception as e:
            logger.exception(f"❌ Failed to send to RabbitMQ: {e}")
            raise
    
    async def get_button_text(self, data, inline_keyboard):
            for row in inline_keyboard:
                for button in row:
                    if button.callback_data == data:
                        return button.text
    
    @logger.catch
    async def track_action(
        self, 
        event: 'TelegramObject', # type: ignore
        message: 'Message', # type: ignore
        from_user: 'User', # type: ignore
        ) -> None:
        if event.event_type == 'callback_query':
            button_text = await self.get_button_text(
                event.callback_query.data,
                message.reply_markup.inline_keyboard if message.reply_markup else []
                )
            event_data = {
                "user_id": from_user.id,
                "event_type": event.event_type,
                "text": button_text,
                "data": event.callback_query.data.split("|")[0],
                "timestamp": message.date.isoformat()
            }
        elif event.event_type == 'message':
            text, content_type, _, _ = \
                await Func.parsing_message(message)
            event_data = {
                "user_id": from_user.id,
                "event_type": event.event_type,
                "text": text or None,
                "content_type": content_type or 'text',
                "timestamp": message.date.isoformat()
            }
        else:
            logger.warning(event.event_type)
        
        self.produce_action(
            RabbitMQConfig.TOPICS.USER_ACTIONS,
            event_data
            )
    
    @logger.catch
    async def track_shop(
        self, 
        user_id: int,
        product_id: int
        ) -> None:
        event_data = {
            "user_id": user_id,
            "product_id": product_id
        }
        self.produce_action(
            RabbitMQConfig.TOPICS.SHOP_ACTIONS,
            event_data
            )
    
    @logger.catch
    async def track_quest(
        self, 
        user_id: int,
        quest_id: int,
        action: str
        ) -> None:
        event_data = {
            "user_id": user_id,
            "quest_id": quest_id,
            "action": action
        }
        self.produce_action(
            RabbitMQConfig.TOPICS.QUEST_ACTIONS,
            event_data
            )
    
    @logger.catch
    async def track_game(
        self, 
        user_id: int,
        win_starcoins: int,
        game: str
        ) -> None:
        event_data = {
            "user_id": user_id,
            "win_starcoins": win_starcoins,
            "game": game
        }
        self.produce_action(
            RabbitMQConfig.TOPICS.GAME_ACTIONS,
            event_data
            )
    
# NOTE можно еще сигмабусты отслеживать
