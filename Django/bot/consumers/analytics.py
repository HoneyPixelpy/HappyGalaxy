# Django/bot/consumers/kafka_analytics_consumer.py
import json
from datetime import datetime
import time
from typing import Dict

from django.db import transaction
from loguru import logger
from pika.exceptions import AMQPConnectionError, ConnectionClosedByBroker, AMQPChannelError, ChannelClosedByBroker
from pika import BlockingConnection
from pika.adapters.blocking_connection import BlockingChannel

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
        self.connection: Optional[BlockingConnection] = None
        self.channel: Optional[BlockingChannel] = None
        self.running = False
        self.queues = ['game-actions', 'user-actions', 'shop-actions', 'quest-actions']
        self.reconnect_delay = 5  # секунды между попытками переподключения
        self.max_reconnect_attempts = 10
                
    def connect(self) -> bool:
        """Установка соединения с RabbitMQ с очисткой очередей."""
        attempt = 0
        
        while attempt < self.max_reconnect_attempts and self.running:
            try:
                logger.info(f"🔗 Connecting to RabbitMQ (attempt {attempt + 1}/{self.max_reconnect_attempts})...")
                
                self.connection = BlockingConnection(self.connection_params)
                self.channel = self.connection.channel()
                
                # Настройка QoS
                self.channel.basic_qos(prefetch_count=1)
                
                # ⚠️ Сначала удаляем очереди если нужно
                for queue in self.queues:
                    try:
                        self.channel.queue_delete(queue=queue)
                        logger.info(f"🗑️ Deleted queue: {queue}")
                    except ChannelClosedByBroker:
                        # Очередь не существует - это нормально
                        pass
                    except Exception as e:
                        logger.debug(f"Could not delete queue {queue}: {e}")
                
                # Создаем очереди с новыми параметрами
                for queue in self.queues:
                    self.channel.queue_declare(
                        queue=queue,
                        durable=True,
                        arguments={
                            'x-message-ttl': 604800000,
                            'x-max-length': 10000,
                            'x-overflow': 'drop-head'
                        }
                    )
                
                logger.info("✅ Successfully connected to RabbitMQ")
                return True
                
            except (AMQPConnectionError, ConnectionClosedByBroker) as e:
                attempt += 1
                logger.warning(f"⚠️ Connection failed: {e}")
                
                if attempt < self.max_reconnect_attempts:
                    logger.info(f"🔄 Retrying in {self.reconnect_delay} seconds...")
                    time.sleep(self.reconnect_delay)
                else:
                    logger.error(f"❌ Max reconnection attempts reached")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Unexpected connection error: {e}")
                return False
        
        return False
    
    def ensure_connection(self) -> bool:
        """Проверка и восстановление соединения."""
        if self.connection is None or self.connection.is_closed:
            logger.warning("⚠️ Connection lost, reconnecting...")
            return self.connect()
        
        if self.channel is None or self.channel.is_closed:
            try:
                self.channel = self.connection.channel()
                self.channel.basic_qos(prefetch_count=10)
                return True
            except Exception as e:
                logger.error(f"❌ Failed to recreate channel: {e}")
                return False
        
        return True
    
    def start_consuming(self) -> None:
        """
        Основной цикл потребления сообщений с обработкой переподключений.
        """
        self.running = True
        
        while self.running:
            if not self.ensure_connection():
                logger.error("❌ Failed to establish connection, retrying...")
                time.sleep(self.reconnect_delay)
                continue
            
            try:
                logger.info("🚀 Starting RabbitMQ analytics consumer...")
                
                # Настраиваем потребителей для каждой очереди
                for queue in self.queues:
                    self.channel.basic_consume(
                        queue=queue,
                        on_message_callback=self._on_message_callback_wrapper,
                        auto_ack=False
                    )
                
                logger.info(f"📥 Listening on queues: {self.queues}")
                
                # Неблокирующий цикл с таймаутом
                while self.running and self.connection and self.connection.is_open:
                    try:
                        self.connection.process_data_events(time_limit=1)  # Таймаут 1 секунда
                    except (AMQPConnectionError, AMQPChannelError) as e:
                        logger.warning(f"⚠️ Connection error in process loop: {e}")
                        break
                    except Exception as e:
                        logger.error(f"❌ Unexpected error in process loop: {e}")
                        time.sleep(1)  # Защита от busy loop
                
                if self.running:
                    logger.warning("⚠️ Connection lost, reconnecting...")
                    
            except KeyboardInterrupt:
                logger.info("🛑 Consumer stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Consumer error: {e}")
                time.sleep(self.reconnect_delay)
        
        self.close_connection()
    
    def _on_message_callback_wrapper(self, channel, method, properties, body):
        """
        Обертка для callback с обработкой ошибок соединения.
        """
        try:
            self._on_message_callback(channel, method, properties, body)
        except (AMQPConnectionError, AMQPChannelError) as e:
            logger.error(f"❌ Channel error in callback: {e}")
            raise  # Перебрасываем для обработки в основном цикле
    
    def _on_message_callback(self, channel, method, properties, body):
        """
        Callback для обработки входящих сообщений.
        """
        start_time = time.time()
        
        try:
            # Проверяем соединение перед обработкой
            if not self.ensure_connection():
                logger.error("❌ Cannot process message - no connection")
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                return
            
            event_data = json.loads(body.decode('utf-8'))
            queue_name = method.routing_key
            
            logger.debug(f"📨 Received message from {queue_name}: {event_data.get('event_type', 'unknown')}")
            
            success = self.process_event_with_ack(
                channel, 
                method, 
                queue_name, 
                event_data
            )
            
            processing_time = time.time() - start_time
            
            if success:
                logger.debug(f"✅ Processed {queue_name} in {processing_time:.2f}s")
            else:
                logger.warning(f"⚠️ Failed to process {queue_name} after {processing_time:.2f}s")
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error: {e}")
            # Некорректное сообщение - не ставить обратно в очередь
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(f"❌ Unexpected error in callback: {e}")
            # Временная ошибка - поставить обратно в очередь
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def process_event_with_ack(self, channel, method, queue_name, event_data) -> bool:
        """
        Обработка события с транзакцией и ручным подтверждением.
        """
        try:
            # Лимит времени на обработку
            processing_start = time.time()
            max_processing_time = 30  # секунд
            
            with transaction.atomic():
                today = datetime.now().date()
                summary = super().get_analytics_summary(today)
                success = self.process_event(queue_name, summary, event_data)
                
                processing_time = time.time() - processing_start
                
                if processing_time > max_processing_time:
                    logger.warning(f"⚠️ Slow processing: {processing_time:.2f}s for {queue_name}")
                
                if success:
                    # Подтверждаем только после успешной записи в БД
                    channel.basic_ack(delivery_tag=method.delivery_tag)
                    
                    # Периодически фиксируем соединение
                    if random.random() < 0.01:  # 1% chance
                        self.connection.process_data_events()
                    
                    return True
                else:
                    # Отклоняем без повторной постановки в очередь
                    channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Transaction failed: {e}")
            # Временная ошибка БД - ставим обратно в очередь
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            
            # Задержка перед следующей попыткой
            time.sleep(1)
            
            return False
    
    def process_event(self, queue_name, summary, event_data) -> bool:
        """Обработка различных типов событий с таймаутом."""
        try:
            # Ограничение времени обработки
            import signal
            
            class TimeoutException(Exception):
                pass
            
            def timeout_handler(signum, frame):
                raise TimeoutException("Processing timeout")
            
            # Устанавливаем таймаут (только для Unix-систем)
            try:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(25)  # 25 секунд
                
                if queue_name == 'shop-actions':
                    result = super().process_shop_purchase(summary, event_data)
                elif queue_name == 'quest-actions':
                    result = super().process_quest_action(summary, event_data)
                elif queue_name == 'game-actions':
                    result = super().process_game_action(summary, event_data)
                elif queue_name == 'user-actions':
                    result = super().process_user_action(summary, event_data)
                else:
                    logger.warning(f"Unknown queue: {queue_name}")
                    result = True  # Подтверждаем неизвестные очереди
                
                signal.alarm(0)  # Сбрасываем таймер
                return result
                
            except TimeoutException:
                logger.error(f"⏰ Processing timeout for {queue_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing {queue_name}: {e}")
            return False
    
    def close_connection(self):
        """Закрытие соединения с RabbitMQ."""
        try:
            if self.channel and self.channel.is_open:
                self.channel.close()
        except Exception as e:
            logger.debug(f"Error closing channel: {e}")
        
        try:
            if self.connection and self.connection.is_open:
                self.connection.close()
        except Exception as e:
            logger.debug(f"Error closing connection: {e}")
        
        self.connection = None
        self.channel = None
        logger.info("🔌 RabbitMQ connection closed")
    
    def stop_consuming(self):
        """Остановка потребителя."""
        logger.info("🛑 Stopping consumer...")
        self.running = False
        
        if self.channel and self.channel.is_open:
            try:
                self.channel.stop_consuming()
            except Exception as e:
                logger.debug(f"Error stopping consumption: {e}")
        
        self.close_connection()
