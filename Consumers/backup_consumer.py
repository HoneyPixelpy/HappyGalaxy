import asyncio
import json
import base64
import os
from pathlib import Path
import time
from loguru import logger
from aiogram import types, Bot

from dotenv import load_dotenv
import pika

BASE_DIR = Path(__file__).resolve().parent

load_dotenv()


class BackupConsumer:
    def __init__(self):
        self.connection_params = pika.ConnectionParameters(
            host=os.getenv('RABBITMQ_HOST', 'localhost'),
            port=int(os.getenv('RABBITMQ_PORT', 5672)),
            credentials=pika.PlainCredentials(
                os.getenv('RABBITMQ_USER', 'guest'),
                os.getenv('RABBITMQ_PASSWORD', 'guest')
            )
        )

    def start_consuming(self):
        """Запуск потребителя backup сообщений"""
        with pika.BlockingConnection(self.connection_params) as connection:
            with connection.channel() as channel:
                # Объявляем очередь
                channel.queue_declare(queue='backup_queue')
                channel.basic_qos(prefetch_count=1)
                
                logger.info("✅ Connected to RabbitMQ")
                logger.info("🚀 Backup Consumer started. Waiting for messages...")
                
                channel.basic_consume(
                    queue='backup_queue',
                    on_message_callback=self.callback
                )
                
                channel.start_consuming()
        
    def callback(self, ch, method, properties, body):
        """Callback для обработки сообщений"""
        try:
            logger.info(f"📨 Received message, body type: {type(body)}")
            
            # Декодируем сообщение
            if isinstance(body, bytes): body_str = body.decode('utf-8')
            else:                       body_str = str(body)
            
            # Запускаем с новым event loop
            asyncio.run(
                self.process_with_fresh_bot(
                    json.loads(body_str)
                    )
                )
            
            # Подтверждаем обработку
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info("✅ Message processed and acknowledged")
            
        except Exception as e:
            logger.exception(f"❌ Error processing: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag)
            
    async def process_with_fresh_bot(self, message_data):
        """Создаем новый экземпляр бота для каждого сообщения"""
        await self.process_backup_message(
            message_data, 
            Bot(
                token=os.getenv('TEST_TOKEN') if os.getenv('DEBUG') else os.getenv('TOKEN')
                )
            )

    async def process_backup_message(self, backup_data, bot: Bot):
        """Обработка backup сообщения"""
        chat_id = backup_data['chat_id']
        formatted_time = backup_data['formatted_time']
        filename = f'postgres_backup_{formatted_time}.sql'
        backup_path = BASE_DIR / filename
        
        content = backup_data['content'].encode('utf-8')
        
        try:
            logger.info(f"Processing backup task {formatted_time}")
            
            # Сохраняем временный файл
            with open(backup_path, 'wb') as f:
                f.write(content)
            
            # Проверяем что файл создан
            if not backup_path.exists() or backup_path.stat().st_size == 0:
                raise ValueError("Backup file is empty or not created")
            
            # Отправляем в Telegram
            await bot.send_document(
                chat_id=chat_id,
                document=types.FSInputFile(
                    path=backup_path, 
                    filename=filename
                ),
                caption=backup_data['caption']
            )
            
            logger.info(f"✅ Backup {formatted_time} sent successfully")
            
        except Exception as e:
            logger.exception(f"❌ Failed to process backup: {e}")
            raise  # Пробрасываем исключение для обработки на уровне message
        finally:
            # Удаляем временный файл
            await self._delete_temporary_file(backup_path)
    
    async def _delete_temporary_file(self, backup_path):
        """Удаляем временный файл"""
        if 'backup_path' in locals() and backup_path.exists():
            try:
                backup_path.unlink()
                logger.debug("🧹 Temporary file cleaned up")
            except Exception as e:
                logger.warning(f"⚠️ Could not delete temp file: {e}")

if __name__ == "__main__":
    time.sleep(30)
    consumer = BackupConsumer()
    consumer.start_consuming()
