# utils/rabbitmq_producer.py
import json
import os

from pika import ConnectionParameters, PlainCredentials, BlockingConnection
from pika.exceptions import AMQPConnectionError
from loguru import logger


class RabbitMQBackupProducer:
    def __init__(self):
        self.connection_params = ConnectionParameters(
            host=os.getenv('RABBITMQ_HOST', 'rabbitmq'),
            port=int(os.getenv('RABBITMQ_PORT', 5672)),
            credentials=PlainCredentials(
                os.getenv('RABBITMQ_USER', 'guest'),
                os.getenv('RABBITMQ_PASSWORD', 'guest')
            )
        )
    
    def send_backup_message(self, backup_data):
        """Отправка backup в RabbitMQ с гарантией доставки"""
        try:
            with BlockingConnection(self.connection_params) as connection:
                with connection.channel() as channel:
                    channel.queue_declare(queue='backup_queue') 
                    
                    channel.basic_publish(
                        exchange='',
                        routing_key='backup_queue',
                        body=json.dumps(backup_data, ensure_ascii=False)
                    )
                    logger.info("✅ Backup message sent to RabbitMQ")
            
        except AMQPConnectionError:
            logger.error("❌ Failed to connect to RabbitMQ")
            raise
        except Exception as e:
            logger.exception(f"❌ Failed to send to RabbitMQ: {e}")
            raise

