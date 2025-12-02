# Django/bot/consumers/kafka_analytics_consumer.py
import json
from datetime import datetime
from typing import Dict

from django.db import transaction
from loguru import logger
from pika.exceptions import AMQPConnectionError, AMQPChannelError
from pika import BlockingConnection

from .config import RabbitMQConfig
from bot.models import *


class RabbitMQAnalyticsBD:

    def get_analytics_summary(self, today) -> AnalyticsSummary:
        try:
            return AnalyticsSummary.objects.get(date=today)
        except AnalyticsSummary.DoesNotExist:
            return AnalyticsSummary.objects.create(date=today)

    @logger.catch
    def process_shop_purchase(
        self, 
        summary: AnalyticsSummary, 
        event_data: Dict
        ):
        user_id = event_data['user_id']
        
        product = Pikmi_Shop.objects.get(pk=event_data['product_id'])
        
        product_stats, _ = ShopStats.objects.get_or_create(
            product=product,
            summary=summary
        )
        
        product_stats.items_sold += 1
        product_stats.total_revenue += product.price
        
        if user_id not in product_stats.unique_buyers:
            product_stats.unique_buyers.append(user_id)
        
        product_stats.save()
        
        return True

    def add_reward(
        self, 
        user_id: int, 
        quest: Quests
        ) -> float:
        """
        Расчет награды
        """
        if (quest.type_quest == "daily" and 
            quest.quest_data.scale_type == 'x_count_use'
            ):
            user = Users.objects.get(user_id=user_id)
            use_quest_obj = UseQuests.objects.filter(user=user, quest=quest).first()
            return quest.quest_data.reward_starcoins * use_quest_obj.count_use
        else:
            return quest.quest_data.reward_starcoins

    def process_quest_action(
        self, 
        summary: AnalyticsSummary, 
        event_data: Dict
        ):
        """
        fast_success
        attempt
        success
        delete
        """
        user_id = event_data['user_id']
        quest_id = event_data['quest_id']
        action = event_data['action']
        
        quest = Quests.objects.get(pk=quest_id)
        
        quest_stats, _ = QuestStats.objects.get_or_create(
            quest=quest,
            summary=summary
        )
        
        if action == 'pending':
            quest_stats.attempts += 1
            if not quest.success_admin:
                quest_stats.success += 1
                quest_stats.total_rewards += self.add_reward(user_id, quest)
        
        elif action == 'fast_success':
            quest_stats.attempts += 1
            quest_stats.success += 1
            quest_stats.total_rewards += self.add_reward(user_id, quest)
                
        elif action == 'approved':
            quest_stats.success += 1
            quest_stats.total_rewards += self.add_reward(user_id, quest)
                
        elif action == 'rejected' or action == 'auto_rejected':
            quest_stats.failed += 1
            
        else:
            logger.error(f"Неизвестный тип события: {action}")
            return
        
        if user_id not in quest_stats.unique_users:
            quest_stats.unique_users.append(user_id)
        
        quest_stats.save()
        
        return True

    def process_game_action(
        self, 
        summary: AnalyticsSummary, 
        event_data: Dict
        ):
        user_id = event_data['user_id']
        win_starcoins = event_data['win_starcoins']
        game = event_data['game']
        
        quest_stats, _ = GamesStats.objects.get_or_create(
            summary=summary
        )
        
        if game == 'lumberjack':
            quest_stats.lumberjack_clicks += 1
            
            quest_stats.lumberjack_profit += win_starcoins
            if user_id not in quest_stats.lumberjack_unique_users:
                quest_stats.lumberjack_unique_users.append(user_id)
        
        elif game == 'geohunter':
            if win_starcoins:
                quest_stats.geohunter_true += 1
                quest_stats.geohunter_profit += win_starcoins
            else:
                quest_stats.geohunter_false += 1
                
            if user_id not in quest_stats.geohunter_unique_users:
                quest_stats.geohunter_unique_users.append(user_id)
        
        quest_stats.save()
        
        return True

    def process_user_action(
        self, 
        summary: AnalyticsSummary, 
        event_data: Dict
        ):
        """
        Записываем действие пользователя
        """
        user_id = event_data['user_id']
        event_type = event_data['event_type']
        
        text = event_data['text']
        timestamp = event_data['timestamp']
        # timestamp = datetime.fromisoformat(event_data['timestamp'])
        
        if event_type == 'callback_query':
            data = event_data['data']
            CallbackAction.objects.create(
                summary=summary,
                user_id=user_id,
                timestamp=timestamp,
                text=text,
                data=data
            )
        elif event_type == 'message':
            content_type = event_data['content_type']
            MessageAction.objects.create(
                summary=summary,
                user_id=user_id,
                timestamp=timestamp,
                text=text,
                content_type=content_type
            )
                
        return True


class RabbitMQAnalyticsConsumer(RabbitMQAnalyticsBD):
    def __init__(self):
        self.connection_params = RabbitMQConfig.connection_params
        self.connection = None
        self.channel = None
        self.running = False
        self.queues = ['game-actions', 'user-actions', 'shop-actions', 'quest-actions']
        # self.queues = RabbitMQConfig.TOPICS.__dict__.values()
        logger.debug(f"📤 Queues: {self.queues}")
        
    def connect(self):
        """Установка соединения с RabbitMQ"""
        try:
            self.connection = BlockingConnection(self.connection_params)
            self.channel = self.connection.channel()
            
            for queue in self.queues:
                self.channel.queue_declare(
                    queue=queue, 
                    durable=True,
                    arguments={
                        'x-message-ttl': 604800000,
                        'x-max-length': 100000
                    }
                )
                
            # Настраиваем QoS для контроля количества неподтвержденных сообщений
            self.channel.basic_qos(prefetch_count=1)
            
            logger.info("✅ Connected to RabbitMQ successfully")
            return True
            
        except AMQPConnectionError as e:
            logger.error(f"❌ Failed to connect to RabbitMQ: {e}")
            return False

    def start_consuming(self) -> None:
        """
        Основной цикл потребления сообщений
        """
        self.running = True
        
        if not self.connect():
            logger.error("❌ Failed to establish RabbitMQ connection")
            return
        
        logger.info("🚀 Starting RabbitMQ analytics consumer...")
        
        # Настраиваем потребителей для каждой очереди
        for queue in self.queues:
            self.channel.basic_consume(
                queue=queue,
                on_message_callback=self._on_message_callback,
                auto_ack=False  # Ручное подтверждение
            )
        
        try:
            logger.info(f"📥 Listening on queues: {self.queues}")
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info("🛑 Consumer stopped by user")
        except Exception as e:
            logger.error(f"❌ Consumer error: {e}")
        finally:
            self.close_connection()

    def _on_message_callback(self, channel, method, properties, body):
        """
        Callback для обработки входящих сообщений
        """
        try:
            event_data = json.loads(body.decode('utf-8'))
            queue_name = method.routing_key
            logger.debug(event_data)
            logger.debug(queue_name)
            
            success = self.process_event_with_ack(
                channel, 
                method, 
                queue_name, 
                event_data
            )
            logger.debug(success)
            
            if success:
                logger.debug(f"✅ Processed message from {queue_name}: {event_data.get('event_type')}")
            else:
                logger.error(f"❌ Failed to process message from {queue_name}")
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error: {e}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(f"❌ Unexpected error in callback: {e}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def process_event_with_ack(self, channel, method, queue_name, event_data):
        """
        Обработка события с транзакцией и ручным подтверждением
        """
        try:
            with transaction.atomic():
                today = datetime.now().date()
                summary = super().get_analytics_summary(today)
                success = self.process_event(queue_name, summary, event_data)
                
                if success:
                    # Подтверждаем только после успешной записи в БД
                    channel.basic_ack(delivery_tag=method.delivery_tag)
                    return True
                else:
                    # Отклоняем без повторной постановки в очередь
                    channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Transaction failed: {e}")
            # Отклоняем с повторной постановкой в очередь для временных ошибок
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            return False

    def process_event(self, queue_name, summary, event_data):
        """Обработка различных типов событий"""
        logger.debug(f"Processing event from {queue_name}: {event_data}")
        
        try:
            if queue_name == 'shop-actions':
                return super().process_shop_purchase(summary, event_data)
            elif queue_name == 'quest-actions':
                return super().process_quest_action(summary, event_data)
            elif queue_name == 'game-actions':
                return super().process_game_action(summary, event_data)
            elif queue_name == 'user-actions':
                return super().process_user_action(summary, event_data)
            else:
                logger.warning(f"Unknown queue: {queue_name}")
                return True  # Подтверждаем неизвестные очереди
                
        except Exception as e:
            logger.error(f"Error processing {queue_name}: {e}")
            return False

    def close_connection(self):
        """Закрытие соединения с RabbitMQ"""
        try:
            if self.channel and self.channel.is_open:
                self.channel.close()
            if self.connection and self.connection.is_open:
                self.connection.close()
            logger.info("🔌 RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")

    def stop_consuming(self):
        """Остановка потребителя"""
        self.running = False
        if self.channel and self.channel.is_open:
            self.channel.stop_consuming()
        self.close_connection()


